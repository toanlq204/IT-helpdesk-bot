import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from .config import settings

# Ensure data directory exists
os.makedirs(os.path.dirname(settings.DB_PATH), exist_ok=True)

SQLALCHEMY_DATABASE_URL = f"sqlite:///{settings.DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)

def seed_demo():
    """Seed database with demo data"""
    from ..models.user import User
    from ..models.document import Document, DocumentText
    from ..models.ticket import Ticket
    from ..utils.auth import get_password_hash
    
    db = SessionLocal()
    try:
        # Check if users already exist
        if db.query(User).first():
            return
            
        # Create demo users
        users = [
            User(
                email="admin@ex.com",
                hashed_password=get_password_hash("Admin123!"),
                role="admin"
            ),
            User(
                email="tech@ex.com", 
                hashed_password=get_password_hash("Tech123!"),
                role="technician"
            ),
            User(
                email="user@ex.com",
                hashed_password=get_password_hash("User123!"),
                role="user"
            )
        ]
        
        for user in users:
            db.add(user)
        
        db.commit()
        
        # Create a sample document
        sample_doc = Document(
            filename="sample_guide.txt",
            filepath="sample_guide.txt",
            content_type="text/plain",
            size_bytes=100,
            uploaded_by=1,  # admin
            status="parsed"
        )
        db.add(sample_doc)
        db.commit()
        
        # Add sample document text
        doc_text = DocumentText(
            document_id=sample_doc.id,
            text="This is a sample IT helpdesk guide. It contains basic troubleshooting steps for common computer issues.",
            char_count=100
        )
        db.add(doc_text)
        
        # Create a sample ticket
        sample_ticket = Ticket(
            created_by=3,  # user
            title="Computer won't start",
            description="My computer is not turning on when I press the power button.",
            status="open",
            priority="medium"
        )
        db.add(sample_ticket)
        
        db.commit()
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()
