from fastapi import FastAPI, HTTPException, Form, Depends, Header, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from dotenv import load_dotenv
from sqlmodel import select, Session
from starlette.responses import JSONResponse
from jose import JWTError, jwt
import bcrypt
import os
import random
import requests
import threading
import time
from database import init_db, get_session
from models import User, Message
from secure_routes import router as secure_router

load_dotenv()

app = FastAPI()
app.include_router(secure_router)
init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
TOKEN_EXPIRE_SECONDS = 3600
otp_store = {}
security = HTTPBearer()

class RegisterModel(BaseModel):
    username: str
    password: str
    role: str
    community_id: str

class LoginModel(BaseModel):
    username: str
    password: str

class OTPModel(BaseModel):
    username: str
    code: str

class MessageCreate(BaseModel):
    subject: str
    body: str
    receiver_role: str

def create_token(username: str):
    payload = {"sub": username, "exp": time.time() + TOKEN_EXPIRE_SECONDS}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(authorization: str = Header(...)):
    try:
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid auth format")
        token = parts[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except (JWTError, ValueError, KeyError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")

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

def cleanup_expired_otps():
    while True:
        now = time.time()
        expired_users = [user for user, data in otp_store.items() if now - data["timestamp"] > 180]
        for user in expired_users:
            del otp_store[user]
        time.sleep(60)

@app.on_event("startup")
def start_cleanup_thread():
    thread = threading.Thread(target=cleanup_expired_otps, daemon=True)
    thread.start()

@app.post("/register")
def register(user: RegisterModel, session: Session = Depends(get_session)):
    existing_user = session.exec(select(User).where(User.email == user.username)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_pw = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt()).decode()
    new_user = User(
        email=user.username,
        hashed_password=hashed_pw,
        role=user.role,
        community_id=user.community_id,
        is_premium=False,
        is_board_member=(user.role.lower() == "admin"),
        is_verified=False
    )
    session.add(new_user)
    session.commit()
    return {"message": "User registered successfully"}

@app.post("/login")
def login(user: LoginModel, session: Session = Depends(get_session)):
    db_user = session.exec(select(User).where(User.email == user.username)).first()
    if not db_user or not bcrypt.checkpw(user.password.encode("utf-8"), db_user.hashed_password.encode()):
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
        raise HTTPException(status_code=401, detail=f"Invalid OTP. Attempt {user_data['attempts']} of 3.")

    del otp_store[username]
    token = create_token(username)
    return {"message": "OTP verified successfully!", "token": token}

@app.get("/me")
def get_me(username: str = Depends(verify_token)):
    return {"message": f"Hello, {username}. You're authenticated!"}

@app.post("/send-message")
def send_message(
    message: MessageCreate,
    user_email: str = Depends(verify_token),
    session: Session = Depends(get_session)
):
    new_message = Message(
        sender_email=user_email,
        receiver_role=message.receiver_role,
        subject=message.subject,
        body=message.body
    )
    session.add(new_message)
    session.commit()
    return {"message": "Message sent to board successfully."}

@app.get("/board/messages")
def get_board_messages(
    user_email: str = Depends(verify_token),
    session: Session = Depends(get_session)
):
    db_user = session.exec(select(User).where(User.email == user_email)).first()
    if not db_user or not db_user.is_board_member:
        raise HTTPException(status_code=403, detail="Access denied. Board members only.")

    messages = session.exec(select(Message).where(Message.receiver_role == "board")).all()

    return [
        {
            "id": msg.id,
            "sender_email": msg.sender_email,
            "subject": msg.subject,
            "body": msg.body,
            "created_at": msg.created_at,
            "is_replied": msg.is_replied
        }
        for msg in messages
    ]

@app.get("/verify-users")
def get_unverified_users(
    user_email: str = Depends(verify_token),
    session: Session = Depends(get_session)
):
    db_user = session.exec(select(User).where(User.email == user_email)).first()
    if not db_user or not db_user.is_board_member:
        raise HTTPException(status_code=403, detail="Board access only.")

    unverified_users = session.exec(select(User).where(User.is_verified == False)).all()

    return [
        {
            "email": u.email,
            "community_id": u.community_id,
            "role": u.role,
            "created_at": u.created_at
        } for u in unverified_users
    ]

@app.patch("/verify-user/{email}")
def approve_user(
    email: str,
    user_email: str = Depends(verify_token),
    session: Session = Depends(get_session)
):
    db_user = session.exec(select(User).where(User.email == user_email)).first()
    if not db_user or not db_user.is_board_member:
        raise HTTPException(status_code=403, detail="Board access only.")

    user_to_verify = session.exec(select(User).where(User.email == email)).first()
    if not user_to_verify:
        raise HTTPException(status_code=404, detail="User not found")

    if user_to_verify.is_verified:
        return {"message": f"{email} is already verified."}

    user_to_verify.is_verified = True
    session.add(user_to_verify)
    session.commit()
    return {"message": f"{email} is now verified."}

@app.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    print("✅ STRIPE ENDPOINT HIT")
    payload = await request.body()
    print(payload)
    return JSONResponse(status_code=200, content={"status": "ok"})

@app.get("/")
def read_root():
    return {"message": "HOA backend is online."}

