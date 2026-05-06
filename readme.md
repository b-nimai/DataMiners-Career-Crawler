# DataMiners-Career-Crawler 
 
DataMiners-Career-Crawler is a web scraping project developed for a hackathon. It extracts job listings from multiple company career pages, standardizes the data into a consistent format, and exports it as CSV files for easy analysis.

---

## Objective

- Scrape job listings from company career pages  
- Extract relevant job-related data  
- Standardize the data into a uniform structure  
- Export clean and structured CSV files  

---

## Companies Covered

- Pro5.ai  
- GharPayy  
- The Wine Group  
- Astreya  
- Bridgenext  
- PRI India IT Services Private Limited  
- Restroworks  
- Aviatrix  
- Hydizo Global Solutions Private Limited  
- Durlston Partners  

---

## Project Structure


DataMiners-Career-Crawler/
│
├── scrapers/ # Python scripts for each company
├── data/ # Output CSV files
├── utils/ # Helper/helper functions
├── requirements.txt # Dependencies
└── README.md # Documentation


---

## CSV Output Format

Each CSV file follows this schema:

| Field                  | Description                          |
|-----------------------|--------------------------------------|
| Job_name              | Title of the job                     |
| Job_description       | Detailed job description             |
| Posting_date          | Format: dd-mm-yyyy                   |
| Experience            | Required experience                  |
| Location              | Job location                         |
| Company_name          | Name of the company                  |
| Job_application_link  | Direct application link              |
| Type                  | Remote / Hybrid / Onsite             |

---

## Tech Stack

- Python  
- BeautifulSoup    

---

## How to Run

### 1. Clone the repository

git clone https://github.com/
<your-username>/DataMiners-Career-Crawler.git


### 2. Navigate to the project folder

cd DataMiners-Career-Crawler


### 3. Install dependencies

pip install -r requirements.txt


### 4. Run a scraper

python scrapers/<company_name>.py


---

## Deliverables

- 10 Web Scraper Scripts  
- 10 CSV Files  
- Standardized data format across all companies  
