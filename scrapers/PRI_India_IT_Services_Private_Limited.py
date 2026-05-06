import csv
import os
import re
from datetime import datetime, timedelta, timezone

import requests
from bs4 import BeautifulSoup

PORTAL_KEY = "74jdnww6u8rk6etus6fjb7z7jh2bqs0267mjowh28c4pbat3q8pogch40ecq88g5"
PORTAL_ID = "615"
COMPANY_NAME = "PRI India IT Services Private Limited"

AUTH_URL = "https://ws.jobdiva.com/candPortal/rest/auth/a"
SEARCH_URL = "https://ws.jobdiva.com/candPortal/rest/job/searchjobsportal"
APPLY_URL_TEMPLATE = (
    f"https://www1.jobdiva.com/portal/?a={PORTAL_KEY}#/jobs/{{job_id}}"
)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "PRI_India_IT_Services_Private_Limited.csv")

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

PAGE_SIZE = 50
RECENT_DAYS = 15


def auth_headers():
    base = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Origin": "https://www1.jobdiva.com",
        "Referer": "https://www1.jobdiva.com/",
        "portalid": PORTAL_ID,
        "a": PORTAL_KEY,
    }
    response = requests.get(AUTH_URL, headers=base, timeout=30)
    response.raise_for_status()
    base["token"] = response.json()["token"]
    base["Content-Type"] = "application/x-www-form-urlencoded"
    return base


def fetch_jobs(headers):
    jobs = []
    start = 1
    while True:
        body = (
            f"city=&country=&from={start}&jobCategories=&jobDivisions="
            f"&jobTypes=&keywords=&miles=&onsiteFlex=&portalID=1"
            f"&qualifications=&states=&to={start + PAGE_SIZE - 1}&unit=mi&zipcode="
        )
        response = requests.post(SEARCH_URL, headers=headers, data=body, timeout=30)
        response.raise_for_status()
        payload = response.json()
        chunk = payload.get("data", []) or []
        jobs.extend(chunk)
        total = payload.get("total", len(jobs))
        if not chunk or len(jobs) >= total:
            break
        start += PAGE_SIZE
    return jobs


def clean_html(raw):
    if not raw:
        return "N/A"
    text = BeautifulSoup(raw, "html.parser").get_text(" ", strip=True)
    return re.sub(r"\s+", " ", text).strip() or "N/A"


def ms_to_date(ms):
    if not ms:
        return None
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).date()


def extract_experience(job, description):
    raw = job.get("experience")
    if raw:
        return str(raw).strip()
    match = re.search(
        r"(\d+\+?\s*(?:to\s*\d+\s*)?(?:years?|yrs?)[^.\n]{0,80})",
        description,
        flags=re.IGNORECASE,
    )
    return match.group(1).strip() if match else "N/A"


def classify_type(job, description):
    remote_flag = (job.get("workingRemote") or "").lower()
    if "fully remote" in remote_flag or remote_flag == "remote":
        return "Remote"
    if "hybrid" in remote_flag or "partial" in remote_flag:
        return "Hybrid"
    if "on-site" in remote_flag or "onsite" in remote_flag:
        return "Onsite"
    haystack = description.lower()
    if "fully remote" in haystack or "100% remote" in haystack:
        return "Remote"
    if "hybrid" in haystack:
        return "Hybrid"
    return "Onsite"


def to_row(job):
    description = clean_html(job.get("jobDescription", ""))
    post_date = ms_to_date(job.get("postDate"))
    return {
        "Job_name": job.get("title") or "N/A",
        "Job_description": description,
        "Posting_date": post_date.strftime("%d-%m-%Y") if post_date else "N/A",
        "Experience": extract_experience(job, description),
        "Location": job.get("location") or job.get("mainLocation") or "N/A",
        "Company_name": COMPANY_NAME,
        "Job_application_link": APPLY_URL_TEMPLATE.format(job_id=job.get("id")),
        "Type": classify_type(job, description),
    }, post_date


def write_csv(rows):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main():
    headers = auth_headers()
    jobs = fetch_jobs(headers)
    cutoff = datetime.now(timezone.utc).date() - timedelta(days=RECENT_DAYS)

    rows = []
    skipped_no_date = 0
    for job in jobs:
        row, post_date = to_row(job)
        if post_date is None:
            skipped_no_date += 1
            continue
        if post_date >= cutoff:
            rows.append(row)

    write_csv(rows)
    print(
        f"Fetched {len(jobs)} total jobs. "
        f"Kept {len(rows)} posted on/after {cutoff.strftime('%d-%m-%Y')} "
        f"(skipped {skipped_no_date} with no date) -> {os.path.abspath(OUTPUT_FILE)}"
    )
    for row in rows:
        print(f"- {row['Posting_date']} | {row['Job_name']} | {row['Location']} | {row['Type']}")


if __name__ == "__main__":
    main()
