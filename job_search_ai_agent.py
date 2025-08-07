# job_search_ai_agent.py
import streamlit as st
import openai
import PyPDF2
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
import csv
from datetime import datetime
import argparse
from multi_portal_bot import route_application, detect_portal

# -------------------- CONFIG -------------------- #
load_dotenv()
print("🔐 API Key Loaded:", os.getenv("OPENAI_API_KEY"))
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = st.secrets["openai"]["api_key"]
LOG_FILE = "application_log.csv"

# -------------------- Extract Resume Text -------------------- #

def extract_resume_text(file_path):
    if os.path.getsize(file_path) == 0:
        raise ValueError(f"🚫 Error: {file_path} is empty.")
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        text = ''
        for page in reader.pages:
            text += page.extract_text()
    return text

# -------------------- Scrape Jobs from Indeed -------------------- #
def scrape_indeed_jobs(query="data analyst", location="remote"):
    headers = {'User-Agent': 'Mozilla/5.0'}
    url = f"https://www.indeed.com/jobs?q={query}&l={location}"
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    jobs = []
    for card in soup.select('a.tapItem'):
        title = card.select_one('h2.jobTitle')
        company = card.select_one('.companyName')
        description = card.select_one('.job-snippet')
        link = card['href']
        if title and company and description and link:
            jobs.append({
                'title': title.text.strip(),
                'company': company.text.strip(),
                'description': description.text.strip().replace('\n', ''),
                'url': f"https://www.indeed.com{link}",
                'source': 'Indeed'
            })
    return jobs

# -------------------- Scrape Jobs from SimplyHired -------------------- #
def scrape_simplyhired_jobs(query="data analyst", location="remote"):
    headers = {'User-Agent': 'Mozilla/5.0'}
    url = f"https://www.simplyhired.com/search?q={query.replace(' ', '+')}&l={location.replace(' ', '+')}"
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    jobs = []
    for card in soup.select('div.SerpJob-jobCard'):
        title = card.select_one('a.SerpJob-link')
        company = card.select_one('.JobPosting-labelWithIcon')
        description = card.select_one('.SerpJob-snippet')
        if title and company and description:
            link = title['href']
            jobs.append({
                'title': title.text.strip(),
                'company': company.text.strip(),
                'description': description.text.strip(),
                'url': f"https://www.simplyhired.com{link}",
                'source': 'SimplyHired'
            })
    return jobs

# -------------------- Scrape Jobs from Monster -------------------- #
def scrape_monster_jobs(query="data analyst", location="remote"):
    headers = {'User-Agent': 'Mozilla/5.0'}
    url = f"https://www.monster.com/jobs/search/?q={query.replace(' ', '-')}&where={location.replace(' ', '-')}"
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    jobs = []
    for card in soup.select('section.card-content'):
        title = card.select_one('h2.title')
        company = card.select_one('div.company')
        location_tag = card.select_one('div.location')
        link = card.select_one('a')
        if title and company and link:
            jobs.append({
                'title': title.text.strip(),
                'company': company.text.strip(),
                'description': location_tag.text.strip() if location_tag else '',
                'url': link['href'],
                'source': 'Monster'
            })
    return jobs

# -------------------- Unified Multi-Portal Scraper -------------------- #
def scrape_jobs_from_all_sources(query="data analyst", location="remote"):
    print("🔍 Scraping from multiple portals...")
    jobs = []
    try:
        jobs.extend(scrape_indeed_jobs(query, location))
    except Exception as e:
        print(f"❌ Failed scraping Indeed: {e}")
    try:
        jobs.extend(scrape_simplyhired_jobs(query, location))
    except Exception as e:
        print(f"❌ Failed scraping SimplyHired: {e}")
    try:
        jobs.extend(scrape_monster_jobs(query, location))
    except Exception as e:
        print(f"❌ Failed scraping Monster: {e}")
    return jobs

# -------------------- GPT Cover Letter Generator -------------------- #
def generate_cover_letter(job_title, company, job_description, resume_text, first_name, last_name):
    prompt = f"""
You are a career assistant AI. Write a professional, concise cover letter for the following job.

Job Title: {job_title}
Company: {company}

Job Description:
{job_description}

Resume:
{resume_text}

Guidelines:
- Address it to the hiring manager
- Highlight relevant experience and skills
- Match tone to the job type (formal but enthusiastic)
- Keep it under 300 words
- End with: Sincerely, {first_name} {last_name}
"""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response['choices'][0]['message']['content']

# -------------------- GPT Resume Tailoring -------------------- #
def tailor_resume(job_description, resume_text):
    prompt = f"""
You are a resume assistant. Given this resume and job description, rewrite the resume to match the job.

Job Description:
{job_description}

Resume:
{resume_text}

Return the tailored resume only, preserving professionalism and formatting.
"""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response['choices'][0]['message']['content']

# -------------------- Application Logger -------------------- #
def log_application(first_name, last_name, email, job_url, portal, status):
    headers = ["First Name", "Last Name", "Email", "Job URL", "Portal", "Status", "Timestamp"]
    row = [
        first_name,
        last_name,
        email,
        job_url,
        portal,
        status,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ]
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(headers)
        writer.writerow(row)

# -------------------- Main Agent Function -------------------- #
def run_job_search_agent(first_name, last_name, email, resume_path, query, location):
    if not os.path.exists(resume_path):
        print(f"❌ Resume not found at {resume_path}")
        return

    print("✅ Extracting resume...")
    resume_text = extract_resume_text(resume_path)

    print("✅ Scraping jobs from multiple sources...")
    jobs = scrape_jobs_from_all_sources(query=query, location=location)

    os.makedirs("output", exist_ok=True)

    for i, job in enumerate(jobs[:5]):
        print(f"\n📌 Job {i+1}: {job['title']} at {job['company']} ({job['source']})")

        job_url = job['url']
        job_title = job['title']
        company = job['company']
        description = job['description']

        print("✍️ Generating cover letter...")
        cover_letter = generate_cover_letter(job_title, company, description, resume_text, first_name, last_name)

        print("🧩 Tailoring resume to job description...")
        tailored_resume = tailor_resume(description, resume_text)

        # Save tailored resume to file for review
        resume_file = f"output/tailored_resume_{i+1}_{company.replace(' ', '_')}.txt"
        with open(resume_file, 'w', encoding='utf-8') as f:
            f.write(tailored_resume)

        user_info = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "cover_letter": cover_letter
        }

        print(f"🧠 Detecting portal from URL: {job_url}")
        portal = detect_portal(job_url)
        print(f"🔍 Detected portal: {portal}")

        try:
            print("🛠️ Simulating application (no submission)...")
            route_application(job_url, resume_path, user_info)
            log_application(first_name, last_name, email, job_url, portal, "Success")
        except Exception as e:
            print(f"❌ Error during simulation: {e}")
            log_application(first_name, last_name, email, job_url, portal, f"Error: {e}")

# -------------------- Command Line Entry -------------------- #
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Job Search AI Agent")
    parser.add_argument("--first", help="First name", required=True)
    parser.add_argument("--last", help="Last name", required=True)
    parser.add_argument("--email", help="Email address", required=True)
    parser.add_argument("--resume", help="Path to resume PDF", required=True)
    parser.add_argument("--query", help="Job title to search", required=True)
    parser.add_argument("--location", help="Job location", required=True)

    args = parser.parse_args()

    run_job_search_agent(
        first_name=args.first,
        last_name=args.last,
        email=args.email,
        resume_path=args.resume,
        query=args.query,
        location=args.location
    )
