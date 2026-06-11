"""
fetch_sec_data.py
Retrieves REAL Prologis SEC EDGAR financial data via the official EDGAR API.
No scraping — uses SEC's public JSON API (no API key required).

Usage: python fetch_sec_data.py
"""
import requests
import json
import boto3
import os
from datetime import datetime

# ── Config ──
PROLOGIS_CIK = "0001045609"
COMPANY_NAME = "Prologis Inc"
TICKER       = "PLD"
S3_BUCKET    = "prologis-financial-assistant-362612348837"
AWS_REGION   = "us-east-2"

HEADERS = {
    "User-Agent": "Vamsi DePaul University vamsi@depaul.edu",
    "Accept-Encoding": "gzip, deflate",
}

def fetch_metric(facts: dict, concept: str, unit: str = "USD") -> list:
    """Extract a financial metric from EDGAR facts."""
    try:
        entries = facts["us-gaap"][concept]["units"][unit]
        # Filter for 10-K and 10-Q only, last 8 quarters
        filtered = [
            e for e in entries
            if e.get("form") in ("10-K", "10-Q")
            and e.get("val") is not None
        ]
        # Sort by end date descending
        filtered.sort(key=lambda x: x.get("end", ""), reverse=True)
        # Return last 8 unique periods
        seen = set()
        result = []
        for e in filtered:
            key = (e.get("end"), e.get("form"))
            if key not in seen:
                seen.add(key)
                result.append({
                    "period":     e.get("end"),
                    "form":       e.get("form"),
                    "value":      e.get("val"),
                    "filed":      e.get("filed"),
                })
            if len(result) >= 8:
                break
        return result
    except KeyError:
        return []

def fetch_prologis_sec_data() -> dict:
    """Fetch real Prologis financial data from SEC EDGAR API."""
    print("Fetching Prologis company facts from SEC EDGAR...")

    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{PROLOGIS_CIK}.json"
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()

    data  = response.json()
    facts = data.get("facts", {})
    print("✅ Company facts retrieved")

    # ── Extract key financial metrics ──
    # Revenue — try multiple concept names
    revenues = (
        fetch_metric(facts, "Revenues") or
        fetch_metric(facts, "RevenueFromContractWithCustomerExcludingAssessedTax") or
        fetch_metric(facts, "SalesRevenueNet")
    )

    # Net Income
    net_income = (
        fetch_metric(facts, "NetIncomeLoss") or
        fetch_metric(facts, "ProfitLoss")
    )

    # Operating Expenses
    op_expenses = (
        fetch_metric(facts, "OperatingExpenses") or
        fetch_metric(facts, "CostsAndExpenses")
    )

    # Operating Income
    op_income = fetch_metric(facts, "OperatingIncomeLoss")

    # Total Assets
    total_assets = fetch_metric(facts, "Assets")

    # Build structured output matching our app's expected format
    # Create filings list from revenues (most complete metric)
    filings = []
    for rev in revenues[:8]:
        period = rev["period"]
        # Find matching net income for same period
        ni  = next((x["value"] for x in net_income  if x["period"] == period), None)
        exp = next((x["value"] for x in op_expenses if x["period"] == period), None)
        oi  = next((x["value"] for x in op_income   if x["period"] == period), None)

        # Determine quarter label
        month = int(period.split("-")[1]) if period else 0
        year  = period.split("-")[0] if period else ""
        if rev["form"] == "10-K":
            period_label = f"FY {year}"
        elif month <= 3:
            period_label = f"Q1 {year}"
        elif month <= 6:
            period_label = f"Q2 {year}"
        elif month <= 9:
            period_label = f"Q3 {year}"
        else:
            period_label = f"Q4 {year}"

        filings.append({
            "period":               period_label,
            "end_date":             period,
            "type":                 rev["form"],
            "filed":                rev["filed"],
            "revenue":              rev["value"],
            "net_income":           ni,
            "operating_expenses":   exp,
            "operating_income":     oi,
        })

    sec_data = {
        "company":        COMPANY_NAME,
        "ticker":         TICKER,
        "cik":            PROLOGIS_CIK,
        "source":         "SEC EDGAR XBRL API",
        "retrieved_at":   datetime.now().isoformat(),
        "api_url":        url,
        "filings":        filings,
        "latest_revenue": revenues[0]["value"] if revenues else None,
        "latest_net_income": net_income[0]["value"] if net_income else None,
        "latest_op_expenses": op_expenses[0]["value"] if op_expenses else None,
    }

    print(f"✅ Extracted {len(filings)} filings")
    if filings:
        print(f"   Latest period: {filings[0]['period']}")
        print(f"   Revenue: ${filings[0]['revenue']/1e9:.2f}B" if filings[0]['revenue'] else "")
        print(f"   Net Income: ${filings[0]['net_income']/1e9:.2f}B" if filings[0]['net_income'] else "")

    return sec_data


def save_locally(data: dict):
    """Save SEC data to local JSON file."""
    os.makedirs("data", exist_ok=True)
    with open("data/sec_mock.json", "w") as f:
        json.dump(data, f, indent=2)
    print("✅ Saved to data/sec_mock.json")


def upload_to_s3(data: dict):
    """Upload SEC data to AWS S3."""
    try:
        s3 = boto3.client("s3", region_name=AWS_REGION)
        s3.put_object(
            Bucket=S3_BUCKET,
            Key="data/sec_mock.json",
            Body=json.dumps(data, indent=2).encode(),
            ContentType="application/json",
        )
        print(f"✅ Uploaded to s3://{S3_BUCKET}/data/sec_mock.json")
    except Exception as e:
        print(f"⚠️  S3 upload failed: {e}")


def main():
    print("=" * 55)
    print("Prologis SEC EDGAR Data Fetcher")
    print("Source: https://data.sec.gov (official SEC API)")
    print("=" * 55)

    # Fetch real data
    sec_data = fetch_prologis_sec_data()

    # Save locally
    save_locally(sec_data)

    # Upload to S3
    upload_to_s3(sec_data)

    print()
    print("=" * 55)
    print("✅ Done! Real SEC data now in data/sec_mock.json and S3")
    print(f"   {len(sec_data['filings'])} filings retrieved")
    print("   Source: SEC EDGAR XBRL API (no mock data)")
    print("=" * 55)


if __name__ == "__main__":
    main()
