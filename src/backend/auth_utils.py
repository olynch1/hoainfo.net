from typing import Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv
from fastapi import HTTPException, Security, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from jose import JWTError, jwt
from database import get_session
from src.backend.models import User
from sqlmodel import select, Session
import os

from src.backend.models import User
from src.backend.database import get_session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

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

def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = session.exec(select(User).where(User.id == user_id)).first()
    if user is None:
        raise credentials_exception
    return user

