from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session
from starlette.status import HTTP_403_FORBIDDEN

from src.backend.models import User
from src.backend.database import get_db, get_session
from src.backend.auth_utils import verify_token  # ✅ trusted token verifier

# 🔐 Token config
SECRET_KEY = "super-secret-dev-key"
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# ✅ Validate current user using trusted verifier
def get_current_user(user: User = Depends(verify_token)) -> User:
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# 🔐 Require a specific role (e.g., "admin")
def require_role(required_role: str):
    def role_dependency(user: User = Depends(get_current_user)):
        if user.role != required_role:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return user
    return role_dependency

# 🔐 Require any role from a set (e.g., "board", "admin")
def require_any_role(*roles):
    def checker(user: User = Depends(verify_token)):
        if user.role not in roles:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail=f"Access denied. Your role '{user.role}' is not authorized."
            )
        return user
    return checker

# 💳 Require a specific subscription tier
def require_tier(*tiers):
    def checker(user: User = Depends(verify_token)):
        if user.tier not in tiers:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail=f"Requires subscription tier: {', '.join(tiers)}"
            )
        return user
    return checker

