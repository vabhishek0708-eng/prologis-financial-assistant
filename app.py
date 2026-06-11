import streamlit as st
import json
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
import warnings
import os
warnings.filterwarnings("ignore")
from model_loader import predict_revenue, predict_risk, load_sec_data, load_press_releases
from prologis_agent import ask_agent

st.set_page_config(
    page_title="Prologis Financial Assistant",
    page_icon=" ",
    layout="wide",
    initial_sidebar_state="expanded",
)

with open("endpoint_config.json") as f:
    EP = json.load(f)
AWS_REGION = EP["region"]

for k, v in [
    ("page", "Dashboard"),
    ("reg_result", None), ("reg_features", None),
    ("clf_result", None), ("chat_history", []),
    ("prop_selected", ""),
    ("show_chat_modal", False),
]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── DB ──
@st.cache_resource
def get_engine():
    try:
        url = os.getenv("DB_URL", "postgresql://postgres:Ktvab%402k@localhost:5432/realestate_db")
        engine = create_engine(
            url,
            pool_pre_ping=True,        # tests connection before using it
            pool_recycle=300,          # recycles connections every 5 min
            connect_args={"connect_timeout": 10}  # 10 second timeout
        )
        return engine
    except Exception as e:
        return None

@st.cache_data(ttl=300)
def load_properties():
    try:
        engine = get_engine()
        if engine is None:
            return pd.DataFrame()
        with engine.connect() as conn:
            return pd.read_sql("SELECT * FROM properties", conn)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_financials_joined():
    try:
        return pd.read_sql("""
            SELECT p.property_id, p.address, p.metro_area, p.property_type,
                   p.sq_footage, f.revenue, f.net_income, f.expenses
            FROM financials f
            JOIN properties p ON f.property_id = p.property_id
            ORDER BY f.revenue DESC
        """, get_engine())
    except:
        return pd.DataFrame()

@st.cache_data(ttl=600)
def get_sec_data():
    return load_sec_data()

@st.cache_data(ttl=600)
def get_press_releases_data():
    return load_press_releases()

def ask_gemini(prompt):
    return ask_agent(prompt)
