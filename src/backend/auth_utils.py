from typing import Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlmodel import select, Session
import os

from src.backend.models import User
from src.backend.database import get_session

# Load .env values
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

#Define both schemes
bearer_scheme = HTTPBearer()
optional_bearer_scheme = HTTPBearer(auto_error=False)  # For optional token

# ✅ Token verification for protected routes
def verify_token(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
    session: Session = Depends(get_session)
) -> User:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Token missing subject (email)")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid JWT token")

    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# ✅ Optional token verification for public/protected hybrid routes
def verify_token_optional(
    credentials: HTTPAuthorizationCredentials = Security(optional_bearer_scheme),
    session: Session = Depends(get_session)
) -> Optional[User]:
    if not credentials:
        return None

    try:
        payload = jwt.decode(credentials.credentials, os.getenv("SECRET_KEY", "dev-secret"), algorithms=["HS256"])
        email = payload.get("sub")
        if not email:
            return None
    except JWTError:
        return None

    user = session.exec(select(User).where(User.email == email)).first()
    return user

# ✅ Token creation for login and OTP flow
def create_access_token(email: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": email, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

