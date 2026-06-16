import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Fail fast: refuse to silently fall back to a hardcoded localhost+root
    # connection string in production. Tests override DATABASE_URL in their
    # conftest before importing this module.
    raise RuntimeError(
        "DATABASE_URL environment variable is required. "
        "Set it in .env or your environment."
    )

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()