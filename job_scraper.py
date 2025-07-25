import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Initialize Google Sheet connection
def init_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    sheet = client.open_by_key(sheet_id).sheet1
    return sheet

# Example: Fetch jobs from SerpApi (replace with your actual scraping logic)
def fetch_jobs():
    serpapi_key = os.getenv("SERPAPI_KEY")
    # Example query parameters — customize as needed
    params = {
        "engine": "google_jobs",
        "q": "SAP Hybris Developer OR Java Full Stack Developer OR Frontend Developer",
        "location": "United States",
        "api_key": serpapi_key,
        "limit": 20
    }
    response = requests.get("https://serpapi.com/search.json", params=params)
    data = response.json()
    # Extract and return job info list - you need to adapt this based on actual response structure
    jobs = []
    for job in data.get("jobs_results", []):
        jobs.append({
            "title": job.get("title"),
            "company": job.get("company_name"),
            "location": job.get("location"),
            "link": job.get("link"),
            "summary": job.get("description"),
            "tags": ["Skill match", "Remote/Flexibility"]  # adjust as needed
        })

print(f"Fetched {len(jobs)} jobs")
    return jobs

# Update Google Sheet with new jobs
def update_sheet(sheet, jobs):
    # Clear existing data except headers (assuming headers on row 1)
    sheet.resize(rows=1)
    # Append header row if needed
    sheet.append_row(["Job Title", "Company", "Location", "Apply Link", "Summary", "Tags"])
    for job in jobs:
        sheet.append_row([
            job["title"],
            job["company"],
            job["location"],
            job["link"],
            job["summary"],
            ", ".join(job["tags"])
        ])

# Send email alert with job listings
def send_email(jobs):
    gmail_user = os.getenv("GMAIL_ADDRESS")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD")
    to_email = gmail_user  # or set a different recipient

    subject = f"Hourly Job Alert: {len(jobs)} new jobs found"
    body = ""
    for job in jobs:
        body += f"{job['title']} at {job['company']} ({job['location']})\n"
        body += f"Apply here: {job['link']}\n"
        body += f"Summary: {job['summary']}\n"
        body += f"Tags: {', '.join(job['tags'])}\n\n"

    msg = MIMEMultipart()
    msg["From"] = gmail_user
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_password)
            server.send_message(msg)
        print("Email sent successfully.")
    except Exception as e:
        print("Error sending email:", e)

def main():
    sheet = init_sheet()
    jobs = fetch_jobs()
    if jobs:
        update_sheet(sheet, jobs)
        send_email(jobs)
    else:
        print("No new jobs found.")

if __name__ == "__main__":
    main()
