import os
import requests
from datetime import datetime
from dateutil.relativedelta import relativedelta
from fastapi import FastAPI

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "2c45c208d21c80678ea5dac14abdba02")

app = FastAPI()

def calculate_end_date(start_date_str, period):
    start_date = datetime.fromisoformat(start_date_str.replace("Z", "+00:00"))
    if period.lower() == "monthly":
        end_date = start_date + relativedelta(months=1)
    elif period.lower() == "yearly":
        end_date = start_date + relativedelta(years=1)
    else:
        end_date = start_date
    return end_date.isoformat()

def add_end_date_column():
    # Add End Date column if not exists
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

    # Fetch existing properties
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    props = resp.json().get("properties", {})

    if "End Date" not in props:
        payload = {"properties": {"End Date": {"date": {}}}}
        r = requests.patch(url, headers=headers, json=payload)
        r.raise_for_status()
        print("End Date column created!")
    else:
        print("End Date column already exists.")

def update_all_pages():
    # Fetch all pages in database
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    r = requests.post(url, headers=headers, json={})
    r.raise_for_status()
    pages = r.json().get("results", [])

    for page in pages:
        props = page["properties"]
        start_date = props.get("Date", {}).get("date", {}).get("start")
        period = props.get("Period", {}).get("select", {}).get("name", "monthly")
        if start_date:
            end_date = calculate_end_date(start_date, period)
            # Update page with End Date
            page_url = f"https://api.notion.com/v1/pages/{page['id']}"
            payload = {"properties": {"End Date": {"date": {"start": end_date}}}}
            r = requests.patch(page_url, headers=headers, json=payload)
            print(f"Updated page {page['id']} with End Date {end_date}")

@app.get("/update-end-dates")
def update_endpoint():
    add_end_date_column()
    update_all_pages()
    return {"status": "success", "message": "End Dates updated!"}
