from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.orm import sessionmaker

# === Database Configuration ===
sqlite_file_name = "hoainfo_reset.db"  # renamed to force a fresh DB
DATABASE_URL = f"sqlite:///{sqlite_file_name}"
engine = create_engine(DATABASE_URL, echo=True)

# SQLAlchemy-compatible session factory
SessionLocal = sessionmaker(bind=engine, class_=Session, autocommit=False, autoflush=False)

# Create all tables defined in SQLModel models
def init_db():
    SQLModel.metadata.create_all(engine)

# Return a session directly (for use with `with` blocks)
def get_session():
    return SessionLocal()

