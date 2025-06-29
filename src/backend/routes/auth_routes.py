from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from datetime import datetime, timedelta
from jose import jwt
import bcrypt, random, time, os

from src.backend.schemas import RegisterModel, LoginRequest, EmailRequest, OTPVerifyRequest
from src.backend.models import User
from src.backend.database import get_session, otp_store

router = APIRouter()
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
ALGORITHM = "HS256"

@router.post("/register")
def register(user: RegisterModel, session: Session = Depends(get_session)):
    existing = session.exec(select(User).where(User.email == user.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt()).decode()
    new_user = User(email=user.email, password_hash=hashed_pw, community_id=user.community_id)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    return {"message": "User registered. OTP sent."}

@router.post("/login")
def login(credentials: LoginRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == credentials.email)).first()
    if not user or not bcrypt.checkpw(credentials.password.encode(), user.password_hash.encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    otp_code = str(random.randint(100000, 999999))
    otp_store[credentials.email] = (otp_code, time.time(), 0)
    print(f"[OTP] {credentials.email}: {otp_code}")

    return {"message": "OTP sent to your email"}

@router.post("/resend-otp")
def resend_otp(request: EmailRequest):
    otp_code = str(random.randint(100000, 999999))
    otp_store[request.email] = (otp_code, time.time(), 0)
    print(f"[OTP] {request.email}: {otp_code}")
    return {"message": f"OTP reissued for {request.email}"}

@router.post("/verify-otp")
def verify_otp(request: OTPVerifyRequest, session: Session = Depends(get_session)):
    stored = otp_store.get(request.email)
    if not stored:
        raise HTTPException(status_code=400, detail="OTP not found or expired")

    otp, timestamp, attempts = stored
    if attempts >= 3:
        raise HTTPException(status_code=403, detail="Too many attempts")

    if request.otp != otp:
        otp_store[request.email] = (otp, timestamp, attempts + 1)
        raise HTTPException(status_code=401, detail="Invalid OTP")

    del otp_store[request.email]

    user = session.exec(select(User).where(User.email == request.email)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    payload = {
        "sub": user.email,
        "user_id": str(user.id),
        "role": user.role,
        "tier": user.tier,
        "community_id": user.community_id,
        "exp": datetime.utcnow() + timedelta(minutes=60),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}

