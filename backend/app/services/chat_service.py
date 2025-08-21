from datetime import datetime
from sqlalchemy.orm import Session
from typing import Dict, List
from ..models.conversation import Conversation, Message
from ..models.document import Document

# TODO: replace placeholder_reply with LangChain+Retriever pipeline

def placeholder_reply(db: Session, user_id: int, session_id: str, text: str) -> Dict:
    """
    Returns a canned response. 
    Optionally surfaces up to 3 recently parsed document filenames to pretend as 'related'.
    NO embeddings, NO LLM. Pure placeholder.
    """
    # Get recent document filenames
    recent_docs = db.query(Document).filter(
        Document.status == "parsed"
    ).order_by(Document.uploaded_at.desc()).limit(3).all()
    
    related_filenames = [doc.filename for doc in recent_docs]
    
    reply = (
        "🔧 Placeholder response:\n"
        f"• You said: \"{text}\"\n"
        "• I'll use your uploaded documents to answer once RAG is connected.\n"
    )
    
    if related_filenames:
        reply += "• Potential sources:\n" + "\n".join([f"  - {f}" for f in related_filenames])
    
    citations = [{"filename": filename} for filename in related_filenames]
    
    return {"reply": reply, "citations": citations}


def get_or_create_conversation(db: Session, user_id: int, session_id: str = None) -> Conversation:
    """Get existing conversation or create new one"""
    if session_id:
        conversation = db.query(Conversation).filter(
            Conversation.session_id == session_id,
            Conversation.user_id == user_id
        ).first()
        if conversation:
            return conversation
    
    # Create new conversation
    conversation = Conversation(user_id=user_id)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def add_message(db: Session, conversation_id: int, role: str, content: str, message_metadata: Dict = None) -> Message:
    """Add a message to the conversation"""
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        message_metadata=message_metadata
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_conversation_history(db: Session, session_id: str, user_id: int) -> List[Message]:
    """Get conversation history for a session"""
    conversation = db.query(Conversation).filter(
        Conversation.session_id == session_id,
        Conversation.user_id == user_id
    ).first()
    
    if not conversation:
        return []
    
    return db.query(Message).filter(
        Message.conversation_id == conversation.id
    ).order_by(Message.created_at.asc()).all()
