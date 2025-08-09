
from fastapi import APIRouter, HTTPException, Depends
from models.chat_models import ChatMessage, ChatResponse
from services.conversation_service import ConversationService
from services.ticket_service import TicketService
from services.chat_service import ChatService
from services.conversation_memory_service import conversation_memory
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime

router = APIRouter()

# Dependency injection


def get_conversation_service():
    return ConversationService()


def get_ticket_service():
    return TicketService()


def get_chat_service():
    return ChatService()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    chat_request: ChatMessage,
    conversation_service: ConversationService = Depends(
        get_conversation_service),
    ticket_service: TicketService = Depends(get_ticket_service),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Handle chat messages with OpenAI integration and function calling"""
    try:
        conversation_id = chat_request.conversation_id or str(uuid.uuid4())

        # Load existing conversation or create new one
        conversation = conversation_service.load_conversation(conversation_id)
        if not conversation:
            conversation = conversation_service.create_conversation(
                conversation_id)

        conversation_service.add_message(
            conversation,
            role="user",
            content=chat_request.message,
        )

        # Get AI response
        # assistant_message, function_calls = await openai_service.get_chat_response(messages)
        assistant_message = chat_service.get_response(conversation['messages'])
        # Add user message to conversation

        if assistant_message is not None and isinstance(assistant_message, str):
            # Add assistant message to conversation
            conversation_service.add_message(
                conversation,
                role="assistant",
                content=assistant_message
            )

        # Save conversation
        conversation_service.save_conversation(conversation)

        return ChatResponse(
            response=assistant_message,
            conversation_id=conversation_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# New models for enhanced chat


class EnhancedChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class EnhancedChatResponse(BaseModel):
    response: str
    conversation_id: Optional[str]
    conversation_turns: int
    confidence_level: str
    needs_human_review: bool
    sources: list
    retrieved_count: int
    log_id: Optional[str] = None  # For feedback tracking
    recommendation: Optional[str] = None


@router.post("/chat/enhanced", response_model=EnhancedChatResponse)
async def enhanced_chat(
    chat_request: EnhancedChatMessage,
    chat_service: ChatService = Depends(get_chat_service)
):
    """Handle chat messages with ChromaDB knowledge base and conversation memory"""
    try:
        # Generate conversation ID if not provided
        conversation_id = chat_request.conversation_id or str(uuid.uuid4())

        # Get enhanced response with conversation context
        result = chat_service.get_enhanced_response(
            chat_request.message,
            conversation_id=conversation_id
        )

        return EnhancedChatResponse(
            response=result["response"],
            conversation_id=result.get("conversation_id", conversation_id),
            conversation_turns=result.get("conversation_turns", 0),
            confidence_level=result.get("confidence_level", "unknown"),
            needs_human_review=result.get("needs_human_review", False),
            sources=result.get("sources", []),
            retrieved_count=result.get("retrieved_count", 0),
            log_id=result.get("log_id"),  # Include log_id for feedback
            recommendation=result.get("recommendation")
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversation/{conversation_id}/stats")
async def get_conversation_stats(conversation_id: str):
    """Get conversation statistics"""
    try:
        stats = conversation_memory.get_conversation_stats(conversation_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/conversation/{conversation_id}")
async def clear_conversation(conversation_id: str):
    """Clear conversation history"""
    try:
        success = conversation_memory.clear_conversation(conversation_id)
        return {"success": success, "message": f"Conversation {conversation_id} cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")
