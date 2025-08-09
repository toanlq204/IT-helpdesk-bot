from models.ticket_models import TicketCreate
import openai
import os
import json
from services.ticket_service import TicketService

class ChatService:
    def __init__(self, chat_data_path: str = "storage/data/messages.json", ticket_service: TicketService = TicketService()):
        self.chat_data_path = chat_data_path
        self.ticket_service = ticket_service
        os.makedirs(os.path.dirname(chat_data_path), exist_ok=True)

    def ticket_to_friendly_message(self, ticket: dict) -> str:
        """Transform a ticket dictionary into a user-friendly message."""
        if not ticket:
            return "Ticket not found."
        message = (
            f"Ticket ID: {ticket.get('id', 'N/A')}\n"
            f"Title: {ticket.get('title', 'N/A')}\n"
            f"Description: {ticket.get('description', 'N/A')}\n"
            f"Priority: {ticket.get('priority', 'N/A')}\n"
            f"Status: {ticket.get('status', 'N/A')}\n"
            f"Assignee: {ticket.get('assignee', 'Unassigned')}\n"
            f"Created At: {ticket.get('created_at', 'N/A')}\n"
            f"Last Updated: {ticket.get('updated_at', 'N/A')}\n"
        )
        return message

    def get_system_prompt(self) -> str:
        return   [{
            "role": "system",
            "content": "You are a helpful assistant that can answer questions and help with tasks. always answer in the same language as the user, with max 500 tokens."
        }]

    def load_data_messages(self) -> list:
        try:
            # Check if file exists first
            if not os.path.exists(self.chat_data_path):
                print(f"Warning: {self.chat_data_path} not found, creating default messages")
                # Create default messages if file doesn't exist
                default_messages = [{
                    "role": "system",
                    "content": "You are a helpful IT HelpDesk assistant that can answer questions and help with tasks. Always answer in the same language as the user, with max 500 tokens."
                }]
                # Create the directory if it doesn't exist
                os.makedirs(os.path.dirname(self.chat_data_path), exist_ok=True)
                # Save default messages to file
                with open(self.chat_data_path, "w") as f:
                    json.dump(default_messages, f, indent=2)
                return default_messages
            
            with open(self.chat_data_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading messages from {self.chat_data_path}: {str(e)}")
            # Return default system message if file can't be loaded
            return [{
                "role": "system",
                "content": "You are a helpful IT HelpDesk assistant that can answer questions and help with tasks. Always answer in the same language as the user, with max 500 tokens."
            }]

    def prepare_messages(self, messages: list) -> list:
        default_messages = self.load_data_messages()
        messages = default_messages + messages
        return messages
    #sk-DRKoljlUoP4FtPCOBVy71Q
    def get_response(self, messages: list) -> str:
        try:
            client = openai.OpenAI(
                base_url=os.getenv("OPENAI_BASE_URL"),
                api_key=os.getenv("AZOPENAI_API_KEY")
            )

            # Check if API key is available
            api_key = os.getenv("AZOPENAI_API_KEY")
            if not api_key or api_key == "your-api-key-here":
                return "I'm sorry, but the AI service is not properly configured. Please contact your administrator to set up the API key."

            response = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL"),
                max_tokens=int(os.getenv("OPENAI_MAX_TOKENS")),
                temperature=float(os.getenv("OPENAI_TEMPERATURE")),
                messages=self.prepare_messages(messages),
                tools=[
                    {
                        "type": "function",
                        "function": {
                            "name": "get_ticket_status",
                            "description": "Get the status of a ticket",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "ticket_id": {"type": "string"}
                                }
                            },
                            "required": ["ticket_id"]
                        }
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "create_ticket",
                            "description": "Create a ticket",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"}, 
                                    "description": {"type": "string"}
                                }
                            },
                            "required": ["title", "description"]
                        }
                    }
                ]
            )
            
            tool_calls = response.choices[0].message.tool_calls
            if tool_calls is not None:
                for tool_call in tool_calls:
                    if tool_call.function.name == "get_ticket_status":
                        try:
                            arguments = json.loads(tool_call.function.arguments)
                            ticket_id = arguments["ticket_id"]
                            ticket = self.ticket_service.find_ticket_by_partial_id(ticket_id)
                            return self.ticket_to_friendly_message(ticket)
                        except Exception as e:
                            return None
                    elif tool_call.function.name == "create_ticket":
                        try:
                            arguments = json.loads(tool_call.function.arguments)
                            title = arguments["title"]
                            description = arguments["description"]
                            priority = arguments["priority"] if "priority" in arguments else "medium"
                           
                            ticket = self.ticket_service.create_ticket(TicketCreate(
                                title=title,
                                description=description,
                                priority=priority,
                                status="open"
                            ))
                            return self.ticket_to_friendly_message(ticket)
                        except Exception as e:
                            return None
            
            if response.choices[0].message.content is not None:
                return response.choices[0].message.content
            else:
                return "I'm sorry, I couldn't generate a response. Please try again."
                
        except Exception as e:
            print(f"Error in get_response: {str(e)}")
            return f"I'm sorry, I encountered an error while processing your request: {str(e)}"
