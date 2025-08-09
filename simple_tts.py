#!/usr/bin/env python3
"""
Simple TTS System for Corporate Environments
============================================

Lightweight Text-to-Speech implementation for environments where
heavy ML dependencies (PyTorch, transformers) are not available.

Supported Backends:
1. System TTS (macOS 'say', Windows SAPI, Linux espeak)
2. Web Speech API (browser-based synthesis)
3. Audio placeholders for UI consistency

Features:
- Zero external dependencies
- Cross-platform compatibility
- Voice control (start/stop)
- Corporate network friendly
- Graceful degradation

Author: GitHub Copilot
Version: 1.0
Date: August 2025
"""

import subprocess
import sys
import platform
import tempfile
import base64
import os
from typing import Optional, List

class SimpleTTSManager:
    """
    Lightweight TTS Manager for Corporate Environments
    
    Provides reliable text-to-speech functionality without heavy dependencies.
    Automatically detects and uses available system voice capabilities.
    
    Supported Systems:
    - macOS: Built-in 'say' command
    - Windows: SAPI (Speech API) 
    - Linux: espeak (if installed)
    - Web: Browser Speech Synthesis API
    
    Features:
    - Zero ML dependencies
    - Instant voice control (start/stop)
    - Cross-platform compatibility
    - Audio file generation for UI consistency
    """
    
    def __init__(self):
        """Initialize TTS manager and detect available voice methods"""
        self.system = platform.system()
        self.available_methods = self._check_available_methods()
    
    def _check_available_methods(self) -> List[str]:
        """
        Check which TTS methods are available on this system
        
        Returns:
            List[str]: Available TTS methods
        """
        methods = []
        
        # Check for system TTS
        if self.system == "Darwin":  # macOS
            try:
                subprocess.run(["which", "say"], check=True, capture_output=True)
                methods.append("macos_say")
            except subprocess.CalledProcessError:
                pass
        
        elif self.system == "Windows":
            methods.append("windows_sapi")
        
        elif self.system == "Linux":
            # Check for espeak
            try:
                subprocess.run(["which", "espeak"], check=True, capture_output=True)
                methods.append("espeak")
            except subprocess.CalledProcessError:
                pass
        
        # Web Speech API is always available (browser-based)
        methods.append("web_speech")
        
        return methods
    
    def text_to_speech_system(self, text: str) -> bool:
        """Use system TTS to speak text directly"""
        try:
            if "macos_say" in self.available_methods:
                subprocess.run(["say", text], check=True)
                return True
            
            elif "windows_sapi" in self.available_methods:
                # Windows PowerShell TTS
                ps_command = f'Add-Type -AssemblyName System.Speech; $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; $speak.Speak("{text}")'
                subprocess.run(["powershell", "-Command", ps_command], check=True)
                return True
            
            elif "espeak" in self.available_methods:
                subprocess.run(["espeak", text], check=True)
                return True
                
        except Exception as e:
            print(f"System TTS failed: {e}")
        
        return False
    
    def stop_system_speech(self) -> bool:
        """Stop current system TTS playback"""
        try:
            if "macos_say" in self.available_methods:
                # Kill any running 'say' processes
                subprocess.run(["pkill", "-f", "say"], check=False)
                return True
            
            elif "windows_sapi" in self.available_methods:
                # Stop Windows SAPI speech
                ps_command = 'Get-Process | Where-Object {$_.ProcessName -eq "powershell"} | Stop-Process -Force'
                subprocess.run(["powershell", "-Command", ps_command], check=False)
                return True
            
            elif "espeak" in self.available_methods:
                subprocess.run(["pkill", "-f", "espeak"], check=False)
                return True
                
        except Exception as e:
            print(f"Stop system TTS failed: {e}")
        
        return False
    
    def text_to_speech_web(self, text: str) -> str:
        """Generate Web Speech API JavaScript for browser TTS"""
        # Clean text for JavaScript
        clean_text = text.replace('"', '\\"').replace('\n', ' ').replace('\r', '')
        
        web_speech_js = f"""
        <script>
        // Stop any existing speech
        if (window.speechSynthesis) {{
            window.speechSynthesis.cancel();
        }}
        
        function speakText() {{
            if ('speechSynthesis' in window) {{
                const utterance = new SpeechSynthesisUtterance("{clean_text}");
                utterance.rate = 0.9;
                utterance.pitch = 1.0;
                utterance.volume = 1.0;
                
                // Try to use a good voice
                const voices = speechSynthesis.getVoices();
                const englishVoice = voices.find(voice => voice.lang.startsWith('en'));
                if (englishVoice) {{
                    utterance.voice = englishVoice;
                }}
                
                // Store reference for stopping
                window.currentUtterance = utterance;
                
                speechSynthesis.speak(utterance);
            }} else {{
                console.log('Speech synthesis not supported');
            }}
        }}
        
        // Add global stop function
        window.stopSpeech = function() {{
            if (window.speechSynthesis) {{
                window.speechSynthesis.cancel();
            }}
        }};
        
        speakText();
        </script>
        """
        
        return web_speech_js
    
    def stop_web_speech(self) -> str:
        """Generate JavaScript to stop web speech"""
        stop_js = """
        <script>
        if (window.speechSynthesis) {
            window.speechSynthesis.cancel();
        }
        console.log('Web speech stopped');
        </script>
        """
        return stop_js
    
    def create_audio_placeholder(self, text: str) -> str:
        """Create a base64 encoded simple beep as audio placeholder"""
        try:
            # Create a simple sine wave beep (440Hz for 0.5 seconds)
            import wave
            import math
            
            # Audio parameters
            sample_rate = 16000
            duration = 0.5
            frequency = 440  # A4 note
            
            # Generate sine wave
            samples = []
            for i in range(int(sample_rate * duration)):
                sample = int(32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
                samples.extend([sample & 0xFF, (sample >> 8) & 0xFF])  # 16-bit little-endian
            
            # Create WAV file in memory
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                with wave.open(temp_file.name, 'wb') as wav_file:
                    wav_file.setnchannels(1)  # Mono
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(sample_rate)
                    wav_file.writeframes(bytes(samples))
                
                # Read and encode as base64
                with open(temp_file.name, 'rb') as f:
                    audio_data = f.read()
                    audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                
                # Clean up
                os.unlink(temp_file.name)
                
                return audio_base64
                
        except Exception as e:
            print(f"Audio placeholder creation failed: {e}")
            return ""

def get_simple_tts_manager():
    """Factory function to get TTS manager"""
    return SimpleTTSManager()

# Test the implementation
if __name__ == "__main__":
    tts = SimpleTTSManager()
    print(f"Available TTS methods: {tts.available_methods}")
    
    test_text = "Hello! This is a test of the simple TTS system."
    
    print("Testing system TTS...")
    if tts.text_to_speech_system(test_text):
        print("✅ System TTS working")
    else:
        print("❌ System TTS not available")
    
    print("\nTesting web speech generation...")
    web_js = tts.text_to_speech_web(test_text)
    if web_js:
        print("✅ Web Speech JavaScript generated")
        print(f"Length: {len(web_js)} characters")
    else:
        print("❌ Web Speech generation failed")
