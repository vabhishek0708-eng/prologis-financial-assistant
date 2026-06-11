

import os
import json
import boto3
import warnings
import tempfile
warnings.filterwarnings("ignore")

# Load GCP credentials on Streamlit Cloud
gcp_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
if gcp_creds:
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(gcp_creds)
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = f.name
        print("GCP credentials loaded from environment")
    except Exception as e:
        print(f"GCP credentials error: {e}")

# ── Config ──
GCP_PROJECT  = "project-f47a88c6-9a3a-4b51-903"
GCP_LOCATION = "us-central1"
AWS_REGION   = "us-east-2"
S3_BUCKET    = "prologis-financial-assistant-362612348837"
REG_ENDPOINT = "prologis-regression-endpoint"
CLF_ENDPOINT = "prologis-classification-endpoint"
DB_URL = os.getenv("DB_URL", "postgresql://postgres:Ktvab%402k@localhost:5432/realestate_db")

# ════════════════════════════════════════════
# ADK TOOLS — each tool is a function the
# agent can call to get real data
# ════════════════════════════════════════════
AWS_KEY    = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET = os.getenv("AWS_SECRET_ACCESS_KEY")

def _s3():
    return boto3.client("s3",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_KEY,
        aws_secret_access_key=AWS_SECRET)

def _sm():
    return boto3.client("sagemaker-runtime",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_KEY,
        aws_secret_access_key=AWS_SECRET)

def get_portfolio_summary() -> dict:
    """
    Get a summary of the Prologis property portfolio from PostgreSQL.
    Returns total properties, revenue, net income, expenses by metro area.
    """
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            # Overall summary with financials JOIN
            result = conn.execute(text("""
                SELECT
                    COUNT(DISTINCT p.property_id)     AS total_properties,
                    SUM(f.revenue)                    AS total_revenue,
                    SUM(f.net_income)                 AS total_net_income,
                    SUM(f.expenses)                   AS total_expenses,
                    SUM(p.sq_footage)                 AS total_sqft
                FROM properties p
                JOIN financials f ON p.property_id = f.property_id
            """))
            row = result.fetchone()

            # Metro area breakdown
            metro = conn.execute(text("""
                SELECT p.metro_area,
                       SUM(f.revenue)    AS total_revenue,
                       SUM(f.net_income) AS total_net_income,
                       SUM(f.expenses)   AS total_expenses,
                       COUNT(*)          AS property_count
                FROM properties p
                JOIN financials f ON p.property_id = f.property_id
                GROUP BY p.metro_area
                ORDER BY total_revenue DESC
            """))
            metro_data = [
                {"metro": r[0], "revenue": float(r[1] or 0),
                 "net_income": float(r[2] or 0), "expenses": float(r[3] or 0),
                 "count": r[4]}
                for r in metro.fetchall()
            ]

            # Property type breakdown
            types = conn.execute(text(
                "SELECT property_type, COUNT(*) FROM properties GROUP BY property_type"
            ))
            type_data = {r[0]: r[1] for r in types.fetchall()}

        return {
            "total_properties":  row[0],
            "total_revenue_usd": float(row[1] or 0),
            "total_net_income":  float(row[2] or 0),
            "total_expenses":    float(row[3] or 0),
            "total_sqft":        float(row[4] or 0),
            "by_metro":          metro_data,
            "by_type":           type_data,
        }
    except Exception as e:
        return {"error": str(e)}


