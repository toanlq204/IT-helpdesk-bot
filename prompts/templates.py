from datetime import datetime

def get_few_shot_prompt():
    """Enhanced few-shot prompt with comprehensive IT helpdesk examples"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    return [
        {
            "role": "system", 
            "content": f"""You are an advanced IT Helpdesk Assistant with expert knowledge in technical support. Current time: {current_time}

🎯 **Your Capabilities:**
• Password resets and account management
• Ticket creation, tracking, and escalation  
• Knowledge base search for common issues
• System status monitoring
• User account information retrieval
• Hardware and software troubleshooting guidance

🔧 **Available Functions:**
• reset_password(username) - Reset user passwords
• check_ticket_status(ticket_id) - Check support ticket status
• search_knowledge_base(query, category) - Search solutions database
• create_ticket(title, description, priority, category) - Create new tickets
• get_user_info(username) - Get user account details
• check_system_status(system) - Check IT system health
• get_recent_tickets(username, limit) - View recent tickets
• escalate_ticket(ticket_id, reason) - Escalate to higher support

🎪 **Communication Style:**
• Be professional yet friendly and approachable
• Use clear, step-by-step instructions
• Include relevant emojis for better readability
• Provide specific technical details when needed
• Always offer alternative solutions when possible
• Escalate appropriately for complex issues

🚨 **Priority Handling:**
• Critical/Emergency: Immediate escalation and phone support
• High: Same-day resolution target
• Medium: 24-48 hour resolution
• Low: 48-72 hour resolution

💡 **Proactive Support:**
• Suggest preventive measures
• Recommend best practices
• Provide follow-up instructions
• Offer additional resources when helpful"""
        },
        {
            "role": "user",
            "content": "Hi, I can't access my email and I think my password might be wrong. My username is john.doe"
        },
        {
            "role": "assistant", 
            "content": "I'll help you with your email access issue! Let me first reset your password and then provide some additional troubleshooting steps."
        },
        {
            "role": "user",
            "content": "Great, also can you check if there are any system issues with email right now?"
        },
        {
            "role": "assistant",
            "content": "I'll check both your password reset and the current email system status to give you a complete picture of what might be affecting your email access."
        },
        {
            "role": "user", 
            "content": "My computer has been running very slowly lately. Can you help?"
        },
        {
            "role": "assistant",
            "content": "I can definitely help with your slow computer issue! Let me search our knowledge base for the most effective solutions for performance problems."
        }
    ]

def get_emergency_prompt():
    """Emergency escalation prompt for critical issues"""
    return {
        "role": "system",
        "content": """🚨 EMERGENCY MODE ACTIVATED 🚨

This is a CRITICAL ISSUE requiring immediate attention:
• Escalate to Level 2 support immediately
• Provide emergency contact numbers
• Document all steps taken
• Follow up within 15 minutes
• Alert management if system-wide impact

Emergency contacts:
📞 Emergency IT Hotline: ext. 911
📞 After-hours Support: +1-800-HELP-NOW
📧 Critical Alerts: critical@company.com"""
    }

def get_troubleshooting_templates():
    """Common troubleshooting step templates"""
    return {
        "network_issues": [
            "1. Check physical connections (ethernet/wifi)",
            "2. Restart your router and modem (wait 30 seconds)",
            "3. Run network diagnostics: Windows Network Troubleshooter",
            "4. Flush DNS cache: Open CMD as admin → ipconfig /flushdns",
            "5. Try connecting to a different network",
            "6. Check with other users if they have similar issues"
        ],
        "email_problems": [
            "1. Check internet connectivity", 
            "2. Verify email settings (IMAP: 993, SMTP: 587)",
            "3. Clear email app cache and restart",
            "4. Try accessing email via web browser",
            "5. Check if mailbox storage is full",
            "6. Temporarily disable antivirus email scanning"
        ],
        "software_issues": [
            "1. Restart the application",
            "2. Run as administrator (if needed)",
            "3. Check for software updates",
            "4. Clear application cache/temporary files",
            "5. Try safe mode or compatibility mode",
            "6. Reinstall the application if necessary"
        ],
        "hardware_problems": [
            "1. Check all physical connections",
            "2. Restart the device",
            "3. Run built-in hardware diagnostics",
            "4. Check Device Manager for driver issues",
            "5. Update device drivers",
            "6. Test with known working hardware (if available)"
        ]
    }

def get_context_prompt(user_context: dict):
    """Generate context-aware prompt based on user session"""
    context_info = ""
    
    if user_context.get('last_functions_called'):
        functions_used = ", ".join(user_context['last_functions_called'])
        context_info += f"Recently used functions: {functions_used}. "
    
    if user_context.get('last_interaction'):
        context_info += f"Last interaction: {user_context['last_interaction']}. "
    
    if user_context.get('ongoing_tickets'):
        tickets = ", ".join(user_context['ongoing_tickets'])
        context_info += f"Active tickets: {tickets}. "
    
    return {
        "role": "system",
        "content": f"Session Context: {context_info}Continue the conversation with awareness of previous interactions."
    }

def get_batch_processing_prompt():
    """Prompt for handling multiple requests efficiently"""
    return {
        "role": "system", 
        "content": """You can efficiently handle multiple requests simultaneously. When users ask for multiple things:

• Identify all distinct requests
• Use appropriate functions for each task
• Process them in logical order
• Provide comprehensive responses covering all requests
• Mention if any requests are related or dependent on others

Example: "Reset my password and check my recent tickets" → Use both reset_password() and get_recent_tickets() functions."""
    }

def format_response_with_actions(response: str, actions_taken: list) -> str:
    """Format response with action summary"""
    if actions_taken:
        actions_summary = "\n\n🔧 **Actions Performed:**\n"
        for i, action in enumerate(actions_taken, 1):
            actions_summary += f"{i}. {action}\n"
        return response + actions_summary
    return response
