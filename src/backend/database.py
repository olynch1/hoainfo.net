from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = "sqlite:///hoainfo.db"
engine = create_engine(DATABASE_URL, echo=False)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    return Session(engine)

# (Optional) In-memory OTP store
otp_store = {}

