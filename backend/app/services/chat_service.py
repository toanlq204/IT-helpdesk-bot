from datetime import datetime
from sqlalchemy.orm import Session
from typing import Dict, List
from ..models.conversation import Conversation, Message
from ..models.document import Document
from ..repositories.document_repository import search_documents
from ..core.config import settings
import logging

logger = logging.getLogger(__name__)

# TODO: replace enhanced_reply with full LangChain+LLM pipeline

def enhanced_reply(db: Session, user_id: int, session_id: str, text: str, messages: List[Dict]) -> Dict:
    """
    Enhanced response using vector search to find relevant document chunks.
    Still a placeholder for LLM integration, but now uses actual RAG search.
    """
    try:
        # Search for relevant document chunks using vector similarity
        relevant_chunks = search_documents(text, limit=3)
        
        if relevant_chunks:
            # Extract unique filenames from the chunks
            unique_filenames = list(set([
                chunk["metadata"].get("filename", "Unknown") 
                for chunk in relevant_chunks
            ]))
            
            # Create a more intelligent response based on search results
            reply = (
                "🤖 Enhanced AI Assistant Response:\n\n"
                f"Based on your question: \"{text}\"\n\n"
                "I found relevant information in your knowledge base:\n\n"
            )
            
            # Add content from relevant chunks
            for i, chunk in enumerate(relevant_chunks):  # Limit to top 2 chunks
                content_preview = chunk["content"]
                filename = chunk["metadata"].get("filename", "Unknown")
                
                reply += f"**Source {i}** ({filename}):\n"
                reply += f"{content_preview}\n\n"
            
            reply += "💡 **AI Analysis**: This information from your uploaded documents should help answer your question. "
            reply += "Once full LLM integration is complete, I'll provide more comprehensive analysis and synthesis.\n\n"
            
            if len(relevant_chunks) > 2:
                reply += f"📚 Found {len(relevant_chunks)} total relevant sections across your documents."
            
            citations = [{"filename": filename} for filename in unique_filenames]
            
        else:
            # Fallback to basic response if no relevant chunks found
            reply = (
                f"I understand you're asking about: \"{text}\"\n\n"
                "I couldn't find specific information in your uploaded documents that directly relates to this question. "
            )
            citations = []
        
        return {"reply": reply, "citations": citations}
        
    except Exception as e:
        logger.error(f"Error in enhanced_reply: {e}")
        # Fallback to simple response
        return {
            "reply": (
                "🔧 AI Assistant (Fallback Mode):\n\n"
                f"I received your question: \"{text}\"\n\n"
                "I'm currently experiencing some technical difficulties accessing the knowledge base. "
                "Please try again in a moment, or contact your system administrator if the issue persists.\n\n"
                f"Error: {str(e)}"
            ),
            "citations": []
        }


def placeholder_reply(db: Session, user_id: int, session_id: str, text: str, messages: List[Dict]) -> Dict:
    """
    Backward compatibility wrapper - now uses enhanced_reply
    """
    return enhanced_reply(db, user_id, session_id, text, messages)


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
