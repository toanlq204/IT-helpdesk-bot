import json
import os
import uuid
from datetime import datetime
from typing import List, Optional, Dict

class ConversationService:
    def __init__(self, conversations_dir: str = "storage/threads"):
        self.conversations_dir = conversations_dir
        os.makedirs(conversations_dir, exist_ok=True)

    def get_all_conversations(self) -> List[Dict]:
        """Get list of all conversations with metadata"""
        conversations = []
        if os.path.exists(self.conversations_dir):
            for filename in os.listdir(self.conversations_dir):
                if filename.endswith(".json"):
                    file_path = os.path.join(self.conversations_dir, filename)
                    try:
                        with open(file_path, 'r') as f:
                            conversation = json.load(f)
                            # Extract metadata for list view
                            conversation_summary = {
                                "id": conversation["id"],
                                "title": conversation.get("title", f"Chat {conversation['id'][:8]}"),
                                "lastMessage": conversation["messages"][-1]["content"][:100] if conversation["messages"] else "No messages",
                                "updatedAt": conversation["updated_at"],
                                "createdAt": conversation["created_at"]
                            }
                            conversations.append(conversation_summary)
                    except (json.JSONDecodeError, KeyError) as e:
                        print(f"Error reading conversation file {filename}: {e}")
                        continue
        
        # Sort by updated time, newest first
        conversations.sort(key=lambda x: x["updatedAt"], reverse=True)
        return conversations

    def get_conversation_messages(self, conversation_id: str) -> Optional[Dict]:
        """Get messages from a specific conversation"""
        file_path = os.path.join(self.conversations_dir, f"{conversation_id}.json")
        if not os.path.exists(file_path):
            return None
        
        try:
            with open(file_path, 'r') as f:
                conversation = json.load(f)
            return {"messages": conversation["messages"]}
        except (json.JSONDecodeError, KeyError):
            return None

    def load_conversation(self, conversation_id: str) -> Optional[Dict]:
        """Load a complete conversation"""
        file_path = os.path.join(self.conversations_dir, f"{conversation_id}.json")
        if not os.path.exists(file_path):
            return None
        
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return None

    def create_conversation(self, conversation_id: Optional[str] = None) -> Dict:
        """Create a new conversation"""
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        conversation = {
            "id": conversation_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "messages": []
        }
        
        return conversation

    def save_conversation(self, conversation: Dict) -> None:
        """Save conversation to file"""
        conversation["updated_at"] = datetime.now().isoformat()
        file_path = os.path.join(self.conversations_dir, f"{conversation['id']}.json")
        
        with open(file_path, 'w') as f:
            json.dump(conversation, f, indent=2)

    def add_message(self, conversation: Dict, role: str, content: str, 
                   timestamp: Optional[str] = None, **kwargs) -> None:
        """Add a message to conversation"""
        if not timestamp:
            timestamp = datetime.now().isoformat()
        
        message = {
            "role": role,
            "content": content,
            "timestamp": timestamp,
            **kwargs
        }
        
        conversation["messages"].append(message)

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation"""
        file_path = os.path.join(self.conversations_dir, f"{conversation_id}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False 