# app1.py
# Streamlit app with Supabase PostgreSQL backend

import streamlit as st
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from create_database import (
    Submission,
    Base,
    ALLOWED_CATEGORIES,
    ALLOWED_PLATFORMS,
    init_db
)

# =========================
# CONFIG
# =========================

st.set_page_config(
    page_title="Hate Speech Data Collection",
    page_icon="⚠️",
    layout="centered"
)

DATABASE_URL = os.getenv("SUPABASE_DB_URL")

if not DATABASE_URL:
    st.error("SUPABASE_DB_URL not configured")
    st.stop()

# =========================
# DATABASE SESSION
# =========================

@st.cache_resource
def get_session():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(bind=engine)  # safety
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()

session = get_session()

# =========================
# UI
# =========================

st.title("⚠️ Hate Speech Data Collection Portal")

st.markdown("""
**Categories:** Gender, Religion, Language, Conspiracy  
**Sources:** X (Twitter), Reddit  
Data is stored securely in Supabase (PostgreSQL).
""")

# =========================
# FORM
# =========================

with st.form("submission_form", clear_on_submit=True):
    text = st.text_area("Text Content", height=150)
    category = st.selectbox("Category", sorted(ALLOWED_CATEGORIES))
    platform = st.selectbox("Source Platform", sorted(ALLOWED_PLATFORMS))
    context = st.text_area("Optional Context", height=80)
    submitted = st.form_submit_button("Submit")

if submitted:
    if not text.strip():
        st.error("Text cannot be empty")
    else:
        submission = Submission(
            text=text.strip(),
            anonymized_text=text.strip(),
            category=category,
            platform=platform,
            context=context.strip() if context else None,
            status="pending"
        )
        session.add(submission)
        session.commit()
        st.success("✅ Submission stored in Supabase")

# =========================
# METRICS
# =========================

st.markdown("---")
st.subheader("📊 Dataset Overview")

total = session.query(Submission).count()
pending = session.query(Submission).filter_by(status="pending").count()
approved = session.query(Submission).filter_by(status="approved").count()

st.metric("Total", total)
st.metric("Pending", pending)
st.metric("Approved", approved)

# =========================
# LATEST ENTRIES
# =========================

st.subheader("🕒 Latest Submissions")

latest = (
    session.query(Submission)
    .order_by(Submission.timestamp.desc())
    .limit(5)
    .all()
)

for s in latest:
    with st.expander(f"[{s.category.upper()}] {s.platform}"):
        st.write(s.anonymized_text)
        st.caption(f"Status: {s.status}")
