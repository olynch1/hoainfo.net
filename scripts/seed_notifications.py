from models import Notification
from sqlmodel import Session
from database import engine
import uuid

# Replace this with a real user_id
user_id = "your_user_id_here"

notif = Notification(
    user_id=user_id,
    message="🔔 Reminder: HOA meeting tomorrow at 6 PM."
)

with Session(engine) as session:
    session.add(notif)
    session.commit()
    print("✅ Notification inserted.")

