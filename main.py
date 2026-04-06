import requests
import time
import json
import os
from datetime import datetime

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

def send_telegram(message, retries=3):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    for attempt in range(retries):
        try:
            r = requests.post(url, json={
                "chat_id": CHAT_ID,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }, timeout=15)
            if r.status_code == 200:
                print(f"[{datetime.now()}] Telegram OK")
                return True
            else:
                print(f"[{datetime.now()}] Telegram error {r.status_code}: {r.text}")
        except Exception as e:
            print(f"[{datetime.now()}] Telegram exception attempt {attempt+1}: {e}")
        time.sleep(5)
    return False

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE) as f:
            return json.load(f)
    return []

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(seen, f)

def search_reed(keyword):
    try:
        r = requests.get(
            "https://www.reed.co.uk/api/1.0/search",
            params={"keywords": keyword, "location": "London", "distancefromlocation": 10, "resultsToTake": 10},
            auth=(REED_API_KEY, ""), timeout=15
        )
        return r.json().get("results", [])
    except Exception as e:
        print(f"[{datetime.now()}] Reed error: {e}")
        return []

def search_adzuna(keyword):
    try:
        r = requests.get(
            "https://api.adzuna.com/v1/api/jobs/gb/search/1",
            params={"app_id": ADZUNA_APP_ID, "app_key": ADZUNA_APP_KEY,
                    "what": keyword, "where": "London", "distance": 10, "results_per_page": 10},
            timeout=15
        )
        return r.json().get("results", [])
    except Exception as e:
        print(f"[{datetime.now()}] Adzuna error: {e}")
        return []

def check_jobs():
    seen = load_seen()
    new_jobs = []

    for keyword in KEYWORDS:
        for job in search_reed(keyword):
            job_id = f"reed_{job.get('jobId')}"
            if job_id not in seen:
                seen.append(job_id)
                salary = f"\n💰 £{int(job['minimumSalary']):,}" if job.get("minimumSalary") else ""
                new_jobs.append(f"🆕 <b>{job.get('jobTitle','')}</b>\n🏢 {job.get('employerName','')}\n📍 {job.get('locationName','London')}{salary}\n🔗 https://www.reed.co.uk/jobs/{job.get('jobId')}\n📌 Reed")

        for job in search_adzuna(keyword):
            job_id = f"adzuna_{job.get('id')}"
            if job_id not in seen:
                seen.append(job_id)
                salary = f"\n💰 £{int(job['salary_min']):,}" if job.get("salary_min") else ""
                new_jobs.append(f"🆕 <b>{job.get('title','')}</b>\n🏢 {job.get('company',{}).get('display_name','')}\n📍 {job.get('location',{}).get('display_name','London')}{salary}\n🔗 {job.get('redirect_url','')}\n📌 Adzuna")

    save_seen(seen)

    if new_jobs:
        print(f"[{datetime.now()}] Found {len(new_jobs)} new jobs")
        send_telegram(f"🔍 <b>{len(new_jobs)} нових вакансій!</b>")
        for msg in new_jobs:
            send_telegram(msg)
            time.sleep(1)
    else:
        print(f"[{datetime.now()}] No new jobs")

if __name__ == "__main__":
    print(f"[{datetime.now()}] Bot starting...")
    ok = send_telegram("✅ London Jobs Bot started!\nЩогодини перевіряю Reed + Adzuna 🔍")
    print(f"[{datetime.now()}] Telegram reachable: {ok}")
    while True:
        try:
            check_jobs()
        except Exception as e:
            print(f"[{datetime.now()}] Error: {e}")
        print(f"[{datetime.now()}] Sleeping 1 hour...")
        time.sleep(3600)
