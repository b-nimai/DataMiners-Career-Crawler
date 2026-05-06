import csv
import os
import re
from datetime import datetime, timedelta

from playwright.sync_api import sync_playwright

CAREERS_URL = "https://careers.restroworks.com/jobs/Careers"
COMPANY_NAME = "Restroworks"

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "restroworks.csv")

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

RECENT_DAYS = None  # None = no filter, write every job


def parse_zoho_date(raw):
    """Restroworks' Zoho Recruit instance emits dates as mm/dd/yyyy."""
    if not raw:
        return None
    try:
        return datetime.strptime(raw.strip(), "%m/%d/%Y").date()
    except ValueError:
        return None


def field_after(text, label):
    """Zoho's detail page renders 'Label\\nValue' for each field."""
    match = re.search(rf"\b{re.escape(label)}\s*\n([^\n]+)", text)
    return match.group(1).strip() if match else ""


def extract_experience(description):
    match = re.search(
        r"(\d+\s*(?:\+|to|-|–)\s*\d+\s*(?:years?|yrs?))",
        description,
        flags=re.IGNORECASE,
    )
    if match:
        return match.group(1).strip()
    match = re.search(r"(\d+\+?\s*(?:years?|yrs?)[^.\n]{0,40})", description, flags=re.IGNORECASE)
    return match.group(1).strip() if match else "N/A"


def classify_type(text_blob):
    blob = text_blob.lower()
    if "fully remote" in blob or "100% remote" in blob or "work from home" in blob:
        return "Remote"
    if "hybrid" in blob:
        return "Hybrid"
    return "Onsite"


def extract_description(text):
    """Body text under the 'Job Description' heading, before the trailing 'Requirements' boilerplate or footer."""
    match = re.search(r"Job Description\s*\n(.+?)(?:\n\s*I'm interested\b|\n\s*Share this job\b|$)",
                      text, flags=re.S | re.IGNORECASE)
    body = match.group(1) if match else text
    body = re.sub(r"\s+", " ", body).strip()
    return body[:2500] or "N/A"


def collect_job_links(page):
    page.goto(CAREERS_URL, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(2500)
    hrefs = page.eval_on_selector_all("a[href*='/jobs/Careers/']", "els => els.map(e => e.href)")
    seen, links = set(), []
    for h in hrefs:
        if h.endswith("/rss") or h in seen:
            continue
        seen.add(h)
        links.append(h)
    return links


def scrape_job(page, url):
    page.goto(url, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(1200)
    text = page.inner_text("body")

    title_match = re.search(r"Restroworks\s*\|\s*[^\n]+\n+([^\n]+)", text)
    title = title_match.group(1).strip() if title_match else field_after(text, "Job Title") or "N/A"

    date_raw = field_after(text, "Date Opened")
    posted = parse_zoho_date(date_raw)

    city = field_after(text, "City")
    state = field_after(text, "State/Province")
    country = field_after(text, "Country")
    location = ", ".join(part for part in [city, state, country] if part) or "N/A"

    description = extract_description(text)

    return {
        "Job_name": title,
        "Job_description": description,
        "Posting_date": posted.strftime("%d-%m-%Y") if posted else "N/A",
        "Experience": extract_experience(description),
        "Location": location,
        "Company_name": COMPANY_NAME,
        "Job_application_link": url,
        "Type": classify_type(description + " " + location),
    }, posted


def write_csv(rows):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main():
    cutoff = (
        datetime.utcnow().date() - timedelta(days=RECENT_DAYS)
        if RECENT_DAYS is not None else None
    )
    rows = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_context().new_page()

        links = collect_job_links(page)
        print(f"Found {len(links)} listings on the careers page")

        for link in links:
            try:
                row, posted = scrape_job(page, link)
            except Exception as exc:
                print(f"  ! failed {link}: {exc}")
                continue
            if cutoff is not None and posted is not None and posted < cutoff:
                print(f"  - skip ({posted}) {row['Job_name']}")
                continue
            rows.append(row)

        browser.close()

    write_csv(rows)
    window = (
        f"posted on/after {cutoff.strftime('%d-%m-%Y')}"
        if cutoff else "all postings"
    )
    print(f"Kept {len(rows)} jobs ({window}) -> {os.path.abspath(OUTPUT_FILE)}")
    for row in rows:
        print(f"- {row['Posting_date']} | {row['Job_name']} | {row['Location']} | {row['Type']}")


if __name__ == "__main__":
    main()
