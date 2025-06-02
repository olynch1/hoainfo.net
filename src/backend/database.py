
from sqlmodel import SQLModel, create_engine, Session
from contextlib import contextmanager

DATABASE_URL = "sqlite:///hoainfo.db"
engine = create_engine(DATABASE_URL, echo=False)

# ✅ Initialize DB tables
def init_db():
    SQLModel.metadata.create_all(engine)

# ✅ Session generator for FastAPI dependency
def get_db():
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()

# ✅ Optional helper for ad-hoc use
def get_session():
    return Session(engine)

# ✅ In-memory OTP store
otp_store = {}

