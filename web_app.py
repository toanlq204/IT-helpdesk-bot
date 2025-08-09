#!/usr/bin/env python3
"""
Enhanced IT Helpdesk Bot Web Interface
======================================

Enterprise-grade Streamlit web application with advanced features:

🌍 **Multi-Language Support**
- Automatic language detection (EN, ES, FR, DE, PT, ZH, JA)
- Localized responses and UI elements
- User language preferences

👥 **Multi-Role User System**
- Staff: Basic ticket operations
- Manager: Department-level access + password resets
- BOD: Full statistics and reporting
- Admin: Complete system access + data management

🎫 **Advanced Ticket Management**
- Role-based ticket visibility
- Functional calling for ticket operations
- Real-time statistics and analytics
- Multi-department tracking

� **Voice Features**
- Text-to-speech with multiple backends
- System voice (macOS/Windows/Linux)
- Web Speech API fallback
- Voice control with start/stop functionality

�📊 **Enterprise Features**
- Statistical dashboards by role
- Data upload capabilities (Admin)
- Multi-session chat support
- Progressive UI with enhanced UX

🔐 **Security & Authentication**
- Role-based access control
- Permission validation
- Secure data handling

Author: GitHub Copilot
Version: 3.1 - Voice-Enabled Enterprise Edition
Date: August 2025
"""

# Standard library imports
import streamlit as st
import asyncio
import json
import time
import os
import base64
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any

