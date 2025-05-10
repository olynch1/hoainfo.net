from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, Session, select
from datetime import datetime
from uuid import uuid4

from auth_utils import verify_token, hash_password, create_jwt_token
from src.backend.models import User, Complaint, Message, ActivityLog, TenantInvite
from src.backend.database import engine

app = FastAPI()

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_user_activity(request: Request, call_next):
    try:
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if token:
            user = verify_token(token)
            ip_address = request.client.host
            user_agent = request.headers.get("user-agent")
            log = ActivityLog(
                id=str(uuid4()),
                user_id=user.id,
                action=f"{request.method} {request.url.path}",
                endpoint=request.url.path,
                ip_address=ip_address,
                user_agent=user_agent,
                community_id=user.community_id
            )
            with Session(engine) as session:
                session.add(log)
                session.commit()
    except Exception as e:
        print(f"❌ Log middleware error: {e}")
    return await call_next(request)

@app.post("/messages")
def send_message(data: dict, user=Depends(verify_token)):
    message = Message(
        id=str(uuid4()),
        subject=data.get("subject"),
        body=data.get("body"),
        user_id=user.id,
        community_id=user.community_id
    )
    with Session(engine) as session:
        session.add(message)
        session.commit()
    return {"message": "Your message was sent to the board."}

@app.get("/board/messages")
def get_board_messages(user=Depends(verify_token)):
    if user.role not in ["admin", "board"]:
        raise HTTPException(status_code=403, detail="Unauthorized")
    with Session(engine) as session:
        messages = session.exec(
            select(Message).where(Message.community_id == user.community_id)
        ).all()
    return messages

@app.post("/board/messages/{message_id}/reply")
def reply_to_message(message_id: str, data: dict, user=Depends(verify_token)):
    if user.role not in ["admin", "board"]:
        raise HTTPException(status_code=403, detail="Unauthorized")
    with Session(engine) as session:
        message = session.get(Message, message_id)
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        message.response = data.get("response")
        message.responded_by = user.email
        message.responded_at = datetime.utcnow()
        session.add(message)
        session.commit()
    return {"message": "Reply sent successfully"}

@app.post("/board/messages/{message_id}/read")
def mark_as_read(message_id: str, user=Depends(verify_token)):
    if user.role not in ["admin", "board"]:
        raise HTTPException(status_code=403, detail="Unauthorized")
    with Session(engine) as session:
        message = session.get(Message, message_id)
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        message.is_read = True
        session.add(message)
        session.commit()
    return {"message": "Message marked as read."}

@app.get("/dashboard/metrics")
def get_dashboard_metrics(user=Depends(verify_token)):
    with Session(engine) as session:
        complaints = session.exec(
            select(Complaint).where(Complaint.community_id == user.community_id)
        ).all()
        messages = session.exec(
            select(Message).where(Message.community_id == user.community_id)
        ).all()
        unread_count = len([m for m in messages if not m.is_read])
        tenants = session.exec(
            select(User).where(User.community_id == user.community_id, User.is_tenant == True)
        ).all()

    return {
        "total_complaints": len(complaints),
        "total_messages": len(messages),
        "unread_messages": unread_count,
        "total_tenants": len(tenants)
    }

@app.post("/upgrade")
def upgrade_user(data: dict, user=Depends(verify_token)):
    new_tier = data.get("tier")
    if new_tier not in ["solo", "household", "landlord"]:
        raise HTTPException(status_code=400, detail="Invalid tier")
    with Session(engine) as session:
        db_user = session.get(User, user.id)
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        db_user.tier = new_tier
        session.add(db_user)
        session.commit()
    return {"message": f"Your plan was upgraded to {new_tier.capitalize()}."}

@app.post("/invite-tenant")
def invite_tenant(data: dict, user=Depends(verify_token)):
    if user.tier != "landlord":
        raise HTTPException(status_code=403, detail="Only landlords can invite tenants")
    tenant_email = data.get("email")
    if not tenant_email:
        raise HTTPException(status_code=400, detail="Tenant email is required")
    invite = TenantInvite(
        id=str(uuid4()),
        landlord_id=user.id,
        tenant_email=tenant_email,
        status="pending",
        community_id=user.community_id,
        created_at=datetime.utcnow()
    )
    with Session(engine) as session:
        session.add(invite)
        session.commit()
    print(f"🏘️ Tenant invite saved for {tenant_email} by {user.email}")
    return {"message": f"Invitation saved for {tenant_email}."}

@app.post("/accept-invite")
def accept_invite(data: dict):
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")
    with Session(engine) as session:
        invite = session.exec(
            select(TenantInvite).where(TenantInvite.tenant_email == email, TenantInvite.status == "pending")
        ).first()
        if not invite:
            raise HTTPException(status_code=404, detail="No pending invite found")
        existing = session.exec(select(User).where(User.email == email)).first()
        if existing:
            raise HTTPException(status_code=400, detail="Account already exists")
        tenant = User(
            id=str(uuid4()),
            email=email,
            hashed_password=hash_password(password),
            role="resident",
            is_tenant=True,
            community_id=invite.community_id,
            created_at=datetime.utcnow()
        )
        session.add(tenant)
        invite.status = "accepted"
        session.add(invite)
        session.commit()
        token = create_jwt_token(tenant)
    return {"message": "Tenant registered", "access_token": token, "user": {"email": email, "role": "resident"}}

@app.post("/verify-tenant")
def verify_tenant(data: dict, user=Depends(verify_token)):
    if user.role not in ["admin", "landlord"]:
        raise HTTPException(status_code=403, detail="Unauthorized")
    tenant_id = data.get("user_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant user ID is required")
    with Session(engine) as session:
        tenant = session.get(User, tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        tenant.verified = True
        session.add(tenant)
        session.commit()
    return {"message": "Tenant successfully verified."}

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

