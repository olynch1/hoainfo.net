from sqlmodel import SQLModel, Session, create_engine

# 📦 SQLite database file
DATABASE_URL = "sqlite:///./database.db"

# 🌐 Create engine
engine = create_engine(DATABASE_URL, echo=True)  # Set echo=False to silence SQL logs

# 🔁 Used by FastAPI routes
def get_session():
    return Session(engine)

# 🏗️ Called to create all tables from models.py
def init_db():
    SQLModel.metadata.create_all(engine)

