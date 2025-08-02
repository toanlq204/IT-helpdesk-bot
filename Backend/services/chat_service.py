import openai
import os
import json

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
        response = client.chat.completions.create(
            model="Gemini-2.5-Flash",
            messages=self.prepare_messages(messages)
        )
        return response.choices[0].message.content