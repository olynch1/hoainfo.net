from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import pytz

from src.backend.dependencies import require_role, require_any_role, require_tier
from src.backend.auth_utils import verify_token
from src.backend.database import get_session
from src.backend.models import BoardVerificationRequest, User

router = APIRouter()

# 🤖 AI Helpdesk Access
@router.get("/ai/helpdesk")
def ai_helpdesk(user=Depends(require_tier("solo", "household", "landlord"))):
    return {"response": f"You're accessing premium AI support as a {user.tier} user."}

# 🧩 Submit Board Verification Request
class BoardRequestModel(BaseModel):
    community_id: str

@router.post("/board/request")
def board_verification_request(
    data: BoardRequestModel,
    user: User = Depends(verify_token),
    session: Session = Depends(get_session)
):
    existing = session.exec(
        select(BoardVerificationRequest).where(BoardVerificationRequest.user_id == user.id)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Request already submitted.")

    request = BoardVerificationRequest(
        user_id=user.id,
        community_id=data.community_id,
        approved_by=[],
        verified=False
    )
    session.add(request)
    session.commit()
    session.refresh(request)
    return {"message": "Board verification request submitted."}

# 📋 View All Board Requests
@router.get("/board/requests")
def list_board_requests(
    user: User = Depends(verify_token),
    session: Session = Depends(get_session)
):
    return session.exec(
        select(BoardVerificationRequest).where(BoardVerificationRequest.community_id == user.community_id)
    ).all()

# 🔍 View My Board Request
@router.get("/board/requests/my")
def view_my_board_request(
    user: User = Depends(verify_token),
    session: Session = Depends(get_session)
):
    request = session.exec(
        select(BoardVerificationRequest).where(BoardVerificationRequest.user_id == user.id)
    ).first()
    if not request:
        raise HTTPException(status_code=404, detail="You have not submitted a board verification request.")
    return request

# ✅ Approve Board Candidate
@router.post("/board/approve/{candidate_id}")
def approve_board_candidate(   
    candidate_id: str,
    user: User = Depends(verify_token),
    session: Session = Depends(get_session)
):
    request = session.exec( 
        select(BoardVerificationRequest).where(BoardVerificationRequest.id == candidate_id)
    ).first()
    if not request:
        raise HTTPException(status_code=404, detail="Candidate request not found")

    if user.id in request.approved_by: 
        raise HTTPException(status_code=400, detail="You have already approved this candidate")
    
    # ✅ Explicit reassignment so SQLModel detects JSON change
    updated_list = list(request.approved_by)
    updated_list.append(user.id)
    request.approved_by = updated_list

    if len(request.approved_by) >= 4:
        request.verified = True

    session.add(request)
    session.commit()
    return {
        "message": f"Approved. Total approvals: {len(request.approved_by)}",
        "verified": request.verified
    }


