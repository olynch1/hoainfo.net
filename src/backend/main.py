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
import threading
import time

# 🔐 Local imports
from backend.database import init_db, get_session
from backend.models import User
from backend.secure_routes import router as secure_router

# 👇 Add this to guarantee table creation during startup
init_db()

# 🔐 Load env vars
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# 🔐 JWT token validator
bearer_scheme = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)) -> User: 
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token payload missing email")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid JWT token")

    db = get_session()
    user = db.exec(select(User).where(User.email == email)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# 🧾 Request models
class RegisterModel(BaseModel):
    email: str
    password: str
    community_id: str

class LoginModel(BaseModel):
    email: str
    password: str
    otp: str 

# 🌐 Initialize FastAPI app
app = FastAPI()

# 🔁 Enable CORS (allow all for now — restrict later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🧠 OTP store — memory-based
otp_store = {}

def cleanup_expired_otps():
    while True:
        time.sleep(60)
        now = time.time()
        expired = [email for email, (otp, ts, attempts) in otp_store.items() if now - ts > 300]
        for email in expired:
            del otp_store[email]

# Start cleanup thread
threading.Thread(target=cleanup_expired_otps, daemon=True).start()

# 🧾 Registration route
@app.post("/register")
def register(user: RegisterModel, session: Session = Depends(get_session)):
    existing = session.exec(select(User).where(User.email == user.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt()).decode()
    new_user = User(email=user.email, password_hash=hashed_pw, community_id=user.community_id)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    otp_code = str(random.randint(100000, 999999))
    otp_store[user.email] = (otp_code, time.time(), 0)
    print(f"[OTP] {user.email}: {otp_code}")  # 🔄 Replace with email sender later
    return {"message": "User registered. OTP sent."}

# 🔐 Login route with OTP verification
@app.post("/login")
def login(credentials: LoginModel, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == credentials.email)).first()
    if not user or not bcrypt.checkpw(credentials.password.encode(), user.password_hash.encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    otp_entry = otp_store.get(credentials.email)
    if not otp_entry:   
        raise HTTPException(status_code=401, detail="OTP expired or not found")
    
    otp_code, timestamp, attempts = otp_entry
    if attempts >= 3:
        raise HTTPException(status_code=403, detail="Too many OTP attempts")

    if credentials.otp != otp_code:
        otp_store[credentials.email] = (otp_code, timestamp, attempts + 1)
        raise HTTPException(status_code=401, detail="Invalid OTP")
    
    del otp_store[credentials.email]
    payload = {"sub": user.email}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}

    # ✅ OTP passed — issue JWT
    del otp_store[credentials.email]
    payload = {"sub": user.email}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}

# 🔗 Include your secure and OTP routes
app.include_router(secure_router)

