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

📊 **Enterprise Features**
- Statistical dashboards by role
- Data upload capabilities (Admin)
- Multi-session chat support
- Progressive UI with enhanced UX

🔐 **Security & Authentication**
- Role-based access control
- Permission validation
- Secure data handling

Author: GitHub Copilot
Version: 3.0 - Enterprise Edition
Date: August 2025
"""

import streamlit as st
import asyncio
import json
import time
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

# Configure page
st.set_page_config(
    page_title="🤖 Enterprise IT Helpdesk Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import enhanced bot modules
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    from chatbot.core import EnhancedITHelpdeskBot
    from functions.helpdesk_functions import (
        get_user_by_username, get_localized_text, load_mock_data
    )
except ImportError as e:
    st.error("❌ Unable to load chatbot modules. Please check installation.")
    st.error(f"Error details: {e}")
    st.stop()

# Initialize enhanced bot
@st.cache_resource
def get_enhanced_bot():
    """Initialize and cache the enhanced helpdesk bot"""
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
        'thread_list': []
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

async def process_bot_response():
    """Process bot response asynchronously with enhanced conversation context"""
    if not st.session_state.processing_message or not st.session_state.pending_user_message:
        return
    
    try:
        # Get bot instance
        if not st.session_state.bot_instance:
            st.session_state.bot_instance = get_enhanced_bot()
        
        # Ensure conversation continuity by maintaining session context
        session_id = st.session_state.session_id
        
        # Get response from enhanced bot with thread management
        response, thread_id = await st.session_state.bot_instance.get_response(
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
        st.session_state.messages.append({
            "role": "assistant",
            "content": response_content,
            "timestamp": current_time.strftime("%H:%M"),
            "language": st.session_state.current_language,
            "thread_id": st.session_state.current_thread_id,
            "conversation_turn": len(st.session_state.messages) + 1
        })
        
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
    """Render admin panel for system administrators"""
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
    
    # Knowledge Base Upload Section
    st.markdown("### 📚 Knowledge Base Management")
    
    # Show current knowledge base info
    bot = get_enhanced_bot()
    kb_info = bot.get_knowledge_base_info()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📁 KB Files", kb_info["total_files"])
    with col2:
        st.metric("❓ FAQs", kb_info["total_faqs"])
    with col3:
        st.metric("🔧 Guides", kb_info["total_troubleshooting_guides"])
    with col4:
        st.metric("⚡ Quick Solutions", kb_info["total_quick_solutions"])
    
    st.info(f"**Version:** {kb_info['version']} | **Last Updated:** {kb_info['last_updated']}")
    
    # Knowledge Base Upload
    uploaded_kb_file = st.file_uploader(
        "📚 Upload Knowledge Base File",
        type=['json'],
        help="Upload a JSON file with FAQs, troubleshooting guides, or other knowledge base content",
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
                        st.info("💡 Knowledge base will be automatically reloaded due to file monitoring")
                        
                        # Force reload the knowledge base in the session
                        if bot.reload_knowledge_base():
                            st.success("🔄 Knowledge base reloaded successfully")
                            # Set a flag to trigger rerun on next interaction instead of immediate rerun
                            st.session_state.kb_upload_success = True
                        else:
                            st.error("❌ Failed to reload knowledge base")
                    except Exception as e:
                        st.error(f"❌ Error uploading file: {e}")
            
            with col2:
                if st.button("🔄 Reload Knowledge Base", key="reload_kb_btn"):
                    if bot.reload_knowledge_base():
                        st.success("✅ Knowledge base reloaded successfully!")
                        # Use session state flag instead of immediate rerun to avoid DataCloneError
                        st.session_state.kb_reload_success = True
                    else:
                        st.error("❌ Failed to reload knowledge base")
        
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
    for message in st.session_state.messages:
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
            asyncio.run(process_bot_response())
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")
            st.session_state.processing_message = False
            st.session_state.pending_user_message = None

def main():
    """Main application function with enhanced features and login"""
    # Initialize session state
    initialize_session_state()
    
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
