# create_database.py
# Database setup for Hate Speech Dataset (Streamlit compatible)

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# =========================
# CONFIGURATION
# =========================

DATABASE_URL = "sqlite:///./hate_speech.db"

ALLOWED_CATEGORIES = {"religion", "language", "gender", "conspiracy"}
ALLOWED_PLATFORMS = {"X", "Reddit"}
ALLOWED_STATUS = {"pending", "approved", "rejected"}

Base = declarative_base()

# =========================
# DATABASE MODEL
# =========================

class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    anonymized_text = Column(Text, nullable=True)

    category = Column(String, nullable=False)
    platform = Column(String, nullable=False)

    context = Column(Text, nullable=True)
    status = Column(String, default="pending")
    timestamp = Column(DateTime, default=datetime.utcnow)

# =========================
# DATABASE FUNCTIONS
# =========================

def create_database():
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

    Base.metadata.create_all(bind=engine)
    print("✅ Database and tables created successfully")

def reset_database():
    if os.path.exists("hate_speech.db"):
        os.remove("hate_speech.db")
        print("🗑️ Old database deleted")

    create_database()

# =========================
# VALIDATED INSERT FUNCTION
# =========================

def add_submission(
    session,
    text,
    category,
    platform,
    anonymized_text=None,
    context=None,
    status="pending"
):
    if category not in ALLOWED_CATEGORIES:
        raise ValueError(f"Invalid category: {category}")

    if platform not in ALLOWED_PLATFORMS:
        raise ValueError(f"Invalid platform: {platform}")

    if status not in ALLOWED_STATUS:
        raise ValueError(f"Invalid status: {status}")

    submission = Submission(
        text=text,
        anonymized_text=anonymized_text or text,
        category=category,
        platform=platform,
        context=context,
        status=status
    )

    session.add(submission)
    session.commit()

# =========================
# SAMPLE DATA (SAFE)
# =========================

def add_sample_data():
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    samples = [
        {
            "text": "Women should not be allowed to work",
            "category": "gender",
            "platform": "X",
            "status": "pending"
        },
        {
            "text": "This religion is responsible for all problems",
            "category": "religion",
            "platform": "Reddit",
            "status": "approved"
        },
        {
            "text": "People speaking this language are stupid",
            "category": "language",
            "platform": "X",
            "status": "pending"
        },
        {
            "text": "This group secretly controls the government",
            "category": "conspiracy",
            "platform": "Reddit",
            "status": "pending"
        }
    ]

    for s in samples:
        add_submission(
            session=session,
            text=s["text"],
            category=s["category"],
            platform=s["platform"],
            status=s["status"]
        )

    session.close()
    print("✅ Sample data added")

# =========================
# DATABASE INFO
# =========================

def view_database_info():
    if not os.path.exists("hate_speech.db"):
        print("❌ Database not found")
        return

    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    total = session.query(Submission).count()
    pending = session.query(Submission).filter_by(status="pending").count()
    approved = session.query(Submission).filter_by(status="approved").count()
    rejected = session.query(Submission).filter_by(status="rejected").count()

    print("\nDATABASE STATS")
    print("-" * 40)
    print(f"Total: {total}")
    print(f"Pending: {pending}")
    print(f"Approved: {approved}")
    print(f"Rejected: {rejected}")
    print("-" * 40)

    session.close()

# =========================
# CSV EXPORT
# =========================

def export_to_csv():
    import csv

    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    approved = session.query(Submission).filter_by(status="approved").all()

    if not approved:
        print("❌ No approved data to export")
        return

    filename = f"dataset_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "text", "category", "platform", "timestamp"])

        for s in approved:
            writer.writerow([
                s.id,
                s.anonymized_text or s.text,
                s.category,
                s.platform,
                s.timestamp
            ])

    session.close()
    print(f"✅ Exported to {filename}")

# =========================
# MAIN (LOCAL USE ONLY)
# =========================

if __name__ == "__main__":
    create_database()
    add_sample_data()
    view_database_info()
