from fastapi import FastAPI, HTTPException, Form
from dotenv import load_dotenv
import os
import random
import requests

load_dotenv()

app = FastAPI()


otp_store = {}

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(recipient_email, otp_code):
    print(f"Generated OTP for {recipient_email}: {otp_code}")

    api_key = os.getenv("RESEND_API_KEY")
    url = "https://api.resend.com/emails"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "from": "onboarding@resend.dev",
        "to": recipient_email,
        "subject": "Your OTP Code",
        "html": f"<p>Your one-time password is: <strong>{otp_code}</strong></p>"
    }

    response = requests.post(url, headers=headers, json=payload)
    print("Resend response:", response.status_code, response.text)


@app.post("/login")
def login(email: str = Form(...)):
    otp = generate_otp()
    otp_store[email] = otp
    send_otp_email(email, otp)
    return {"message": f"OTP sent to {email}"}


@app.post("/verify-otp")
def verify_otp(email: str = Form(...), code: str = Form(...)):
    stored_otp = otp_store.get(email)
    if not stored_otp:
        raise HTTPException(status_code=400, detail="No OTP found for this email")
    if stored_otp != code:
        raise HTTPException(status_code=401, detail="Invalid OTP")
    return {"message": "OTP verified successfully!"}
