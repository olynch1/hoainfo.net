from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel import Session, select
from dependencies import require_role, require_any_role, require_tier, get_current_user
from models import Complaint, ComplaintResponse
from database import get_session

router = APIRouter()

# ✅ Admin-only access
@router.get("/admin/dashboard")
def admin_dashboard(user=Depends(require_role("admin"))):
    return {"message": f"Welcome, Admin {user.email}"}

# ✅ Board or Admin access
@router.get("/board/votes")
def view_votes(user=Depends(require_any_role("board", "admin"))):
    return {"votes": ["motion1: passed", "motion2: failed"]}

# ✅ AI Helpdesk (Tier-based)
@router.get("/ai/helpdesk")
def ai_helpdesk(user=Depends(require_tier("landlord", "household"))):
    return {
        "response": "You're accessing premium AI features. What legal help do you need today?"
    }

# ✅ Landlord-only route
@router.get("/landlord/summary")
def landlord_tools(user=Depends(require_role("landlord"))):
    return {"message": f"Landlord tools unlocked for {user.email}"}

# ✅ Household and above route
@router.get("/household/tools")
def household_tools(user=Depends(require_tier("household", "landlord"))):
    return {"message": f"Household-tier access granted to {user.email}"}

# ✅ Resident-only dashboard
@router.get("/resident/dashboard")
def resident_dashboard(user=Depends(require_role("resident"))):
    return {"message": f"Welcome to the Resident Dashboard, {user.email}"}

# ✅ Submit a complaint (all residents)
@router.post("/complaints")
def file_complaint(
    complaint: Complaint,
    session: Session = Depends(get_session),
    user=Depends(require_any_role("resident", "landlord", "household"))
):
    complaint.user_email = user.email
    session.add(complaint)
    session.commit()
    session.refresh(complaint)
    return {"message": "Complaint submitted successfully", "id": complaint.id}

# ✅ View all complaints (Admin only)
@router.get("/complaints")
def get_all_complaints(
    session: Session = Depends(get_session),
    user=Depends(require_role("admin"))
):
    return session.exec(select(Complaint)).all()

# ✅ Filter complaints by user (Admin + Board)
@router.get("/complaints/search")
def filter_complaints_by_user(email: str, session: Session = Depends(get_session), user=Depends(require_any_role("admin", "board"))):
    statement = select(Complaint).where(Complaint.user_email == email)
    return session.exec(statement).all()

