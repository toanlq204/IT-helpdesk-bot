import openai
import json
import os
from openai import AzureOpenAI
from functions.helpdesk_functions import (
    reset_password, check_ticket_status, create_ticket,
    search_knowledge_base, escalate_ticket, get_system_status
)
from prompts.templates import get_few_shot_prompt

client = AzureOpenAI(
    api_version="2024-07-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY")
)

functions = [
    {
        "name": "reset_password",
        "description": "Reset user password for account access issues",
        "parameters": {
            "type": "object",
            "properties": {
                "username": {
                    "type": "string",
                    "description": "Username or email address of the user"
                }
            },
            "required": ["username"]
        }
    },
    {
        "name": "check_ticket_status",
        "description": "Check the status of an existing support ticket",
        "parameters": {
            "type": "object",
            "properties": {
                "ticket_id": {
                    "type": "string",
                    "description": "The ticket ID (e.g., TKT001)"
                }
            },
            "required": ["ticket_id"]
        }
    },
    {
        "name": "create_ticket",
        "description": "Create a new support ticket for IT issues",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Brief title describing the issue"
                },
                "description": {
                    "type": "string",
                    "description": "Detailed description of the problem"
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "critical"],
                    "description": "Priority level of the issue"
                },
                "category": {
                    "type": "string",
                    "enum": ["hardware", "software", "network", "authentication", "email", "other"],
                    "description": "Category of the IT issue"
                },
                "reporter_email": {
                    "type": "string",
                    "description": "Email address of the person reporting the issue"
                }
            },
            "required": ["title", "description", "priority", "category", "reporter_email"]
        }
    },
    {
        "name": "search_knowledge_base",
        "description": "Search the knowledge base for solutions to common IT problems",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search terms or keywords describing the issue"
                },
                "category": {
                    "type": "string",
                    "enum": ["authentication", "performance", "network", "software", "hardware", "remote_access", "general"],
                    "description": "Optional category to filter search results"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "escalate_ticket",
        "description": "Escalate a ticket to higher level support or management",
        "parameters": {
            "type": "object",
            "properties": {
                "ticket_id": {
                    "type": "string",
                    "description": "The ticket ID to escalate"
                },
                "reason": {
                    "type": "string",
                    "description": "Reason for escalation"
                }
            },
            "required": ["ticket_id", "reason"]
        }
    },
    {
        "name": "get_system_status",
        "description": "Check the status of company IT systems and services",
        "parameters": {
            "type": "object",
            "properties": {
                "service": {
                    "type": "string",
                    "enum": ["email", "vpn", "wifi", "servers", "all"],
                    "description": "Specific service to check, or 'all' for complete status"
                }
            },
            "required": ["service"]
        }
    }
]


def chat(user_input: str, messages: list):
    """
    Enhanced chat function with comprehensive IT helpdesk capabilities
    """
    messages.append({"role": "user", "content": user_input})

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            functions=functions,
            function_call="auto",
            temperature=0.7,
            max_tokens=1000
        )

        message = response.choices[0].message

        if message.get("function_call"):
            func_name = message.function_call.name
            args = json.loads(message.function_call.arguments)

            # Execute the appropriate function
            if func_name == "reset_password":
                result = reset_password(**args)
            elif func_name == "check_ticket_status":
                result = check_ticket_status(**args)
            elif func_name == "create_ticket":
                result = create_ticket(**args)
            elif func_name == "search_knowledge_base":
                result = search_knowledge_base(**args)
            elif func_name == "escalate_ticket":
                result = escalate_ticket(**args)
            elif func_name == "get_system_status":
                result = get_system_status(**args)
            else:
                result = "Unknown function called"

            # Add function result to conversation
            messages.append({
                "role": "function",
                "name": func_name,
                "content": result
            })

            # Get final response from AI
            final_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7
            )

            return final_response.choices[0].message.content, messages

        return message.content, messages

    except Exception as e:
        error_msg = f"I apologize, but I encountered an error: {str(e)}. Please try again or contact IT support directly."
        return error_msg, messages
