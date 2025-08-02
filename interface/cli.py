from chatbot.core import chat
from prompts.templates import get_few_shot_prompt


def run():
    print("🤖 IT Helpdesk Chatbot. Type 'exit' to quit.")
    messages = get_few_shot_prompt()
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break
        response, messages = chat(user_input, messages)
        print(f"Bot: {response}")


if __name__ == "__main__":
    run()
