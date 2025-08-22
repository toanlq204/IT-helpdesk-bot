from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..core.database import get_db
from ..models.user import User
from ..models.conversation import Conversation
from ..schemas.chat import ChatStart, ChatMessage, ChatResponse, ChatStartResponse, ConversationResponse
from ..utils.auth import get_current_user
from ..services.chat_service import (
    placeholder_reply, get_or_create_conversation, add_message, get_conversation_history
)

router = APIRouter()

# TODO: stream responses (SSE/WebSocket) once LLM added


@router.post("/start", response_model=ChatStartResponse)
async def start_conversation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start a new chat conversation"""
    conversation = get_or_create_conversation(db, current_user.id)
    return ChatStartResponse(session_id=conversation.session_id)


@router.post("/message", response_model=ChatResponse)
async def send_message(
    chat_message: ChatMessage,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a message and get placeholder AI response"""
    # Get or create conversation
    conversation = get_or_create_conversation(db, current_user.id, chat_message.session_id)
    
    messages = [{
        "role": msg.role,
        "content": msg.content,
        "metadata": msg.metadata
    } for msg in conversation.messages]
    messages.append({"role": "user", "content": chat_message.message})
    user_message = chat_message.message

    # Add user message
    add_message(db, conversation.id, "user", chat_message.message)
    
    # Generate placeholder response
    response_data = placeholder_reply(db, current_user, chat_message.session_id, chat_message.message, messages)
    
    # Add assistant message
    add_message(db, conversation.id, "assistant", response_data["reply"], message_metadata={"citations": response_data["citations"]})
    
    return ChatResponse(
        reply=response_data["reply"],
        citations=response_data["citations"]
    )


@router.get("/{session_id}/history", response_model=ConversationResponse)
async def get_chat_history(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get conversation history for a session"""
    messages = get_conversation_history(db, session_id, current_user.id)
    
    # Get conversation details
    from ..models.conversation import Conversation
    conversation = db.query(Conversation).filter(
        Conversation.session_id == session_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return ConversationResponse(
        id=conversation.id,
        user_id=conversation.user_id,
        session_id=conversation.session_id,
        created_at=conversation.created_at,
        messages=messages
    )


@router.get("/conversations", response_model=List[ConversationResponse])
async def get_user_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all conversations for the current user"""
    conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(Conversation.created_at.desc()).all()
    
    return [
        ConversationResponse(
            id=conv.id,
            user_id=conv.user_id,
            session_id=conv.session_id,
            created_at=conv.created_at,
            messages=conv.messages
        ) for conv in conversations
    ]
