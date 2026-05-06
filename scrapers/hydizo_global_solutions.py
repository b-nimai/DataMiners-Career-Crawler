import csv
import os
import re
import requests
from bs4 import BeautifulSoup

CAREER_URL = "https://hydizo.com/company/career/"
COMPANY_NAME = "Hydizo Global Solutions Private Limited"
HEADERS = {"User-Agent": "Mozilla/5.0"}

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "hydizo_global_solutions.csv")

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


def find_job_card(soup, title):
    """Walk up from the title heading to the surrounding job-card container."""
    h = soup.find("h2", string=lambda x: x and title in x)
    if not h:
        return None
    node = h
    for _ in range(8):
        node = node.parent
        if node is None:
            return None
        classes = node.get("class") or []
        if node.name == "div" and "e-con-full" in classes:
            text = node.get_text(" ", strip=True)
            if "Key Requirements" in text or "HYDERABAD" in text:
                return node
    return None


def extract_experience(card_text):
    """Pull a years-of-experience phrase out of the requirements block."""
    match = re.search(r"(\d+\+?\s*years?[^|.\n]*)", card_text, flags=re.IGNORECASE)
    return match.group(1).strip() if match else "N/A"


def extract_description(card):
    """The intro paragraph sits directly under the title, before the requirements list."""
    paras = [
        p.get_text(strip=True)
        for p in card.find_all("p")
        if "elementor-icon-box-description" not in (p.get("class") or [])
    ]
    paras = [p for p in paras if p]
    return paras[0] if paras else "N/A"


def extract_apply_link(card):
    for a in card.find_all("a", href=True):
        href = a["href"]
        if href.startswith("http") and "/job/" in href:
            return href
    return CAREER_URL


def extract_employment_type(card_text):
    if "Internship" in card_text:
        return "Internship"
    if "Full Time" in card_text or "Full-Time" in card_text:
        return "Full Time"
    return "N/A"


def scrape():
    response = requests.get(CAREER_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")

    titles = []
    headings = [
        h.get_text(strip=True) for h in soup.find_all("h2", class_="elementor-heading-title")
    ]
    for i, text in enumerate(headings):
        if text in ("Full Time", "Internship") and i + 1 < len(headings):
            titles.append(headings[i + 1])

    jobs = []
    for title in titles:
        card = find_job_card(soup, title)
        if card is None:
            continue
        card_text = card.get_text(" | ", strip=True)
        employment_type = extract_employment_type(card_text)

        jobs.append({
            "Job_name": f"{title} ({employment_type})" if employment_type != "N/A" else title,
            "Job_description": extract_description(card),
            "Posting_date": "N/A",
            "Experience": extract_experience(card_text),
            "Location": "Hyderabad",
            "Company_name": COMPANY_NAME,
            "Job_application_link": extract_apply_link(card),
            "Type": "Onsite",
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
        print(f"- {job['Job_name']} | {job['Experience']} | {job['Job_application_link']}")
