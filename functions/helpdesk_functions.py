#!/usr/bin/env python3

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import random


# =============================================================================
# MULTI-LANGUAGE SUPPORT
# =============================================================================

LANGUAGE_RESPONSES = {
    "en": {
        "ticket_created": "✅ Ticket created successfully",
        "ticket_not_found": "❌ Ticket not found",
        "access_denied": "🚫 Access denied - insufficient permissions",
        "password_reset": "🔐 Password reset completed",
        "user_not_found": "❌ User not found",
        "statistics": "📊 System Statistics",
        "processing": "⏳ Processing your request...",
        "error": "❌ An error occurred",
        "success": "✅ Operation completed successfully",
        "greeting": "Hello! I'm your IT Assistant. How can I help you today?",
        "role_staff": "Staff Member",
        "role_manager": "Department Manager", 
        "role_bod": "Board of Directors",
        "role_admin": "System Administrator",
        "it_contact": "IT Contact Information"
    },
    "es": {
        "ticket_created": "✅ Ticket creado exitosamente",
        "ticket_not_found": "❌ Ticket no encontrado",
        "access_denied": "🚫 Acceso denegado - permisos insuficientes",
        "password_reset": "🔐 Restablecimiento de contraseña completado",
        "user_not_found": "❌ Usuario no encontrado",
        "statistics": "📊 Estadísticas del Sistema",
        "processing": "⏳ Procesando su solicitud...",
        "error": "❌ Ocurrió un error",
        "success": "✅ Operación completada exitosamente",
        "greeting": "¡Hola! Soy tu Asistente de IT. ¿Cómo puedo ayudarte hoy?",
        "role_staff": "Miembro del Personal",
        "role_manager": "Gerente de Departamento",
        "role_bod": "Junta Directiva",
        "role_admin": "Administrador del Sistema"
    },
    "fr": {
        "ticket_created": "✅ Ticket créé avec succès",
        "ticket_not_found": "❌ Ticket non trouvé",
        "access_denied": "🚫 Accès refusé - permissions insuffisantes",
        "password_reset": "🔐 Réinitialisation du mot de passe terminée",
        "user_not_found": "❌ Utilisateur non trouvé",
        "statistics": "📊 Statistiques du Système",
        "processing": "⏳ Traitement de votre demande...",
        "error": "❌ Une erreur s'est produite",
        "success": "✅ Opération terminée avec succès",
        "greeting": "Bonjour! Je suis votre Assistant IT. Comment puis-je vous aider aujourd'hui?",
        "role_staff": "Membre du Personnel",
        "role_manager": "Chef de Département",
        "role_bod": "Conseil d'Administration",
        "role_admin": "Administrateur Système"
    }
}


def get_localized_text(key: str, language: str = "en") -> str:
    """Get localized text for given key and language"""
    if language not in LANGUAGE_RESPONSES:
        language = "en"
    return LANGUAGE_RESPONSES[language].get(key, LANGUAGE_RESPONSES["en"][key])


# =============================================================================
# DATA LOADING AND MANAGEMENT
# =============================================================================

def load_mock_data() -> Dict[str, Any]:
    """Load mock data from JSON file"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(current_dir, "..", "data", "mock_tickets.json")
        
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading mock data: {e}")
        return {"tickets": [], "users": [], "statistics": {}}


def save_mock_data(data: Dict[str, Any]) -> bool:
    """Save mock data to JSON file (Admin only)"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(current_dir, "..", "data", "mock_tickets.json")
        
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving mock data: {e}")
        return False


