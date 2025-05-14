from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import pytz

from backend.dependencies import require_role, require_any_role, require_tier, get_current_user
from backend.database import get_session
from backend.models import Complaint, Message, User, BoardVerificationRequest

router = APIRouter()

# 📩 Submit Complaint
class ComplaintModel(BaseModel):
    title: str
    description: str
    timestamp: Optional[str] = None
    photo_url: Optional[str] = None

from datetime import datetime
import pytz  # Make sure pytz is installed

@router.post("/complaints")
def submit_complaint(data: ComplaintModel, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    # Get current time in America/Los_Angeles timezone
    tz = pytz.timezone("America/Los_Angeles")
    local_timestamp = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

    new_complaint = Complaint(
        title=data.title,
        description=data.description,
        timestamp=local_timestamp,
        user_id=user.id,
        community_id=user.community_id
    )
    session.add(new_complaint)
    session.commit()
    return {"message": "Complaint submitted."}

# 📬 Submit Message
class MessageModel(BaseModel):
    subject: str
    body: str

@router.post("/messages")
def submit_message(
    data: MessageModel,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    new_message = Message(
        subject=data.subject,
        body=data.body,
        timestamp=datetime.utcnow().isoformat(),
        user_id=user.id,
        community_id=user.community_id
    )
    session.add(new_message)
    session.commit()
    return {"message": "Message sent."}

# 🚀 Plan Upgrade
@router.post("/upgrade")
def upgrade_tier(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    user.tier = "landlord"
    session.add(user)
    session.commit()
    return {"message": f"{user.email} upgraded to landlord tier."}

# 🤖 AI Helpdesk Access
@router.get("/ai/helpdesk")
def ai_helpdesk(user=Depends(require_tier("solo", "household", "landlord"))):
    return {"response": f"You're accessing premium AI support as a {user.tier} user."}

# 📖 Get Complaints
@router.get("/complaints", response_model=List[Complaint])
def get_complaints(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    complaints = session.exec(
        select(Complaint).where(Complaint.community_id == user.community_id)
    ).all()
    return complaints

# 📖 Get Messages
@router.get("/messages", response_model=List[Message])
def get_messages(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    messages = session.exec(
        select(Message).where(Message.community_id == user.community_id)
    ).all()
    return messages

# 🧩 Submit Board Verification Request
class BoardRequestModel(BaseModel):
    community_id: str

@router.post("/board/request")
def board_verification_request(
    data: BoardRequestModel,
    user: User = Depends(get_current_user),
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
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    return session.exec(
        select(BoardVerificationRequest).where(BoardVerificationRequest.community_id == user.community_id)
    ).all()

# 🔍 View My Board Request
@router.get("/board/requests/my")
def view_my_board_request(
    user: User = Depends(get_current_user),
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
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    request = session.exec(
        select(BoardVerificationRequest).where(BoardVerificationRequest.id == candidate_id)
    ).first()
    if not request:
        raise HTTPException(status_code=404, detail="Candidate request not found")

    if user.id in request.approved_by:
        raise HTTPException(status_code=400, detail="You have already approved this candidate")

    request.approved_by.append(user.id)
    if len(request.approved_by) >= 4:
        request.verified = True

    session.add(request)
    session.commit()
    return {"message": f"Approved. Total approvals: {len(request.approved_by)}", "verified": request.verified}

