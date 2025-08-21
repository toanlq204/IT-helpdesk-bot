from datetime import datetime
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from ..models.conversation import Conversation, Message
from ..models.document import Document
from ..repositories.document_repository import search_documents
from ..core.config import settings
import logging

# LangChain imports for LLM integration
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain.schema import BaseMessage

logger = logging.getLogger(__name__)


class ITSupportChatService:
    """
    Enhanced IT Support Chat Service with LLM integration and RAG capabilities
    """
    
    def __init__(self):
        self.llm = None
        self.system_prompt = None
        self._init_llm()
    
    def _init_llm(self):
        """Initialize the LLM (Azure OpenAI or OpenAI)"""
        try:
            # Try Azure OpenAI first
            if (settings.AZ_OPEN_AI_URL and 
                settings.AZ_OPEN_AI_CHAT_KEY and 
                settings.AZ_OPEN_AI_CHAT_MODEL):
                
                logger.info("Initializing Azure OpenAI LLM")
                self.llm = ChatOpenAI(
                    api_key=settings.AZ_OPEN_AI_CHAT_KEY,
                    base_url=settings.AZ_OPEN_AI_URL,
                    model=settings.AZ_OPEN_AI_CHAT_MODEL,
                    temperature=float(settings.AZ_OPEN_AI_CHAT_MODEL_TEMPERATURE or "0.7"),
                    max_tokens=1000,
                    timeout=30
                )
                logger.info("Azure OpenAI LLM initialized successfully")
            else:
                logger.warning("No LLM configuration found. Using fallback mode.")
                return
            
            # Initialize system prompt
            self._init_conversation_chain()
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            self.llm = None
    
    def _init_conversation_chain(self):
        """Initialize the conversation chain with proper prompt template"""
        if not self.llm:
            return
        
        try:
            # Simple prompt template that will be manually formatted
            self.system_prompt = settings.SYSTEM_PROMPT
            logger.info("LLM prompt template initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize system prompt: {e}")
            self.system_prompt = settings.SYSTEM_PROMPT
    
    def _format_conversation_history(self, messages: List[Dict]) -> List[BaseMessage]:
        """Convert message history to LangChain format"""
        formatted_messages = []
        
        for msg in messages[-settings.MAX_CONVERSATION_TURNS:]:  # Limit history
            if msg["role"] == "user":
                formatted_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                formatted_messages.append(AIMessage(content=msg["content"]))
        
        return formatted_messages
    
    def _get_relevant_context(self, query: str, max_chunks: int = 3) -> str:
        """Get relevant context from documents using RAG"""
        try:
            relevant_chunks = search_documents(query, limit=max_chunks)
            
            if not relevant_chunks:
                return "No relevant context found in knowledge base."
            
            context_parts = []
            for i, chunk in enumerate(relevant_chunks, 1):
                filename = chunk["metadata"].get("filename", "Unknown")
                content = chunk["content"]
                score = chunk.get("score", 0)
                
                context_parts.append(
                    f"Document {i}: {filename} (relevance: {score:.3f})\n"
                    f"Content: {content}\n"
                )
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Error getting relevant context: {e}")
            return "Error retrieving context from knowledge base."
    
    def generate_response(self, 
                         user_message: str, 
                         conversation_history: List[Dict],
                         session_id: str) -> Dict:
        """
        Generate LLM response with RAG context and conversation history
        """
        try:
            if not self.llm:
                logger.warning("LLM not available, using fallback")
                return self._fallback_response(user_message, conversation_history)
            
            # Get relevant context from RAG
            context = self._get_relevant_context(user_message)
            
            # Format conversation history
            formatted_history = self._format_conversation_history(conversation_history)
            
            # Build messages for LLM
            messages = []
            
            # Add system prompt
            system_content = f"{self.system_prompt}\n\nContext from knowledge base:\n{context}"
            messages.append(SystemMessage(content=system_content))
            
            # Add conversation history (limit to recent messages)
            messages.extend(formatted_history[-settings.MAX_CONVERSATION_TURNS:])
            
            # Add current user message
            messages.append(HumanMessage(content=user_message))
            
            # Generate response using direct LLM call
            response = self.llm.invoke(messages)
            
            # Extract citations from context
            citations = self._extract_citations_from_context(context)
            
            logger.info(f"Generated LLM response for session {session_id}")
            
            return {
                "reply": response.content,
                "citations": citations
            }
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            return self._fallback_response(user_message, conversation_history, error=str(e))
    
    def _extract_citations_from_context(self, context: str) -> List[Dict]:
        """Extract document citations from context"""
        citations = []
        try:
            lines = context.split('\n')
            for line in lines:
                if line.startswith("Document") and ":" in line:
                    # Extract filename from "Document X: filename (relevance: ...)"
                    parts = line.split(": ", 1)
                    if len(parts) > 1:
                        filename_part = parts[1].split(" (relevance:")[0]
                        filename = filename_part.strip()
                        if filename not in citations:
                            citations.append({"filename": filename})
        except Exception as e:
            logger.error(f"Error extracting citations: {e}")
        
        return citations
    
    def _fallback_response(self, 
                          user_message: str, 
                          conversation_history: List[Dict],
                          error: Optional[str] = None) -> Dict:
        """Fallback response when LLM is not available"""
        try:
            # Still try to get relevant context using RAG
            relevant_chunks = search_documents(user_message, limit=2)
            
            if relevant_chunks:
                unique_filenames = list(set([
                    chunk["metadata"].get("filename", "Unknown") 
                    for chunk in relevant_chunks
                ]))
                
                reply = f"**IT Support Assistant (Knowledge Base Mode)**\n\n"
                reply += f"Regarding your question: \"{user_message}\"\n\n"
                reply += "I found relevant information in the knowledge base:\n\n"
                
                for i, chunk in enumerate(relevant_chunks, 1):
                    content_preview = chunk["content"][:300] + "..." if len(chunk["content"]) > 300 else chunk["content"]
                    filename = chunk["metadata"].get("filename", "Unknown")
                    
                    reply += f"**Source {i}** ({filename}):\n{content_preview}\n\n"
                
                reply += "💡 This information should help with your question. "
                
                if error:
                    reply += f"\n\n⚠️ Note: Full AI assistance is temporarily unavailable ({error})"
                
                citations = [{"filename": filename} for filename in unique_filenames]
                
            else:
                reply = f"**IT Support Assistant**\n\n"
                reply += f"I understand you're asking about: \"{user_message}\"\n\n"
                reply += "I couldn't find specific information in the knowledge base. "
                reply += "Please try rephrasing your question or contact IT support directly.\n\n"
                
                if error:
                    reply += f"⚠️ Technical issue: {error}"
                
                citations = []
            
            return {"reply": reply, "citations": citations}
            
        except Exception as e:
            logger.error(f"Error in fallback response: {e}")
            return {
                "reply": f"I apologize, but I'm experiencing technical difficulties. "
                        f"Please contact IT support directly for assistance with: \"{user_message}\"",
                "citations": []
            }


# Global chat service instance
chat_service = ITSupportChatService()


def enhanced_reply(db: Session, user_id: int, session_id: str, text: str, messages: List[Dict]) -> Dict:
    """
    Enhanced response using LLM with RAG context and conversation history
    """
    return chat_service.generate_response(text, messages, session_id)


def placeholder_reply(db: Session, user_id: int, session_id: str, text: str, messages: List[Dict]) -> Dict:
    """
    Backward compatibility wrapper - now uses enhanced LLM reply
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