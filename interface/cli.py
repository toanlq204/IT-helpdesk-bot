import os
import sys
from datetime import datetime
from chatbot.core import chat
from prompts.templates import get_few_shot_prompt


def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')


def display_banner():
    """Display welcome banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    🤖 IT HELPDESK CHATBOT                    ║
║                   Powered by Azure OpenAI                   ║
╠══════════════════════════════════════════════════════════════╣
║  🎯 Available Services:                                      ║
║  • Password Reset & Account Issues                          ║
║  • Hardware & Software Troubleshooting                     ║
║  • Network & Connectivity Support                          ║
║  • Ticket Creation & Status Tracking                       ║
║  • Knowledge Base Search                                    ║
║  • System Status Monitoring                                ║
╠══════════════════════════════════════════════════════════════╣
║  💡 Quick Commands:                                          ║
║  • Type 'help' for assistance                              ║
║  • Type 'status' for system status                         ║
║  • Type 'new ticket' to create support ticket              ║
║  • Type 'exit' or 'quit' to end session                    ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def display_help():
    """Display help information"""
    help_text = """
🆘 IT HELPDESK CHATBOT - HELP GUIDE

📋 COMMON TASKS:
• "Reset my password" - Initiate password reset process
• "Check ticket TKT001" - Get status of existing ticket  
• "My computer is slow" - Get performance troubleshooting help
• "Can't connect to WiFi" - Network connectivity assistance
• "Install software request" - Submit software installation request
• "System status" - Check IT services availability

🎫 TICKET MANAGEMENT:
• "Create new ticket" - Start guided ticket creation
• "Check my tickets" - View your support requests  
• "Escalate ticket TKT001" - Request ticket escalation

🔍 KNOWLEDGE BASE:
• "Search for [issue]" - Find solutions in knowledge base
• "Password policy" - Get password requirements
• "VPN setup" - Remote access instructions

⚡ EMERGENCY SUPPORT:
For critical issues affecting business operations:
📞 Call IT Emergency Line: ext. 911
📧 Email: emergency@company.com

💡 TIP: Be specific about your issue for faster resolution!
"""
    print(help_text)


def display_session_stats(messages_count: int, start_time: datetime):
    """Display session statistics"""
    session_duration = datetime.now() - start_time
    minutes = int(session_duration.total_seconds() / 60)

    print(f"""
📊 SESSION SUMMARY:
• Messages exchanged: {messages_count}
• Session duration: {minutes} minutes
• Thank you for using IT Helpdesk Chatbot!
""")


def run():
    """Enhanced main CLI interface"""
    clear_screen()
    display_banner()

    print("🤖 IT Helpdesk Chatbot initialized successfully!")
    print("💬 How can I assist you with your IT needs today?\n")

    # Initialize conversation
    messages = get_few_shot_prompt()
    messages_count = 0
    start_time = datetime.now()

    # Check if Azure OpenAI credentials are set
    if not os.getenv("AZURE_OPENAI_ENDPOINT") or not os.getenv("AZURE_OPENAI_API_KEY"):
        print("⚠️  WARNING: Azure OpenAI credentials not found!")
        print("Please set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY environment variables.")
        print("Running in demo mode with limited functionality.\n")

    while True:
        try:
            # Get user input with enhanced prompt
            user_input = input("👤 You: ").strip()

            if not user_input:
                continue

            # Handle special commands
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("\n🤖 Bot: Thank you for using IT Helpdesk Chatbot!")
                display_session_stats(messages_count, start_time)
                break

            elif user_input.lower() == 'help':
                display_help()
                continue

            elif user_input.lower() == 'clear':
                clear_screen()
                display_banner()
                continue

            elif user_input.lower() in ['status', 'system status']:
                user_input = "Check system status for all services"

            # Process user input through chatbot
            print("🤖 Bot: ", end="", flush=True)

            try:
                response, messages = chat(user_input, messages)
                print(response)
                messages_count += 1

            except Exception as e:
                print(f"❌ I apologize, but I encountered an error: {str(e)}")
                print(
                    "🔧 Please try rephrasing your question or contact IT support directly at ext. 4357")

            print()  # Empty line for better readability

        except KeyboardInterrupt:
            print("\n\n🤖 Bot: Session interrupted. Goodbye!")
            display_session_stats(messages_count, start_time)
            break

        except EOFError:
            print("\n🤖 Bot: Session ended. Thank you!")
            display_session_stats(messages_count, start_time)
            break


if __name__ == "__main__":
    run()
