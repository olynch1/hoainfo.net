from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from models import Notification
from database import get_session
from typing import List

from src.backend.auth_utils import get_current_user

router = APIRouter()

@router.get("/notifications", response_model=List[Notification])
def get_notifications(
    session: Session = Depends(get_session),
    user=Depends(get_current_user)
):
    notifications = session.exec(
        select(Notification).where(Notification.user_id == user.id).order_by(Notification.created_at.desc())
    ).all()
    return notifications

