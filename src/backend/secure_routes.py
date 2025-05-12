from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from sqlalchemy import Column
from sqlalchemy.dialects.sqlite import JSON

from backend.dependencies import require_role, require_any_role, require_tier, get_current_user
from backend.database import get_session
from backend.models import Complaint, Message, User, BoardVerificationRequest

router = APIRouter()

# --- Admin & Board Routes ---
@router.get("/admin/dashboard")
def admin_dashboard(user=Depends(require_role("admin"))):
    return {"message": f"Welcome, Admin {user.email}"}

@router.get("/board/votes")
def board_votes(user=Depends(require_any_role("board", "admin"))):
    return {"votes": ["motion1: passed", "motion2: failed"]}

# --- Complaints ---
class ComplaintModel(BaseModel):
    title: str
    description: str
    timestamp: str
    user_email: str

@router.post("/complaints")
def submit_complaint(data: ComplaintModel, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    new_complaint = Complaint(
        title=data.title,
        description=data.description,
        timestamp=data.timestamp,
        user_email=data.user_email,
        user_id=user.id,
        community_id=user.community_id
    )
    session.add(new_complaint)
    session.commit()
    return {"message": "Complaint submitted."}

# --- Messages ---
class MessageModel(BaseModel):
    subject: str
    body: str
    timestamp: str

@router.post("/messages")
def send_message(data: MessageModel, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    new_msg = Message(
        subject=data.subject,
        body=data.body,
        timestamp=data.timestamp,
        user_id=user.id,
        community_id=user.community_id
    )
    session.add(new_msg)
    session.commit()
    return {"message": "Message sent."}

# --- AI Helpdesk ---
@router.get("/ai/helpdesk")
def ai_helpdesk(user=Depends(require_tier("landlord", "household", "solo"))):
    print(f"[DEBUG] User tier: {user.tier}")
    return {"response": f"You're accessing premium AI support as a {user.tier} user."}

# --- Simulated Tier Upgrade ---
@router.post("/upgrade")
def upgrade_tier(user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    user.tier = "landlord"
    session.add(user)
    session.commit()
    return {"message": f"{user.email} upgraded to landlord tier."}

# --- Board Verification ---
class BoardRequestModel(BaseModel):
    user_id: str
    community_id: str

@router.post("/board/request")
def submit_board_verification(data: BoardRequestModel, session: Session = Depends(get_session)):
    existing = session.exec(
        select(BoardVerificationRequest).where(
            BoardVerificationRequest.user_id == data.user_id,
            BoardVerificationRequest.community_id == data.community_id
        )
    ).first()

    if existing:
        return {"message": "Request already exists."}

    request = BoardVerificationRequest(
        user_id=data.user_id,
        community_id=data.community_id,
        approved_by=[],
        verified=False
    )
    session.add(request)
    session.commit()
    return {"message": "Board verification request submitted."}

@router.post("/board/approve/{candidate_id}")
def approve_board_candidate(candidate_id: str, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    req = session.get(BoardVerificationRequest, candidate_id)
    if not req:
        raise HTTPException(status_code=404, detail="Candidate not found")

    if user.community_id != req.community_id:
        raise HTTPException(status_code=403, detail="Cannot approve outside your community")

    if user.id in req.approved_by:
        return {"message": "You already approved this request."}

    req.approved_by.append(user.id)

    if len(req.approved_by) >= 4:
        req.verified = True

    session.add(req)
    session.commit()
    return {
        "message": "Approval recorded.",
        "current_approvals": len(req.approved_by),
        "verified": req.verified
    }

@router.get("/board/status/{user_id}")
def check_board_status(user_id: str, session: Session = Depends(get_session)):
    req = session.exec(
        select(BoardVerificationRequest).where(BoardVerificationRequest.user_id == user_id)
    ).first()

    if not req:
        return {"verified": False, "approvals": 0}

    return {
        "verified": req.verified,
        "approvals": len(req.approved_by),
        "approved_by": req.approved_by
    }

@router.get("/board/requests")
def list_all_requests(session: Session = Depends(get_session)):
    return session.exec(select(BoardVerificationRequest)).all()

