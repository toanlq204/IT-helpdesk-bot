from sqlalchemy.orm import Session
from typing import List, Optional
from ..models.document import Document, DocumentText
from ..schemas.document import DocumentCreate


def create_document(db: Session, document: DocumentCreate, filepath: str, size_bytes: int, user_id: int) -> Document:
    """Create a new document record"""
    db_document = Document(
        filename=document.filename,
        filepath=filepath,
        content_type=document.content_type,
        size_bytes=size_bytes,
        uploaded_by=user_id,
        status="pending"
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document


def get_documents(db: Session, limit: int = 100) -> List[Document]:
    """Get all documents"""
    return db.query(Document).order_by(Document.uploaded_at.desc()).limit(limit).all()


def get_document_by_id(db: Session, document_id: int) -> Optional[Document]:
    """Get document by ID"""
    return db.query(Document).filter(Document.id == document_id).first()


def update_document_status(db: Session, document_id: int, status: str) -> Optional[Document]:
    """Update document status"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if document:
        document.status = status
        db.commit()
        db.refresh(document)
    return document


def delete_document(db: Session, document_id: int) -> bool:
    """Delete document and its text"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if document:
        # Delete associated text first
        db.query(DocumentText).filter(DocumentText.document_id == document_id).delete()
        db.delete(document)
        db.commit()
        return True
    return False


def create_document_text(db: Session, document_id: int, text: str) -> DocumentText:
    """Create document text record"""
    db_text = DocumentText(
        document_id=document_id,
        text=text,
        char_count=len(text)
    )
    db.add(db_text)
    db.commit()
    db.refresh(db_text)
    return db_text


def get_recent_filenames(db: Session, limit: int = 3) -> List[str]:
    """Get recent document filenames for placeholder responses"""
    documents = db.query(Document).filter(
        Document.status == "parsed"
    ).order_by(Document.uploaded_at.desc()).limit(limit).all()
    
    return [doc.filename for doc in documents]
