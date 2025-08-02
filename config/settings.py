"""
Configuration settings for IT Helpdesk Chatbot
"""

import os
from typing import Dict, List

# Azure OpenAI Configuration
AZURE_OPENAI_CONFIG = {
    "api_version": "2024-07-01-preview",
    "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
    "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
    "model": "gpt-4o-mini",
    "temperature": 0.7,
    "max_tokens": 1000
}

# Ticket System Configuration
TICKET_CONFIG = {
    "id_prefix": "TKT",
    "priority_levels": ["low", "medium", "high", "critical"],
    "categories": ["hardware", "software", "network", "authentication", "email", "other"],
    "statuses": ["open", "in_progress", "pending_approval", "resolved", "closed"],
    "auto_assignment": "auto_assignment",
    "escalation_threshold_hours": 24
}

# Service Level Agreements (SLA)
SLA_CONFIG = {
    "response_times": {
        "critical": "30 minutes",
        "high": "2 hours",
        "medium": "8 hours",
        "low": "24 hours"
    },
    "resolution_times": {
        "authentication": {
            "critical": "30 minutes",
            "high": "1 hour",
            "medium": "2 hours",
            "low": "4 hours"
        },
        "hardware": {
            "critical": "4 hours",
            "high": "8 hours",
            "medium": "1 day",
            "low": "3 days"
        },
        "software": {
            "critical": "4 hours",
            "high": "8 hours",
            "medium": "1 day",
            "low": "2 days"
        },
        "network": {
            "critical": "1 hour",
            "high": "2 hours",
            "medium": "4 hours",
            "low": "8 hours"
        }
    }
}

# System Status Configuration
SYSTEM_SERVICES = {
    "email": {
        "name": "Email Service",
        "description": "Microsoft Exchange Server",
        "critical": True
    },
    "vpn": {
        "name": "VPN Service",
        "description": "Remote Access VPN",
        "critical": True
    },
    "wifi": {
        "name": "WiFi Network",
        "description": "Corporate Wireless Network",
        "critical": False
    },
    "servers": {
        "name": "Application Servers",
        "description": "Core Business Applications",
        "critical": True
    }
}

# Contact Information
CONTACT_INFO = {
    "it_support": "ext. 4357",
    "emergency": "ext. 911",
    "security_team": "ext. 4444",
    "network_ops": "ext. 5555",
    "manager_oncall": "ext. 6666",
    "email_support": "itsupport@company.com",
    "emergency_email": "emergency@company.com"
}

# Knowledge Base Configuration
KNOWLEDGE_BASE_CONFIG = {
    "search_limit": 3,
    "categories": ["authentication", "performance", "network", "software", "hardware", "remote_access", "general"],
    "enable_fuzzy_search": True,
    "min_search_length": 2
}

# Security Configuration
SECURITY_CONFIG = {
    "enable_logging": True,
    "log_level": "INFO",
    "mask_sensitive_data": True,
    "session_timeout_minutes": 30,
    "max_message_length": 2000
}

# Feature Flags
FEATURE_FLAGS = {
    "enable_function_calling": True,
    "enable_knowledge_base": True,
    "enable_ticket_creation": True,
    "enable_system_status": True,
    "enable_escalation": True,
    "enable_batch_processing": False,  # Future feature
    "enable_voice_interface": False,   # Future feature
    "enable_analytics": True
}


def get_config(section: str) -> Dict:
    """Get configuration for a specific section"""
    config_map = {
        "azure": AZURE_OPENAI_CONFIG,
        "ticket": TICKET_CONFIG,
        "sla": SLA_CONFIG,
        "services": SYSTEM_SERVICES,
        "contact": CONTACT_INFO,
        "knowledge": KNOWLEDGE_BASE_CONFIG,
        "security": SECURITY_CONFIG,
        "features": FEATURE_FLAGS
    }
    return config_map.get(section, {})


def validate_config() -> List[str]:
    """Validate configuration and return list of issues"""
    issues = []

    # Check Azure OpenAI credentials
    if not AZURE_OPENAI_CONFIG["endpoint"]:
        issues.append("AZURE_OPENAI_ENDPOINT environment variable not set")
    if not AZURE_OPENAI_CONFIG["api_key"]:
        issues.append("AZURE_OPENAI_API_KEY environment variable not set")

    # Check required directories exist
    required_dirs = ["data", "functions", "prompts", "interface", "tests"]
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            issues.append(f"Required directory '{dir_name}' not found")

    return issues
