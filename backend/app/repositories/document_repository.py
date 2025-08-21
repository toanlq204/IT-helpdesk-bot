from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from ..models.document import Document, DocumentText
from ..schemas.document import DocumentCreate
from ..services.document_parser import document_processor
import logging

logger = logging.getLogger(__name__)


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


def process_document_with_rag(db: Session, document: Document) -> Dict[str, Any]:
    """
    Process document with enhanced RAG capabilities:
    - Extract text
    - Chunk content
    - Generate embeddings
    - Store in vector database
    
    Returns:
        Dict containing processing results
    """
    try:
        logger.info(f"Processing document {document.id} with RAG pipeline")
        
        # Update status to processing
        update_document_status(db, document.id, "processing")
        
        # Process document with enhanced parser
        result = document_processor.process_and_store_document(
            filepath=document.filepath,
            content_type=document.content_type,
            document_id=document.id,
            filename=document.filename
        )
        
        if result["success"]:
            # Store extracted text in database
            create_document_text(db, document.id, result.get("text", ""))
            
            # Update document status to parsed
            update_document_status(db, document.id, "parsed")
            
            logger.info(f"Successfully processed document {document.id}: "
                       f"{result['chunk_count']} chunks, "
                       f"{result['text_length']} characters")
            
            return {
                "success": True,
                "document_id": document.id,
                "chunks_created": result["chunk_count"],
                "text_length": result["text_length"],
                "vectors_stored": len(result.get("vector_ids", [])),
                "chunks": result.get("chunks", [])
            }
        else:
            # Update status to failed
            update_document_status(db, document.id, "failed")
            
            logger.error(f"Failed to process document {document.id}: {result.get('error')}")
            
            return {
                "success": False,
                "document_id": document.id,
                "error": result.get("error", "Unknown error")
            }
            
    except Exception as e:
        logger.error(f"Error processing document {document.id}: {e}")
        update_document_status(db, document.id, "failed")
        
        return {
            "success": False,
            "document_id": document.id,
            "error": str(e)
        }


def search_documents(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search for relevant document chunks using vector similarity
    
    Args:
        query: Search query
        limit: Maximum number of results
        
    Returns:
        List of relevant document chunks with metadata
    """
    try:
        return document_processor.search_similar_chunks(query, k=limit)
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        return []


def get_recent_filenames(db: Session, limit: int = 3) -> List[str]:
    """Get recent document filenames for placeholder responses"""
    documents = db.query(Document).filter(
        Document.status == "parsed"
    ).order_by(Document.uploaded_at.desc()).limit(limit).all()
    
    return [doc.filename for doc in documents]
