import requests
import random
import time

BASE_URL = "http://127.0.0.1:8000"
email = f"testuser_{random.randint(100000, 999999):x}@example.com"
password = "Test1234!"
token = None

def register():
    print(f"🟢 Registering: {email}")
    r = requests.post(f"{BASE_URL}/register", json={
        "email": email,
        "password": password,
        "community_id": "00001"
    })
    print(f"➡️ Register Response: {r.status_code}", r.text)

def verify_otp():
    global token
    otp = input("📨 Enter the OTP sent to your email: ")
    r = requests.post(f"{BASE_URL}/login", json={
        "email": email,
        "password": password,
        "otp": otp
    })
    if r.status_code == 200:
        token = r.json()["access_token"]
        print("✅ Logged in successfully.")
        print(f"🔐 Your JWT token:\n{token}")
    else:
        print("❌ Login failed:", r.status_code, r.text)

def submit_complaint():
    r = requests.post(f"{BASE_URL}/complaints", json={
        "title": "Gate Still Broken",
        "description": "Day 5. Gate not opening for deliveries.",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "user_email": email
    }, headers={"Authorization": f"Bearer {token}"})
    print("📝 Complaint:", r.status_code, r.text)

def send_message():
    r = requests.post(f"{BASE_URL}/messages", json={
        "subject": "Need Help with Gate",
        "body": "The delivery guy can’t get in again.",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }, headers={"Authorization": f"Bearer {token}"})
    print("📩 Message:", r.status_code, r.text)

def upgrade_tier():
    r = requests.post(f"{BASE_URL}/upgrade", headers={"Authorization": f"Bearer {token}"})
    print("⬆️ Upgrade Tier:", r.status_code, r.text)

def access_ai_helpdesk():
    r = requests.get(f"{BASE_URL}/ai/helpdesk", headers={"Authorization": f"Bearer {token}"})
    print("🤖 AI Helpdesk:", r.status_code, r.text)

def run():
    register()
    verify_otp()
    submit_complaint()
    send_message()
    upgrade_tier()
    access_ai_helpdesk()

if __name__ == "__main__":
    run()

