import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import gspread
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
import os

# Load credentials from environment variables
GMAIL_ADDRESS = os.environ["GMAIL_ADDRESS"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
SERPAPI_KEY = os.environ["SERPAPI_KEY"]
GOOGLE_SHEET_ID = os.environ["GOOGLE_SHEET_ID"]

# Define job titles
job_roles = [
    "SAP Hybris Developer", "SAP Commerce Cloud Developer", "Java Full Stack Developer",
    "Java Backend Developer", "Frontend Developer React", "Frontend Developer Angular"
]

# Initialize Google Sheets API
def init_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    return client.open_by_key(GOOGLE_SHEET_ID).sheet1

# Email sender
def send_email(job_list):
    msg = MIMEMultipart()
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = GMAIL_ADDRESS
    msg["Subject"] = "📬 Hourly Job Alerts - SAP/Java/Frontend Roles"

    body = ""
    for job in job_list:
        body += f"""**{job['title']}**  
Company: {job['company']}  
Location: {job['location']}  
🔗 [Apply Now]({job['link']})  
Summary: {job['summary']}  
Tags: {job['tags']}\n\n"""

    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.send_message(msg)

# Get jobs from SerpApi
def fetch_jobs():
    all_jobs = []
    for role in job_roles:
        url = f"https://serpapi.com/search.json?q={role.replace(' ', '+')}+United+States&engine=google_jobs&api_key={SERPAPI_KEY}"
        res = requests.get(url)
        jobs = res.json().get("jobs_results", [])
        for job in jobs[:5]:
            all_jobs.append({
                "title": job.get("title", "N/A"),
                "company": job.get("company_name", "N/A"),
                "location": job.get("location", "N/A"),
                "link": job.get("related_links", [{}])[0].get("link", ""),
                "summary": job.get("description", "").replace("\n", " ")[:150] + "...",
                "tags": "[Skill Match, U.S., Remote/Flexibility]",
                "timestamp": datetime.now().isoformat(),
                "source": "SerpApi"
            })
    return all_jobs

# Push new jobs to Sheet
def update_sheet(sheet, jobs):
    existing_links = [row[3] for row in sheet.get_all_values()[1:]]
    new_jobs = []
    for job in jobs:
        if job["link"] not in existing_links:
            sheet.append_row([
                job["title"], job["company"], job["location"], job["link"],
                job["summary"], job["tags"], job["timestamp"], job["source"]
            ])
            new_jobs.append(job)
    return new_jobs

def main():
    sheet = init_sheet()
    jobs = fetch_jobs()
    new_jobs = update_sheet(sheet, jobs)
    if new_jobs:
        send_email(new_jobs)

if __name__ == "__main__":
    main()
