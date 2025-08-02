import json
import os
from datetime import datetime
from typing import Dict, List, Optional


def reset_password(username: str) -> str:
    """Reset user password with enhanced security measures"""
    # Simulate password reset process
    if not username or "@" not in username:
        return "❌ Invalid username format. Please provide a valid email address."

    # Log the reset request (in real implementation, this would be logged securely)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return f"""✅ Password reset initiated for {username}
    
📧 An email with reset instructions has been sent to your registered email address.
⏰ Reset link will expire in 24 hours.
🔒 For security, please:
   - Use a strong password (8+ characters, mixed case, numbers, symbols)
   - Don't reuse previous passwords
   - Enable 2FA if available

📞 If you don't receive the email within 10 minutes, contact IT support at ext. 4357.
📝 Request logged at: {timestamp}"""


def check_ticket_status(ticket_id: str) -> str:
    """Check ticket status with detailed information"""
    # Load mock ticket data
    try:
        with open('data/mock_tickets.json', 'r') as f:
            tickets_data = json.load(f)

        # Find the ticket
        for ticket in tickets_data['tickets']:
            if ticket['id'] == ticket_id:
                status_emoji = {
                    'open': '🔴',
                    'in_progress': '🟡',
                    'pending_approval': '🟠',
                    'resolved': '✅',
                    'closed': '⚫'
                }.get(ticket['status'], '❓')

                priority_emoji = {
                    'low': '🟢',
                    'medium': '🟡',
                    'high': '🟠',
                    'critical': '🔴'
                }.get(ticket['priority'], '❓')

                result = f"""🎫 Ticket Status: {ticket_id}
                
{status_emoji} Status: {ticket['status'].replace('_', ' ').title()}
{priority_emoji} Priority: {ticket['priority'].title()}
📋 Title: {ticket['title']}
📝 Description: {ticket['description']}
👤 Assigned to: {ticket['assigned_to']}
📅 Created: {ticket['created_date']}
⏱️ Est. Resolution: {ticket.get('estimated_resolution', 'TBD')}"""

                if ticket['status'] == 'resolved' and 'resolution_notes' in ticket:
                    result += f"\n✅ Resolution: {ticket['resolution_notes']}"

                return result

        return f"❌ Ticket {ticket_id} not found. Please check the ticket ID and try again."

    except FileNotFoundError:
        return "❌ Unable to access ticket database. Please contact IT support."


def create_ticket(title: str, description: str, priority: str, category: str, reporter_email: str) -> str:
    """Create a new support ticket"""
    import random

    # Generate new ticket ID
    ticket_id = f"TKT{random.randint(100, 999):03d}"

    # Create new ticket object
    new_ticket = {
        "id": ticket_id,
        "title": title,
        "description": description,
        "status": "open",
        "priority": priority,
        "category": category,
        "created_date": datetime.now().strftime("%Y-%m-%d"),
        "assigned_to": "auto_assignment",
        "reporter": reporter_email,
        "estimated_resolution": get_estimated_resolution(priority, category)
    }

    # In a real implementation, save to database
    priority_emoji = {
        'low': '🟢',
        'medium': '🟡',
        'high': '🟠',
        'critical': '🔴'
    }.get(priority, '❓')

    return f"""✅ Support ticket created successfully!
    
🎫 Ticket ID: {ticket_id}
{priority_emoji} Priority: {priority.title()}
📂 Category: {category.title()}
📧 Reporter: {reporter_email}
⏱️ Estimated Resolution: {new_ticket['estimated_resolution']}

📋 Your Issue:
Title: {title}
Description: {description}

📞 You'll receive updates via email. For urgent issues, call IT support at ext. 4357.
💡 Tip: Save your ticket ID for future reference."""


def search_knowledge_base(query: str, category: Optional[str] = None) -> str:
    """Search knowledge base for solutions"""
    try:
        with open('data/faqs.json', 'r') as f:
            faqs_data = json.load(f)

        # Simple search implementation
        relevant_faqs = []
        query_lower = query.lower()

        for faq in faqs_data['faqs']:
            # Check if query matches question, answer, or keywords
            matches_question = query_lower in faq['question'].lower()
            matches_answer = query_lower in faq['answer'].lower()
            matches_keywords = any(
                keyword.lower() in query_lower for keyword in faq['keywords'])
            matches_category = not category or faq['category'] == category

            if (matches_question or matches_answer or matches_keywords) and matches_category:
                relevant_faqs.append(faq)

        if not relevant_faqs:
            return f"""🔍 No direct matches found for "{query}"
            
