import requests
import json
import csv
from bs4 import BeautifulSoup
import time
import re

CSV_FILE = 'pro5_jobs.csv'
CSV_HEADERS = ['Job Name', 'Job Description', 'posting date', 'Expereince', 'Location', 'Company Name', 'Job Applicatio link', 'Job Type']

def clean_html(raw_html):
    if not raw_html:
        return "Not Specified"
    soup = BeautifulSoup(raw_html, "html.parser")
    return soup.get_text(separator="\n", strip=True)

def main():
    print("Scraping Pro5.ai jobs from foundit.in...")
    search_url = "https://www.foundit.in/search/pro5-ai-907581-jobs-career"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5'
    }

    try:
        # Fetch search page using curl
        print("Executing curl for search page...")
        import subprocess
        result = subprocess.run(["curl", "-sL", search_url], capture_output=True, text=True)
        if result.returncode != 0:
            print("curl failed.")
            return

        soup = BeautifulSoup(result.stdout, 'html.parser')
        
        scripts = soup.find_all('script', type='application/ld+json')
        job_urls = []
        for s in scripts:
            try:
                data = json.loads(s.text)
                items_to_check = data if isinstance(data, list) else [data]
                for item in items_to_check:
                    if isinstance(item, dict) and item.get('@type') == 'ItemList':
                        for el in item.get('itemListElement', []):
                            if el.get('url'):
                                job_urls.append(el.get('url'))
            except Exception as e:
                continue

        print(f"Found {len(job_urls)} job links.")

        jobs_data = []

        for idx, job_url in enumerate(job_urls):
            print(f"Fetching job {idx+1}/{len(job_urls)}: {job_url}")
            try:
                j_result = subprocess.run(["curl", "-sL", job_url], capture_output=True, text=True)
                if j_result.returncode != 0:
                    print(f"curl failed for {job_url}")
                    continue

                j_soup = BeautifulSoup(j_result.stdout, 'html.parser')
                
                j_scripts = j_soup.find_all('script', type='application/ld+json')
                job_data = None
                for s in j_scripts:
                    try:
                        d = json.loads(s.text)
                        if d.get('@type') == 'JobPosting':
                            job_data = d
                            break
                    except:
                        pass
                
                if job_data:
                    title = job_data.get('title', 'Not Specified')
                    raw_description = job_data.get('description', '')
                    description = clean_html(raw_description)
                    posting_date = job_data.get('datePosted', 'Not Specified')
                    if posting_date != 'Not Specified' and '-' in posting_date:
                        parts = posting_date.split('-')
                        if len(parts) == 3:
                            if len(parts[0]) == 4:
                                posting_date = f"{parts[2]}/{parts[1]}/{parts[0]}"
                            elif len(parts[2]) == 4:
                                posting_date = f"{parts[0]}/{parts[1]}/{parts[2]}"
                    
                    # Try to parse experience
                    experience = "Not Specified"
                    exp_req = job_data.get('experienceRequirements', {})
                    if exp_req and isinstance(exp_req, dict) and 'monthsOfExperience' in exp_req:
                        months = exp_req['monthsOfExperience']
                        if isinstance(months, (int, float)):
                            years = months // 12
                            experience = f"{years} Years"
                    
                    # Try to parse location
                    location = "Not Specified"
                    loc_data = job_data.get('jobLocation', {})
                    if isinstance(loc_data, dict):
                        address = loc_data.get('address', {})
                        locality = address.get('addressLocality')
                        region = address.get('addressRegion')
                        if locality and locality != 'NA':
                            location = locality
                        elif region and region != 'NA':
                            location = region
                            
                    company_name = job_data.get('hiringOrganization', {}).get('name', 'Pro5.ai')
                    job_type = job_data.get('employmentType', 'Not Specified')
                    
                    jobs_data.append({
                        'Job Name': title,
                        'Job Description': description,
                        'posting date': posting_date,
                        'Expereince': experience,
                        'Location': location,
                        'Company Name': company_name,
                        'Job Applicatio link': job_url,
                        'Job Type': job_type
                    })
                else:
                    print(f"  Warning: No JobPosting schema found for {job_url}")

            except Exception as e:
                print(f"  Error fetching {job_url}: {e}")
            
            time.sleep(1) # respectful delay

        # Write to CSV
        with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            writer.writeheader()
            for row in jobs_data:
                writer.writerow(row)
                
        print(f"Successfully scraped {len(jobs_data)} jobs and saved to {CSV_FILE}")

    except Exception as e:
        print(f"Failed to scrape: {e}")

if __name__ == "__main__":
    main()
