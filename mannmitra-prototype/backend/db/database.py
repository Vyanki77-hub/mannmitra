import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/mannmitra.db")

# If using a local SQLite file, ensure its parent directory exists
if DATABASE_URL.startswith("sqlite:///"):
    sqlite_path = DATABASE_URL.replace("sqlite:///", "")
    db_dir = os.path.dirname(sqlite_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from . import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
