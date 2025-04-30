from sqlmodel import SQLModel, Session, create_engine
from pathlib import Path

sqlite_file_name = "hoa.db"
db_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(db_url, echo=True)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    return Session(engine)