💡 Try these suggestions:
• Check your spelling and try different keywords
• Browse our FAQ categories: authentication, performance, network, software, hardware
• Contact IT support for personalized assistance at ext. 4357
• Create a support ticket for complex issues"""

        result = f"🔍 Found {len(relevant_faqs)} solution(s) for '{query}':\n\n"

        # Limit to top 3 results
        for idx, faq in enumerate(relevant_faqs[:3], 1):
            result += f"""📋 Solution #{idx}:
❓ Q: {faq['question']}
✅ A: {faq['answer']}
🏷️ Category: {faq['category'].title()}

"""

        if len(relevant_faqs) > 3:
            result += f"📚 {len(relevant_faqs) - 3} more solutions available. Contact IT for comprehensive help."

        return result

    except FileNotFoundError:
        return "❌ Knowledge base unavailable. Please contact IT support directly."


def escalate_ticket(ticket_id: str, reason: str) -> str:
    """Escalate ticket to higher level support"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return f"""⬆️ Ticket Escalation Request: {ticket_id}
    
🎯 Escalation Reason: {reason}
⏰ Escalated at: {timestamp}
👨‍💼 Forwarded to: IT Manager & Senior Technical Support
📧 You'll receive confirmation within 2 hours

🔄 Next Steps:
• Senior technician will review your case
• Priority may be increased based on impact
• You'll be contacted within 4 business hours
• Alternative solutions may be provided

📞 For immediate assistance: Call IT Emergency Line at ext. 911"""


def get_system_status(service: str) -> str:
    """Get current system status"""
    # Mock system status data
    system_status = {
        "email": {"status": "operational", "uptime": "99.9%", "last_incident": "None in 30 days"},
        "vpn": {"status": "operational", "uptime": "99.7%", "last_incident": "2 days ago - brief connection issues"},
        "wifi": {"status": "degraded", "uptime": "98.5%", "last_incident": "Conference Room B - resolved"},
        "servers": {"status": "operational", "uptime": "99.95%", "last_incident": "None in 45 days"}
    }

    if service == "all":
        result = "🖥️ **IT Systems Status Dashboard**\n\n"
        for svc, info in system_status.items():
            status_emoji = {"operational": "✅", "degraded": "⚠️",
                            "down": "❌"}.get(info["status"], "❓")
            result += f"{status_emoji} **{svc.upper()}**: {info['status'].title()}\n"
            result += f"   📊 Uptime: {info['uptime']}\n"
            result += f"   🕐 Last Issue: {info['last_incident']}\n\n"

        result += "📱 For real-time updates: Check company status page or IT notifications"
        return result

    elif service in system_status:
        info = system_status[service]
        status_emoji = {"operational": "✅", "degraded": "⚠️",
                        "down": "❌"}.get(info["status"], "❓")

        return f"""{status_emoji} **{service.upper()} Service Status**

🔄 Current Status: {info['status'].title()}
📊 Uptime: {info['uptime']}
🕐 Last Incident: {info['last_incident']}

{'✅ Service is running normally' if info['status'] == 'operational' else '⚠️ Some users may experience issues'}

📞 Report new issues: ext. 4357 or create a support ticket"""

    else:
        return f"❌ Unknown service '{service}'. Available services: email, vpn, wifi, servers, or 'all' for complete status."


def get_estimated_resolution(priority: str, category: str) -> str:
    """Calculate estimated resolution time based on priority and category"""
    base_times = {
        "authentication": {"low": "4 hours", "medium": "2 hours", "high": "1 hour", "critical": "30 minutes"},
        "performance": {"low": "1 day", "medium": "8 hours", "high": "4 hours", "critical": "2 hours"},
        "network": {"low": "8 hours", "medium": "4 hours", "high": "2 hours", "critical": "1 hour"},
        "software": {"low": "2 days", "medium": "1 day", "high": "8 hours", "critical": "4 hours"},
        "hardware": {"low": "3 days", "medium": "1 day", "high": "8 hours", "critical": "4 hours"},
        "email": {"low": "4 hours", "medium": "2 hours", "high": "1 hour", "critical": "30 minutes"}
    }

    return base_times.get(category, {}).get(priority, "TBD - will be assessed by technician")
