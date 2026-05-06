import requests
from bs4 import BeautifulSoup
import csv
import time
import json
import re

CSV_FILE = 'bridgenext_jobs.csv'
CSV_HEADERS = ['Job Name', 'Job Description', 'posting date', 'Expereince', 'Location', 'Company Name', 'Job Applicatio link', 'Job Type']

jobs_data = []

def scrape_main_site():
    print("Scraping URL 1: https://www.bridgenext.com/company/careers/india-openings/")
    url = "https://www.bridgenext.com/company/careers/india-openings/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        job_containers = soup.find_all('div', class_='job-position-container')
        print(f"Found {len(job_containers)} jobs on main site.")
        
        for container in job_containers:
            job_name = ""
            location = "Not Specified"
            experience = "Not Specified"
            job_link = ""
            
            title_elem = container.find('h2')
            if title_elem and title_elem.find('a'):
                job_name = title_elem.text.strip()
                job_link = "https://www.bridgenext.com" + title_elem.find('a')['href'] if title_elem.find('a')['href'].startswith('/') else title_elem.find('a')['href']
            
            # Extract Location and Experience from divs
            divs = container.find_all('div')
            for div in divs:
                text = div.text.strip()
                if text.startswith("Location:"):
                    location = text.replace("Location:", "").strip()
                elif text.startswith("Experience:"):
                    experience = text.replace("Experience:", "").strip()
            
            # Fetch job description
            description = ""
            if job_link:
                try:
                    res = requests.get(job_link, headers=headers)
                    job_soup = BeautifulSoup(res.text, 'html.parser')
                    content = job_soup.find('div', class_='entry-content')
                    if content:
                        description = content.text.strip()
                    else:
                        description = "Not Found"
                except Exception as e:
                    print(f"Error fetching {job_link}: {e}")
            
            jobs_data.append({
                'Job Name': job_name,
                'Job Description': description,
                'posting date': 'Not Specified',
                'Expereince': experience,
                'Location': location,
                'Company Name': 'Bridgenext',
                'Job Applicatio link': job_link,
                'Job Type': 'Full time' # Assuming full time for main site
            })
            
    except Exception as e:
        print(f"Error scraping main site: {e}")

def scrape_icims_search_page(search_url):
    print(f"Scraping iCIMS Search Page: {search_url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    # Needs to hit the iframe URL directly
    if 'in_iframe' not in search_url:
        if '?' in search_url:
            search_url += '&in_iframe=1'
        else:
            search_url += '?in_iframe=1'
            
    try:
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        job_links = soup.find_all('a', class_='iCIMS_Anchor')
        print(f"Found {len(job_links)} jobs on this search page.")
        
        for a in job_links:
            job_url = a['href']
            if 'in_iframe' not in job_url:
                if '?' in job_url:
                    job_url += '&in_iframe=1'
                else:
                    job_url += '?in_iframe=1'
                    
            try:
                res = requests.get(job_url, headers=headers)
                job_soup = BeautifulSoup(res.text, 'html.parser')
                
                job_name_elem = job_soup.find('h1', class_='iCIMS_Header')
                job_name = job_name_elem.text.strip() if job_name_elem else "Not Specified"
                
                location = "Not Specified"
                loc_div = job_soup.find('div', class_='header left')
                if loc_div:
                    spans = loc_div.find_all('span')
                    if len(spans) > 1:
                        location = spans[1].text.strip()
                    else:
                        location = loc_div.text.replace('Job Locations', '').strip()
                        
                job_type = "Not Specified"
                tags = job_soup.find_all('div', class_='iCIMS_JobHeaderTag')
                for tag in tags:
                    dt = tag.find('dt')
                    dd = tag.find('dd')
                    if dt and dd:
                        if 'Type' in dt.text:
                            job_type = dd.text.strip()
                            
                description_div = job_soup.find('div', class_='iCIMS_JobContent')
                description = description_div.text.strip() if description_div else "Not Specified"
                
                # Try to find experience in description
                experience = "Not Specified"
                # Use basic regex to find experience patterns
                exp_match = re.search(r'(\d+[\+-]?\s*(to|-)?\s*\d*\s*years?)', description, re.IGNORECASE)
                if exp_match:
                    experience = exp_match.group(1)
                
                # Determine clean job link
                clean_job_link = job_url.split('?')[0]
                
                jobs_data.append({
                    'Job Name': job_name,
                    'Job Description': description,
                    'posting date': 'Not Specified',
                    'Expereince': experience,
                    'Location': location,
                    'Company Name': 'Bridgenext',
                    'Job Applicatio link': clean_job_link,
                    'Job Type': job_type
                })
                
                time.sleep(0.5) # Be respectful
            except Exception as e:
                print(f"Error parsing job {job_url}: {e}")
                
    except Exception as e:
        print(f"Error scraping search page {search_url}: {e}")


def main():
    scrape_main_site()
    
    icims_urls = [
        "https://careers-bridgenext.icims.com/jobs/search?ss=1&searchLocation=12955--",
        "https://careers-bridgenext.icims.com/jobs/search?ss=1&searchLocation=12781--&mobile=false&width=1280&height=500&bga=true&needsRedirect=false&jan1offset=330&jun1offset=330"
    ]
    
    for url in icims_urls:
        scrape_icims_search_page(url)
        
    print(f"Total jobs collected: {len(jobs_data)}")
    
    with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=CSV_HEADERS)
        writer.writeheader()
        for job in jobs_data:
            writer.writerow(job)
            
    print(f"Data saved to {CSV_FILE}")

if __name__ == "__main__":
    main()
