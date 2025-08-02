from fastapi import APIRouter, HTTPException, Depends
from typing import List
from services.conversation_service import ConversationService

router = APIRouter()

# Dependency injection
def get_conversation_service():
    return ConversationService()

@router.get("/conversations")
async def get_conversations(
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """Get list of all conversations with metadata"""
    try:
        return conversation_service.get_all_conversations()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load conversations: {str(e)}")

@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """Get messages from a specific conversation"""
    try:
        messages = conversation_service.get_conversation_messages(conversation_id)
        if messages is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return messages
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load messages: {str(e)}")

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """Delete a conversation"""
    success = conversation_service.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"message": "Conversation deleted successfully"}