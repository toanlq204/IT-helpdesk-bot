def get_few_shot_prompt():
    return [
        {"role": "system", "content": "You are a helpful IT helpdesk assistant."},
        {"role": "user", "content": "How can I reset my password?"},
        {"role": "assistant",
            "content": "You can reset your password by providing your username."}
    ]