# Configure Streamlit page
st.set_page_config(
    page_title="🤖 Enterprise IT Helpdesk Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Core application imports
try:
    from chatbot.core import EnhancedITHelpdeskBot
    from functions.helpdesk_functions import (
        get_user_by_username, get_localized_text, load_mock_data
    )
    from prompts.templates import get_user_role_prompt
except ImportError as e:
    st.error("❌ Unable to load chatbot modules. Please check installation.")
    st.error(f"Error details: {e}")
    st.stop()

# =============================================================================
# TTS (Text-to-Speech) System Configuration
# =============================================================================

# Full AI TTS with Hugging Face models (requires PyTorch)
TTS_AVAILABLE = False
try:
    from transformers import SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan
    from datasets import load_dataset
    import torch
    import soundfile as sf
    import io
    import logging
    TTS_AVAILABLE = True
    print("✅ Full AI TTS available (Hugging Face SpeechT5)")
except ImportError:
    print("⚠️  Full AI TTS not available. Install with: pip install transformers torch soundfile datasets")

# Simple TTS fallback (system voice + web speech)
SIMPLE_TTS_AVAILABLE = False
try:
    from simple_tts import SimpleTTSManager
    SIMPLE_TTS_AVAILABLE = True
    print("✅ Simple TTS fallback available (System voice + Web Speech)")
except ImportError:
    print("❌ Simple TTS fallback not available")

# TTS Manager Class with fallback support
# =============================================================================
# TTS Manager Class - Enterprise Voice System
# =============================================================================

class TTSManager:
    """
    Enterprise Text-to-Speech Manager with Multi-Backend Support
    
    Provides intelligent fallback between different TTS systems:
    1. Full AI TTS: Hugging Face SpeechT5 models (high quality)
    2. Simple TTS: System voice + Web Speech API (reliable fallback)
    
    Features:
    - Automatic backend selection based on availability
    - Voice playback control (start/stop)
    - Text preprocessing for better speech quality
    - Session state management
    - Corporate environment compatibility
    """
    
    def __init__(self):
        """Initialize TTS manager with automatic backend detection"""
        # Full AI TTS components
        self.processor = None
        self.model = None
        self.vocoder = None
        self.speaker_embeddings = None
        
        # Simple TTS fallback
        self.simple_tts = None
        
        # Manager state
        self.is_initialized = False
        self.mode = None  # 'full', 'simple', or 'none'
        
        # Auto-initialize with best available backend
        self.initialize()
    
    def initialize(self) -> bool:
        """
        Initialize TTS with best available method
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            if TTS_AVAILABLE:
                return self._initialize_full_tts()
            elif SIMPLE_TTS_AVAILABLE:
                return self._initialize_simple_tts()
            else:
                print("❌ No TTS capabilities available")
                return False
        except Exception as e:
            print(f"TTS initialization failed: {e}")
            # Try simple fallback even if full TTS failed
            if SIMPLE_TTS_AVAILABLE:
                return self._initialize_simple_tts()
            return False
    
    def _initialize_full_tts(self) -> bool:
        """Initialize full Hugging Face TTS"""
        try:
            print("Initializing SpeechT5 TTS model...")
            # Load SpeechT5 models
            self.processor = SpeechT5Processor.from_pretrained("microsoft/speecht5_tts")
            self.model = SpeechT5ForTextToSpeech.from_pretrained("microsoft/speecht5_tts")
            self.vocoder = SpeechT5HifiGan.from_pretrained("microsoft/speecht5_hifigan")
            
            # Load speaker embeddings dataset
            embeddings_dataset = load_dataset("Matthijs/cmu-arctic-xvectors", split="validation")
            self.speaker_embeddings = torch.tensor(embeddings_dataset[7306]["xvector"]).unsqueeze(0)
            
            self.is_initialized = True
            self.mode = 'full'
            print("✅ Full TTS models initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error initializing full TTS: {e}")
            return False
    
    def _initialize_simple_tts(self) -> bool:
        """Initialize simple TTS fallback"""
        try:
            self.simple_tts = SimpleTTSManager()
            self.is_initialized = True
            self.mode = 'simple'
            print(f"✅ Simple TTS initialized with methods: {self.simple_tts.available_methods}")
            return True
        except Exception as e:
            print(f"❌ Error initializing simple TTS: {e}")
            return False
    
    def text_to_speech(self, text: str, max_length: int = 500) -> Optional[str]:
        """
        Convert text to speech and return base64 encoded audio or web speech JS
        
        Args:
            text: Text to convert to speech
            max_length: Maximum text length to prevent memory issues
            
        Returns:
            Base64 encoded audio data, web speech JS, or None if failed
        """
        if not self.is_initialized:
            return None
        
        try:
            # Truncate text if too long
            if len(text) > max_length:
                text = text[:max_length] + "..."
            
            # Clean text for TTS
            text = self._clean_text_for_tts(text)
            
            if self.mode == 'full':
                return self._generate_full_tts(text)
            elif self.mode == 'simple':
                return self._generate_simple_tts(text)
            else:
                return None
                
        except Exception as e:
            print(f"❌ TTS generation failed: {e}")
            return None
    
    def _generate_full_tts(self, text: str) -> Optional[str]:
        """Generate TTS using full Hugging Face models"""
        try:
            # Process text
            inputs = self.processor(text=text, return_tensors="pt")
            
            # Generate speech
            with torch.no_grad():
                speech = self.model.generate_speech(
                    inputs["input_ids"], 
                    self.speaker_embeddings, 
                    vocoder=self.vocoder
                )
            
            # Convert to audio file in memory
            audio_buffer = io.BytesIO()
            sf.write(audio_buffer, speech.numpy(), samplerate=16000, format='WAV')
            audio_buffer.seek(0)
            
            # Encode to base64
            audio_base64 = base64.b64encode(audio_buffer.read()).decode()
            return audio_base64
            
        except Exception as e:
            print(f"❌ Full TTS generation failed: {e}")
            return None
    
    def _generate_simple_tts(self, text: str) -> Optional[str]:
        """Generate TTS using simple fallback methods"""
        try:
            # Try system TTS first
            if self.simple_tts.text_to_speech_system(text):
                # Return a simple audio placeholder for UI consistency
                return self.simple_tts.create_audio_placeholder(text)
            else:
                # Return web speech JavaScript
                return self.simple_tts.text_to_speech_web(text)
                
        except Exception as e:
            print(f"❌ Simple TTS generation failed: {e}")
            return None
    
    def _clean_text_for_tts(self, text: str) -> str:
        """Clean text for better TTS output"""
        import re
        
        # Remove markdown formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # Italic
        text = re.sub(r'`(.*?)`', r'\1', text)        # Code
        
        # Remove emojis and special characters
        text = re.sub(r'[😀-🙏🌀-🗿🚀-🛿🇀-🇿]', '', text)  # Emojis
        text = re.sub(r'[•◦▪▫◾◽]', '', text)          # Bullets
        text = re.sub(r'[📊📈📉📋📌📍📎📏📐📑📒📓📔📕📖📗📘📙📚📛📜📝📞📟📠📡📢📣📤📥📦📧📨📩📪📫📬📭📮📯📰📱📲📳📴📵📶📷📸📹📺📻📼📽📾📿🔀-🔿]', '', text)  # Various symbols
        
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove URLs
        text = re.sub(r'http[s]?://\S+', '', text)
        
        # Clean up common IT terms for better pronunciation
        replacements = {
            'IT': 'I T',
            'FAQ': 'frequently asked questions',
            'VPN': 'V P N',
            'DNS': 'D N S',
            'CPU': 'C P U',
            'RAM': 'R A M',
            'USB': 'U S B',
            'WiFi': 'Wi-Fi',
            'API': 'A P I',
            'URL': 'U R L',
            'HTTP': 'H T T P',
            'HTTPS': 'H T T P S',
            'SSL': 'S S L',
            'TLS': 'T L S'
        }
        
        for term, replacement in replacements.items():
            text = text.replace(term, replacement)
        
        return text.strip()
    
    def stop_speech(self) -> bool:
        """Stop current TTS playback"""
        try:
            if self.mode == 'simple' and self.simple_tts:
                # Stop system speech
                success = self.simple_tts.stop_system_speech()
                # Also stop web speech
                stop_js = self.simple_tts.stop_web_speech()
                # Return the JavaScript to execute
                return stop_js if stop_js else success
            elif self.mode == 'full':
                # For future implementation with PyTorch models
                # Could implement interruption of model generation
                return True
            return False
        except Exception as e:
            print(f"❌ Stop speech failed: {e}")
            return False

# Initialize TTS manager
@st.cache_resource
def get_tts_manager():
    """Initialize and cache TTS manager"""
    return TTSManager()

# Initialize enhanced bot
@st.cache_resource
def get_enhanced_bot():
    """Initialize and cache the enhanced helpdesk bot with ChromaDB preloaded"""
    try:
        # Initialize bot
        bot = EnhancedITHelpdeskBot()
        
        # Force ChromaDB initialization and knowledge base loading
        if hasattr(bot, 'chroma_kb') and bot.chroma_kb:
            # Get initial status to trigger any lazy loading
            status = bot.chroma_kb.get_status()
            
            # If ChromaDB is empty, reload from knowledge base files
            if status.get('collection_size', 0) == 0:
                kb_dir = os.path.join("data", "kb")
                if os.path.exists(kb_dir):
                    reload_result = bot.chroma_kb.reload_from_directory(kb_dir)
                    if reload_result.get('success'):
                        print(f"✅ ChromaDB initialized with {reload_result.get('total_items', 0)} items")
                    else:
                        print(f"⚠️ ChromaDB reload warning: {reload_result.get('error', 'Unknown issue')}")
            else:
                print(f"✅ ChromaDB already loaded with {status.get('collection_size', 0)} items")
        
        # Also ensure legacy knowledge base is loaded
        if hasattr(bot, 'knowledge_base') and not bot.knowledge_base:
            bot.reload_knowledge_base()
        
        return bot
        
    except Exception as e:
        print(f"❌ Error initializing bot: {e}")
        # Return basic bot even if ChromaDB fails
        return EnhancedITHelpdeskBot()

# Language configuration
LANGUAGES = {
    "en": {"name": "English", "flag": "🇺🇸"},
    "es": {"name": "Español", "flag": "🇪🇸"},
    "fr": {"name": "Français", "flag": "🇫🇷"},
    "de": {"name": "Deutsch", "flag": "🇩🇪"},
    "pt": {"name": "Português", "flag": "🇵🇹"},
    "zh": {"name": "中文", "flag": "🇨🇳"},
    "ja": {"name": "日本語", "flag": "🇯🇵"}
}

# Multi-language UI text
UI_TEXT = {
    "en": {
        "title": "🤖 Enterprise IT Helpdesk Assistant",
        "user_management": "👤 User Management",
        "username": "Username",
        "select_user": "Select your username",
        "language": "Language",
        "role_info": "Role Information",
        "chat_interface": "💬 Chat Interface",
        "type_message": "Type your message here...",
        "clear_chat": "🗑️ Clear Chat",
        "statistics": "📊 Statistics Dashboard",
        "admin_panel": "⚙️ Admin Panel",
        "system_info": "ℹ️ System Information"
    },
    "es": {
        "title": "🤖 Asistente IT Empresarial",
        "user_management": "👤 Gestión de Usuarios",
        "username": "Nombre de Usuario",
        "select_user": "Selecciona tu nombre de usuario",
        "language": "Idioma",
        "role_info": "Información de Rol",
        "chat_interface": "💬 Interfaz de Chat",
        "type_message": "Escribe tu mensaje aquí...",
        "clear_chat": "🗑️ Limpiar Chat",
        "statistics": "📊 Panel de Estadísticas",
        "admin_panel": "⚙️ Panel de Administrador",
        "system_info": "ℹ️ Información del Sistema"
    },
    "fr": {
        "title": "🤖 Assistant IT d'Entreprise",
        "user_management": "👤 Gestion des Utilisateurs",
        "username": "Nom d'Utilisateur",
        "select_user": "Sélectionnez votre nom d'utilisateur",
        "language": "Langue",
        "role_info": "Informations de Rôle",
        "chat_interface": "💬 Interface de Chat",
        "type_message": "Tapez votre message ici...",
        "clear_chat": "🗑️ Effacer le Chat",
        "statistics": "📊 Tableau de Bord des Statistiques",
        "admin_panel": "⚙️ Panneau d'Administration",
        "system_info": "ℹ️ Informations Système"
    }
}

def get_ui_text(key: str, language: str) -> str:
    """Get localized UI text"""
    return UI_TEXT.get(language, UI_TEXT["en"]).get(key, key)

def format_markdown_to_html(text: str) -> str:
    """Convert basic markdown formatting to HTML for chat bubbles"""
    import re
    
    # Escape any existing HTML to prevent XSS
    import html
    text = html.escape(text)
    
    # Convert **bold** to <strong>
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    
    # Convert bullet points • to properly spaced bullets
    text = re.sub(r'^• ', '• ', text, flags=re.MULTILINE)
    
    # Convert line breaks to <br> for proper display
    text = text.replace('\n', '<br>')
    
    return text

def stop_current_tts():
    """Stop any currently playing TTS"""
    try:
        if st.session_state.get('tts_manager'):
            tts_manager = st.session_state.tts_manager
            result = tts_manager.stop_speech()
            
            if isinstance(result, str) and result.startswith('<script>'):
                # Execute JavaScript to stop web speech
                st.markdown(result, unsafe_allow_html=True)
                st.session_state.tts_current_playing = None
                st.session_state.tts_stop_requested = True
                st.success("🔇 Voice stopped")
                return True
            elif result:
                # System TTS stopped
                st.session_state.tts_current_playing = None
                st.session_state.tts_stop_requested = True
                st.success("🔇 Voice stopped")
                return True
        return False
    except Exception as e:
        st.error(f"Failed to stop voice: {str(e)}")
        return False

def generate_and_play_tts(text, session_key):
    """Generate TTS audio and store in session state for playback"""
    if not (TTS_AVAILABLE or SIMPLE_TTS_AVAILABLE):
        st.error("TTS libraries not available")
        return
    
    # Check if stop was requested
    if st.session_state.get('tts_stop_requested', False):
        st.session_state.tts_stop_requested = False
        return
    
    try:
        if not st.session_state.tts_manager_initialized:
            with st.spinner("Initializing TTS model..."):
                tts_manager = TTSManager()
                if tts_manager.is_initialized:
                    st.session_state.tts_manager = tts_manager
                    st.session_state.tts_manager_initialized = True
                    st.session_state.tts_mode = tts_manager.mode
                else:
                    st.error("Failed to initialize TTS model")
                    return
        
        # Set current playing state
        st.session_state.tts_current_playing = session_key
        
        # Generate audio
        tts_manager = st.session_state.get('tts_manager')
        if tts_manager:
            with st.spinner("Generating speech..."):
                audio_result = tts_manager.text_to_speech(text)
                if audio_result and not st.session_state.get('tts_stop_requested', False):
                    tts_mode = st.session_state.get('tts_mode', 'unknown')
                    
                    if tts_mode == 'full':
                        # Base64 audio data - use HTML audio player
                        st.session_state[session_key] = audio_result
                        audio_html = f"""
                        <audio autoplay>
                            <source src="data:audio/wav;base64,{audio_result}" type="audio/wav">
                        </audio>
                        """
                        st.markdown(audio_html, unsafe_allow_html=True)
                        st.success("🔊 Audio generated and playing!")
                        
                    elif tts_mode == 'simple':
                        if audio_result.startswith('<script>'):
                            # Web Speech API JavaScript
                            st.markdown(audio_result, unsafe_allow_html=True)
                            st.success("🔊 Using browser speech synthesis!")
                        else:
                            # Simple audio placeholder
                            st.session_state[session_key] = audio_result
                            st.success("🔊 System TTS activated!")
                    
                else:
                    st.error("Failed to generate audio")
        else:
            st.error("TTS manager not initialized")
            
    except Exception as e:
        st.error(f"TTS generation failed: {str(e)}")
    finally:
        # Clear playing state
        st.session_state.tts_current_playing = None

# Initialize session state
def initialize_session_state():
    """Initialize all session state variables for enhanced functionality"""
    defaults = {
        'messages': [],
        'bot_instance': None,
        'current_username': '',
        'current_language': 'en',
        'user_role': 'staff',
        'user_department': 'Unknown',
        'session_id': f"session_{int(time.time())}",
        'processing_message': False,
        'pending_user_message': None,
        'conversation_count': 0,
        'last_activity': datetime.now(),
        'admin_mode': False,
        'show_statistics': False,
        'is_logged_in': False,
        'login_error': '',
        'pending_ticket_creation': False,
        'ticket_form_data': {},
        # Thread management
        'current_thread_id': None,
        'show_thread_history': False,
        'selected_thread_id': None,
        'thread_list': [],
        # TTS settings
        'tts_enabled': False,
        'tts_auto_play': False,
        'tts_manager_initialized': False,
        'tts_mode': 'none',
        'tts_current_playing': None,
        'tts_stop_requested': False
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

def render_login_screen():
    """Render login screen for user authentication"""
    st.markdown("# 🔐 IT Helpdesk Login")
    st.markdown("### Please enter your credentials to access the system")
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("---")
        
        # Login form
        with st.form("login_form"):
            st.markdown("#### Enter your username")
            username = st.text_input(
                "Username:",
                placeholder="Enter your username (e.g., john.doe)",
                label_visibility="collapsed"
            )
            
            # Show available users for demo purposes
            with st.expander("📋 Demo Users Available"):
                users = load_available_users()
                for user in users[:4]:  # Show first 4 users
                    role_badge = {
                        'staff': '👤', 'manager': '👨‍💼', 
                        'bod': '👔', 'admin': '⚙️'
                    }.get(user['role'], '👤')
                    st.markdown(f"**{user['username']}** {role_badge} {user['role'].title()} - {user['department']}")
            
            submitted = st.form_submit_button("🚀 Login", use_container_width=True, type="primary")
            
            if submitted:
                if username.strip():
                    # Validate user
                    users = load_available_users()
                    found_user = next((user for user in users if user["username"].lower() == username.lower()), None)
                    
                    if found_user:
                        # Auto-detect user's preferred language from their profile or default to English
                        user_lang = found_user.get("preferred_language", "en")
                        
                        # Set session state
                        st.session_state.current_username = found_user["username"]
                        st.session_state.user_role = found_user["role"]
                        st.session_state.user_department = found_user["department"]
                        st.session_state.current_language = user_lang
                        st.session_state.is_logged_in = True
                        st.session_state.login_error = ""
                        
                        # Reset conversation state for new login
                        st.session_state.messages = []
                        st.session_state.bot_instance = None
                        st.session_state.session_id = f"session_{int(time.time())}"
                        st.session_state.current_thread_id = None
                        st.session_state.show_thread_history = False
                        st.session_state.thread_list = []
                        
                        st.success(f"✅ Welcome back, {found_user['username']}!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.session_state.login_error = "❌ Username not found. Please check your username."
                        st.error(st.session_state.login_error)
                else:
                    st.session_state.login_error = "⚠️ Please enter a username."
                    st.error(st.session_state.login_error)
        
        st.markdown("---")
        st.markdown("💡 **Demo System** - Use any of the usernames shown above to explore different role capabilities.")


def render_ticket_creation_form():
    """Render enhanced ticket creation form"""
    st.markdown("## 🎫 Create New Support Ticket")
    st.markdown("Please provide details about your issue:")
    
    with st.form("ticket_creation_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input(
                "Issue Title*",
                placeholder="Brief description of the problem",
                help="Provide a short, clear title for your issue"
            )
            
            priority = st.selectbox(
                "Priority Level*",
                ["low", "medium", "high", "critical"],
                index=1,
                help="Select the urgency level of your issue"
            )
        
        with col2:
            category = st.selectbox(
                "Category*",
                ["hardware", "software", "network", "email", "account", "general"],
                help="Select the category that best describes your issue"
            )
            
            department = st.text_input(
                "Department",
                value=st.session_state.user_department,
                disabled=True
            )
        
        description = st.text_area(
            "Detailed Description*",
            placeholder="Please describe your issue in detail. Include any error messages, steps you've tried, and when the problem started.",
            height=120,
            help="The more details you provide, the faster we can resolve your issue"
        )
        
        # Additional options
        with st.expander("🔧 Additional Options"):
            contact_method = st.selectbox(
                "Preferred Contact Method",
                ["Email", "Phone", "In-person", "Chat"]
            )
            
            urgent_contact = st.checkbox(
                "This is blocking my work - please contact me immediately",
                help="Check this if the issue is preventing you from working"
            )
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            submitted = st.form_submit_button("🚀 Create Ticket", type="primary", use_container_width=True)
        
        with col2:
            if st.form_submit_button("📝 Save Draft", use_container_width=True):
                st.session_state.ticket_form_data = {
                    'title': title, 'description': description, 'priority': priority,
                    'category': category, 'contact_method': contact_method, 'urgent_contact': urgent_contact
                }
                st.success("💾 Draft saved!")
        
        with col3:
            if st.form_submit_button("❌ Cancel", use_container_width=True):
                st.session_state.pending_ticket_creation = False
                st.rerun()
        
        if submitted:
            if title.strip() and description.strip():
                # Create the ticket using the bot's function system
                try:
                    if not st.session_state.bot_instance:
                        st.session_state.bot_instance = get_enhanced_bot()
                    
                    # Call the create_ticket function
                    from functions.helpdesk_functions import route_helpdesk_function
                    
                    result = route_helpdesk_function(
                        function_name="create_ticket",
                        username=st.session_state.current_username,
                        language=st.session_state.current_language,
                        title=title,
                        description=description,
                        priority=priority,
                        category=category
                    )
                    
                    # Add to conversation history
                    current_time = datetime.now()
                    st.session_state.messages.append({
                        "role": "user",
                        "content": f"Create ticket: {title}",
                        "timestamp": current_time.strftime("%H:%M"),
                        "language": st.session_state.current_language,
                        "session_id": st.session_state.session_id
                    })
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": result,
                        "timestamp": current_time.strftime("%H:%M"),
                        "language": st.session_state.current_language,
                        "session_id": st.session_state.session_id
                    })
                    
                    st.success("✅ Ticket created successfully!")
                    st.session_state.pending_ticket_creation = False
                    time.sleep(2)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error creating ticket: {str(e)}")
            else:
                st.error("⚠️ Please fill in all required fields (marked with *)")


def load_available_users() -> List[Dict[str, Any]]:
    """Load available users from mock data"""
    try:
        data = load_mock_data()
        return data.get("users", [])
    except Exception as e:
        st.error(f"Error loading users: {e}")
        return []

# Thread Management Functions
def switch_to_thread(thread_id: str):
    """Switch to a specific conversation thread"""
    if not st.session_state.bot_instance:
        st.session_state.bot_instance = get_enhanced_bot()
    
    # Switch to the thread
    thread = st.session_state.bot_instance.switch_to_thread(st.session_state.current_username, thread_id)
    
    if thread:
        st.session_state.current_thread_id = thread_id
        st.session_state.show_thread_history = False
        
        # Load messages from thread into UI
        st.session_state.messages = []
        for msg in thread.messages:
            st.session_state.messages.append({
                "role": msg["role"],
                "content": msg["content"], 
                "timestamp": datetime.fromisoformat(msg["timestamp"]).strftime("%H:%M"),
                "language": msg.get("language", "en"),
                "thread_id": thread_id
            })
        
        st.success(f"Switched to conversation: {thread.title}")
    else:
        st.error("Could not load conversation thread")

def start_new_thread(title: str = None):
    """Start a new conversation thread"""
    if not st.session_state.bot_instance:
        st.session_state.bot_instance = get_enhanced_bot()
    
    # Create new thread
    new_thread = st.session_state.bot_instance.create_new_thread(st.session_state.current_username, title)
    st.session_state.current_thread_id = new_thread.thread_id
    
    # Clear current messages
    st.session_state.messages = []
    st.session_state.session_id = new_thread.thread_id
    
    # Update thread list
    st.session_state.thread_list = st.session_state.bot_instance.get_user_thread_list(st.session_state.current_username)

def handle_user_input(user_input: str):
    """Handle user input with progressive UI updates, conversation context, and auto language detection"""
    if not user_input.strip():
        return
    
    current_time = datetime.now()
    
    # Auto-detect language from user input
    detected_language = st.session_state.current_language  # Default to current
    try:
        from functions.helpdesk_functions import detect_user_language
        detected_language = detect_user_language(user_input)
        
        # Update user's language preference if different language detected
        if detected_language != st.session_state.current_language:
            st.session_state.current_language = detected_language
            st.success(f"🌍 Language auto-detected: {LANGUAGES.get(detected_language, {}).get('name', detected_language)}")
    except Exception as e:
        # Fallback to current language if detection fails
        pass
    
    # Add user message immediately with conversation metadata
    st.session_state.messages.append({
        "role": "user", 
        "content": user_input,
        "timestamp": current_time.strftime("%H:%M"),
        "language": detected_language,
        "session_id": st.session_state.session_id,
        "conversation_turn": len(st.session_state.messages) + 1
    })
    
    # Set processing state
    st.session_state.processing_message = True
    st.session_state.pending_user_message = user_input
    
    # Update activity timestamp and conversation tracking
    st.session_state.last_activity = current_time
    st.session_state.conversation_count += 1
    
    # Ensure bot instance maintains session context
    if st.session_state.bot_instance:
        # The bot will handle conversation history automatically through session_id
        pass

def process_bot_response():
    """Process bot response with enhanced conversation context"""
    if not st.session_state.processing_message or not st.session_state.pending_user_message:
        return
    
    try:
        # Get bot instance
        if not st.session_state.bot_instance:
            st.session_state.bot_instance = get_enhanced_bot()
        
        # Ensure conversation continuity by maintaining session context
        session_id = st.session_state.session_id
        
        # Get response from enhanced bot with thread management
        response, thread_id = st.session_state.bot_instance.get_response(
            st.session_state.pending_user_message,
            st.session_state.current_username,
            st.session_state.current_thread_id
        )
        # Update current thread ID
        st.session_state.current_thread_id = thread_id
        
        # Handle response format
        response_content = response if isinstance(response, str) else response
        
        # Add bot response with conversation metadata
        current_time = datetime.now()
        timestamp_str = current_time.strftime("%H:%M")
        
        st.session_state.messages.append({
            "role": "assistant",
            "content": response_content,
            "timestamp": timestamp_str,
            "language": st.session_state.current_language,
            "thread_id": st.session_state.current_thread_id,
            "conversation_turn": len(st.session_state.messages) + 1
        })
        
        # Auto-play TTS if enabled
        if st.session_state.tts_enabled and st.session_state.tts_auto_play and (TTS_AVAILABLE or SIMPLE_TTS_AVAILABLE):
            try:
                # Use the current message count as index for consistency
                msg_index = len(st.session_state.messages) - 1
                generate_and_play_tts(response_content, f"tts_audio_{msg_index}_{timestamp_str}")
            except Exception as tts_e:
                # Silently fail TTS to not interrupt chat flow
                pass
        
        # Update conversation tracking
        st.session_state.last_activity = current_time
        
    except Exception as e:
        error_msg = get_localized_text("error", st.session_state.current_language)
        
        st.session_state.messages.append({
            "role": "assistant", 
            "content": f"{error_msg}: {str(e)}",
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "language": st.session_state.current_language
        })
    
    finally:
        # Reset processing state
        st.session_state.processing_message = False
        st.session_state.pending_user_message = None

def render_enhanced_sidebar():
    """Render simplified sidebar focused on essentials with login/logout"""
    with st.sidebar:
        # Simple header with logout
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("# 🤖 IT Assistant")
        with col2:
            if st.button("🚪", help="Logout", use_container_width=True):
                # Clear all session state for logout
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                initialize_session_state()
                st.rerun()
        
        st.divider()
        
        # User info
        role_name = get_localized_text(f"role_{st.session_state.user_role}", st.session_state.current_language)
        
        st.info(f"**{st.session_state.current_username}**\n{role_name} • {st.session_state.user_department}")
        
        # Current language display with auto-detection info
        lang_info = LANGUAGES.get(st.session_state.current_language, {})
        st.markdown(f"**Language:** {lang_info.get('flag', '🌍')} {lang_info.get('name', 'English')}")
        st.caption("💡 Language auto-detected from your messages")
        
        st.divider()
        
        # Navigation
        st.markdown("### 🧭 Features")
        
        if st.button("💬 Chat", use_container_width=True, 
                    type="primary" if not st.session_state.show_statistics and not st.session_state.admin_mode and not st.session_state.pending_ticket_creation else "secondary"):
            st.session_state.show_statistics = False
            st.session_state.admin_mode = False
            st.session_state.pending_ticket_creation = False
            st.rerun()
        
        if st.session_state.user_role in ['manager', 'bod', 'admin']:
            if st.button("📊 Statistics", use_container_width=True, 
                        type="primary" if st.session_state.show_statistics else "secondary"):
                st.session_state.show_statistics = True
                st.session_state.admin_mode = False
                st.session_state.pending_ticket_creation = False
                st.rerun()
        
        if st.session_state.user_role == 'admin':
            if st.button("⚙️ Admin", use_container_width=True, 
                        type="primary" if st.session_state.admin_mode else "secondary"):
                st.session_state.admin_mode = True
                st.session_state.show_statistics = False
                st.session_state.pending_ticket_creation = False
                st.rerun()
        
        st.divider()
        
        # Enhanced Quick actions with proper ticket creation
        st.markdown("### ⚡ Quick Actions")
        
        # New Ticket - opens form instead of auto-message
        if st.button("🎫 New Ticket", use_container_width=True, type="primary"):
            st.session_state.pending_ticket_creation = True
            st.session_state.show_statistics = False
            st.session_state.admin_mode = False
            st.rerun()
        
        # Other quick actions that send messages
        other_actions = [
            ("🔍 My Tickets", "Show me all my tickets"),
            ("🔐 Password Help", "I need help with password reset or account access"),
            ("📞 Contact IT", "Show me IT contact information and support hours"),
            ("📊 System Status", "Show me current system status and any ongoing issues")
        ]
        
        for label, message in other_actions:
            if st.button(label, use_container_width=True):
                handle_user_input(message)
                st.rerun()
        
        st.divider()
        
        # TTS Controls
        st.markdown("### 🔊 Voice Settings")
        
        # Show TTS availability status
        if TTS_AVAILABLE:
            st.success("✅ Full AI Voice Available")
        elif SIMPLE_TTS_AVAILABLE:
            st.info("📢 Basic System Voice Available")
        else:
            st.error("❌ No Voice Features Available")
        
        # Show current TTS mode if initialized
        if st.session_state.tts_manager_initialized:
            tts_mode = st.session_state.get('tts_mode', 'unknown')
            if tts_mode == 'full':
                st.success("🤖 Using AI Voice Models")
            elif tts_mode == 'simple':
                st.info("💬 Using System Voice")
        
        if TTS_AVAILABLE or SIMPLE_TTS_AVAILABLE:
            # TTS toggle
            tts_enabled = st.checkbox(
                "🔊 Enable Voice Reading", 
                value=st.session_state.tts_enabled,
                help="Enable text-to-speech for bot responses"
            )
            
            if tts_enabled != st.session_state.tts_enabled:
                st.session_state.tts_enabled = tts_enabled
                if tts_enabled and not st.session_state.tts_manager_initialized:
                    with st.spinner("Initializing voice models..."):
                        tts_manager = TTSManager()
                        if tts_manager.is_initialized:
                            st.session_state.tts_manager = tts_manager
                            st.session_state.tts_manager_initialized = True
                            st.session_state.tts_mode = tts_manager.mode
                    st.success("🔊 Voice ready!")
                st.rerun()
            
            if st.session_state.tts_enabled:
                # Auto-play toggle
                st.session_state.tts_auto_play = st.checkbox(
                    "🔄 Auto-play responses",
                    value=st.session_state.tts_auto_play,
                    help="Automatically read new bot responses aloud"
                )
                
                # Stop voice button
                st.markdown("---")
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("🔇 Stop Voice", help="Stop current voice playback"):
                        stop_current_tts()
                        st.rerun()
                
                with col2:
                    # Show current status
                    if st.session_state.get('tts_current_playing'):
                        st.success("🎵 Playing")
                    else:
                        st.info("🔇 Silent")
                        
        else:
            st.info("🔊 Voice feature requires additional packages")
            if st.button("📥 Install TTS Dependencies", help="Install transformers, torch, soundfile, datasets"):
                st.code("pip install transformers torch soundfile datasets")
                st.info("Or try: python install_tts.py")
        
        st.divider()
        
        # Thread Management Section
        st.markdown("### 💬 Conversations")
        
        # Thread History Button
        if st.button("📂 Conversation History", use_container_width=True, 
                    type="primary" if st.session_state.show_thread_history else "secondary"):
            st.session_state.show_thread_history = not st.session_state.show_thread_history
            if st.session_state.show_thread_history and st.session_state.bot_instance:
                # Load user's threads
                st.session_state.thread_list = st.session_state.bot_instance.get_user_thread_list(st.session_state.current_username)
            st.rerun()
        
        # Show thread list if enabled
        if st.session_state.show_thread_history and st.session_state.thread_list:
            st.markdown("**Recent Conversations:**")
            
            for i, thread_info in enumerate(st.session_state.thread_list[:5]):  # Show last 5 threads
                thread_id = thread_info['thread_id']
                is_current = thread_id == st.session_state.current_thread_id
                
                # Thread button with info
                thread_label = f"{'🟢' if is_current else '💬'} {thread_info['title'][:25]}..."
                thread_subtitle = f"{thread_info['message_count']} msgs • {thread_info['last_updated'][:10]}"
                
                col1, col2 = st.columns([4, 1])
                with col1:
                    if st.button(f"{thread_label}\n{thread_subtitle}", 
                               key=f"thread_{i}", 
                               use_container_width=True,
                               type="primary" if is_current else "secondary"):
                        # Switch to this thread
                        switch_to_thread(thread_id)
                        st.rerun()
                with col2:
                    if st.button("🗑️", key=f"delete_thread_{i}", help="Archive thread"):
                        # Archive this thread  
                        if st.session_state.bot_instance:
                            st.session_state.bot_instance.clear_conversation(st.session_state.current_username, thread_id)
                            st.session_state.thread_list = st.session_state.bot_instance.get_user_thread_list(st.session_state.current_username)
                        st.rerun()
        
        # Current thread info
        if st.session_state.current_thread_id:
            st.caption(f"📌 Active: Thread {st.session_state.current_thread_id[:8]}...")
        
        st.divider()
        
        # New session
        if st.button("🔄 New Chat", use_container_width=True):
            # Start a new conversation thread
            start_new_thread("New Conversation")
            st.success("Started new conversation thread!")
            st.rerun()
            st.session_state.user_department = user_dept
            st.session_state.current_language = lang
            st.session_state.is_logged_in = True
            
            st.rerun()

def render_statistics_dashboard():
    """Render statistics dashboard for authorized users"""
    if not (st.session_state.user_role in ["bod", "admin"] and st.session_state.show_statistics):
        return
    
    st.markdown(f"## 📊 {get_ui_text('statistics', st.session_state.current_language)}")
    
    if st.button("← Back to Chat"):
        st.session_state.show_statistics = False
        st.rerun()
    
    try:
        # Get raw statistics data
        from functions.helpdesk_functions import load_mock_data
        
        # Load data directly to create formatted display
        data = load_mock_data()
        tickets = data.get("tickets", [])
        stats = data.get("statistics", {})
        
        # Calculate real-time statistics
        current_stats = {
            "total": len(tickets),
            "open": len([t for t in tickets if t["status"] == "open"]),
            "in_progress": len([t for t in tickets if t["status"] == "in_progress"]),
            "resolved": len([t for t in tickets if t["status"] == "resolved"]),
            "closed": len([t for t in tickets if t["status"] == "closed"])
        }
        
        # Priority breakdown
        priority_stats = {}
        for ticket in tickets:
            priority = ticket.get("priority", "medium")
            priority_stats[priority] = priority_stats.get(priority, 0) + 1
        
        # Department breakdown
        dept_stats = {}
        for ticket in tickets:
            dept = ticket.get("department", "Unknown")
            dept_stats[dept] = dept_stats.get(dept, 0) + 1
        
        # Display with proper Streamlit formatting
        st.markdown("### 🎫 Ticket Overview")
        
        # Ticket overview metrics
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("📊 Total", current_stats['total'])
        with col2:
            st.metric("🆕 Open", current_stats['open'])
        with col3:
            st.metric("⏳ In Progress", current_stats['in_progress'])
        with col4:
            st.metric("✅ Resolved", current_stats['resolved'])
        with col5:
            st.metric("✅ Closed", current_stats['closed'])
        
        st.markdown("---")
        
        # Priority breakdown
        st.markdown("### 🔴 Priority Breakdown")
        priority_cols = st.columns(4)
        priority_emojis = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
        
        for i, (priority, count) in enumerate(sorted(priority_stats.items(), key=lambda x: ["critical", "high", "medium", "low"].index(x[0]) if x[0] in ["critical", "high", "medium", "low"] else 999)):
            with priority_cols[i % 4]:
                emoji = priority_emojis.get(priority, "⚪")
                st.metric(f"{emoji} {priority.title()}", count)
        
        st.markdown("---")
        
        # Department breakdown
        st.markdown("### 🏢 Department Breakdown")
        dept_df_data = []
        for dept, count in sorted(dept_stats.items(), key=lambda x: x[1], reverse=True):
            dept_df_data.append({"Department": dept, "Tickets": count})
        
        if dept_df_data:
            import pandas as pd
            df = pd.DataFrame(dept_df_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # Performance metrics
        st.markdown("### 📈 Performance Metrics")
        avg_resolution = stats.get("average_resolution_time_hours", 22.3)
        satisfaction = stats.get("satisfaction_score", 4.3)
        sla_compliance = stats.get("sla_compliance", 0.87)
        
        perf_col1, perf_col2, perf_col3 = st.columns(3)
        with perf_col1:
            st.metric("⏱️ Avg Resolution Time", f"{avg_resolution:.1f} hours")
        with perf_col2:
            st.metric("😊 Satisfaction Score", f"{satisfaction:.1f}/5.0")
        with perf_col3:
            st.metric("📋 SLA Compliance", f"{sla_compliance*100:.1f}%")
        
        # Report timestamp
        from datetime import datetime
        st.caption(f"📅 Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
    except Exception as e:
        st.error(f"Error loading statistics: {e}")

def render_admin_panel():
    """Render admin panel for system administrators with ChromaDB management"""
    if not (st.session_state.user_role == "admin" and st.session_state.admin_mode):
        return
    
    st.markdown(f"## {get_ui_text('admin_panel', st.session_state.current_language)}")
    
    # Handle session state flags to show success messages without DataCloneError
    if st.session_state.get('kb_upload_success', False):
        st.success("🎉 Knowledge base upload completed successfully!")
        st.session_state.kb_upload_success = False
    
    if st.session_state.get('kb_reload_success', False):
        st.success("🔄 Knowledge base reloaded successfully!")
        st.session_state.kb_reload_success = False
    
    if st.button("← Back to Chat"):
        st.session_state.admin_mode = False
        st.rerun()
    
    # Knowledge Base Management Section
    st.markdown("### 📚 Knowledge Base Management")
    
    # Show current knowledge base info
    bot = get_enhanced_bot()
    kb_info = bot.get_knowledge_base_info()
    
    # Display Legacy KB Info
    st.markdown("#### 📁 Legacy Knowledge Base")
    legacy_kb = kb_info.get("legacy_kb", {})
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📁 KB Files", legacy_kb.get("total_files", 0))
    with col2:
        st.metric("❓ FAQs", legacy_kb.get("total_faqs", 0))
    with col3:
        st.metric("🔧 Guides", legacy_kb.get("total_troubleshooting_guides", 0))
    with col4:
        st.metric("⚡ Quick Solutions", legacy_kb.get("total_quick_solutions", 0))
    
    st.info(f"**Version:** {legacy_kb.get('version', 'unknown')} | **Last Updated:** {legacy_kb.get('last_updated', 'unknown')}")
    
    # Display ChromaDB Status
    st.markdown("#### 🧠 ChromaDB Vector Database")
    chroma_db = kb_info.get("chroma_db", {})
    
    if chroma_db.get("available", False):
        # Status indicator with color coding
        status = chroma_db.get("status", "unknown")
        collection_size = chroma_db.get("collection_size", 0)
        
        if status == "ready" and collection_size > 0:
            st.success(f"🟢 **ChromaDB Status: READY** - {collection_size} items loaded")
        elif status == "ready" and collection_size == 0:
            st.warning(f"🟡 **ChromaDB Status: EMPTY** - Database ready but no content loaded")
        else:
            st.error(f"🔴 **ChromaDB Status: {status.upper()}**")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 Vector Items", collection_size)
        with col2:
            embedding_type = chroma_db.get("embedding_type", "unknown")
            embedding_icon = "🤖" if "OpenAI" in embedding_type or "Azure" in embedding_type else "🧠"
            st.metric(f"{embedding_icon} Embeddings", embedding_type)
        with col3:
            categories = chroma_db.get("categories", [])
            st.metric("📂 Categories", len(categories))
        with col4:
            persist_dir = chroma_db.get("persist_directory", "unknown")
            dir_name = os.path.basename(persist_dir) if persist_dir != "unknown" else "unknown"
            st.metric("💾 Storage", dir_name)
        
        # Auto-reload ChromaDB if empty
        if collection_size == 0:
            st.info("💡 **ChromaDB is empty.** Would you like to load the knowledge base now?")
            if st.button("🔄 Auto-Load Knowledge Base", key="auto_load_kb", type="primary"):
                try:
                    kb_dir = os.path.join("data", "kb")
                    if hasattr(bot, 'chroma_kb') and bot.chroma_kb:
                        with st.spinner("Loading knowledge base into ChromaDB..."):
                            result = bot.chroma_kb.reload_from_directory(kb_dir)
                            if result["success"]:
                                st.success(f"✅ ChromaDB loaded: {result['total_items']} items from {result['files_loaded']} files")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"❌ ChromaDB loading failed: {result.get('error', 'Unknown error')}")
                    else:
                        st.error("❌ ChromaDB not available")
                except Exception as e:
                    st.error(f"❌ Error loading ChromaDB: {e}")
        
        # Show embedding configuration details
        if chroma_db.get("use_openai_embeddings"):
            provider = "Azure OpenAI" if chroma_db.get("use_azure_openai") else "OpenAI API"
            model_name = chroma_db.get("model_name", "unknown")
            st.success(f"🚀 **Using {provider} Embeddings:** {model_name}")
        elif chroma_db.get("azure_openai_configured"):
            st.info("💡 **Azure OpenAI configured** but no embedding deployment set. Add AZURE_OPENAI_EMBEDDING_DEPLOYMENT to use Azure OpenAI embeddings.")
        elif chroma_db.get("openai_configured"):
            st.info("💡 **OpenAI API configured.** OpenAI embeddings available as alternative.")
        else:
            st.info("� **Using ChromaDB default embeddings** (fast and reliable). Add OpenAI API key for cloud embeddings.")
        
        # Show categories if available
        if categories:
            st.info(f"**Categories:** {', '.join(categories)}")
        
        # ChromaDB detailed stats
        with st.expander("🔍 ChromaDB Detailed Statistics"):
            stats = chroma_db.get("stats", {})
            if stats:
                st.json(stats)
            else:
                # Show embedding configuration details
                config_info = {
                    "embedding_provider": chroma_db.get("embedding_provider", "unknown"),
                    "embedding_type": chroma_db.get("embedding_type", "unknown"),
                    "model_name": chroma_db.get("model_name", "unknown"),
                    "use_openai_embeddings": chroma_db.get("use_openai_embeddings", False),
                    "use_azure_openai": chroma_db.get("use_azure_openai", False),
                    "azure_openai_configured": chroma_db.get("azure_openai_configured", False),
                    "openai_configured": chroma_db.get("openai_configured", False)
                }
                st.json(config_info)
        
        # ChromaDB Management Actions
        st.markdown("#### 🔧 ChromaDB Management")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Reload ChromaDB", key="reload_chroma_btn", help="Reload ChromaDB from knowledge base files"):
                try:
                    kb_dir = os.path.join("data", "kb")
                    if hasattr(bot, 'chroma_kb') and bot.chroma_kb:
                        result = bot.chroma_kb.reload_from_directory(kb_dir)
                        if result["success"]:
                            st.success(f"✅ ChromaDB reloaded: {result['total_items']} items from {result['files_loaded']} files")
                        else:
                            st.error(f"❌ ChromaDB reload failed: {result.get('error', 'Unknown error')}")
                    else:
                        st.error("❌ ChromaDB not available")
                except Exception as e:
                    st.error(f"❌ Error reloading ChromaDB: {e}")
        
        with col2:
            if st.button("📊 Test Search", key="test_chroma_search", help="Test ChromaDB search functionality"):
                try:
                    test_query = "password reset"
                    if hasattr(bot, 'chroma_kb') and bot.chroma_kb:
                        results = bot.chroma_kb.search_knowledge_base(test_query, n_results=3)
                        if results:
                            st.success(f"✅ Search test successful: Found {len(results)} results for '{test_query}'")
                            with st.expander("Search Results"):
                                for i, result in enumerate(results, 1):
                                    st.write(f"**{i}. {result.get('question', 'No question')}** (Score: {result.get('similarity_score', 0):.3f})")
                        else:
                            st.warning("⚠️ Search test returned no results")
                    else:
                        st.error("❌ ChromaDB not available for testing")
                except Exception as e:
                    st.error(f"❌ Error testing ChromaDB search: {e}")
        
        with col3:
            persist_dir = chroma_db.get("persist_directory", "unknown")
            st.text_input("💾 Persist Directory", value=persist_dir, disabled=True, key="chroma_persist_dir")
    
    else:
        st.error("❌ ChromaDB Vector Database Not Available")
        st.info("**Reasons might include:**")
        st.info("- ChromaDB not installed (`pip install chromadb`)")
        st.info("- SentenceTransformers not installed (`pip install sentence-transformers`)")
        st.info("- Initialization error - check logs for details")
        
        error_msg = chroma_db.get("error", "Unknown error")
        st.warning(f"**Error:** {error_msg}")
    
    # Knowledge Base Upload Section
    st.markdown("#### 📤 Knowledge Base Upload")
    
    # Knowledge Base Upload
    uploaded_kb_file = st.file_uploader(
        "📚 Upload Knowledge Base File",
        type=['json'],
        help="Upload a JSON file with FAQs, troubleshooting guides, or other knowledge base content. Will be synced to both legacy KB and ChromaDB.",
        key="kb_upload_widget"
    )
    
    if uploaded_kb_file is not None:
        try:
            json_data = json.load(uploaded_kb_file)
            
            # Show preview of the data
            with st.expander("📋 Preview Knowledge Base Content"):
                if "faqs" in json_data:
                    st.write(f"**FAQs:** {len(json_data['faqs'])} items")
                if "troubleshooting_guides" in json_data:
                    st.write(f"**Troubleshooting Guides:** {len(json_data['troubleshooting_guides'])} items")
                if "quick_solutions" in json_data:
                    st.write(f"**Quick Solutions:** {len(json_data['quick_solutions'])} items")
                if "emergency_contacts" in json_data:
                    st.write(f"**Emergency Contacts:** {len(json_data['emergency_contacts'])} items")
                
                st.json(json_data)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📤 Upload to Knowledge Base", type="primary", key="upload_kb_btn"):
                    try:
                        # Save to data/kb directory
                        kb_dir = os.path.join("data", "kb")
                        os.makedirs(kb_dir, exist_ok=True)
                        
                        # Generate filename based on upload timestamp
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"kb_upload_{timestamp}.json"
                        file_path = os.path.join(kb_dir, filename)
                        
                        # Save the uploaded knowledge base
                        with open(file_path, "w", encoding="utf-8") as f:
                            json.dump(json_data, f, indent=2, ensure_ascii=False)
                        
                        st.success(f"✅ Knowledge base uploaded successfully as {filename}")
                        
                        # Force reload both legacy and ChromaDB
                        reload_success = bot.reload_knowledge_base()  # This will sync both
                        
                        if reload_success:
                            st.success("🔄 Both legacy KB and ChromaDB reloaded successfully")
                            st.session_state.kb_upload_success = True
                        else:
                            st.warning("⚠️ File saved but reload had issues - check logs")
                            
                    except Exception as e:
                        st.error(f"❌ Error uploading file: {e}")
            
            with col2:
                if st.button("🔄 Reload All Knowledge Bases", key="reload_all_kb_btn"):
                    success = bot.reload_knowledge_base()  # This syncs both legacy and ChromaDB
                    if success:
                        st.success("✅ All knowledge bases reloaded successfully!")
                        st.session_state.kb_reload_success = True
                    else:
                        st.error("❌ Failed to reload knowledge bases")
        
        except json.JSONDecodeError:
            st.error("❌ Invalid JSON file")
        except Exception as e:
            st.error(f"❌ Error processing file: {e}")
    
    # System Information
    st.markdown("### 🖥️ System Information")
    
    data = load_mock_data()
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Tickets", len(data.get("tickets", [])))
    
    with col2:
        st.metric("Total Users", len(data.get("users", [])))
    
    with col3:
        st.metric("Active Sessions", len(st.session_state.get("conversations", {})) if hasattr(st.session_state, 'conversations') else 1)

def render_chat_interface():
    """Render chat interface with login screen and ticket creation form"""
    # Check if user is logged in
    if not st.session_state.is_logged_in:
        render_login_screen()
        return
    
    # Handle different views
    if st.session_state.show_statistics:
        render_statistics_dashboard()
        return
    
    if st.session_state.admin_mode:
        render_admin_panel()
        return
    
    # Handle ticket creation form
    if st.session_state.pending_ticket_creation:
        render_ticket_creation_form()
        return
    
    # Simple header
    st.markdown("## 💬 IT Support Chat")
    
    # Show current user context in a simple way
    role_name = get_localized_text(f"role_{st.session_state.user_role}", st.session_state.current_language)
    
    # Language detection indicator
    lang_info = LANGUAGES.get(st.session_state.current_language, {})
    st.caption(f"👤 **{st.session_state.current_username}** ({role_name}) | 🌍 {lang_info.get('flag', '🌍')} {lang_info.get('name', 'Unknown')}")
    
    # Initialize with a simple welcome if no messages
    if len(st.session_state.messages) == 0:
        greeting = get_localized_text("greeting", st.session_state.current_language)
        
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"{greeting}\n\n**What I can help with:**\n🎫 Create and manage support tickets\n🔐 Password and account assistance\n📊 System status and information\n💬 Multi-language support\n\nTry the **Quick Actions** in the sidebar or just tell me what you need!",
            "timestamp": datetime.now().strftime("%H:%M"),
            "language": st.session_state.current_language
        })
    
    # Simple chat messages display
    for msg_index, message in enumerate(st.session_state.messages):
        if message["role"] == "user":
            # User message on the right
            col1, col2 = st.columns([1, 3])
            with col2:
                formatted_content = format_markdown_to_html(message['content'])
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #007ACC 0%, #005A9B 100%); 
                    color: white; 
                    padding: 10px 16px; 
                    border-radius: 16px 16px 4px 16px; 
                    margin: 6px 0 12px 0;
                    box-shadow: 0 2px 6px rgba(0, 122, 204, 0.25);
                    word-wrap: break-word;
                    max-width: 100%;
                ">
                    <div style="font-size: 14px; line-height: 1.4;">{formatted_content}</div>
                    <div style="text-align: right; margin-top: 6px;">
                        <small style="opacity: 0.85; font-size: 10px;">🕐 {message['timestamp']}</small>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            # Assistant message on the left
            col1, col2 = st.columns([3, 1])
            with col1:
                formatted_content = format_markdown_to_html(message['content'])
                st.markdown(f"""
                <div style="
                    background: white; 
                    color: #2C3E50; 
                    padding: 10px 16px; 
                    border-radius: 16px 16px 16px 4px; 
                    margin: 6px 0 12px 0;
                    border: 1px solid #E1E8ED;
                    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
                    word-wrap: break-word;
                    max-width: 100%;
                ">
                    <div style="font-size: 14px; line-height: 1.4;">{formatted_content}</div>
                    <div style="text-align: left; margin-top: 6px;">
                        <small style="opacity: 0.7; font-size: 10px;">🤖 {message['timestamp']}</small>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Add voice button for assistant messages
                if st.session_state.tts_enabled and (TTS_AVAILABLE or SIMPLE_TTS_AVAILABLE):
                    col_voice1, col_voice2, col_voice3, col_voice4 = st.columns([1, 1, 1, 7])
                    with col_voice1:
                        if st.button("🔊", key=f"tts_{msg_index}_{message.get('timestamp', 'unknown')}", 
                                   help="Read this message aloud"):
                            generate_and_play_tts(message['content'], f"tts_audio_{msg_index}_{message.get('timestamp', 'unknown')}")
                    
                    with col_voice2:
                        if st.button("🔇", key=f"stop_{msg_index}_{message.get('timestamp', 'unknown')}", 
                                   help="Stop voice playback"):
                            stop_current_tts()
                    
                    with col_voice3:
                        # Download audio button
                        audio_key = f"tts_audio_{msg_index}_{message.get('timestamp', 'unknown')}"
                        if audio_key in st.session_state:
                            audio_data = st.session_state[audio_key]
                            st.download_button(
                                "💾",
                                data=base64.b64decode(audio_data),
                                file_name=f"response_{msg_index}_{message.get('timestamp', 'audio')}.wav",
                                mime="audio/wav",
                                help="Download audio file",
                                key=f"download_{msg_index}_{message.get('timestamp', 'unknown')}"
                            )
    
    # Show processing indicator with improved styling
    if st.session_state.processing_message:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #F8F9FA 0%, #E9ECEF 100%); 
                color: #495057; 
                padding: 10px 16px; 
                border-radius: 16px 16px 16px 4px; 
                margin: 6px 0 12px 0;
                border: 1px solid #DEE2E6;
                box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
                animation: pulse 1.5s ease-in-out infinite;
            ">
                <div style="display: flex; align-items: center; font-size: 14px;">
                    <div style="margin-right: 8px;">⏳</div>
                    <div style="font-style: italic;">Processing your request...</div>
                </div>
            </div>
            
            <style>
            @keyframes pulse {
                0% { opacity: 0.7; }
                50% { opacity: 1; }
                100% { opacity: 0.7; }
            }
            </style>
            """, unsafe_allow_html=True)
    
    # Chat input with language detection hint
    placeholder_text = "Type your message in any language..."
    user_input = st.chat_input(
        placeholder_text,
        disabled=st.session_state.processing_message
    )
    
    if user_input:
        handle_user_input(user_input)
        st.rerun()
    
    # Process response
    if st.session_state.processing_message and st.session_state.pending_user_message:
        try:
            process_bot_response()
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")
            st.session_state.processing_message = False
            st.session_state.pending_user_message = None

def main():
    """Main application function with enhanced features and login"""
    # Initialize session state
    initialize_session_state()
    
    # Show loading indicator while initializing
    if 'bot_initialized' not in st.session_state:
        st.session_state.bot_initialized = False
    
    # Initialize bot early if not already done
    if not st.session_state.bot_initialized:
        with st.spinner("🚀 Initializing IT Helpdesk System..."):
            try:
                # Pre-initialize the bot and ChromaDB
                bot = get_enhanced_bot()
                
                # Verify ChromaDB status
                if hasattr(bot, 'chroma_kb') and bot.chroma_kb:
                    status = bot.chroma_kb.get_status()
                    collection_size = status.get('collection_size', 0)
                    embedding_type = status.get('embedding_type', 'unknown')
                    
                    # Show initialization success message
                    if collection_size > 0:
                        st.success(f"✅ System Ready! ChromaDB loaded with {collection_size} items using {embedding_type} embeddings")
                    else:
                        st.warning("⚠️ ChromaDB initialized but empty. Knowledge base may need to be loaded.")
                else:
                    st.warning("⚠️ ChromaDB not available. System will use legacy knowledge base only.")
                
                st.session_state.bot_initialized = True
                time.sleep(1)  # Brief pause to show success message
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ System initialization error: {e}")
                st.session_state.bot_initialized = True  # Continue anyway
                time.sleep(2)
                st.rerun()
    
    # Show login screen if not logged in
    if not st.session_state.is_logged_in:
        render_login_screen()
        return
    
    # Main title
    st.markdown(f"# {get_ui_text('title', st.session_state.current_language)}")
    
    # Subtitle with version info
    st.markdown("### 🚀 Enterprise Edition - Multi-Language & Role-Based Access")
    
    # Render enhanced sidebar
    render_enhanced_sidebar()
    
    # Render main chat interface
    render_chat_interface()
    
    # Compact enterprise features info with hover tooltip
    st.markdown("---")
    col1, col2 = st.columns([10, 1])
    with col2:
        st.markdown("""
        <style>
        .enterprise-info {
            position: relative;
            display: inline-block;
            cursor: help;
            font-size: 1.5em;
            text-align: right;
            color: #FFD700;
        }
        
        .enterprise-info .tooltip {
            visibility: hidden;
            width: 300px;
            background-color: #333;
            color: #fff;
            text-align: left;
            border-radius: 8px;
            padding: 12px;
            position: absolute;
            z-index: 1000;
            bottom: 125%;
            right: 0;
            margin-right: 0;
            opacity: 0;
            transition: opacity 0.3s;
            font-size: 0.9rem;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }
        
        .enterprise-info .tooltip::after {
            content: "";
            position: absolute;
            top: 100%;
            right: 20px;
            margin-left: -5px;
            border-width: 5px;
            border-style: solid;
            border-color: #333 transparent transparent transparent;
        }
        
        .enterprise-info:hover .tooltip {
            visibility: visible;
            opacity: 1;
        }
        </style>
        
        <div class="enterprise-info">
            🌟
            <div class="tooltip">
                <strong>🌟 Enterprise Features Active</strong><br><br>
                🌍 Multi-Language Auto-Detection<br>
                🔐 User Authentication System<br>
                👥 Role-Based Access Control<br>
                🎫 Advanced Ticket Management<br>
                📊 Real-time Analytics & Statistics<br>
                📤 Admin Data Upload Capabilities
            </div>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
