# app.py
# Streamlit app for Hate Speech Dataset Collection

import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from create_database import (
    Submission,
    ALLOWED_CATEGORIES,
    ALLOWED_PLATFORMS,
    add_submission
)

# =========================
# CONFIG
# =========================

DATABASE_URL = "sqlite:///./hate_speech.db"

st.set_page_config(
    page_title="Hate Speech Data Collection",
    page_icon="⚠️",
    layout="centered"
)

# =========================
# DATABASE SESSION
# =========================

@st.cache_resource
def get_db_session():
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()

session = get_db_session()

# =========================
# UI
# =========================

st.title("⚠️ Hate Speech Data Collection Portal")

st.markdown(
    """
    This tool is used to **collect and annotate hate speech content**
    for academic research purposes only.

    **Allowed categories:** Gender, Religion, Language, Conspiracy  
    **Sources:** X (Twitter), Reddit
    """
)

# =========================
# INPUT FORM
# =========================

with st.form("submission_form", clear_on_submit=True):
    text = st.text_area(
        "Text Content",
        placeholder="Paste the post/comment here...",
        height=150
    )

    category = st.selectbox(
        "Category",
        sorted(ALLOWED_CATEGORIES)
    )

    platform = st.selectbox(
        "Source Platform",
        sorted(ALLOWED_PLATFORMS)
    )

    context = st.text_area(
        "Optional Context (why is this hate speech?)",
        placeholder="Optional annotation notes",
        height=80
    )

    submitted = st.form_submit_button("Submit")

# =========================
# FORM HANDLER
# =========================

if submitted:
    if not text.strip():
        st.error("❌ Text content cannot be empty")
    else:
        try:
            add_submission(
                session=session,
                text=text.strip(),
                category=category,
                platform=platform,
                context=context.strip() if context else None
            )
            st.success("✅ Submission added successfully")
        except Exception as e:
            st.error(f"❌ Error: {e}")

# =========================
# ADMIN VIEW (OPTIONAL)
# =========================

st.markdown("---")
st.subheader("📊 Dataset Overview")

total = session.query(Submission).count()
pending = session.query(Submission).filter_by(status="pending").count()
approved = session.query(Submission).filter_by(status="approved").count()

st.metric("Total Submissions", total)
st.metric("Pending Review", pending)
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

if latest:
    for s in latest:
        with st.expander(f"[{s.category.upper()}] {s.platform} | {s.timestamp}"):
            st.write(s.anonymized_text or s.text)
            st.caption(f"Status: {s.status}")
else:
    st.info("No submissions yet.")
