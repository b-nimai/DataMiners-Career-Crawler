import csv
import requests
from bs4 import BeautifulSoup
import time

def scrape_astreya():
    base_url = "https://astreya.wd5.myworkdayjobs.com"
    search_url = f"{base_url}/wday/cxs/astreya/life-at-astreya-opportunities/jobs"
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    
    jobs_list = []
    limit = 20
    offset = 0
    total_jobs = 1  # will be updated
    
    print("Fetching job list...")
    while offset < total_jobs:
        payload = {
            "appliedFacets": {},
            "limit": limit,
            "offset": offset,
            "searchText": ""
        }
        
        try:
            response = requests.post(search_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if offset == 0:
                total_jobs = data.get("total", 0)
                
            postings = data.get("jobPostings", [])
            if not postings:
                break
            
            for post in postings:
                raw_date = post.get("postedOn", "Not Specified").replace("Posted", "").strip()
                
                # Parse to DD/MM/YYYY
                parsed_date = raw_date
                if raw_date.lower() == 'today':
                    from datetime import datetime
                    parsed_date = datetime.now().strftime('%d/%m/%Y')
                elif raw_date.lower() == 'yesterday':
                    from datetime import datetime, timedelta
                    parsed_date = (datetime.now() - timedelta(days=1)).strftime('%d/%m/%Y')
                else:
                    import re
                    days_ago_match = re.search(r'(\d+)\+?\s*[dD]ays? [aA]go', raw_date)
                    if days_ago_match:
                        from datetime import datetime, timedelta
                        days = int(days_ago_match.group(1))
                        parsed_date = (datetime.now() - timedelta(days=days)).strftime('%d/%m/%Y')

                jobs_list.append({
                    "Job Name": post.get("title", "Not Specified"),
                    "Location": post.get("locationsText", "Not Specified"),
                    "posting date": parsed_date,
                    "Job Applicatio link": f"{base_url}/en-US/life-at-astreya-opportunities{post.get('externalPath', '')}",
                    "externalPath": post.get("externalPath", "")
                })
            
            offset += limit
            print(f"Fetched {len(jobs_list)}/{total_jobs} job postings.")
            time.sleep(1) # be nice to the API
        except Exception as e:
            print(f"Failed to fetch job list at offset {offset}: {e}")
            break
            
    print(f"Found {len(jobs_list)} jobs. Fetching details for each...")
    
    csv_file = "astreya_jobs.csv"
    csv_headers = [
        "Job Name", 
        "Job Description", 
        "posting date", 
        "Expereince", 
        "Location", 
        "Company Name", 
        "Job Applicatio link", 
        "Job Type"
    ]
    
    with open(csv_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=csv_headers)
        writer.writeheader()
        
        for i, job in enumerate(jobs_list):
            if i % 10 == 0:
                print(f"Processing {i+1}/{len(jobs_list)}...")
                
            external_path = job.pop("externalPath")
            detail_url = f"{base_url}/wday/cxs/astreya/life-at-astreya-opportunities{external_path}"
            
            job["Company Name"] = "Astreya"
            job["Job Description"] = "Not Specified"
            job["Job Type"] = "Not Specified"
            job["Expereince"] = "Not Specified" # Workday rarely has a structured experience field, often in description
            
            try:
                detail_resp = requests.get(detail_url, headers=headers)
                if detail_resp.status_code == 200:
                    detail_data = detail_resp.json().get("jobPostingInfo", {})
                    
                    html_desc = detail_data.get("jobDescription", "")
                    if html_desc:
                        soup = BeautifulSoup(html_desc, "html.parser")
                        job["Job Description"] = soup.get_text(separator=" ").strip()
                        
                    job["Job Type"] = detail_data.get("timeType", "Not Specified")
                else:
                    print(f"Failed to get details for {job['Job Name']} (Status: {detail_resp.status_code})")
            except Exception as e:
                print(f"Error getting details for {job['Job Name']}: {e}")
            
            writer.writerow(job)
            time.sleep(0.5) # throttle to avoid rate limits
            
    print(f"Successfully saved {len(jobs_list)} jobs to {csv_file}")

if __name__ == "__main__":
    scrape_astreya()
