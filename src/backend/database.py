from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.orm import sessionmaker
from pathlib import Path

sqlite_file_name = "hoa.db"
db_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(db_url, echo=True)

SessionLocal = sessionmaker(bind=engine, class_=Session, autocommit=False, autoflush=False)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

