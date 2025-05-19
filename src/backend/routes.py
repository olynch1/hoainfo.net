from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from datetime import datetime
from typing import List
import pytz

from src.backend.dependencies import require_role, require_any_role, require_tier
from src.backend.database import get_session
from src.backend.auth_utils import verify_token
from src.backend.models import User, Complaint

router = APIRouter()

# 🔐 Admin-only route
@router.get("/admin/dashboard")
def admin_dashboard(user=Depends(require_role("admin"))):
    return {"message": f"Welcome, Admin {user.email}"}

# 🔐 Board or Admin route
@router.get("/board/votes")
def board_votes(user=Depends(require_any_role("board", "admin"))):
    return {"votes": ["motion1: passed", "motion2: failed"]}

# 💳 Premium tier access route
@router.get("/ai/helpdesk")
def ai_helpdesk(user=Depends(require_tier("landlord", "household"))):
    return {"response": f"You're accessing premium AI support as a {user.tier} user."}

# 🆙 Simulated plan upgrade route
@router.post("/upgrade")
def upgrade_tier(user: User = Depends(verify_token), session: Session = Depends(get_session)):
    user.tier = "landlord"
    session.commit()
    return {"message": f"{user.email} upgraded to landlord tier."}

# 📩 Submit complaint route
class ComplaintModel(BaseModel):
    title: str
    description: str

@router.post("/complaints")
def submit_complaint(
    data: ComplaintModel,
    user: User = Depends(verify_token),
    session: Session = Depends(get_session)
):
    tz = pytz.timezone("America/Los_Angeles")
    local_timestamp = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

    complaint = Complaint(
        title=data.title,
        description=data.description,
        timestamp=local_timestamp,
        user_id=user.id,
        community_id=user.community_id
    )
    session.add(complaint)
    session.commit()
    return {"message": "Complaint submitted."}

@router.get("/complaints", response_model=List[Complaint])
def get_complaints(
    user: User = Depends(verify_token),
    session: Session = Depends(get_session)
):
    complaints = session.exec(
        select(Complaint).where(Complaint.community_id == user.community_id)
    ).all()
    return complaints
