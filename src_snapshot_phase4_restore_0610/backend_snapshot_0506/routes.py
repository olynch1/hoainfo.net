# secure_routes.py
from fastapi import APIRouter, Depends
from dependencies import require_role, require_any_role, require_tier

router = APIRouter()

@router.get("/admin/dashboard")
def admin_dashboard(user=Depends(require_role("admin"))):
    return {"message": f"Welcome, Admin {user.email}"}

@router.get("/board/votes")
def board_votes(user=Depends(require_any_role("board", "admin"))):
    return {"votes": ["motion1: passed", "motion2: failed"]}

@router.get("/ai/helpdesk")
def ai_helpdesk(user=Depends(require_tier("landlord", "household"))):
    return {"response": "You're accessing premium AI support."}

