# app1.py
# Streamlit app with Supabase PostgreSQL backend using Streamlit Secrets

import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, func
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime

# =========================
# CONFIG
# =========================

st.set_page_config(
    page_title="Hate Speech Data Collection",
    page_icon="⚠️",
    layout="centered"
)

# Get database URL from Streamlit secrets
try:
    DATABASE_URL = st.secrets["database"]["SUPABASE_DB_URL"]
    ADMIN_PASSWORD = st.secrets["admin"]["password"]
except KeyError:
    st.error("❌ Secrets not configured properly. Please set up .streamlit/secrets.toml")
    st.stop()

ALLOWED_CATEGORIES = {"Religion", "Language", "Gender", "Conspiracy"}
ALLOWED_PLATFORMS = {"X", "Reddit"}

# =========================
# DATABASE MODEL
# =========================

Base = declarative_base()

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
# DATABASE SESSION
# =========================

@st.cache_resource
def get_engine():
    """Create database engine (cached)"""
    try:
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False  # Set to True for SQL debugging
        )
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        return engine
    except Exception as e:
        st.error(f"Failed to connect to database: {e}")
        st.stop()

def get_session():
    """Get a new database session"""
    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()

# =========================
# UI
# =========================

st.title("⚠️ Hate Speech Data Collection Portal")

st.markdown("""
**Categories:** Gender, Religion, Language, Conspiracy  
**Sources:** X (Twitter), Reddit  

Data is stored securely in Supabase PostgreSQL database.
""")

# Connection status
try:
    session = get_session()
    st.success("✅ Connected to Supabase")
except Exception as e:
    st.error(f"❌ Database connection failed: {e}")
    st.stop()

# =========================
# SUBMISSION FORM
# =========================

st.subheader("📝 Submit New Entry")

with st.form("submission_form", clear_on_submit=True):
    text = st.text_area(
        "Hate Speech Content *", 
        height=150,
        placeholder="Paste the hateful content here..."
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        category = st.selectbox("Category *", sorted(ALLOWED_CATEGORIES))
    
    with col2:
        platform = st.selectbox("Source Platform *", sorted(ALLOWED_PLATFORMS))
    
    context = st.text_area(
        "Optional Context", 
        height=80,
        placeholder="Any additional information about where this was found..."
    )
    
    submitted = st.form_submit_button("Submit Entry", use_container_width=True)

if submitted:
    if not text.strip():
        st.error("⚠️ Text content cannot be empty")
    else:
        try:
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
            st.success("✅ Submission successfully stored in Supabase!")
            st.balloons()
        except Exception as e:
            session.rollback()
            st.error(f"❌ Error saving submission: {e}")
        finally:
            session.close()

# =========================
# DATASET STATISTICS
# =========================

st.markdown("---")
st.subheader("📊 Dataset Overview")

try:
    session = get_session()
    
    total = session.query(Submission).count()
    pending = session.query(Submission).filter_by(status="pending").count()
    approved = session.query(Submission).filter_by(status="approved").count()
    rejected = session.query(Submission).filter_by(status="rejected").count()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total", total, help="Total submissions in database")
    with col2:
        st.metric("Pending", pending, help="Awaiting review")
    with col3:
        st.metric("Approved", approved, help="Approved for dataset")
    with col4:
        st.metric("Rejected", rejected, help="Rejected submissions")
    
    # Category breakdown
    st.markdown("### By Category")
    
    category_stats = (
        session.query(Submission.category, func.count(Submission.id))
        .group_by(Submission.category)
        .all()
    )
    
    if category_stats:
        col1, col2, col3, col4 = st.columns(4)
        cols = [col1, col2, col3, col4]
        
        for idx, (cat, count) in enumerate(category_stats):
            with cols[idx % 4]:
                st.metric(cat, count)
    
    session.close()
    
except Exception as e:
    st.error(f"Error fetching statistics: {e}")

# =========================
# LATEST ENTRIES
# =========================

st.markdown("---")
st.subheader("🕒 Latest Submissions")

try:
    session = get_session()
    
    latest = (
        session.query(Submission)
        .order_by(Submission.timestamp.desc())
        .limit(10)
        .all()
    )
    
    if not latest:
        st.info("No submissions yet. Be the first to contribute!")
    else:
        for s in latest:
            with st.expander(
                f"[{s.category}] from {s.platform} - {s.status.upper()}"
            ):
                st.write("**Content:**")
                st.text(s.anonymized_text[:200] + "..." if len(s.anonymized_text) > 200 else s.anonymized_text)
                
                if s.context:
                    st.write("**Context:**")
                    st.caption(s.context)
                
                st.caption(f"Submitted: {s.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    
    session.close()
    
except Exception as e:
    st.error(f"Error loading submissions: {e}")

# =========================
# ADMIN SECTION
# =========================

with st.sidebar:
    st.header("🔐 Admin Panel")
    
    admin_password = st.text_input("Admin Password", type="password")
    
    if admin_password == ADMIN_PASSWORD:
        st.success("✅ Admin access granted")
        
        st.subheader("Review Submissions")
        
        try:
            session = get_session()
            pending_submissions = (
                session.query(Submission)
                .filter_by(status="pending")
                .order_by(Submission.timestamp.desc())
                .limit(5)
                .all()
            )
            
            if pending_submissions:
                for sub in pending_submissions:
                    with st.container():
                        st.write(f"**ID: {sub.id}** - {sub.category}")
                        st.caption(sub.text[:100] + "...")
                        
                        col1, col2 = st.columns(2)
                        
                        if col1.button("✅ Approve", key=f"approve_{sub.id}"):
                            sub.status = "approved"
                            session.commit()
                            st.success("Approved!")
                            st.rerun()
                        
                        if col2.button("❌ Reject", key=f"reject_{sub.id}"):
                            sub.status = "rejected"
                            session.commit()
                            st.warning("Rejected")
                            st.rerun()
                        
                        st.markdown("---")
            else:
                st.info("No pending submissions")
            
            # Export approved data
            st.markdown("---")
            st.subheader("📥 Export Dataset")
            
            approved_count = session.query(Submission).filter_by(status="approved").count()
            st.write(f"Approved entries: **{approved_count}**")
            
            if st.button("Download CSV", use_container_width=True):
                import pandas as pd
                
                approved = session.query(Submission).filter_by(status="approved").all()
                
                df = pd.DataFrame([{
                    'text': s.anonymized_text,
                    'category': s.category,
                    'platform': s.platform,
                    'timestamp': s.timestamp
                } for s in approved])
                
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download Dataset",
                    data=csv,
                    file_name=f"hate_speech_dataset_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            
            session.close()
            
        except Exception as e:
            st.error(f"Error in admin panel: {e}")
    elif admin_password:
        st.error("❌ Invalid password")

# =========================
# FOOTER
# =========================

st.markdown("---")
st.caption("Built with Streamlit & Supabase | Final Year Project - Content Moderation System")