def search_properties(query: str) -> list:
    """
    Search properties in the PostgreSQL database by address, type, or metro area.
    Includes financial data (revenue, net_income, expenses) from JOIN with financials table.
    Args:
        query: search term (address, city, or property type e.g. "Chicago", "Industrial")
    Returns list of matching properties with financial details.
    """
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT p.address, p.property_type, p.metro_area,
                       p.sq_footage, f.revenue, f.net_income, f.expenses
                FROM properties p
                JOIN financials f ON p.property_id = f.property_id
                WHERE LOWER(p.address)      LIKE :q
                   OR LOWER(p.property_type) LIKE :q
                   OR LOWER(p.metro_area)    LIKE :q
                ORDER BY f.revenue DESC
                LIMIT 10
            """), {"q": f"%{query.lower()}%"})
            rows = result.fetchall()
        return [
            {
                "address":    r[0], "type":       r[1],
                "metro":      r[2], "sqft":       r[3],
                "revenue":    float(r[4] or 0),
                "net_income": float(r[5] or 0),
                "expenses":   float(r[6] or 0),
            }
            for r in rows
        ]
    except Exception as e:
        return [{"error": str(e)}]


def get_sec_filings() -> dict:
    try:
        obj = _s3().get_object(Bucket=S3_BUCKET, Key="data/sec_mock.json")
        return json.loads(obj["Body"].read())
    except Exception as e:
        return {"error": str(e)}

def get_press_releases(limit: int = 3) -> list:
    try:
        obj = _s3().get_object(Bucket=S3_BUCKET, Key="data/press_releases.json")
        data = json.loads(obj["Body"].read())
        return data[:limit] if isinstance(data, list) else []
    except Exception as e:
        return [{"error": str(e)}]

def predict_property_revenue(
    median_income: float,
    house_age: float,
    avg_rooms: float,
    avg_bedrooms: float,
    population: float,
    avg_occupancy: float,
    latitude: float,
    longitude: float,
) -> dict:
    """
    Predict property revenue using the SageMaker regression endpoint.
    Args:
        median_income: median income in block group (scaled, e.g. 5.0)
        house_age: average house age in years
        avg_rooms: average number of rooms per house
        avg_bedrooms: average number of bedrooms per house
        population: block group population
        avg_occupancy: average occupancy rate
        latitude: property latitude
        longitude: property longitude
    Returns predicted annual revenue in USD.
    """
    try:
        sm = _sm()
        features = [median_income, house_age, avg_rooms, avg_bedrooms,
                    population, avg_occupancy, latitude, longitude]
        resp = sm.invoke_endpoint(
            EndpointName=REG_ENDPOINT,
            ContentType="application/json",
            Body=json.dumps({"features": features}),
        )
        result = json.loads(resp["Body"].read())
        pred   = result.get("prediction", [0])
        if isinstance(pred, list): pred = pred[0]
        return {"predicted_revenue_usd": float(pred) * 100000}
    except Exception as e:
        return {"error": str(e)}


def classify_investment_risk(
    age: int, balance: float, duration: int, campaign: int,
    job: str = "management", education: str = "tertiary",
) -> dict:
    """
    Classify investment risk level using the SageMaker classification endpoint.
    Args:
        age: client age
        balance: account balance in USD
        duration: last contact duration in seconds
        campaign: number of contacts in this campaign
        job: client job type
        education: education level
    Returns risk level (Low/Medium/High) with probabilities.
    """
    try:
        job_map = {"admin.":0,"blue-collar":1,"entrepreneur":2,"housemaid":3,
                   "management":4,"retired":5,"self-employed":6,"services":7,
                   "student":8,"technician":9,"unemployed":10,"unknown":11}
        edu_map = {"primary":0,"secondary":1,"tertiary":2,"unknown":3}
        features = [age, job_map.get(job,4), 1, edu_map.get(education,2),
                    0, balance, 0, 0, 0, 3, 5, duration, campaign, -1, 0, 3]

        sm = _sm()
        resp = sm.invoke_endpoint(
            EndpointName=CLF_ENDPOINT,
            ContentType="application/json",
            Body=json.dumps({"features": features}),
        )
        result   = json.loads(resp["Body"].read())
        proba    = result.get("probabilities", [[0.5, 0.5]])
        prob_yes = float(proba[0][1]) if isinstance(proba[0], list) else float(proba[1])
        risk     = "Low" if prob_yes > 0.7 else "Medium" if prob_yes > 0.45 else "High"
        return {
            "risk_level":    risk,
            "probability_low_risk":  round(prob_yes * 100, 1),
            "probability_high_risk": round((1 - prob_yes) * 100, 1),
        }
    except Exception as e:
        return {"error": str(e)}


# ════════════════════════════════════════════
# ADK AGENT SETUP
# ════════════════════════════════════════════

def build_agent():
    """Build and return the Prologis ADK agent with all tools."""
    try:
        import vertexai
        from google.adk.agents import Agent
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService

        vertexai.init(project=GCP_PROJECT, location=GCP_LOCATION)

        agent = Agent(
            name="prologis_financial_assistant",
            model="gemini-2.5-flash",
            description=(
                "You are a financial analyst assistant for Prologis Inc., "
                "a leading industrial REIT (NYSE: PLD). You have access to tools "
                "to query the property database, retrieve SEC filings from AWS S3, "
                "get press releases, and run ML predictions on SageMaker endpoints. "
                "Always use the appropriate tool to get real data before answering."
            ),
            instruction=(
                "For property questions: use search_properties or get_portfolio_summary. "
                "For financial/SEC questions: use get_sec_filings. "
                "For news/announcements: use get_press_releases. "
                "For revenue predictions: use predict_property_revenue. "
                "For risk assessment: use classify_investment_risk. "
                "Be concise, data-driven, and professional."
            ),
            tools=[
                get_portfolio_summary,
                search_properties,
                get_sec_filings,
                get_press_releases,
                predict_property_revenue,
                classify_investment_risk,
            ],
        )
        return agent
    except Exception as e:
        print(f"ADK agent build error: {e}")
        return None


# Singleton agent instance
_agent   = None
_runner  = None
_session = None

def ask_agent(user_message: str) -> str:
    """
    Send a message to the Prologis ADK agent and get a response.
    Falls back to direct Gemini if ADK is unavailable.
    """
    global _agent, _runner, _session

    try:
        from google.adk.agents import Agent
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        import vertexai
        vertexai.init(project=GCP_PROJECT, location=GCP_LOCATION)

        if _agent is None:
            _agent = build_agent()

        if _agent is None:
            raise Exception("Agent not built")

        session_service = InMemorySessionService()
        runner = Runner(
            agent=_agent,
            app_name="prologis_assistant",
            session_service=session_service,
        )

        session = session_service.create_session(
            app_name="prologis_assistant",
            user_id="streamlit_user",
        )

        from google.adk.types import Content, Part
        response_text = ""
        for event in runner.run(
            user_id="streamlit_user",
            session_id=session.id,
            new_message=Content(parts=[Part(text=user_message)]),
        ):
            if event.is_final_response():
                response_text = event.content.parts[0].text
                break

        return response_text if response_text else "No response from agent."

    except Exception as e:
        print(f"ADK FAILED: {e}")
        try:
            import vertexai
            from vertexai.generative_models import GenerativeModel
            vertexai.init(project=GCP_PROJECT, location=GCP_LOCATION)
            sec = get_sec_filings()
            ctx = f"SEC Data: {json.dumps(sec)[:600]}" if sec and "error" not in sec else ""
            prompt = f"You are a Prologis financial analyst. {ctx}\nUser: {user_message}"
            return GenerativeModel("gemini-2.5-flash").generate_content(prompt).text
        except Exception as e2:
            return f"AI service temporarily unavailable. Please try again. Error: {str(e2)[:100]}"


if __name__ == "__main__":
    print("Testing Prologis ADK Agent...")
    print()

    tests = [
        "What is the total portfolio revenue?",
        "Find industrial properties in Chicago",
        "What was Prologis revenue in Q4 2024?",
        "Summarize the latest press releases",
    ]

    for q in tests:
        print(f"Q: {q}")
        ans = ask_agent(q)
        print(f"A: {ans[:300]}")
        print()
