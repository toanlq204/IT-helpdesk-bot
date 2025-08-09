from pydantic import BaseModel
from typing import List, Optional

class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    file_ids: List[str] = []
    enable_tts: bool = False
    tts_language: str = "en"  # "en" or "vn"

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    function_calls: List[str] = []
    has_audio: bool = False
    audio_url: Optional[str] = None 