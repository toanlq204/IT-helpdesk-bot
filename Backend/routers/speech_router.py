from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
import tempfile
import os
import io
import scipy.io.wavfile
from services.speech_service import load_speech_model, generate_speech, load_en_speech_model, load_vn_speech_model, play_audio

router = APIRouter()

class TextToSpeechRequest(BaseModel):
    text: str
    language: str = "en"  # "en" for English, "vn" for Vietnamese

class TextToSpeechResponse(BaseModel):
    success: bool
    message: str = None
    audio_url: str = None

# Global model cache to avoid reloading models frequently
_model_cache = {}

def get_cached_model(language: str):
    """Get cached model or load new one"""
    if language not in _model_cache:
        if language == "vn":
            model, tokenizer = load_vn_speech_model()
        else:  # default to English
            model, tokenizer = load_en_speech_model()
        
        if model is not None and tokenizer is not None:
            _model_cache[language] = (model, tokenizer)
        else:
            return None, None
    
    return _model_cache[language]

@router.post("/text-to-speech", response_model=TextToSpeechResponse)
async def text_to_speech_api(request: TextToSpeechRequest):
    """Convert text to speech and return success status"""
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        # Get model for the specified language
      #   model, tokenizer = get_cached_model(request.language)
        model, tokenizer = load_speech_model()

        if model is None or tokenizer is None:
            return TextToSpeechResponse(
                success=False,
                message=f"Failed to load speech model for language: {request.language}"
            )
        
        # Generate speech
        waveform, sample_rate = generate_speech(model, tokenizer, request.text)
        play_audio(waveform, sample_rate, "pygame")
        
        if waveform is None or sample_rate is None:
            return TextToSpeechResponse(
                success=False,
                message="Failed to generate speech from text"
            )
        
        return TextToSpeechResponse(
            success=True,
            message="Speech generated successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text-to-speech failed: {str(e)}")

@router.post("/text-to-speech/audio")
async def text_to_speech_audio(request: TextToSpeechRequest):
    """Convert text to speech and return audio file"""
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        # Get model for the specified language
        model, tokenizer = get_cached_model(request.language)
        
        if model is None or tokenizer is None:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to load speech model for language: {request.language}"
            )
        
        # Generate speech
        waveform, sample_rate = generate_speech(model, tokenizer, request.text)
        
        if waveform is None or sample_rate is None:
            raise HTTPException(status_code=500, detail="Failed to generate speech from text")
        
        # Convert to bytes
        audio_buffer = io.BytesIO()
        
        # Convert numpy array to 16-bit PCM
        audio_data = (waveform * 32767).astype('int16')
        
        # Write to buffer as WAV
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            scipy.io.wavfile.write(temp_file.name, sample_rate, audio_data)
            temp_file.seek(0)
            
            # Read the file content
            with open(temp_file.name, 'rb') as f:
                audio_content = f.read()
            
            # Clean up temp file
            os.unlink(temp_file.name)
        
        # Return audio as streaming response
        return Response(
            content=audio_content,
            media_type="audio/wav",
            headers={
                "Content-Disposition": "attachment; filename=speech.wav"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text-to-speech failed: {str(e)}")

@router.post("/text-to-speech/stream")
async def text_to_speech_stream(request: TextToSpeechRequest):
    """Convert text to speech and return audio stream"""
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        # Get model for the specified language
        model, tokenizer = get_cached_model(request.language)
        
        if model is None or tokenizer is None:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to load speech model for language: {request.language}"
            )
        
        # Generate speech
        waveform, sample_rate = generate_speech(model, tokenizer, request.text)
        
        if waveform is None or sample_rate is None:
            raise HTTPException(status_code=500, detail="Failed to generate speech from text")
        
        # Convert to WAV format in memory
        audio_buffer = io.BytesIO()
        
        # Convert numpy array to 16-bit PCM
        audio_data = (waveform * 32767).astype('int16')
        
        # Write WAV data to buffer
        with tempfile.NamedTemporaryFile(suffix=".wav") as temp_file:
            scipy.io.wavfile.write(temp_file.name, sample_rate, audio_data)
            
            with open(temp_file.name, 'rb') as f:
                audio_content = f.read()
        
        # Create streaming response
        def audio_stream():
            yield audio_content
        
        return StreamingResponse(
            audio_stream(),
            media_type="audio/wav",
            headers={
                "Content-Length": str(len(audio_content)),
                "Accept-Ranges": "bytes"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text-to-speech failed: {str(e)}")

@router.get("/audio/{filename}")
async def get_audio_file(filename: str):
    """Serve generated audio files"""
    try:
        audio_path = os.path.join("temp_audio", filename)
        
        if not os.path.exists(audio_path):
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        return FileResponse(
            audio_path,
            media_type="audio/wav",
            filename=filename
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to serve audio file: {str(e)}")

@router.get("/speech/models")
async def get_available_models():
    """Get list of available speech models"""
    return {
        "models": [
            {
                "language": "en",
                "name": "English TTS",
                "model_id": "facebook/mms-tts-eng"
            },
            {
                "language": "vn", 
                "name": "Vietnamese TTS",
                "model_id": "facebook/mms-tts-vie"
            }
        ]
    }
