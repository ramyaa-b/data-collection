# create_database.py
# Supabase PostgreSQL database setup

from sqlalchemy import Column, Integer, String, DateTime, Text, create_engine
from sqlalchemy.orm import declarative_base
from datetime import datetime
import os

# =========================
# CONFIG
# =========================

DATABASE_URL = os.getenv("SUPABASE_DB_URL")

if not DATABASE_URL:
    raise RuntimeError("SUPABASE_DB_URL not set")

ALLOWED_CATEGORIES = {"religion", "language", "gender", "conspiracy"}
ALLOWED_PLATFORMS = {"X", "Reddit"}
ALLOWED_STATUS = {"pending", "approved", "rejected"}

Base = declarative_base()

# =========================
# MODEL
# =========================

class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    anonymized_text = Column(Text)
    category = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    context = Column(Text)
    status = Column(String, default="pending")
    timestamp = Column(DateTime, default=datetime.utcnow)

# =========================
# INIT DB
# =========================

def init_db():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    return engine

