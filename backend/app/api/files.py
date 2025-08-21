from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
from ..core.database import get_db
from ..models.user import User
from ..utils.auth import get_admin_user
from ..repositories.document_repository import get_document_by_id

router = APIRouter()


@router.get("/{document_id}")
async def download_file(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Download a file (admin only)"""
    document = get_document_by_id(db, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if not os.path.exists(document.filepath):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk"
        )
    
    return FileResponse(
        path=document.filepath,
        filename=document.filename,
        media_type=document.content_type
    )
