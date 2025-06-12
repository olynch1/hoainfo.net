from uuid import UUID
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from src.backend.database import get_session
from src.backend.models import Complaint
from src.backend.dependencies import get_current_user, require_any_role

router = APIRouter()

# ✅ Data model for complaint submission
class ComplaintCreate(BaseModel):
    title: str
    description: str
    community_id: str

# ✅ Submit a new complaint (resident)
@router.post("/complaints")
def submit_complaint(
    complaint: ComplaintCreate,
    session: Session = Depends(get_session),
    user=Depends(get_current_user)
):
    new_complaint = Complaint(
        user_id=user.id,
        title=complaint.title,
        description=complaint.description,
        community_id=complaint.community_id,
        status="Pending"
    )
    session.add(new_complaint)
    session.commit()
    session.refresh(new_complaint)
    return {
        "id": new_complaint.id,
        "status": new_complaint.status,
        "title": new_complaint.title,
        "description": new_complaint.description,
        "community_id": new_complaint.community_id
    }

# ✅ Get a list of current user's complaints
@router.get("/complaints/me")
def get_my_complaints(
    session: Session = Depends(get_session),
    user=Depends(get_current_user)
):
    complaints = session.exec(
        select(Complaint).where(Complaint.user_id == user.id)
    ).all()
    
    return [
        {
            "id": c.id,
            "title": c.title,
            "description": c.description,
            "status": c.status,
            "timestamp": c.timestamp,
            "photo_url": c.photo_url,
            "read": c.read,
            "read_at": c.read_at
        }
        for c in complaints
    ]

# ✅ Resident can view their own complaint status
@router.get("/complaints/{complaint_id}/status")
def get_complaint_status(
    complaint_id: UUID,
    session: Session = Depends(get_session),
    user=Depends(get_current_user)
):
    complaint = session.exec(select(Complaint).where(Complaint.id == str(complaint_id))).first()
    if not complaint or complaint.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return {"status": complaint.status}

# ✅ Board/Admin can update complaint status
@router.patch("/complaints/{complaint_id}/status")
def update_complaint_status(
    complaint_id: UUID,
    new_status: str,
    session: Session = Depends(get_session),
    user=Depends(require_any_role("board", "admin"))
):
    complaint = session.exec(select(Complaint).where(Complaint.id == str(complaint_id))).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    complaint.status = new_status
    session.add(complaint)
    session.commit()
    return {"message": "Status updated", "status": complaint.status}

@router.delete("/complaints/{complaint_id}")
def delete_complaint(
    complaint_id: UUID,
    session: Session = Depends(get_session),
    user=Depends(get_current_user)
):
    complaint = session.exec(select(Complaint).where(Complaint.id == str(complaint_id))).first()
    if not complaint or complaint.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    session.delete(complaint)
    session.commit()
    return {"message": "Complaint deleted"}

@router.patch("/complaints/{complaint_id}/read")
def mark_complaint_as_read(
    complaint_id: UUID,
    session: Session = Depends(get_session),
    user=Depends(get_current_user)
):
    complaint = session.exec(select(Complaint).where(Complaint.id == str(complaint_id))).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # Only board or admin can mark as read
    if user.role not in ["board", "admin"]:
        raise HTTPException(status_code=403, detail="Only board/admin can mark as read")

    complaint.read = True
    complaint.read_at = datetime.utcnow()
    session.add(complaint)
    session.commit()

    return {
        "message": "Complaint marked as read",
        "read": True,
        "read_at": complaint.read_at
    }
