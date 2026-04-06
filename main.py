import requests
import time
import json
import os
from datetime import datetime

# Config
TELEGRAM_TOKEN = "8514420809:AAFiBzlC-ns_qp8Zq_2ZAoXuGkdxr7pIQA8"
CHAT_ID = "135994270"
REED_API_KEY = "64981013-877a-439a-aa95-da0c901a5f71"
ADZUNA_APP_ID = "8ee4626f"
ADZUNA_APP_KEY = "dae057b5b757e19df2cdfff0d1987fe6"
SEEN_FILE = "seen_jobs.json"

KEYWORDS = [
    "SDET",
    "QA Automation Engineer",
    "Software Engineer in Test",
    "Test Automation Engineer",
    "Quality Assurance Automation"
]

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        })
    except Exception as e:
        print(f"Telegram error: {e}")

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE) as f:
            return json.load(f)
    return []

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(seen, f)

def search_reed(keyword):
    url = "https://www.reed.co.uk/api/1.0/search"
    params = {
        "keywords": keyword,
        "location": "London",
        "distancefromlocation": 10,
        "resultsToTake": 10
    }
    try:
        r = requests.get(url, params=params, auth=(REED_API_KEY, ""), timeout=10)
        return r.json().get("results", [])
    except Exception as e:
        print(f"Reed error: {e}")
        return []

def search_adzuna(keyword):
    url = f"https://api.adzuna.com/v1/api/jobs/gb/search/1"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "what": keyword,
        "where": "London",
        "distance": 10,
        "results_per_page": 10,
        "content-type": "application/json"
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        return r.json().get("results", [])
    except Exception as e:
        print(f"Adzuna error: {e}")
        return []

def check_jobs():
    seen = load_seen()
    new_jobs = []

    for keyword in KEYWORDS:
        # Reed
        for job in search_reed(keyword):
            job_id = f"reed_{job.get('jobId')}"
            if job_id not in seen:
                seen.append(job_id)
                salary = ""
                if job.get("minimumSalary"):
                    salary = f"\n💰 £{int(job['minimumSalary']):,}"
                    if job.get("maximumSalary"):
                        salary += f" – £{int(job['maximumSalary']):,}"
                new_jobs.append(
                    f"🆕 <b>{job.get('jobTitle', '')}</b>\n"
                    f"🏢 {job.get('employerName', '')}\n"
                    f"📍 {job.get('locationName', 'London')}"
                    f"{salary}\n"
                    f"🔗 https://www.reed.co.uk/jobs/{job.get('jobId')}\n"
                    f"📌 Source: Reed"
                )

        # Adzuna
        for job in search_adzuna(keyword):
            job_id = f"adzuna_{job.get('id')}"
            if job_id not in seen:
                seen.append(job_id)
                salary = ""
                if job.get("salary_min"):
                    salary = f"\n💰 £{int(job['salary_min']):,}"
                    if job.get("salary_max"):
                        salary += f" – £{int(job['salary_max']):,}"
                new_jobs.append(
                    f"🆕 <b>{job.get('title', '')}</b>\n"
                    f"🏢 {job.get('company', {}).get('display_name', '')}\n"
                    f"📍 {job.get('location', {}).get('display_name', 'London')}"
                    f"{salary}\n"
                    f"🔗 {job.get('redirect_url', '')}\n"
                    f"📌 Source: Adzuna"
                )

    save_seen(seen)

    if new_jobs:
        send_telegram(f"🔍 Found <b>{len(new_jobs)}</b> new jobs!")
        for job_msg in new_jobs:
            send_telegram(job_msg)
            time.sleep(0.5)
        print(f"[{datetime.now()}] Sent {len(new_jobs)} new jobs")
    else:
        print(f"[{datetime.now()}] No new jobs")

if __name__ == "__main__":
    send_telegram("✅ London Jobs Bot started!\nChecking Reed + Adzuna every hour... 🔍")
    while True:
        check_jobs()
        time.sleep(3600)
