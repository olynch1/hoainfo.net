from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File, Request
from sqlmodel import Session, select
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
import pytz
import uuid
import os

from src.backend.dependencies import require_role, require_any_role, require_tier
from src.backend.database import get_session
from src.backend.auth_utils import verify_token
from src.backend.models import User, Complaint, Document

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

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

@router.get("/directory")
def view_directory(user: User = Depends(verify_token), session: Session = Depends(get_session)):
    if user.role not in ("resident", "board", "admin"):
        raise HTTPException(status_code=403, detail="Access denied")

    # 🔐 Board/Admin see everyone in the community
    if user.role in ("board", "admin"):
        users = session.exec(
            select(User).where(User.community_id == user.community_id)
        ).all()
    else:
        # Residents only see other residents who opted in
        users = session.exec(
            select(User).where(
                User.community_id == user.community_id,
                User.role == "resident",
                User.show_in_directory == True
            )
        ).all()

    return [
        {
            "name": f"{u.first_name} {u.last_name[0]}." if u.first_name and u.last_name else None,
            "community_id": u.community_id
        }
        for u in users
    ]

@router.post("/documents/upload") 
def upload_document(
    title: str = Form(...),
    type: str = Form(...),
    file: UploadFile = File(...),
    user: User = Depends(verify_token),
    session: Session = Depends(get_session)   
):
    # ✅ Allow residents ONLY for ccr or bylaws
    allowed_for_residents = ("ccr", "bylaws")
    if user.role not in ("board", "admin"):
        if type.lower() not in allowed_for_residents:
            raise HTTPException(
                status_code=403,
                detail="Only board/admin can upload this document type."
            )
    
    ext = file.filename.split(".")[-1]
    file_id = str(uuid.uuid4())
    filename = f"{file_id}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    with open(filepath, "wb") as buffer:
        buffer.write(file.file.read())

    document = Document(
        id=file_id,
        title=title,
        type=type.lower(),
        upload_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        community_id=user.community_id,
        uploader_id=user.id, 
        file_url=f"/files/{filename}"
    )
    session.add(document)
    session.commit()
    return {"message": "Document uploaded."}

@router.get("/documents")
def list_documents(
    type: Optional[str] = None,
    title: Optional[str] = None,
    request: Request = None,
    user: User = Depends(verify_token),
    session: Session = Depends(get_session)
):
    query = select(Document).where(Document.community_id == user.community_id)

    if type:
        query = query.where(Document.type == type.lower())

    if title:
        query = query.where(Document.title.ilike(f"%{title}%"))

    docs = session.exec(query).all()

    # Build full public URLs
    base_url = str(request.base_url).rstrip("/")
    for doc in docs:
        doc.file_url = f"{base_url}{doc.file_url}"

    return docs
    
@router.patch("/complaints/{complaint_id}/status")
def update_complaint_status(
    complaint_id: str,
    status: str = Form(...),
    user: User = Depends(verify_token),
    session: Session = Depends(get_session)
):
    complaint = session.get(Complaint, complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    if complaint.community_id != user.community_id:
        raise HTTPException(status_code=403, detail="Unauthorized to update this complaint")

    complaint.status = status
    session.add(complaint)
    session.commit()

    return {"message": f"Complaint status updated to '{status}'."}

