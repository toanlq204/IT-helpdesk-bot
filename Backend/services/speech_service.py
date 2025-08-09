import torch
import scipy.io.wavfile
import numpy as np
import os
from transformers import VitsModel, AutoTokenizer

# Try to import audio playback libraries
try:
    from IPython.display import Audio, display
    IPYTHON_AVAILABLE = True
except ImportError:
    IPYTHON_AVAILABLE = False

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

try:
    from playsound import playsound
    PLAYSOUND_AVAILABLE = True
except ImportError:
    PLAYSOUND_AVAILABLE = False


def load_speech_model(model_name="facebook/mms-tts-vie"):
    try:
        model = VitsModel.from_pretrained(model_name)
        tokenizer = AutoTokenizer.from_pretrained(model_name)

        return model, tokenizer
    except Exception as e:
        return None, None


def generate_speech(model, tokenizer, text):
    try:
        # Tokenize the input text
        inputs = tokenizer(text, return_tensors="pt")

        # Generate speech
        with torch.no_grad():
            output = model(**inputs).waveform

        # Convert PyTorch tensor to numpy array
        waveform = output.squeeze().cpu().numpy()
        sample_rate = model.config.sampling_rate

        # Ensure correct data format
        if waveform.dtype != np.float32:
            waveform = waveform.astype(np.float32)

        # Normalize audio to prevent clipping
        waveform = waveform / np.max(np.abs(waveform)) * 0.9

        return waveform, sample_rate
    except Exception as e:
        return None, None


def play_audio(waveform, sample_rate, method="auto"):
    try:
        if method == "auto":
            # Try IPython first (for Jupyter notebooks)
            if PYGAME_AVAILABLE:
                return _play_with_pygame(waveform, sample_rate)

            # Fallback: save and play file
            else:
                return _play_with_playsound(waveform, sample_rate)
        elif method == "pygame" and PYGAME_AVAILABLE:
            return _play_with_pygame(waveform, sample_rate)
        elif method == "playsound" and PLAYSOUND_AVAILABLE:
            return _play_with_playsound(waveform, sample_rate)
        else:
            return False
    except Exception as e:
        return False


def _play_with_pygame(waveform, sample_rate):
    try:
        import tempfile
        import time

        # Initialize pygame mixer
        pygame.mixer.init(frequency=sample_rate, size=-16, channels=1)

        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = temp_file.name

        # Save audio to temporary file
        scipy.io.wavfile.write(temp_path, sample_rate, waveform)

        # Play audio
        pygame.mixer.music.load(temp_path)
        pygame.mixer.music.play()

        # Wait for playback to complete
        duration = len(waveform) / sample_rate
        time.sleep(duration + 0.5)  # Add small buffer

        # Cleanup
        pygame.mixer.quit()
        os.unlink(temp_path)

        return True
    except Exception as e:
        return False


def _play_with_playsound(waveform, sample_rate):
    try:
        import tempfile
        import time

        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = temp_file.name

        # Save audio to temporary file
        scipy.io.wavfile.write(temp_path, sample_rate, waveform)

        # Play using playsound
        playsound(temp_path)

        # Clean up temporary file
        try:
            os.unlink(temp_path)
        except:
            pass  # File might be locked during playback

        return True

    except Exception as e:
        return False


def text_to_speech(text):
    # Load model
    model, tokenizer = load_speech_model()
    if model is None or tokenizer is None:
        return

    waveform, sample_rate = generate_speech(model, tokenizer, text)
    if waveform is None:
        return

    play_audio(waveform, sample_rate, "pygame")
