import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database file location in backend directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "herwellness.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# Create SQLite engine (check_same_thread=False for SQLite with FastAPI)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency for obtaining database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
