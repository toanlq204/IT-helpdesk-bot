import openai
import json
import os
from openai import AzureOpenAI
from functions.helpdesk_functions import reset_password, check_ticket_status
from prompts.templates import get_few_shot_prompt

client = AzureOpenAI(
    api_version="2024-07-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY")
)

functions = [
    {
        "name": "reset_password",
        "description": "Reset user password",
        "parameters": {
            "type": "object",
            "properties": {"username": {"type": "string"}},
            "required": ["username"]
        }
    },
    {
        "name": "check_ticket_status",
        "description": "Check ticket status by ID",
        "parameters": {
            "type": "object",
            "properties": {"ticket_id": {"type": "string"}},
            "required": ["ticket_id"]
        }
    }
]


def chat(user_input: str, messages: list):
    messages.append({"role": "user", "content": user_input})
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        functions=functions,
        function_call="auto"
    )
    message = response.choices[0].message
    if message.get("function_call"):
        func_name = message.function_call.name
        args = json.loads(message.function_call.arguments)
        if func_name == "reset_password":
            result = reset_password(**args)
        elif func_name == "check_ticket_status":
            result = check_ticket_status(**args)
        else:
            result = "Unknown function"
        messages.append(
            {"role": "function", "name": func_name, "content": result})
        return result, messages
    return message.content, messages
