from fastapi import FastAPI, HTTPException, Form, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from sqlmodel import select
import os
import random
import requests
import time
import bcrypt
from jose import JWTError, jwt
import threading

from .models import User
from .database import init_db, get_session

load_dotenv()
app = FastAPI()
init_db()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT config
SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
TOKEN_EXPIRE_SECONDS = 3600

def create_token(username: str):
    payload = {
        "sub": username,
        "exp": time.time() + TOKEN_EXPIRE_SECONDS
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str = Header(...)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# In-memory OTP store
otp_store = {}

# Cleanup task to remove expired OTPs
def cleanup_expired_otps():
    while True:
        now = time.time()
        expired = [email for email, data in otp_store.items() if now - data["timestamp"] > 180]
        for email in expired:
            del otp_store[email]
            print(f"[CLEANUP] Expired OTP removed for: {email}")
        time.sleep(60)

@app.on_event("startup")
def start_cleanup_thread():
    thread = threading.Thread(target=cleanup_expired_otps, daemon=True)
    thread.start()

# Pydantic model for user
class UserLogin(BaseModel):
    username: str
    password: str

@app.post("/register")
def register(user: UserLogin):
    with get_session() as session:
        existing_user = session.exec(select(User).where(User.email == user.username)).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="User already exists")

        hashed_pw = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt()).decode()
        new_user = User(email=user.username, hashed_password=hashed_pw)
        session.add(new_user)
        session.commit()
        return {"message": "User registered successfully"}

@app.post("/login")
def login(user: UserLogin):
    with get_session() as session:
        db_user = session.exec(select(User).where(User.email == user.username)).first()
        if not db_user:
            raise HTTPException(status_code=401, detail="Invalid username or password")

        if not bcrypt.checkpw(user.password.encode("utf-8"), db_user.hashed_password.encode()):
            raise HTTPException(status_code=401, detail="Invalid username or password")

        otp = str(random.randint(100000, 999999))
        otp_store[user.username] = {
            "otp": otp,
            "timestamp": time.time(),
            "attempts": 0
        }
        send_otp_email(user.username, otp)
        return {"message": f"OTP sent to {user.username}"}

@app.post("/verify-otp")
def verify_otp(username: str = Form(...), code: str = Form(...)):
    user_data = otp_store.get(username)
    if not user_data:
        raise HTTPException(status_code=404, detail="No OTP found for this user")

    if time.time() - user_data["timestamp"] > 180:
        del otp_store[username]
        raise HTTPException(status_code=410, detail="OTP expired")

    user_data.setdefault("attempts", 0)
    if user_data["attempts"] >= 3:
        raise HTTPException(status_code=429, detail="Too many invalid attempts. Please request a new OTP.")

    if user_data["otp"] != code:
        user_data["attempts"] += 1
        raise HTTPException(
            status_code=401,
            detail=f"Invalid OTP. Attempt {user_data['attempts']} of 3."
        )

    del otp_store[username]
    token = create_token(username)
    return {"message": "OTP verified successfully!", "token": token}

@app.get("/me")
def get_me(username: str = Depends(verify_token)):
    return {"message": f"Hello, {username}. You're authenticated!"}

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

