from fastapi import Depends, HTTPException
from starlette.status import HTTP_403_FORBIDDEN
from src.backend.models import User
from src.backend.auth_utils import verify_token  # ✅ use this version only

# 🔐 Require a single specific role (e.g. "admin")
def require_role(required_role: str):
    def checker(user: User = Depends(verify_token)):
        if user.role != required_role:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail=f"Access denied for role: {user.role}"
            )
        return user
    return checker

# 🔐 Require ANY one of multiple roles (e.g. "board" or "admin")
def require_any_role(*roles):
    def checker(user: User = Depends(verify_token)):
        if user.role not in roles:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail=f"Access denied. Your role '{user.role}' is not authorized."
            )
        return user
    return checker

# 💳 Require a specific subscription tier (e.g. "landlord", "household")
def require_tier(*tiers):
    def checker(user: User = Depends(verify_token)):
        if user.tier not in tiers:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail=f"Requires subscription tier: {', '.join(tiers)}"
            )
        return user
    return checker

