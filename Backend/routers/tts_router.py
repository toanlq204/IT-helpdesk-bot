from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import logging
import io
from services.tts_service import get_tts_service, TTSService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/tts")

class TTSRequest(BaseModel):
    """Request model for text-to-speech conversion"""
    text: str
    sample_rate: Optional[int] = 16000

class TTSResponse(BaseModel):
    """Response model for TTS requests"""
    message: str
    audio_length: Optional[float] = None

@router.post("/convert", response_class=StreamingResponse)
async def text_to_speech(
    request: TTSRequest,
    tts_service: TTSService = Depends(get_tts_service)
):
    """
    Convert text to speech and return audio stream
    
    Args:
        request: TTS request containing text and optional sample rate
        tts_service: TTS service dependency
        
    Returns:
        StreamingResponse with audio data in WAV format
    """
    try:
        # Validate input
        if not request.text or not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        if len(request.text) > 1000:
            raise HTTPException(status_code=400, detail="Text too long (max 1000 characters)")
        
        logger.info(f"Converting text to speech: {request.text[:50]}...")
        
        # Generate speech
        audio_data = await tts_service.text_to_speech(
            text=request.text.strip(),
            sample_rate=request.sample_rate
        )
        
        # Create audio stream
        audio_stream = io.BytesIO(audio_data)
        
        logger.info("TTS conversion completed successfully")
        
        # Return streaming response
        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type="audio/wav",
            headers={
                "Content-Disposition": "attachment; filename=speech.wav",
                "Content-Length": str(len(audio_data)),
                "Cache-Control": "no-cache"
            }
        )
        
    except HTTPException:
        raise
    except RuntimeError as e:
        if "TTS dependencies not available" in str(e):
            logger.warning(f"TTS dependencies missing: {e}")
            raise HTTPException(
                status_code=503, 
                detail=f"TTS service unavailable: {str(e)}"
            )
        else:
            logger.error(f"TTS runtime error: {e}")
            raise HTTPException(status_code=500, detail=f"TTS conversion failed: {str(e)}")
    except Exception as e:
        logger.error(f"TTS conversion failed: {e}")
        raise HTTPException(status_code=500, detail=f"TTS conversion failed: {str(e)}")

@router.get("/health")
async def tts_health_check(tts_service: TTSService = Depends(get_tts_service)):
    """
    Health check endpoint for TTS service
    
    Returns:
        Service status and model information
    """
    try:
        if not tts_service._dependencies_available:
            return {
                "status": "dependencies_missing",
                "service": "text-to-speech",
                "model": "microsoft/speecht5_tts",
                "initialized": False,
                "dependencies_available": False,
                "message": "TTS dependencies not installed. Run: pip install transformers torch torchaudio soundfile datasets"
            }
        
        return {
            "status": "healthy" if tts_service._initialized else "not_initialized",
            "service": "text-to-speech",
            "model": "microsoft/speecht5_tts",
            "initialized": tts_service._initialized,
            "dependencies_available": True,
            "device": str(tts_service.device) if tts_service._initialized else "not_initialized"
        }
    except Exception as e:
        logger.error(f"TTS health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
