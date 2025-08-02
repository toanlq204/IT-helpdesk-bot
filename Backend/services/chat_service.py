import openai
import os
import json
import re

from services.ticket_service import TicketService
from routers.ticket_router import create_ticket
from routers.ticket_router import update_ticket
from routers.ticket_router import delete_ticket

class ChatService:
    def __init__(self, chat_data_path: str = "storage/data/messages.json"):
        self.chat_data_path = chat_data_path
        os.makedirs(os.path.dirname(chat_data_path), exist_ok=True)

    def load_data_messages(self) -> list:
        with open(self.chat_data_path, "r") as f:
            return json.load(f)

    def prepare_messages(self, messages: list) -> list:
        default_messages = self.load_data_messages()
        messages = default_messages + messages
        return messages

    def get_response(self, messages: list) -> str:
        client = openai.OpenAI(
            base_url="https://aiportalapi.stu-platform.live/use",
            api_key="sk-DRKoljlUoP4FtPCOBVy71Q"
        )

        functions_ = TicketService.get_all_functions()
        response = client.chat.completions.create(
            model="Gemini-2.5-Flash",
            messages=self.prepare_messages(messages),
            functions=functions_,
            function_call="auto",
        )

        function_call = response.choices[0].message.function_call
        if function_call:
            function_name = function_call.name
            function_args = json.loads(function_call.arguments)
            if function_name == "create_ticket":
                create_ticket(function_args)
            elif function_name == "update_ticket":
                update_ticket(function_args)
            elif function_name == "delete_ticket":
                delete_ticket(function_args)

        return response.choices[0].message.content
