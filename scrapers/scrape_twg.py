import csv
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def scrape_jobs():
    with open('twg_rendered.html', 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    # Dayforce jobs are usually in list items inside a container
    job_items = soup.find_all('li', class_='ant-list-item')
    
    base_url = 'https://jobs.dayforcehcm.com'
    company_name = 'The Wine Group'
    
    data = []
    
    for item in job_items:
        # Job Link & Title
        # Usually there are multiple links. The one inside 'test-id="job-title"' or similar
        job_title_elem = item.find('a', href=lambda h: h and '/jobs/' in h)
        if not job_title_elem:
            continue
            
        job_link = urljoin(base_url, job_title_elem.get('href'))
        job_title = job_title_elem.text.strip()
        if job_title == 'Read More':
            # Sometimes the first link is not the title, let's find the correct one
            links = item.find_all('a', href=lambda h: h and '/jobs/' in h)
            for l in links:
                if l.text.strip() != 'Read More' and l.text.strip() != '':
                    job_title = l.text.strip()
                    break
        
        # Description
        desc_elem = item.find(attrs={"test-id": "job-description"})
        job_desc = desc_elem.text.strip() if desc_elem else "N/A"
        
        # Usually Dayforce puts location in a specific span or div, we can find text that matches locations
        # Let's extract all text from small elements or specific test-ids
        location_elem = item.find(attrs={"test-id": "job-location"})
        location = location_elem.text.strip() if location_elem else "N/A"
        
        # If location is N/A, try to get it from the title (e.g., "Safety Specialist 2 - Woodbridge")
        if location == "N/A" and " - " in job_title:
            location = job_title.split(" - ")[-1].strip()
            
        date_elem = item.find(attrs={"test-id": "job-date-posted"})
        posting_date = date_elem.text.strip() if date_elem else "N/A"
        
        type_elem = item.find(attrs={"test-id": "job-type"})
        job_type = type_elem.text.strip() if type_elem else "N/A"
        
        # Experience is rarely directly on the card
        experience = "N/A"
        
        data.append({
            'Job Name': job_title,
            'Job Description': job_desc,
            'posting date': posting_date,
            'Expereince': experience,
            'Location': location,
            'Company Name': company_name,
            'Job Applicatio link': job_link,
            'Job Type': job_type
        })
        
    print(f"Found {len(data)} jobs.")
    
    # Save to CSV
    csv_file = 'twg_jobs.csv'
    headers = ['Job Name', 'Job Description', 'posting date', 'Expereince', 'Location', 'Company Name', 'Job Applicatio link', 'Job Type']
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)
        
    print(f"Saved to {csv_file}")

if __name__ == '__main__':
    scrape_jobs()
