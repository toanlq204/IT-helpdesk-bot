import io
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

# Try to import TTS dependencies, handle gracefully if not available
try:
    import torch
    import torchaudio
    import soundfile as sf
    from transformers import SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan
    from datasets import load_dataset
    import numpy as np
    TTS_DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    TTS_DEPENDENCIES_AVAILABLE = False
    MISSING_DEPENDENCY_ERROR = str(e)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TTSService:
    """Text-to-Speech service using Hugging Face SpeechT5 model"""
    
    def __init__(self):
        if not TTS_DEPENDENCIES_AVAILABLE:
            logger.warning(f"TTS dependencies not available: {MISSING_DEPENDENCY_ERROR}")
            self._dependencies_available = False
            self._initialized = False
            return
            
        self.processor = None
        self.model = None
        self.vocoder = None
        self.speaker_embeddings = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.executor = ThreadPoolExecutor(max_workers=2)
        self._dependencies_available = True
        self._initialized = False
        
    async def initialize(self):
        """Initialize the TTS models asynchronously"""
        if not self._dependencies_available:
            raise RuntimeError(f"TTS dependencies not available: {MISSING_DEPENDENCY_ERROR}. Please install with: pip install transformers torch torchaudio soundfile datasets")
            
        if self._initialized:
            return
            
        try:
            logger.info("Initializing TTS service...")
            
            # Run model loading in thread pool to avoid blocking
            await asyncio.get_event_loop().run_in_executor(
                self.executor, self._load_models
            )
            
            self._initialized = True
            logger.info("TTS service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize TTS service: {e}")
            raise
    
    def _load_models(self):
        """Load TTS models (runs in thread pool)"""
        # Load processor and model
        self.processor = SpeechT5Processor.from_pretrained("microsoft/speecht5_tts")
        self.model = SpeechT5ForTextToSpeech.from_pretrained("microsoft/speecht5_tts")
        self.vocoder = SpeechT5HifiGan.from_pretrained("microsoft/speecht5_hifigan")
        
        # Move to device
        self.model = self.model.to(self.device)
        self.vocoder = self.vocoder.to(self.device)
        
        # Load speaker embeddings
        embeddings_dataset = load_dataset("Matthijs/cmu-arctic-xvectors", split="validation")
        self.speaker_embeddings = torch.tensor(embeddings_dataset[7306]["xvector"]).unsqueeze(0).to(self.device)
    
    async def text_to_speech(self, text: str, sample_rate: int = 16000) -> bytes:
        """
        Convert text to speech and return audio bytes
        
        Args:
            text: Text to convert to speech
            sample_rate: Sample rate for output audio
            
        Returns:
            Audio data as bytes in WAV format
        """
        if not self._dependencies_available:
            raise RuntimeError(f"TTS dependencies not available: {MISSING_DEPENDENCY_ERROR}. Please install with: pip install transformers torch torchaudio soundfile datasets")
            
        if not self._initialized:
            await self.initialize()
        
        try:
            # Run TTS generation in thread pool
            audio_data = await asyncio.get_event_loop().run_in_executor(
                self.executor, self._generate_speech, text, sample_rate
            )
            return audio_data
            
        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            raise
    
    def _generate_speech(self, text: str, sample_rate: int) -> bytes:
        """Generate speech from text (runs in thread pool)"""
        # Preprocess text
        inputs = self.processor(text=text, return_tensors="pt").to(self.device)
        
        # Generate speech
        with torch.no_grad():
            speech = self.model.generate_speech(
                inputs["input_ids"], 
                self.speaker_embeddings, 
                vocoder=self.vocoder
            )
        
        # Convert to numpy and ensure correct format
        speech_np = speech.cpu().numpy()
        
        # Resample if needed
        if sample_rate != 16000:
            # Use torchaudio for resampling
            speech_tensor = torch.from_numpy(speech_np).unsqueeze(0)
            resampler = torchaudio.transforms.Resample(16000, sample_rate)
            speech_tensor = resampler(speech_tensor)
            speech_np = speech_tensor.squeeze().numpy()
        
        # Convert to bytes using soundfile
        audio_buffer = io.BytesIO()
        sf.write(audio_buffer, speech_np, sample_rate, format='WAV')
        audio_buffer.seek(0)
        
        return audio_buffer.getvalue()
    
    def cleanup(self):
        """Cleanup resources"""
        if hasattr(self, 'executor') and self.executor:
            self.executor.shutdown(wait=True)

# Global TTS service instance
tts_service = TTSService()

async def get_tts_service() -> TTSService:
    """Get initialized TTS service instance"""
    if not tts_service._dependencies_available:
        # Return service even if dependencies aren't available - the error will be handled in the endpoint
        return tts_service
    if not tts_service._initialized:
        await tts_service.initialize()
    return tts_service
