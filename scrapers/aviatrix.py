import csv
import html
import os
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup

JOBS_API = "https://boards-api.greenhouse.io/v1/boards/aviatrix/jobs?content=true"
COMPANY_NAME = "Aviatrix"
HEADERS = {"User-Agent": "Mozilla/5.0"}

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "aviatrix.csv")

CSV_FIELDS = [
    "Job_name",
    "Job_description",
    "Posting_date",
    "Experience",
    "Location",
    "Company_name",
    "Job_application_link",
    "Type",
]


def clean_description(raw_html):
    """Greenhouse double-encodes HTML; decode entities then strip tags."""
    decoded = html.unescape(html.unescape(raw_html or ""))
    text = BeautifulSoup(decoded, "html.parser").get_text(" ", strip=True)
    return re.sub(r"\s+", " ", text).strip() or "N/A"


def parse_posting_date(iso_str):
    if not iso_str:
        return "N/A"
    try:
        return datetime.fromisoformat(iso_str).strftime("%d-%m-%Y")
    except ValueError:
        return "N/A"


def extract_experience(description):
    match = re.search(r"(\d+\+?\s*(?:to\s*\d+\s*)?years?[^.\n]{0,80})", description, flags=re.IGNORECASE)
    return match.group(1).strip() if match else "N/A"


def classify_type(location_name):
    name = (location_name or "").lower()
    if "remote" in name:
        return "Remote"
    if "hybrid" in name:
        return "Hybrid"
    return "Onsite"


def scrape():
    response = requests.get(JOBS_API, headers=HEADERS, timeout=30)
    response.raise_for_status()
    payload = response.json()

    jobs = []
    for item in payload.get("jobs", []):
        location = (item.get("location") or {}).get("name", "N/A")
        description = clean_description(item.get("content", ""))
        jobs.append({
            "Job_name": item.get("title", "N/A"),
            "Job_description": description,
            "Posting_date": parse_posting_date(item.get("first_published")),
            "Experience": extract_experience(description),
            "Location": location or "N/A",
            "Company_name": COMPANY_NAME,
            "Job_application_link": item.get("absolute_url", "N/A"),
            "Type": classify_type(location),
        })
    return jobs


def write_csv(jobs):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(jobs)


if __name__ == "__main__":
    jobs = scrape()
    write_csv(jobs)
    print(f"Scraped {len(jobs)} jobs -> {os.path.abspath(OUTPUT_FILE)}")
    for job in jobs:
        print(f"- {job['Job_name']} | {job['Location']} | {job['Posting_date']} | {job['Type']}")
