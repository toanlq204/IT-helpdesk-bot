import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from ..core.database import get_db
from ..core.config import settings
from ..models.user import User
from ..schemas.document import DocumentResponse, DocumentWithText
from ..utils.auth import get_admin_user
from ..repositories.document_repository import (
    create_document, get_documents, get_document_by_id, 
    update_document_status, delete_document, create_document_text
)
from ..services.document_parser import extract_text_from_file

router = APIRouter()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Upload and parse a document (admin only)"""
    # Validate file type
    file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    if file_extension not in settings.ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(settings.ALLOWED_FILE_TYPES)}"
        )
    
    # Validate file size
    if file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE} bytes"
        )
    
    # Save file to disk
    file_path = os.path.join(settings.UPLOAD_DIR, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not save file: {str(e)}"
        )
    
    # Create document record
    document = create_document(
        db=db,
        document=type('obj', (object,), {
            'filename': file.filename,
            'content_type': file.content_type
        })(),
        filepath=file_path,
        size_bytes=file.size,
        user_id=current_user.id
    )
    
    # Extract text and update status
    try:
        extracted_text = extract_text_from_file(file_path, file.content_type)
        if extracted_text:
            create_document_text(db, document.id, extracted_text)
            update_document_status(db, document.id, "parsed")
        else:
            update_document_status(db, document.id, "failed")
    except Exception as e:
        print(f"Error parsing document {file.filename}: {e}")
        update_document_status(db, document.id, "failed")
    
    # Refresh document to get updated status
    db.refresh(document)
    return document


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """List all documents (admin only)"""
    return get_documents(db)


@router.get("/{document_id}", response_model=DocumentWithText)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Get document details with text (admin only)"""
    document = get_document_by_id(db, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    return document


@router.delete("/{document_id}")
async def delete_document_endpoint(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Delete a document (admin only)"""
    document = get_document_by_id(db, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Delete file from disk
    try:
        if os.path.exists(document.filepath):
            os.remove(document.filepath)
    except Exception as e:
        print(f"Error deleting file {document.filepath}: {e}")
    
    # Delete from database
    success = delete_document(db, document_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not delete document"
        )
    
    return {"message": "Document deleted successfully"}


@router.post("/{document_id}/reparse")
async def reparse_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Re-parse a document (admin only)"""
    document = get_document_by_id(db, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Re-extract text
    try:
        extracted_text = extract_text_from_file(document.filepath, document.content_type)
        if extracted_text:
            # Delete existing text
            from ..models.document import DocumentText
            db.query(DocumentText).filter(DocumentText.document_id == document_id).delete()
            
            # Create new text record
            create_document_text(db, document.id, extracted_text)
            update_document_status(db, document.id, "parsed")
        else:
            update_document_status(db, document.id, "failed")
    except Exception as e:
        print(f"Error reparsing document {document.filename}: {e}")
        update_document_status(db, document.id, "failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not reparse document: {str(e)}"
        )
    
    db.refresh(document)
    return document
