#!/usr/bin/env python3
"""
Conversation Thread Management System
=====================================

Manages persistent conversation threads for users, allowing them to:
- Create multiple conversation threads
- Switch between active conversations  
- View conversation history
- Resume previous conversations
- Organize conversations by topic/date

Features:
- Thread persistence to JSON storage
- Thread metadata (title, date, message count)
- Automatic thread summarization
- Thread search and filtering
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class ConversationThread:
    """Represents a single conversation thread"""
    
    def __init__(self, thread_id: str = None, username: str = "", title: str = "New Conversation"):
        self.thread_id = thread_id or str(uuid.uuid4())
        self.username = username
        self.title = title
        self.created_date = datetime.now().isoformat()
        self.last_updated = datetime.now().isoformat()
        self.messages: List[Dict[str, Any]] = []
        self.is_active = True
        self.tags: List[str] = []
        self.summary = ""
        
    def add_message(self, role: str, content: str, language: str = "en", metadata: Dict[str, Any] = None):
        """Add a message to the thread"""
        message = {
            "id": str(uuid.uuid4()),
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "language": language,
            "metadata": metadata or {}
        }
        self.messages.append(message)
        self.last_updated = datetime.now().isoformat()
        
        # Auto-update title if this is the first user message
        if role == "user" and len([m for m in self.messages if m["role"] == "user"]) == 1:
            self.auto_generate_title(content)
    
    def auto_generate_title(self, first_message: str):
        """Generate a title based on the first user message"""
        # Extract key topics for title
        content_lower = first_message.lower()
        
        if any(word in content_lower for word in ["ticket", "create", "issue", "problem"]):
            if any(word in content_lower for word in ["computer", "laptop", "pc"]):
                self.title = "Computer Issue Support"
            elif any(word in content_lower for word in ["password", "login", "access"]):
                self.title = "Password/Access Help"
            elif any(word in content_lower for word in ["printer", "print"]):
                self.title = "Printer Support"
            elif any(word in content_lower for word in ["email", "outlook"]):
                self.title = "Email Support"
            else:
                self.title = "General IT Support"
        elif any(word in content_lower for word in ["hello", "hi", "help"]):
            self.title = "General Assistance"
        else:
            # Use first 50 characters of the message
            words = first_message.split()[:8]
            self.title = " ".join(words) + ("..." if len(first_message.split()) > 8 else "")
    
    def get_message_count(self) -> int:
        """Get total message count"""
        return len(self.messages)
    
    def get_user_message_count(self) -> int:
        """Get user message count"""
        return len([m for m in self.messages if m["role"] == "user"])
    
    def get_summary(self) -> str:
        """Get or generate thread summary"""
        if not self.summary and self.messages:
            user_messages = [m["content"] for m in self.messages if m["role"] == "user"]
            if user_messages:
                self.summary = f"Started with: {user_messages[0][:100]}..."
        return self.summary
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert thread to dictionary for JSON storage"""
        return {
            "thread_id": self.thread_id,
            "username": self.username,
            "title": self.title,
            "created_date": self.created_date,
            "last_updated": self.last_updated,
            "messages": self.messages,
            "is_active": self.is_active,
            "tags": self.tags,
            "summary": self.get_summary(),
            "message_count": self.get_message_count(),
            "user_message_count": self.get_user_message_count()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationThread':
        """Create thread from dictionary"""
        thread = cls(
            thread_id=data.get("thread_id"),
            username=data.get("username", ""),
            title=data.get("title", "New Conversation")
        )
        thread.created_date = data.get("created_date", datetime.now().isoformat())
        thread.last_updated = data.get("last_updated", datetime.now().isoformat())
        thread.messages = data.get("messages", [])
        thread.is_active = data.get("is_active", True)
        thread.tags = data.get("tags", [])
        thread.summary = data.get("summary", "")
        return thread


class ConversationThreadManager:
    """Manages all conversation threads for all users"""
    
    def __init__(self, storage_file: str = "data/conversation_threads.json"):
        self.storage_file = storage_file
        self.threads: Dict[str, ConversationThread] = {}
        self.load_threads()
    
    def load_threads(self):
        """Load threads from storage file"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for thread_data in data.get("threads", []):
                        thread = ConversationThread.from_dict(thread_data)
                        self.threads[thread.thread_id] = thread
                logger.info(f"Loaded {len(self.threads)} conversation threads")
            else:
                logger.info("No existing conversation threads found, starting fresh")
        except Exception as e:
            logger.error(f"Error loading conversation threads: {e}")
            self.threads = {}
    
    def save_threads(self):
        """Save threads to storage file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            
            data = {
                "threads": [thread.to_dict() for thread in self.threads.values()],
                "last_updated": datetime.now().isoformat(),
                "total_threads": len(self.threads)
            }
            
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(self.threads)} conversation threads")
        except Exception as e:
            logger.error(f"Error saving conversation threads: {e}")
    
    def create_thread(self, username: str, title: str = None) -> ConversationThread:
        """Create a new conversation thread"""
        thread = ConversationThread(username=username, title=title or "New Conversation")
        self.threads[thread.thread_id] = thread
        self.save_threads()
        logger.info(f"Created new thread {thread.thread_id} for user {username}")
        return thread
    
    def get_thread(self, thread_id: str) -> Optional[ConversationThread]:
        """Get a specific thread by ID"""
        return self.threads.get(thread_id)
    
    def get_user_threads(self, username: str, active_only: bool = True) -> List[ConversationThread]:
        """Get all threads for a specific user"""
        user_threads = [
            thread for thread in self.threads.values() 
            if thread.username == username and (not active_only or thread.is_active)
        ]
        # Sort by last updated (most recent first)
        return sorted(user_threads, key=lambda t: t.last_updated, reverse=True)
    
    def get_user_active_thread(self, username: str) -> Optional[ConversationThread]:
        """Get the most recently updated thread for a user"""
        user_threads = self.get_user_threads(username, active_only=True)
        return user_threads[0] if user_threads else None
    
    def add_message_to_thread(self, thread_id: str, role: str, content: str, 
                            language: str = "en", metadata: Dict[str, Any] = None) -> bool:
        """Add a message to a specific thread"""
        thread = self.get_thread(thread_id)
        if thread:
            thread.add_message(role, content, language, metadata)
            self.save_threads()
            return True
        return False
    
    def archive_thread(self, thread_id: str) -> bool:
        """Archive a thread (mark as inactive)"""
        thread = self.get_thread(thread_id)
        if thread:
            thread.is_active = False
            self.save_threads()
            return True
        return False
    
    def delete_thread(self, thread_id: str, username: str) -> bool:
        """Delete a thread (only if user owns it)"""
        thread = self.get_thread(thread_id)
        if thread and thread.username == username:
            del self.threads[thread_id]
            self.save_threads()
            return True
        return False
    
    def search_threads(self, username: str, query: str) -> List[ConversationThread]:
        """Search user's threads by content or title"""
        user_threads = self.get_user_threads(username, active_only=False)
        query_lower = query.lower()
        
        matching_threads = []
        for thread in user_threads:
            # Search in title
            if query_lower in thread.title.lower():
                matching_threads.append(thread)
                continue
            
            # Search in message content
            for message in thread.messages:
                if query_lower in message["content"].lower():
                    matching_threads.append(thread)
                    break
        
        return matching_threads
    
    def get_thread_statistics(self, username: str = None) -> Dict[str, Any]:
        """Get statistics about threads"""
        if username:
            threads = self.get_user_threads(username, active_only=False)
        else:
            threads = list(self.threads.values())
        
        active_threads = [t for t in threads if t.is_active]
        total_messages = sum(t.get_message_count() for t in threads)
        
        return {
            "total_threads": len(threads),
            "active_threads": len(active_threads),
            "archived_threads": len(threads) - len(active_threads),
            "total_messages": total_messages,
            "average_messages_per_thread": total_messages / len(threads) if threads else 0
        }


# Global thread manager instance
thread_manager = ConversationThreadManager()
