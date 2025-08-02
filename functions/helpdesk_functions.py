def reset_password(username: str):
    return f"Password for user {username} has been reset successfully."


def check_ticket_status(ticket_id: str):
    # Dummy logic
    status = "Resolved" if ticket_id.endswith("1") else "In Progress"
    return f"Ticket {ticket_id} is currently: {status}"