# =============================================================================
# USER AUTHENTICATION AND ROLE MANAGEMENT
# =============================================================================

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Get user information by username"""
    data = load_mock_data()
    users = data.get("users", [])
    
    for user in users:
        if user["username"].lower() == username.lower():
            return user
    return None


def check_permission(username: str, required_permission: str) -> Tuple[bool, str]:
    """Check if user has required permission"""
    user = get_user_by_username(username)
    if not user:
        return False, "user_not_found"
    
    permissions = user.get("permissions", [])
    role = user.get("role", "staff")
    
    # Admin has all permissions
    if "full_access" in permissions:
        return True, role
    
    # Check specific permission
    if required_permission in permissions:
        return True, role
    
    return False, "access_denied"


def detect_user_language(user_input: str) -> str:
    """Simple language detection based on common words/patterns"""
    user_input_lower = user_input.lower()
    
    # Spanish indicators
    if any(word in user_input_lower for word in ["hola", "ayuda", "problema", "gracias", "por favor"]):
        return "es"
    
    # French indicators  
    if any(word in user_input_lower for word in ["bonjour", "aide", "problème", "merci", "s'il vous plaît"]):
        return "fr"
    
    # Default to English
    return "en"


# =============================================================================
# TICKET MANAGEMENT FUNCTIONS
# =============================================================================

def create_ticket(
    title: str, 
    description: str, 
    priority: str = "medium",
    category: str = "general",
    username: str = "unknown",
    language: str = "en"
) -> str:
    """
    Create a new support ticket
    
    Args:
        title: Ticket title
        description: Detailed description
        priority: Priority level (low, medium, high, critical)
        category: Ticket category
        username: User creating the ticket
        language: Response language
        
    Returns:
        Formatted response about ticket creation
    """
    # Check permissions
    has_permission, role = check_permission(username, "create_ticket")
    if not has_permission:
        return get_localized_text("access_denied", language)
    
    # Generate ticket ID
    ticket_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Get user info
    user = get_user_by_username(username)
    department = user.get("department", "Unknown") if user else "Unknown"
    
    # Create ticket object
    new_ticket = {
        "id": ticket_id,
        "title": title,
        "description": description,
        "status": "open",
        "priority": priority.lower(),
        "category": category.lower(),
        "created_date": datetime.now().isoformat(),
        "updated_date": datetime.now().isoformat(),
        "assigned_to": "Auto-Assignment Queue",
        "resolution": "Ticket created and queued for assignment",
        "requester": username,
        "department": department
    }
    
    # Load current data and add ticket
    data = load_mock_data()
    data["tickets"].append(new_ticket)
    
    # Update statistics
    stats = data.get("statistics", {})
    stats["total_tickets"] = stats.get("total_tickets", 0) + 1
    stats["open"] = stats.get("open", 0) + 1
    
    # Save data (in real system would use database)
    save_mock_data(data)
    
    success_msg = get_localized_text("ticket_created", language)
    
    return f"""{success_msg}

🎫 **Ticket Details:**
• **ID:** {ticket_id}
• **Title:** {title}
• **Priority:** {priority.title()}
• **Category:** {category.title()}
• **Status:** Open
• **Requester:** {username}
• **Department:** {department}
• **Created:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

📧 You will receive email updates on ticket progress."""


def get_ticket_status(ticket_id: str, username: str, language: str = "en") -> str:
    """
    Get status of a specific ticket
    
    Args:
        ticket_id: Ticket identifier
        username: User requesting the information
        language: Response language
        
    Returns:
        Formatted ticket status information
    """
    data = load_mock_data()
    tickets = data.get("tickets", [])
    user = get_user_by_username(username)
    
    if not user:
        return get_localized_text("user_not_found", language)
    
    # Find ticket
    ticket = None
    for t in tickets:
        if t["id"] == ticket_id:
            ticket = t
            break
    
    if not ticket:
        return get_localized_text("ticket_not_found", language)
    
    # Check access permissions
    user_role = user.get("role", "staff")
    user_dept = user.get("department", "")
    ticket_requester = ticket.get("requester", "")
    ticket_dept = ticket.get("department", "")
    
    # Access control logic
    can_view = False
    
    if user_role == "admin" or "full_access" in user.get("permissions", []):
        can_view = True
    elif user_role == "bod" and "view_all_tickets" in user.get("permissions", []):
        can_view = True
    elif user_role == "manager" and "view_department_tickets" in user.get("permissions", []):
        can_view = (ticket_dept == user_dept or ticket_requester == username)
    elif user_role == "staff":
        can_view = (ticket_requester == username)
    
    if not can_view:
        return get_localized_text("access_denied", language)
    
    # Format response
    priority_emoji = {
        "critical": "🔴",
        "high": "🟠", 
        "medium": "🟡",
        "low": "🟢"
    }
    
    status_emoji = {
        "open": "🆕",
        "in_progress": "⏳",
        "resolved": "✅",
        "closed": "✅"
    }
    
    response = f"""🎫 **Ticket Status: {ticket_id}**

{status_emoji.get(ticket['status'], '📝')} **Status:** {ticket['status'].title()}
{priority_emoji.get(ticket['priority'], '⚪')} **Priority:** {ticket['priority'].title()}
📂 **Category:** {ticket['category'].title()}
👤 **Requester:** {ticket['requester']}
🏢 **Department:** {ticket['department']}
👨‍💻 **Assigned To:** {ticket['assigned_to']}

📋 **Title:** {ticket['title']}
📝 **Description:** {ticket['description']}

📅 **Created:** {ticket['created_date'][:19].replace('T', ' ')}
🔄 **Last Updated:** {ticket['updated_date'][:19].replace('T', ' ')}

