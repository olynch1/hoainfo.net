import os
from dotenv import load_dotenv
import bcrypt
import jwt
from datetime import datetime, timedelta
from fastapi import Header, HTTPException

# ✅ Explicitly load the correct .env file from backend directory
load_dotenv(dotenv_path="src/backend/.env")
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret")

print("[KEY] ACTUAL SECRET_KEY:", SECRET_KEY)  # Debug only; remove in production

# ✅ Token Verification (used in Depends and Middleware)
def verify_token(authorization: str = Header(...)):
    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return type("User", (), payload)  # Mock User object with attributes like user.email
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ✅ Hash a plain-text password
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

# ✅ Verify a plain password against a hashed one
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

# ✅ Create JWT token from user object
def create_jwt_token(user):
    payload = {
        "sub": user.email,
        "id": user.id,
        "role": user.role,
        "community_id": user.community_id,
        "exp": datetime.utcnow() + timedelta(days=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

