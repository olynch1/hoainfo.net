# dependencies.py

from fastapi import Depends, HTTPException
from starlette.status import HTTP_403_FORBIDDEN
from models import User  # Adjust if needed
from auth import get_current_user  # Make sure this returns User with role and tier

# 🔐 Require a single specific role (e.g. "admin")
def require_role(required_role: str):
    def checker(user: User = Depends(get_current_user)):
        if user.role != required_role:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail=f"Access denied for role: {user.role}"
            )
        return user
    return checker

# 🔐 Require ANY one of multiple roles (e.g. "board" or "admin")
def require_any_role(*roles):
    def checker(user: User = Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail=f"Access denied. Your role '{user.role}' is not authorized."
            )
        return user
    return checker

# 💳 Require a specific subscription tier (e.g. "landlord", "household")
def require_tier(*tiers):
    def checker(user: User = Depends(get_current_user)):
        if user.subscription_tier not in tiers:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail=f"Requires subscription tier: {', '.join(tiers)}"
            )
        return user
    return checker


