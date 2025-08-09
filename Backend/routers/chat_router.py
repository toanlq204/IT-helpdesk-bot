
from fastapi import APIRouter, HTTPException, Depends
from models.chat_models import ChatMessage, ChatResponse
from services.conversation_service import ConversationService
from services.ticket_service import TicketService
from services.chat_service import ChatService
from services.speech_service import load_en_speech_model, load_vn_speech_model, generate_speech
import uuid
import tempfile
import os
from datetime import datetime

router = APIRouter()

# Global model cache to avoid reloading models frequently
_speech_model_cache = {}

def get_cached_speech_model(language: str):
    """Get cached speech model or load new one"""
    if language not in _speech_model_cache:
        if language == "vn":
            model, tokenizer = load_vn_speech_model()
        else:  # default to English
            model, tokenizer = load_en_speech_model()
        
        if model is not None and tokenizer is not None:
            _speech_model_cache[language] = (model, tokenizer)
        else:
            return None, None
    
    return _speech_model_cache[language]

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
    conversation_service: ConversationService = Depends(get_conversation_service),
    ticket_service: TicketService = Depends(get_ticket_service),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Handle chat messages with OpenAI integration and function calling"""
    try:
        conversation_id = chat_request.conversation_id or str(uuid.uuid4())
        
        # Load existing conversation or create new one
        conversation = conversation_service.load_conversation(conversation_id)
        if not conversation:
            conversation = conversation_service.create_conversation(conversation_id)
        
        conversation_service.add_message(
            conversation,
            role="user",
            content=chat_request.message,
        )
        
        # Get AI response
        #assistant_message, function_calls = await openai_service.get_chat_response(messages)
        assistant_message = chat_service.get_response(conversation['messages'])
        
        # Initialize response data
        has_audio = False
        audio_url = None
        
        # Generate speech if TTS is enabled and we have a valid response
        if (chat_request.enable_tts and 
            assistant_message and 
            isinstance(assistant_message, str) and 
            assistant_message.strip()):
            
            try:
                # Get speech model for the requested language
                model, tokenizer = get_cached_speech_model(chat_request.tts_language)
                
                if model is not None and tokenizer is not None:
                    # Generate speech
                    waveform, sample_rate = generate_speech(model, tokenizer, assistant_message)
                    
                    if waveform is not None and sample_rate is not None:
                        # Save audio to temporary file (in production, you might want to save to a permanent location)
                        temp_audio_dir = "temp_audio"
                        os.makedirs(temp_audio_dir, exist_ok=True)
                        
                        audio_filename = f"speech_{conversation_id}_{uuid.uuid4().hex[:8]}.wav"
                        audio_path = os.path.join(temp_audio_dir, audio_filename)
                        
                        # Convert to 16-bit PCM and save
                        import scipy.io.wavfile
                        audio_data = (waveform * 32767).astype('int16')
                        scipy.io.wavfile.write(audio_path, sample_rate, audio_data)
                        
                        has_audio = True
                        audio_url = f"/audio/{audio_filename}"
                        
            except Exception as e:
                print(f"TTS generation failed: {str(e)}")
                # Continue without audio if TTS fails
                pass
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
            conversation_id=conversation_id,
            has_audio=has_audio,
            audio_url=audio_url
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}") 