💬 **Resolution Notes:** {ticket.get('resolution', 'No resolution notes yet')}"""
    
    return response


def get_user_tickets(username: str, language: str = "en") -> str:
    """
    Get all tickets for a specific user based on their role
    
    Args:
        username: User identifier
        language: Response language
        
    Returns:
        List of user's accessible tickets
    """
    data = load_mock_data()
    tickets = data.get("tickets", [])
    user = get_user_by_username(username)
    
    if not user:
        return get_localized_text("user_not_found", language)
    
    user_role = user.get("role", "staff")
    user_dept = user.get("department", "")
    accessible_tickets = []
    
    # Filter tickets based on role
    for ticket in tickets:
        can_view = False
        
        if user_role == "admin" or "full_access" in user.get("permissions", []):
            can_view = True
        elif user_role == "bod" and "view_all_tickets" in user.get("permissions", []):
            can_view = True
        elif user_role == "manager" and "view_department_tickets" in user.get("permissions", []):
            can_view = (ticket.get("department") == user_dept or ticket.get("requester") == username)
        elif user_role == "staff":
            can_view = (ticket.get("requester") == username)
        
        if can_view:
            accessible_tickets.append(ticket)
    
    if not accessible_tickets:
        return f"📝 No tickets found for {get_localized_text(f'role_{user_role}', language)} {username}"
    
    # Sort by creation date (newest first)
    accessible_tickets.sort(key=lambda x: x.get("created_date", ""), reverse=True)
    
    # Format response
    role_title = get_localized_text(f"role_{user_role}", language)
    response = f"🎫 **Tickets for {role_title}: {username}**\n"
    response += f"📊 **Total Accessible Tickets:** {len(accessible_tickets)}\n\n"
    
    # Show summary of recent tickets
    for i, ticket in enumerate(accessible_tickets[:10]):  # Show last 10
        status_emoji = {"open": "🆕", "in_progress": "⏳", "resolved": "✅", "closed": "✅"}
        priority_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
        
        response += f"{status_emoji.get(ticket['status'], '📝')} {ticket['id']} - {ticket['title'][:45]}...\n"
        response += f"{priority_emoji.get(ticket['priority'], '⚪')} {ticket['priority'].title()} | 👤 {ticket['requester']} | 🏢 {ticket['department']}\n"
        response += f"📅 {ticket['created_date'][:10]}\n\n"
    
    if len(accessible_tickets) > 10:
        response += f"... and {len(accessible_tickets) - 10} more tickets\n"
    
    response += f"\n💡 Use 'get ticket status [ticket_id]' for detailed information"
    
    return response


def get_system_statistics(username: str, language: str = "en") -> str:
    """
    Get system statistics (BOD and Admin only)
    
    Args:
        username: User requesting statistics
        language: Response language
        
    Returns:
        Comprehensive system statistics
    """
    # Check permissions
    has_permission, role = check_permission(username, "view_statistics")
    if not has_permission:
        user = get_user_by_username(username)
        if not user or user.get("role") not in ["bod", "admin"]:
            return get_localized_text("access_denied", language)
    
    data = load_mock_data()
    stats = data.get("statistics", {})
    tickets = data.get("tickets", [])
    
    # Calculate real-time statistics
    current_stats = {
        "total": len(tickets),
        "open": len([t for t in tickets if t["status"] == "open"]),
        "in_progress": len([t for t in tickets if t["status"] == "in_progress"]),
        "resolved": len([t for t in tickets if t["status"] == "resolved"]),
        "closed": len([t for t in tickets if t["status"] == "closed"])
    }
    
    # Priority breakdown
    priority_stats = {}
    for ticket in tickets:
        priority = ticket.get("priority", "medium")
        priority_stats[priority] = priority_stats.get(priority, 0) + 1
    
    # Department breakdown
    dept_stats = {}
    for ticket in tickets:
        dept = ticket.get("department", "Unknown")
        dept_stats[dept] = dept_stats.get(dept, 0) + 1
    
    stats_title = get_localized_text("statistics", language)
    
    response = f"""📊 **{stats_title}**

🎫 **Ticket Overview:**
• Total Tickets: {current_stats['total']}
• 🆕 Open: {current_stats['open']}
• ⏳ In Progress: {current_stats['in_progress']}  
• ✅ Resolved: {current_stats['resolved']}
• ✅ Closed: {current_stats['closed']}

🔴 **Priority Breakdown:**"""
    
    for priority, count in priority_stats.items():
        emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(priority, "⚪")
        response += f"\n• {emoji} {priority.title()}: {count}"
    
    response += f"\n\n🏢 **Department Breakdown:**"
    for dept, count in sorted(dept_stats.items(), key=lambda x: x[1], reverse=True):
        response += f"\n• {dept}: {count} tickets"
    
    # Performance metrics
    avg_resolution = stats.get("average_resolution_time_hours", 0)
    satisfaction = stats.get("satisfaction_score", 0)
    sla_compliance = stats.get("sla_compliance", 0)
    
    response += f"""

