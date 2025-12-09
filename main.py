import requests
from datetime import datetime
from dateutil.relativedelta import relativedelta
from fastapi import FastAPI

# Notion API token and Database ID
NOTION_API_KEY = "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"
NOTION_DATABASE_ID = "2c45c208d21c80678ea5dac14abdba02"

app = FastAPI()

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def calculate_end_date(start_date_str, period):
    start_date = datetime.fromisoformat(start_date_str.replace("Z", "+00:00"))
    if period.lower() == "monthly":
        return (start_date + relativedelta(months=1)).isoformat()
    elif period.lower() == "yearly":
        return (start_date + relativedelta(years=1)).isoformat()
    else:
        return start_date.isoformat()

def fetch_database_properties():
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    return r.json().get("properties", {})

def create_missing_column(column_name, column_type="date"):
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}"
    payload = {"properties": {column_name: {column_type: {}}}}
    r = requests.patch(url, headers=HEADERS, json=payload)
    r.raise_for_status()
    print(f"Created missing column: {column_name}")

def update_all_pages():
    # Ensure End Date column exists
    props = fetch_database_properties()
    if "End Date" not in props:
        create_missing_column("End Date", "date")

    # Fetch pages
    query_url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    r = requests.post(query_url, headers=HEADERS, json={})
    r.raise_for_status()
    pages = r.json().get("results", [])

    for page in pages:
        page_props = page["properties"]
        start_date = page_props.get("Date", {}).get("date", {}).get("start")
        period = page_props.get("Period", {}).get("select", {}).get("name", "monthly")
        if start_date:
            end_date = calculate_end_date(start_date, period)
            page_url = f"https://api.notion.com/v1/pages/{page['id']}"
            payload = {"properties": {"End Date": {"date": {"start": end_date}}}}
            r = requests.patch(page_url, headers=HEADERS, json=payload)
            print(f"Updated page {page['id']} with End Date {end_date}")

@app.get("/update-end-dates")
def update_endpoint():
    """Auto-create End Date column and update all pages"""
    update_all_pages()
    return {"status": "success", "message": "End Dates updated and column auto-created if missing!"}
