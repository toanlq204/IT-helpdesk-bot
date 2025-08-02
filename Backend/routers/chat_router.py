from fastapi import APIRouter, HTTPException, Depends
from models.chat_models import ChatMessage, ChatResponse
from services.conversation_service import ConversationService
from services.ticket_service import TicketService
import uuid
from datetime import datetime

router = APIRouter()

# Dependency injection
def get_conversation_service():
    return ConversationService()

def get_ticket_service():
    return TicketService()

@router.post("/chat", response_model=ChatResponse)
async def chat(
    chat_request: ChatMessage,
    conversation_service: ConversationService = Depends(get_conversation_service),
    ticket_service: TicketService = Depends(get_ticket_service)
):
    """Handle chat messages with OpenAI integration and function calling"""
    try:
        conversation_id = chat_request.conversation_id or str(uuid.uuid4())
        
        # Load existing conversation or create new one
        conversation = conversation_service.load_conversation(conversation_id)
        if not conversation:
            conversation = conversation_service.create_conversation(conversation_id)
        
        # Get file content if any files are attached
        
        
        # Prepare messages for OpenAI
        
        # Get AI response
        #assistant_message, function_calls = await openai_service.get_chat_response(messages)
        assistant_message = "Hello, how can I help you today?"
        # Add user message to conversation
        conversation_service.add_message(
            conversation,
            role="user",
            content=chat_request.message,
        )
        
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
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}") 