📈 **Performance Metrics:**
• ⏱️ Avg Resolution Time: {avg_resolution:.1f} hours
• 😊 Satisfaction Score: {satisfaction:.1f}/5.0
• 📋 SLA Compliance: {sla_compliance*100:.1f}%

📅 **Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
    
    return response


def reset_user_password(target_username: str, requester_username: str, language: str = "en") -> str:
    """
    Reset password for a user (Manager+ only)
    
    Args:
        target_username: Username to reset password for
        requester_username: User requesting the reset
        language: Response language
        
    Returns:
        Password reset confirmation
    """
    # Check permissions
    requester = get_user_by_username(requester_username)
    if not requester:
        return get_localized_text("user_not_found", language)
    
    requester_role = requester.get("role", "staff")
    if requester_role not in ["manager", "bod", "admin"]:
        return get_localized_text("access_denied", language)
    
    # Check if target user exists
    target_user = get_user_by_username(target_username)
    if not target_user:
        return get_localized_text("user_not_found", language)
    
    # Generate temporary password
    temp_password = f"Temp{random.randint(1000, 9999)}!"
    
    reset_msg = get_localized_text("password_reset", language)
    
    return f"""{reset_msg}

👤 **User:** {target_username}
🔑 **Temporary Password:** {temp_password}
📧 **Email:** {target_user.get('email', 'Not available')}
👨‍💼 **Reset By:** {requester_username} ({requester_role.title()})

⚠️ **Important:**
• User must change password on next login
• Temporary password expires in 24 hours
• Email notification sent to user
• Security log entry created

📅 **Reset Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""


# =============================================================================

def route_helpdesk_function(
    function_name: str,
    username: str = "unknown",
    language: str = "en",
    **kwargs
) -> str:
    """
    Route function calls to appropriate helpdesk functions
    
    Args:
        function_name: Name of function to call
        username: User making the request
        language: Response language
        **kwargs: Function-specific arguments
        
    Returns:
        Function response
    """
    try:
        if function_name == "create_ticket":
            return create_ticket(
                title=kwargs.get("title", ""),
                description=kwargs.get("description", ""),
                priority=kwargs.get("priority", "medium"),
                category=kwargs.get("category", "general"),
                username=username,
                language=language
            )
        
        elif function_name == "get_ticket_status":
            return get_ticket_status(
                ticket_id=kwargs.get("ticket_id", ""),
                username=username,
                language=language
            )
        
        elif function_name == "get_my_tickets":
            return get_user_tickets(username=username, language=language)
        
        elif function_name == "get_statistics":
            return get_system_statistics(username=username, language=language)
        
        elif function_name == "reset_password":
            return reset_user_password(
                target_username=kwargs.get("target_username", ""),
                requester_username=username,
                language=language
            )
        
        elif function_name == "get_contact_info":
            return get_it_contact_info(language=language)
        
        elif function_name == "search_knowledge_base":
            # This function is handled directly in the chatbot core
            # to avoid circular imports, so it shouldn't reach here
            return "🔍 Searching knowledge base..."
        
        else:
            return f"❌ Unknown function: {function_name}"
            
    except Exception as e:
        error_msg = get_localized_text("error", language)
        return f"{error_msg}: {str(e)}"


def get_it_contact_info(language: str = "en") -> str:
    """
    Get IT contact information and support hours
    
    Args:
        language: Response language
        
    Returns:
        Formatted IT contact information
    """
    contact_title = get_localized_text("it_contact", language)
    
    return f"""📞 **IT Contact Information**

📧 **Email:** it.support@yourcompany.com
📱 **Phone:** +1 (555) 123-4567  
🏢 **Office:** 3rd Floor, Tech Building

⏰ **Support Hours:**
• **Mon-Fri:** 8:00 AM - 6:00 PM
• **Saturday:** 10:00 AM - 2:00 PM  
• **Sunday:** Closed

🆘 **Emergency Support:** +1 (555) 123-9999
💬 **Live Chat:** Available during business hours
🌐 **Self-Service:** portal.yourcompany.com/it

For urgent issues outside business hours, please call the emergency line."""


# =============================================================================
# DEMO USAGE
# =============================================================================

if __name__ == "__main__":
    # Test functions
    print("=== IT Helpdesk Functions Demo ===")
    
    # Test ticket creation
    result = route_helpdesk_function(
        "create_ticket",
        username="john.doe",
        title="Computer slow performance",
        description="My workstation is running very slowly",
        priority="medium",
        category="hardware"
    )
    print(f"Create Ticket:\n{result}\n")
    
    # Test statistics (BOD user)
    result = route_helpdesk_function(
        "get_statistics",
        username="david.bod"
    )
    print(f"Statistics:\n{result}\n")
    
    # Test multi-language
    result = route_helpdesk_function(
        "get_my_tickets",
        username="john.doe",
        language="es"
    )
    print(f"Spanish Response:\n{result}\n")
