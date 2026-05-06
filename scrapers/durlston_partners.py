import csv
import os
import re
import sys

from playwright.sync_api import sync_playwright

ROLES_URL = "https://durlstonpartners.com/roles/"
COMPANY_NAME = "Durlston Partners"

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "durlston_partners.csv")

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

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def collect_job_links(page):
    page.goto(ROLES_URL, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(2500)
    return page.eval_on_selector_all(
        "a[href*='/jobs/']",
        "els => [...new Set(els.map(e => e.href))]",
    )


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


def classify_type(blob):
    blob = blob.lower()
    if "fully remote" in blob or "100% remote" in blob or "remote" in blob and "hybrid" not in blob:
        return "Remote"
    if "hybrid" in blob:
        return "Hybrid"
    return "Onsite"


def scrape_job(page, url):
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(700)

    data = page.evaluate(
        """
        () => {
          const main = document.querySelector('main') || document.body;
          const text = main.innerText;
          const start = text.indexOf('Examples:');
          const trimmed = start >= 0
            ? text.slice(text.indexOf('\\n', start) + 1)
            : text;
          return trimmed;
        }
        """
    )

    lines = [ln.strip() for ln in data.splitlines() if ln.strip()]
    if not lines:
        return None

    title = lines[0]
    sphere = lines[1] if len(lines) > 1 else ""

    apply_idx = next((i for i, ln in enumerate(lines) if ln.upper() == "APPLY"), None)
    end_idx = next(
        (i for i, ln in enumerate(lines) if ln in ("< BACK", "ROLES", "JOIN US", "CONTACT")),
        len(lines),
    )

    if apply_idx is not None:
        meta = lines[2:apply_idx]
        body_lines = lines[apply_idx + 1 : end_idx]
    else:
        meta = lines[2:3]
        body_lines = lines[3:end_idx]

    salary = ""
    location = ""
    for entry in meta:
        if any(sym in entry for sym in ["$", "£", "€", "k base", "salary", "bonus"]):
            salary = entry
        else:
            location = entry if not location else f"{location}; {entry}"

    description = " ".join(body_lines).strip()
    description = re.sub(r"\s+", " ", description)
    if salary and salary not in description:
        description = f"{salary}. {description}".strip()
    if not description:
        description = "N/A"

    return {
        "Job_name": title or "N/A",
        "Job_description": description[:2500],
        "Posting_date": "N/A",
        "Experience": extract_experience(description),
        "Location": location or "N/A",
        "Company_name": COMPANY_NAME,
        "Job_application_link": url,
        "Type": classify_type(f"{location} {description} {sphere}"),
    }


def write_csv(rows):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    rows = []
    with sync_playwright() as p:
        # Durlston's WAF blocks pure-headless Chromium; a windowed browser passes.
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = browser.new_context(viewport={"width": 1280, "height": 800}).new_page()

        links = collect_job_links(page)
        print(f"Found {len(links)} role links")

        for i, link in enumerate(links, 1):
            try:
                row = scrape_job(page, link)
            except Exception as exc:
                print(f"  ! [{i}/{len(links)}] failed {link}: {exc}")
                continue
            if row is None:
                print(f"  - [{i}/{len(links)}] empty {link}")
                continue
            rows.append(row)
            print(f"  + [{i}/{len(links)}] {row['Job_name']} | {row['Location']} | {row['Type']}")

        browser.close()

    write_csv(rows)
    print(f"Wrote {len(rows)} jobs -> {os.path.abspath(OUTPUT_FILE)}")


if __name__ == "__main__":
    main()