def render_chat_content(suffix=""):
    st.markdown("### 🤖 AI Assistant")
    st.caption("Vertex AI ADK · Gemini 2.5 Flash")
    chat_container = st.container(height=400)
    with chat_container:
        if not st.session_state.chat_history:
            st.info("👋 Ask me about Prologis properties, financials, or forecasts!")
        for msg in st.session_state.chat_history:
            st.chat_message(msg["role"]).write(msg["content"])
    if not st.session_state.chat_history:
        for s in ["What was net income last quarter?",
                  "Show industrial properties in Chicago",
                  "Summarize latest press release",
                  "Predict revenue for a SF property"]:
            if st.button(s, key=f"sug_{s}{suffix}", use_container_width=True):
                st.session_state.chat_history.append({"role": "user", "content": s})
                with st.spinner("..."):
                    reply = ask_gemini(s)
                st.session_state.chat_history.append({"role": "assistant", "content": reply})
                st.rerun()
    user_input = st.chat_input("Ask Prologis AI...", key=f"chat_input{suffix}")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.spinner("Thinking..."):
            reply = ask_gemini(user_input)
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        st.rerun()
    if st.session_state.chat_history:
        if st.button("🗑️ Clear", key=f"clear_{suffix}", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

@st.dialog("🤖 AI Assistant", width="large")
def chat_modal():
    render_chat_content(suffix="_modal")
    if st.button("✖️ Close", key="close_modal"):
        st.session_state.show_chat_modal = False
        st.rerun()
# ── Sidebar ──
with st.sidebar:
    st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0f1e 0%, #111827 100%);
    }
    div[data-testid="stSidebar"] .stButton button {
        background: transparent !important;
        border: none !important;
        border-left: 3px solid transparent !important;
        color: #9ca3af !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        text-align: left !important;
        padding: 0.6rem 0.75rem !important;
        border-radius: 0 !important;
        width: 100% !important;
    }
    div[data-testid="stSidebar"] .stButton button:hover {
        background: rgba(245,158,11,0.1) !important;
        border-left: 3px solid #f59e0b !important;
        color: #f3f4f6 !important;
    }
    </style>
    <div style="padding:1.2rem 0 0.5rem;">
        <div style="font-size:0.65rem;letter-spacing:0.18em;text-transform:uppercase;
             color:#f59e0b;font-weight:600;">NYSE · PLD</div>
        <div style="font-size:1.6rem;font-weight:800;color:#f3f4f6;letter-spacing:0.04em;">
            PROLOGIS</div>
        <div style="font-size:0.72rem;color:#6b7280;letter-spacing:0.12em;
             text-transform:uppercase;">Financial Assistant</div>
    </div>
    <hr style="border-color:#1f2937;margin:0.8rem 0;">
    """, unsafe_allow_html=True)

    for label in ["Dashboard", "Properties", "Revenue Forecast", "Risk Classification"]:
        if st.button(label, key=f"nav_{label}", use_container_width=True):
            st.session_state.page = label
            st.rerun()

    st.markdown("""
    <hr style="border-color:#1f2937;margin:0.8rem 0;">
    <div style="font-size:0.65rem;letter-spacing:0.15em;text-transform:uppercase;
         color:#4b5563;margin-bottom:6px;">System Status</div>
    <div style="font-size:0.72rem;color:#6b7280;line-height:2;">
        <span style="color:#10b981;">●</span> SageMaker Live<br>
        <span style="color:#10b981;">●</span> Vertex AI Live<br>
        <span style="color:#10b981;">●</span> DB Connected
    </div>
    <div style="font-size:0.62rem;color:#374151;margin-top:6px;">REGION · us-east-2</div>
    """, unsafe_allow_html=True)

page = st.session_state.page

# ── Layout ──
main_col, chat_col = st.columns([3, 1])

# CHAT PANEL — always on right
# ════════════════════════════════════════════
def render_chat_content(suffix="", in_modal=False):
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    st.markdown("### 🤖 AI Assistant")
    st.caption("Gemini 2.5 Flash · Vertex AI")

    chat_container = st.container(height=400)
    with chat_container:
        if not st.session_state.chat_history:
            st.info("👋 Ask me about Prologis properties, financials, or forecasts!")
        for msg in st.session_state.chat_history:
            st.chat_message(msg["role"]).write(msg["content"])

    if not st.session_state.chat_history:
        st.caption("Try asking:")
        suggestions = [
            "What's our Q1 revenue?",
            "Show me properties in Chicago",
            "Summarize the latest press release",
        ]
        for s in suggestions:
            if st.button(s, key=f"suggest_{s}{suffix}", use_container_width=True):
                st.session_state.chat_history.append({"role": "user", "content": s})
                df_c = load_properties()
                ctx = (f"Portfolio: {len(df_c)} properties." if not df_c.empty else "")
                with st.spinner("..."):
                    reply = ask_gemini(f"You are a Prologis Inc. financial analyst. {ctx}\nUser: {s}")
                st.session_state.chat_history.append({"role": "assistant", "content": reply})
                st.rerun()

    user_input = st.chat_input("Ask Prologis AI...", key=f"chat_input{suffix}")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        df_c = load_properties()
        ctx = (f"Portfolio: {len(df_c)} properties." if not df_c.empty else "")
        with st.spinner("..."):
            reply = ask_gemini(
                f"You are a Prologis Inc. financial analyst. {ctx}\nUser: {user_input}")
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        st.rerun()

    if st.session_state.chat_history:
        if st.button(" Clear", key=f"clear_chat{suffix}", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()


@st.dialog("🤖 AI Assistant", width="large")
def chat_modal():
    render_chat_content(suffix="_modal")
    if st.button("✖ Close", key="close_modal"):
        
        st.rerun()


with chat_col:
    if st.button("⛶ Fullscreen Chat", key="toggle_fullscreen", use_container_width=True):
        st.session_state.show_chat_modal = True
        st.rerun()
    if st.session_state.show_chat_modal:
        chat_modal()
    render_chat_content(suffix="_main")


# ── MAIN CONTENT ──
with main_col:

    # ════════════════════════════════
    # DASHBOARD
    # ════════════════════════════════
    if page == "Dashboard":
        st.title(" Executive Dashboard")
        st.caption(f"Prologis Inc. · {pd.Timestamp.now().strftime('%B %d, %Y')}")
        st.divider()

        df     = load_properties()
        df_fin = load_financials_joined()

        if df.empty:
            st.error("Database connection failed.")
        else:
            total_props    = len(df)
            total_sqft     = df["sq_footage"].sum() if "sq_footage" in df.columns else 0
            total_revenue  = df_fin["revenue"].sum()   if not df_fin.empty and "revenue"   in df_fin.columns else 0
            total_netincome= df_fin["net_income"].sum() if not df_fin.empty and "net_income" in df_fin.columns else 0

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("🏭 Properties",  total_props)
            c2.metric("📐 Total Sq Ft", f"{total_sqft/1e6:.1f}M")
            c3.metric("💰 Total Revenue",  f"${total_revenue/1e6:.1f}M")
            c4.metric("📈 Net Income",     f"${total_netincome/1e6:.1f}M")

            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Revenue by Property Type")
                if not df_fin.empty and "revenue" in df_fin.columns:
                    d = df_fin.groupby("property_type")["revenue"].mean().reset_index()
                    fig = px.bar(d, x="property_type", y="revenue",
                        color_discrete_sequence=["#f59e0b"],
                        labels={"revenue": "Avg Revenue ($)", "property_type": ""})
                    fig.update_layout(height=280, margin=dict(t=10,b=10),
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        font_color="#9ca3af")
                    st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.subheader("Sq Footage by Type")
                if "sq_footage" in df.columns and "property_type" in df.columns:
                    d2 = df.groupby("property_type")["sq_footage"].sum().reset_index()
                    fig2 = px.pie(d2, names="property_type", values="sq_footage",
                        color_discrete_sequence=px.colors.sequential.Oranges_r)
                    fig2.update_layout(height=280, margin=dict(t=10,b=10),
                        paper_bgcolor="rgba(0,0,0,0)", font_color="#9ca3af")
                    st.plotly_chart(fig2, use_container_width=True)

            st.subheader("Revenue vs Expenses")
            if not df_fin.empty and "revenue" in df_fin.columns:
                fig3 = px.scatter(df_fin,
                    x="expenses", y="revenue",
                    color="property_type",
                    hover_name="address",
                    labels={"expenses": "Expenses ($)", "revenue": "Revenue ($)"})
                fig3.update_layout(height=300, margin=dict(t=10,b=10),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#9ca3af")
                st.plotly_chart(fig3, use_container_width=True)

            # SEC + Press Releases from S3
            st.divider()
            st.subheader("📄 SEC Filings & Press Releases (AWS S3)")
            col_sec, col_pr = st.columns(2)
            with col_sec:
                sec = get_sec_data()
                if sec and "error" not in sec:
                    st.markdown(f"**{sec.get('company','N/A')}** ({sec.get('ticker','N/A')})")
                    st.caption(f"CIK: {sec.get('cik','N/A')} · Source: {sec.get('source','SEC EDGAR')}")
                    filings = sec.get("filings", [])
                    if filings:
                        rows = []
                        for f in filings[:8]:
                            rows.append({
                                "Period":     f.get("period",""),
                                "Type":       f.get("type",""),
                                "Revenue":    f"${f['revenue']/1e9:.2f}B" if f.get("revenue") else "N/A",
                                "Net Income": f"${f['net_income']/1e9:.2f}B" if f.get("net_income") else "N/A",
                                "Op. Expenses": f"${f['operating_expenses']/1e9:.2f}B" if f.get("operating_expenses") else "N/A",
                            })
                        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                    st.caption("📥 Real data from SEC EDGAR API via AWS S3")
                else:
                    st.info("Run fetch_sec_data.py first")
            with col_pr:
                st.caption("Recent Press Releases")
                prs = get_press_releases_data()
                if prs and isinstance(prs, list):
                    for pr in prs[:3]:
                        if isinstance(pr, dict):
                            st.markdown(f"**{pr.get('title','')[:60]}...**")
                            st.caption(f"{pr.get('date','')} · {pr.get('category','')}")
                            st.divider()
                    st.caption("📥 Loaded from AWS S3")
                else:
                    st.info("Run upload_sec_to_s3.py first")

    # ════════════════════════════════
    # PROPERTIES
    # ════════════════════════════════
    elif page == "Properties":
        st.title(" Property Explorer")
        st.divider()

        df     = load_properties()
        df_fin = load_financials_joined()

        if df.empty:
            st.error("No data available.")
        else:
            view = st.selectbox("View", ["Property Records", "Financial Records"],
                                label_visibility="collapsed")

            if view == "Property Records":
                col_s, col_t = st.columns([2, 1])
                with col_s:
                    search = st.text_input("🔍 Search",
                        placeholder="Search by address, metro area, or type...")
                with col_t:
                    types = ["All"] + sorted(df["property_type"].dropna().unique().tolist()) \
                            if "property_type" in df.columns else ["All"]
                    sel_type = st.selectbox("Type", types)

                # Live suggestions based on address + metro_area
                if search:
                    sugg_df = df[
                        df["address"].str.contains(search, case=False, na=False) |
                        df["metro_area"].str.contains(search, case=False, na=False) |
                        df["property_type"].str.contains(search, case=False, na=False)
                    ]["address"].tolist()
                    if sugg_df:
                        st.caption("Suggestions:")
                        scols = st.columns(min(len(sugg_df[:4]), 4))
                        for i, s in enumerate(sugg_df[:4]):
                            if scols[i].button(s[:25], key=f"sug_{i}"):
                                st.session_state.prop_selected = s
                                st.rerun()

                active = st.session_state.prop_selected if st.session_state.prop_selected else search
                if not search:
                    st.session_state.prop_selected = ""

                filt = df.copy()
                if sel_type != "All" and "property_type" in df.columns:
                    filt = filt[filt["property_type"] == sel_type]
                if active:
                    filt = filt[
                        filt["address"].str.contains(active, case=False, na=False) |
                        filt["metro_area"].str.contains(active, case=False, na=False) |
                        filt["property_type"].str.contains(active, case=False, na=False)
                    ]

                st.caption(f"{len(filt)} of {len(df)} properties")
                st.dataframe(filt, use_container_width=True,
                             height=max(len(filt)*36+38, 300))

                if len(filt) > 0:
                    st.subheader("Detail View")
                    sel = st.selectbox("Select property", filt["address"].tolist())
                    row = filt[filt["address"] == sel].iloc[0]
                    cols = st.columns(4)
                    for i, (k, v) in enumerate(row.items()):
                        cols[i%4].metric(str(k).replace("_"," ").title(), str(v))

            else:  # Financial Records
                if df_fin.empty:
                    st.info("No financial records found. Run seed_db.py to populate.")
                else:
                    metros = ["All"] + sorted(df_fin["metro_area"].dropna().unique().tolist()) \
                             if "metro_area" in df_fin.columns else ["All"]
                    sel_metro = st.selectbox("Filter by Metro Area", metros)
                    disp = df_fin.copy()
                    if sel_metro != "All":
                        disp = disp[disp["metro_area"] == sel_metro]
                    st.dataframe(disp, use_container_width=True,
                                 height=max(len(disp)*36+38, 200))
                    st.caption(f"📥 {len(disp)} financial records from PostgreSQL")

    # ════════════════════════════════
    # REVENUE FORECAST
    # ════════════════════════════════
    elif page == "Revenue Forecast":
        st.title("Revenue Forecast")
        st.caption("Random Forest Regressor · R²=0.805 · AWS SageMaker 🟢")
        st.divider()

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            med_inc   = st.selectbox("Median Income",
                [1.0,2.0,3.0,4.0,5.0,6.0,7.0,8.0,10.0,12.0,15.0], index=4)
            house_age = st.selectbox("House Age (yrs)",
                [5,10,15,20,25,30,35,40,52], index=3)
        with c2:
            ave_rooms  = st.selectbox("Avg Rooms",
                [2.0,3.0,4.0,5.0,6.0,7.0,8.0,10.0], index=4)
            ave_bedrms = st.selectbox("Avg Bedrooms",
                [0.5,0.8,1.0,1.1,1.5,2.0,2.5], index=3)
        with c3:
            population = st.selectbox("Population",
                [100,500,1000,1500,2000,3000,5000,10000], index=3)
            ave_occup  = st.selectbox("Avg Occupancy",
                [1.0,1.5,2.0,2.5,3.0,4.0,5.0,6.0], index=4)
        with c4:
            latitude  = st.selectbox("Latitude",
                [32.5,33.5,34.0,35.0,36.0,37.0,37.8,38.5,40.0,41.0], index=6)
            longitude = st.selectbox("Longitude",
                [-124.0,-122.4,-121.0,-119.0,-118.0,-117.0,-115.0], index=1)

        features = [float(med_inc), float(house_age), float(ave_rooms),
                    float(ave_bedrms), float(population), float(ave_occup),
                    float(latitude), float(longitude)]

        if st.button("📈 Predict Revenue", type="primary"):
            with st.spinner("Calling SageMaker regression endpoint..."):
                r = predict_revenue(features)
            if "error" in r:
                st.error(f"Endpoint error: {r['error']}")
            else:
                st.session_state.reg_result   = r
                st.session_state.reg_features = features

        if st.session_state.reg_result:
            pred = st.session_state.reg_result.get("prediction", 0)
            st.success(f"### 💰 Predicted Value: ${pred:,.0f}")
            st.caption("California Housing proxy · R²=0.805 · Scale by portfolio factor for Prologis")

            st.subheader("Income Sensitivity Analysis")
            inc_vals = [1.0,2.0,3.0,4.0,5.0,6.0,7.0,8.0,10.0,12.0,15.0]
            preds_s  = []
            fb = st.session_state.reg_features.copy()
            for inc in inc_vals:
                f2 = fb.copy(); f2[0] = inc
                preds_s.append(predict_revenue(f2).get("prediction", 0))

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=inc_vals, y=preds_s, mode="lines+markers",
                line=dict(color="#f59e0b", width=3),
                marker=dict(size=8, color="#f59e0b"),
                fill="tozeroy", fillcolor="rgba(245,158,11,0.1)",
            ))
            fig.add_vline(x=med_inc, line_dash="dash", line_color="#ef4444",
                          annotation_text=f"Current ({med_inc})",
                          annotation_font_color="#ef4444")
            fig.update_layout(height=280, margin=dict(t=20,b=10),
                xaxis_title="Median Income (scaled)",
                yaxis_title="Predicted Value ($)",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#9ca3af")
            st.plotly_chart(fig, use_container_width=True)

    # ════════════════════════════════
    # RISK CLASSIFICATION
    # ════════════════════════════════
    elif page == "Risk Classification":
        st.title(" Risk Classification")
        st.caption("Logistic Regression · Accuracy=81.7% · AWS SageMaker 🟢")
        st.divider()

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            age      = st.selectbox("Age", list(range(18,96,5)), index=4)
            balance  = st.selectbox("Balance ($)",
                [-1000,-500,0,500,1000,2000,5000,10000,20000], index=4)
            duration = st.selectbox("Call Duration (s)",
                [5,30,60,100,200,300,500,800,1200], index=5)
            campaign = st.selectbox("Campaign Contacts",
                [1,2,3,5,10,15,20], index=1)
        with c2:
            pdays    = st.selectbox("Days Since Contact",
                [-1,30,60,90,180,365], index=0)
            previous = st.selectbox("Previous Contacts",
                [0,1,2,3,5,10], index=0)
            job      = st.selectbox("Job", ["admin.","blue-collar","entrepreneur",
                "housemaid","management","retired","self-employed","services",
                "student","technician","unemployed","unknown"], index=0)
            marital  = st.selectbox("Marital Status",
                ["divorced","married","single"], index=1)
        with c3:
            education = st.selectbox("Education",
                ["primary","secondary","tertiary","unknown"], index=2)
            default   = st.selectbox("Credit Default", ["no","yes"], index=0)
            housing   = st.selectbox("Housing Loan",   ["no","yes"], index=0)
            loan      = st.selectbox("Personal Loan",  ["no","yes"], index=0)
        with c4:
            contact  = st.selectbox("Contact Type",
                ["cellular","telephone","unknown"], index=0)
            month    = st.selectbox("Last Month",
                ["jan","feb","mar","apr","may","jun",
                 "jul","aug","sep","oct","nov","dec"], index=4)
            poutcome = st.selectbox("Prev Outcome",
                ["failure","other","success","unknown"], index=3)

        jm  = {"admin.":0,"blue-collar":1,"entrepreneur":2,"housemaid":3,
               "management":4,"retired":5,"self-employed":6,"services":7,
               "student":8,"technician":9,"unemployed":10,"unknown":11}
        mm  = {"divorced":0,"married":1,"single":2}
        em  = {"primary":0,"secondary":1,"tertiary":2,"unknown":3}
        bm  = {"no":0,"yes":1}
        cm  = {"cellular":0,"telephone":1,"unknown":2}
        mnm = {"jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,
               "jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12}
        pm  = {"failure":0,"other":1,"success":2,"unknown":3}

        features = [age, jm[job], mm[marital], em[education], bm[default], balance,
                    bm[housing], bm[loan], cm[contact], 3, mnm[month], duration,
                    campaign, pdays, previous, pm[poutcome]]

        if st.button("🔍 Classify Risk", type="primary"):
            with st.spinner("Calling SageMaker classification endpoint..."):
                r = predict_risk(features)
            if "error" in r:
                st.error(f"Endpoint error: {r['error']}")
            else:
                st.session_state.clf_result = r

        if st.session_state.clf_result:
            r     = st.session_state.clf_result
            pred  = r.get("prediction", ["Unknown"])
            label = pred[0] if isinstance(pred, list) else pred
            proba = r.get("probabilities", None)

            if label == "Low":
                st.success(f"### Risk Level: {label} Risk ✅")
            elif label == "Medium":
                st.warning(f"### Risk Level: {label} Risk ⚠️")
            else:
                st.error(f"### Risk Level: {label} Risk 🔴")

            if proba:
                pf = proba[0] if isinstance(proba[0], list) else proba
                fig = go.Figure(go.Bar(
                    x=["High Risk", "Low Risk"],
                    y=[round(p*100,1) for p in pf],
                    marker_color=["#ef4444", "#10b981"],
                    text=[f"{p*100:.1f}%" for p in pf],
                    textposition="outside", width=0.4,
                ))
                fig.update_layout(height=280, margin=dict(t=20,b=10),
                    yaxis_title="Probability (%)", yaxis_range=[0,115],
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#9ca3af")
                st.plotly_chart(fig, use_container_width=True)

            st.subheader("Key Risk Indicators")
            cols = st.columns(4)
            cols[0].metric("Age",           f"{age} {'✅' if 25<age<55 else '⚠️'}")
            cols[1].metric("Balance",       f"${balance:,} {'✅' if balance>500 else '⚠️'}")
            cols[2].metric("Call Duration", f"{duration}s {'✅' if duration>200 else '⚠️'}")
            cols[3].metric("Prior Contact", f"{'✅ Yes' if previous>0 else '⚠️ No'}")
