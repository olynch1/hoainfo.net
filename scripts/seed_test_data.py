from sqlmodel import Session
from src.backend.models import User, Message, Complaint, ActivityLog
from src.backend.database import engine

with Session(engine) as session:
    user = User(email="sample@example.com", role="resident", tier="solo", community_id="00001", verified=True)
    session.add(user)

    message = Message(
        subject="Pool Access",
        body="When does the pool open?",
        user_id=user.id,
        community_id=user.community_id
    )
    session.add(message)

    complaint = Complaint(
        title="Broken Sprinkler",
        description="Front yard sprinkler leaking.",
        user_id=user.id,
        community_id=user.community_id
    )
    session.add(complaint)

    log = ActivityLog(
        user_id=user.id,
        action="Test Login",
        endpoint="/login",
        ip_address="127.0.0.1",
        user_agent="curl",
        community_id=user.community_id
    )
    session.add(log)

    session.commit()

