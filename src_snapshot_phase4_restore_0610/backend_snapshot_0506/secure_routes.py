from auth_utils import verify_token
from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File, Form
from sqlmodel import Session, select
from dependencies import require_role, require_any_role, require_tier, get_current_user
from database import get_session
from models import Complaint, Message, User
from typing import Optional
from datetime import datetime
import shutil
import os
import uuid

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

# ✅ Submit a complaint (with optional photo upload)
@router.post("/complaints")
def file_complaint(
    title: str = Form(...),
    description: str = Form(...),
    timestamp: str = Form(...),
    user_email: str = Form(...),
    photo: Optional[UploadFile] = File(None),
    session: Session = Depends(get_session),
    user=Depends(require_any_role("resident", "landlord", "household"))
):
    photo_url = None
    if photo:
        file_extension = photo.filename.split(".")[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        save_path = f"static/uploads/{unique_filename}"
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)
        photo_url = save_path

    complaint = Complaint(
        title=title,
        description=description,
        timestamp=timestamp,
        user_email=user_email,
        photo_url=photo_url
    )
    session.add(complaint)
    session.commit()
    session.refresh(complaint)
    return {"message": "Complaint submitted successfully", "id": complaint.id}

# ✅ Get complaints by email
@router.get("/complaints")
def get_complaints(email: str, session: Session = Depends(get_session)):
    statement = select(Complaint).where(Complaint.user_email == email)
    results = session.exec(statement).all()
    return results

# ✅ Send message route
@router.post("/messages")
def send_message(
    receiver_email: str = Form(...),
    subject: str = Form(...),
    body: str = Form(...),
    sender_email: str = Depends(verify_token),
    session: Session = Depends(get_session)
):
    sender = session.exec(select(User).where(User.email == sender_email)).first()
    receiver = session.exec(select(User).where(User.email == receiver_email)).first()

    if not sender or not receiver:
        raise HTTPException(status_code=404, detail="Sender or receiver not found")

    if sender.community_id != receiver.community_id:
        raise HTTPException(status_code=403, detail="Cannot message outside your community")

    message = Message(
        sender_email=sender_email,
        receiver_email=receiver_email,
        subject=subject,
        body=body,
        timestamp=datetime.utcnow(),
        community_id=sender.community_id,
        is_read=False
    )
    session.add(message)
    session.commit()
    return {"message": "Message sent successfully"}

