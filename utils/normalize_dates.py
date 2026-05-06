import csv
import glob
import re
from datetime import datetime, timedelta

def parse_date(date_str):
    date_str = date_str.strip()
    if date_str in ('Not Specified', 'N/A', '', 'None'):
        return 'Not Specified'
        
    if re.match(r'^\d{2}/\d{2}/\d{4}$', date_str):
        return date_str
        
    today = datetime.now()
    
    if date_str.lower() == 'today':
        return today.strftime('%d/%m/%Y')
    if date_str.lower() == 'yesterday':
        return (today - timedelta(days=1)).strftime('%d/%m/%Y')
    
    days_ago_match = re.search(r'(\d+)\+?\s*[dD]ays? [aA]go', date_str)
    if days_ago_match:
        days = int(days_ago_match.group(1))
        return (today - timedelta(days=days)).strftime('%d/%m/%Y')
        
    twg_match = re.search(r'[A-Za-z]+, ([A-Za-z]+ \d{1,2}, \d{4})', date_str)
    if twg_match:
        try:
            dt = datetime.strptime(twg_match.group(1), '%B %d, %Y')
            return dt.strftime('%d/%m/%Y')
        except ValueError:
            pass

    if '-' in date_str:
        parts = date_str.split('-')
        if len(parts) == 3:
            if len(parts[0]) == 4:
                return f'{parts[2].zfill(2)}/{parts[1].zfill(2)}/{parts[0]}'
            elif len(parts[2]) == 4:
                return f'{parts[0].zfill(2)}/{parts[1].zfill(2)}/{parts[2]}'
                
    return date_str

def main():
    for f in glob.glob('*/*_jobs.csv'):
        print(f"Processing {f}...")
        rows = []
        with open(f, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            fieldnames = reader.fieldnames
            
            # Identify the date column
            date_col = 'posting date' if 'posting date' in fieldnames else ('Posting Date' if 'Posting Date' in fieldnames else None)
            
            for row in reader:
                if date_col and row[date_col]:
                    row[date_col] = parse_date(row[date_col])
                rows.append(row)
                
        with open(f, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            
    print("Done normalizing dates.")

if __name__ == "__main__":
    main()
