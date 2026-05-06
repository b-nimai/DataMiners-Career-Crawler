import csv
import requests
from bs4 import BeautifulSoup

def scrape_jobs():
    url = "https://gharpayy.com/careers/index.html"
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Failed to fetch the webpage. Status code: {response.status_code}")
        return

    soup = BeautifulSoup(response.content, 'html.parser')
    job_posts = soup.find_all('div', class_='single-job-post')
    
    csv_file = "gharpayy_jobs.csv"
    
    with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # Write the header
        writer.writerow([
            "Job Name", 
            "Job Description", 
            "Posting Date", 
            "Experience", 
            "Location", 
            "Company Name", 
            "Job Application Link", 
            "Job Type",
            "Salary"
        ])
        
        for post in job_posts:
            # Job Name
            header = post.find('div', class_='job-header')
            job_name = header.find('h3').text.strip() if header and header.find('h3') else "Not Specified"
            
            # Location
            location = header.find('p').text.strip() if header and header.find('p') else "Not Specified"
            
            # Job Description (Responsibilities)
            inner = post.find('div', class_='job-inner')
            responsibilities_ul = inner.find('ul') if inner else None
            job_desc = ""
            if responsibilities_ul:
                res_items = responsibilities_ul.find_all('li')
                job_desc = "; ".join([item.text.strip() for item in res_items])
            else:
                job_desc = "Not Specified"
                
            # Salary and Application Link
            salary_box = inner.find('div', class_='salary-box') if inner else None
            salary = "Not Specified"
            app_link = "Not Specified"
            
            if salary_box:
                salary_tag = salary_box.find('p')
                if salary_tag:
                    salary = salary_tag.text.strip()
                
                # The 'a' tag points to a Google Form. The job details are on this page itself.
                app_link = url
            
            # Fields not explicitly provided on the page
            posting_date = "Not Specified"
            experience = "Not Specified"
            company_name = "Gharpayy"
            job_type = "Not Specified"
            
            writer.writerow([
                job_name,
                job_desc,
                posting_date,
                experience,
                location,
                company_name,
                app_link,
                job_type,
                salary
            ])
            
    print(f"Successfully scraped {len(job_posts)} jobs and saved to {csv_file}")

if __name__ == "__main__":
    scrape_jobs()
