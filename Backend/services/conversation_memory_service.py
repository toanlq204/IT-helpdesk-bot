import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConversationMemoryService:
    """Service for managing multi-turn conversation context"""

    def __init__(self, storage_path: str = "storage/conversations"):
        """Initialize conversation memory service"""
        self.storage_path = storage_path
        self.max_turns = 5  # Keep last 5 turns (user + assistant pairs)
        self.max_context_length = 3000  # Max characters for context

        # Ensure storage directory exists
        os.makedirs(storage_path, exist_ok=True)
        logger.info("Conversation memory service initialized")

    def get_conversation_file(self, conversation_id: str) -> str:
        """Get file path for conversation"""
        return os.path.join(self.storage_path, f"{conversation_id}.json")

    def load_conversation(self, conversation_id: str) -> List[Dict[str, str]]:
        """Load conversation history from storage"""
        try:
            file_path = self.get_conversation_file(conversation_id)

            if not os.path.exists(file_path):
                return []

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("messages", [])

        except Exception as e:
            logger.error(
                f"Failed to load conversation {conversation_id}: {str(e)}")
            return []

    def save_conversation(self, conversation_id: str, messages: List[Dict[str, str]]) -> bool:
        """Save conversation history to storage"""
        try:
            file_path = self.get_conversation_file(conversation_id)

            # Limit to max turns
            if len(messages) > self.max_turns * 2:  # user + assistant = 2 messages per turn
                messages = messages[-(self.max_turns * 2):]

            data = {
                "conversation_id": conversation_id,
                "messages": messages,
                "last_updated": datetime.now().isoformat(),
                "turn_count": len(messages) // 2
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(
                f"Saved conversation {conversation_id} with {len(messages)} messages")
            return True

        except Exception as e:
            logger.error(
                f"Failed to save conversation {conversation_id}: {str(e)}")
            return False

    def add_message(self, conversation_id: str, role: str, content: str) -> bool:
        """Add a message to conversation history"""
        try:
            messages = self.load_conversation(conversation_id)

            new_message = {
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat()
            }

            messages.append(new_message)
            return self.save_conversation(conversation_id, messages)

        except Exception as e:
            logger.error(
                f"Failed to add message to conversation {conversation_id}: {str(e)}")
            return False

    def get_conversation_context(self, conversation_id: str) -> List[Dict[str, str]]:
        """Get conversation context for OpenAI (without timestamps)"""
        try:
            messages = self.load_conversation(conversation_id)

            # Remove timestamps and limit length
            clean_messages = []
            total_length = 0

            # Process messages in reverse order to keep most recent
            for message in reversed(messages):
                content = message.get("content", "")
                role = message.get("role", "user")

                # Skip if adding this message would exceed context length
                if total_length + len(content) > self.max_context_length:
                    break

                clean_messages.insert(0, {
                    "role": role,
                    "content": content
                })
                total_length += len(content)

            # Limit to max turns
            if len(clean_messages) > self.max_turns * 2:
                clean_messages = clean_messages[-(self.max_turns * 2):]

            return clean_messages

        except Exception as e:
            logger.error(
                f"Failed to get conversation context {conversation_id}: {str(e)}")
            return []

    def clear_conversation(self, conversation_id: str) -> bool:
        """Clear conversation history"""
        try:
            file_path = self.get_conversation_file(conversation_id)
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Cleared conversation {conversation_id}")
                return True
            return True

        except Exception as e:
            logger.error(
                f"Failed to clear conversation {conversation_id}: {str(e)}")
            return False

    def get_conversation_stats(self, conversation_id: str) -> Dict[str, Any]:
        """Get conversation statistics"""
        try:
            messages = self.load_conversation(conversation_id)

            if not messages:
                return {"exists": False}

            user_messages = [m for m in messages if m.get("role") == "user"]
            assistant_messages = [
                m for m in messages if m.get("role") == "assistant"]

            return {
                "exists": True,
                "total_messages": len(messages),
                "user_messages": len(user_messages),
                "assistant_messages": len(assistant_messages),
                "turn_count": len(messages) // 2,
                "last_updated": messages[-1].get("timestamp") if messages else None
            }

        except Exception as e:
            logger.error(
                f"Failed to get conversation stats {conversation_id}: {str(e)}")
            return {"exists": False, "error": str(e)}


# Global instance
conversation_memory = ConversationMemoryService()
