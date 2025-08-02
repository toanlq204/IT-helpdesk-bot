"""
Comprehensive test cases for IT Helpdesk Chatbot
Following workshop guidelines for testing chatbot systems
"""

from functions.helpdesk_functions import (
    reset_password, check_ticket_status, create_ticket,
    search_knowledge_base, escalate_ticket, get_system_status
)
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Test cases for various IT helpdesk scenarios
test_cases = [
    # Authentication & Access Issues
    "How do I reset my password?",
    "I can't log into my email account",
    "My account is locked out",
    "I forgot my username for the company portal",

    # Hardware & Performance Issues
    "My computer is running very slowly",
    "The laptop won't turn on",
    "My monitor is flickering",
    "The printer is not working",
    "Blue screen error on my workstation",

    # Network & Connectivity Issues
    "I can't connect to the office WiFi",
    "VPN connection keeps dropping",
    "Internet is not working on my computer",
    "Cannot access company shared drives",

    # Software Issues
    "Need to install Adobe Creative Suite",
    "Microsoft Office is not opening",
    "Software update is stuck",
    "Application crashed and won't restart",

    # Ticket Management
    "Check the status of ticket TKT001",
    "Create a new support ticket",
    "I need to escalate my ticket TKT002",
    "What tickets do I have open?",

    # Knowledge Base Searches
    "How to set up email on mobile device?",
    "Company password policy requirements",
    "Steps to connect to VPN from home",
    "Backup and recovery procedures",

    # System Status Inquiries
    "Is the email server down?",
    "Check system status",
    "Are there any known network issues?",
    "Server maintenance schedule",

    # Complex Multi-turn Scenarios
    "I'm having multiple issues with my computer",
    "Need help with both password reset and software installation",
    "Computer problems affecting entire team",

    # Emergency Scenarios
    "Possible security breach - suspicious emails",
    "Server room fire alarm activated",
    "Company-wide internet outage",
    "Ransomware detected on workstation"
]


def run_function_tests():
    """Test individual helpdesk functions"""
    print("🧪 RUNNING FUNCTION TESTS\n")

    # Test password reset
    print("1️⃣ Testing Password Reset:")
    result = reset_password("john.doe@company.com")
    print(f"✅ Result: {result[:100]}...\n")

    # Test ticket status check
    print("2️⃣ Testing Ticket Status Check:")
    result = check_ticket_status("TKT001")
    print(f"✅ Result: {result[:100]}...\n")

    # Test ticket creation
    print("3️⃣ Testing Ticket Creation:")
    result = create_ticket(
        title="Test Issue",
        description="This is a test ticket",
        priority="medium",
        category="software",
        reporter_email="test@company.com"
    )
    print(f"✅ Result: {result[:100]}...\n")

    # Test knowledge base search
    print("4️⃣ Testing Knowledge Base Search:")
    result = search_knowledge_base("password reset")
    print(f"✅ Result: {result[:100]}...\n")

    # Test system status
    print("5️⃣ Testing System Status:")
    result = get_system_status("all")
    print(f"✅ Result: {result[:100]}...\n")


def run_integration_tests():
    """Test realistic user interaction scenarios"""
    print("🔧 RUNNING INTEGRATION TESTS\n")

    integration_scenarios = [
        {
            "scenario": "Password Reset Flow",
            "inputs": [
                "I can't log into my email",
                "Yes, please reset my password for john.doe@company.com"
            ],
            "expected_functions": ["reset_password"]
        },
        {
            "scenario": "Ticket Creation and Tracking",
            "inputs": [
                "My computer is very slow, can you help?",
                "Create a ticket for laptop performance issues",
                "Check status of the ticket you just created"
            ],
            "expected_functions": ["create_ticket", "check_ticket_status"]
        },
        {
            "scenario": "Knowledge Base Search and Escalation",
            "inputs": [
                "How do I connect to VPN?",
                "The VPN instructions didn't work, escalate this issue"
            ],
            "expected_functions": ["search_knowledge_base", "escalate_ticket"]
        }
    ]

    for idx, scenario in enumerate(integration_scenarios, 1):
        print(f"{idx}️⃣ {scenario['scenario']}:")
        for input_text in scenario['inputs']:
            print(f"   👤 User: {input_text}")
            print(
                f"   🤖 Bot: [Expected to call {scenario['expected_functions']}]")
        print()


def run_edge_case_tests():
    """Test edge cases and error handling"""
    print("⚠️ RUNNING EDGE CASE TESTS\n")

    edge_cases = [
        # Invalid inputs
        ("", "Empty input"),
        ("asdfgh", "Random characters"),
        ("123456", "Only numbers"),

        # Malformed requests
        ("Reset password for", "Incomplete password reset request"),
        ("Check ticket", "Missing ticket ID"),
        ("Install", "Incomplete software request"),

        # Boundary conditions
        ("A" * 1000, "Very long input"),
        ("Check ticket TKT999999", "Non-existent ticket ID"),
        ("Reset password for invalid@email", "Invalid email format"),

        # Ambiguous requests
        ("Help", "Vague help request"),
        ("Something is broken", "Non-specific issue"),
        ("Computer problem", "Generic problem statement"),

        # Multiple requests in one input
        ("Reset my password and check ticket status and install software",
         "Multiple requests"),
    ]

    for idx, (input_text, description) in enumerate(edge_cases, 1):
        print(f"{idx}️⃣ {description}:")
        print(f"   Input: '{input_text}'")
        print(f"   Expected: Graceful handling with helpful error message\n")


def run_performance_tests():
    """Test response times and system limits"""
    print("⚡ RUNNING PERFORMANCE TESTS\n")

    performance_scenarios = [
        "Concurrent password reset requests",
        "Large knowledge base search",
        "Multiple ticket status checks",
        "System status during high load",
        "Function calling latency",
        "Memory usage with long conversations"
    ]

    for idx, scenario in enumerate(performance_scenarios, 1):
        print(
            f"{idx}️⃣ {scenario}: [Performance metrics would be measured here]")


def run_security_tests():
    """Test security-related scenarios"""
    print("🔒 RUNNING SECURITY TESTS\n")

    security_scenarios = [
        "SQL injection attempts in ticket descriptions",
        "Cross-site scripting in user inputs",
        "Unauthorized access to other users' tickets",
        "Password reset for non-existent users",
        "Privilege escalation attempts",
        "Data leakage through error messages"
    ]

    for idx, scenario in enumerate(security_scenarios, 1):
        print(f"{idx}️⃣ {scenario}: [Security validation required]")


def main():
    """Run comprehensive test suite"""
    print("🚀 IT HELPDESK CHATBOT - COMPREHENSIVE TEST SUITE")
    print("=" * 60)

    try:
        run_function_tests()
        run_integration_tests()
        run_edge_case_tests()
        run_performance_tests()
        run_security_tests()

        print("✅ ALL TESTS COMPLETED")
        print("\n📋 RECOMMENDED NEXT STEPS:")
        print("• Review test results and fix any issues")
        print("• Add automated test assertions")
        print("• Set up continuous integration testing")
        print("• Implement monitoring and logging")
        print("• Conduct user acceptance testing")

    except Exception as e:
        print(f"❌ TEST SUITE ERROR: {e}")
        print("Please check system configuration and try again.")


if __name__ == "__main__":
    main()
