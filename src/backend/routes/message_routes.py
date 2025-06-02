from fastapi.responses import FileResponse
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from typing import List
from datetime import datetime
from pydantic import BaseModel
from pytz import timezone
from fpdf import FPDF
import os

pacific = timezone("America/Los_Angeles")

from src.backend.models import Message, User
from src.backend.database import get_db
from src.backend.dependencies import get_current_user, require_any_role

router = APIRouter()

# ✅ Resident Inbox (Paginated)
@router.get("/messages")
def get_messages(
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    page_size = 10
    offset = (page - 1) * page_size

    messages = db.query(Message)\
    .filter(Message.user_id == user.id)\
    .order_by(Message.timestamp.desc())\
    .offset(offset)\
    .limit(page_size)\
    .all()
    return [
        {
            "id": str(m.id),
            "subject": m.subject,
            "timestamp": m.timestamp,
            "read": m.read,
            "read_at": m.read_at
        }
        for m in messages
    ]


# ✅ Resident Full Inbox (by user_id)
@router.get("/messages/inbox")
def get_inbox(db: Session = Depends(get_db), user=Depends(get_current_user)):
    messages = db.exec(
        select(Message).where(Message.user_id == user.id)
    ).all()

    return [
        {
            "id": msg.id,
            "subject": msg.subject,
            "body": msg.body,
            "timestamp": msg.timestamp,
            "read": msg.read,
            "response": msg.response,
            "sender_email": msg.sender or "board@example.com"
        }
        for msg in messages
    ]


# ✅ Send message to board
class MessageSendRequest(BaseModel):
    receiver_email: str
    subject: str
    body: str

@router.post("/messages/send")
def send_message(
    request: MessageSendRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    receiver = db.exec(select(User).where(User.email == request.receiver_email)).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")

    new_msg = Message(
        user_id=receiver.id,
        subject=request.subject,
        body=request.body,
        timestamp=datetime.now(pacific),
        read=False,
        sender=user.email,
        recipient=request.receiver_email,
        community_id=user.community_id
    )
    db.add(new_msg)
    db.commit()
    return {"status": "sent", "message_id": new_msg.id}


# ✅ Mark message as read
@router.patch("/messages/{message_id}/read")
def mark_message_read(
    message_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    message = db.get(Message, message_id)
    if not message or message.user_id != user.id:
        raise HTTPException(status_code=404, detail="Message not found or unauthorized")

    message.read = True
    message.read_at = datetime.now(pacific)
    db.add(message)
    db.commit()
    return {"status": "read", "read_at": message.read_at}


# ✅ Board/Admin view of all sent messages
@router.get("/board/messages/sent")
def board_sent_messages(
    db: Session = Depends(get_db),
    user=Depends(require_any_role("board", "admin"))
):
    messages = db.exec(select(Message)).all()
    results = []

    for msg in messages:
        receiver = db.get(User, msg.user_id)
        results.append({
            "id": msg.id,
            "to": receiver.email if receiver else "Unknown",
            "subject": msg.subject,
            "timestamp": msg.timestamp,
            "read": msg.read,
            "read_at": msg.read_at
        })

    return results

@router.post("/messages/{message_id}/reply")
def reply_to_message(message_id: str, response: dict, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    message = db.query(Message).filter(Message.id == message_id, Message.user_id == user.id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    message.response = response.get("response")
    db.commit()
    return {"message": "Reply saved"}

@router.get("/export-inbox")
def export_inbox_pdf(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    messages = db.query(Message).filter(Message.user_id == user.id).all()

    pdf = FPDF()
    pdf.set_font("Arial", size=12)
    pdf.add_page()
    pdf.cell(200, 10, txt="📬 HOA Inbox Export", ln=True, align='C')
    pdf.ln(10)

    for msg in messages:
        pdf.multi_cell(0, 10, txt=(
            f"Subject: {msg.subject}\n"
            f"Sent: {msg.timestamp}\n"
            f"Read: {'✅' if msg.read else '❌'}\n"
            f"Response: {msg.response or 'None'}\n"
            f"{'-'*40}"
        ))
        pdf.ln(5)

    export_path = "inbox_export.pdf"
    pdf.output(export_path)

    return FileResponse(export_path, media_type='application/pdf', filename="inbox_export.pdf")

