"""
Setup script for IT Helpdesk Chatbot
Automates environment configuration and validation
"""

import os
import sys
import json
from pathlib import Path


def create_env_template():
    """Create .env template file"""
    env_template = """# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here

# Optional: Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/helpdesk.log

# Optional: Feature Flags
ENABLE_ANALYTICS=True
ENABLE_DEBUG_MODE=False
"""

    with open('.env.template', 'w') as f:
        f.write(env_template)
    print("✅ Created .env.template file")


def create_sample_env():
    """Create sample environment file if not exists"""
    if not os.path.exists('.env'):
        create_env_template()
        print("📝 Please copy .env.template to .env and configure your Azure OpenAI credentials")
    else:
        print("✅ .env file already exists")


def validate_directories():
    """Ensure all required directories exist"""
    required_dirs = [
        'data', 'functions', 'interface', 'prompts',
        'tests', 'config', 'docs', 'logs'
    ]

    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"📁 Created directory: {dir_name}")
        else:
            print(f"✅ Directory exists: {dir_name}")


def validate_data_files():
    """Validate that data files have correct structure"""

    # Validate FAQs structure
    try:
        with open('data/faqs.json', 'r') as f:
            faqs = json.load(f)
            if 'faqs' in faqs and isinstance(faqs['faqs'], list):
                print("✅ FAQs data structure is valid")
            else:
                print("❌ FAQs data structure is invalid")
    except Exception as e:
        print(f"❌ Error validating FAQs: {e}")

    # Validate tickets structure
    try:
        with open('data/mock_tickets.json', 'r') as f:
            tickets = json.load(f)
            if 'tickets' in tickets and isinstance(tickets['tickets'], list):
                print("✅ Tickets data structure is valid")
            else:
                print("❌ Tickets data structure is invalid")
    except Exception as e:
        print(f"❌ Error validating tickets: {e}")


def check_dependencies():
    """Check if required Python packages are installed"""
    required_packages = [
        'openai',
        'python-dotenv',
        'requests',
        'datetime'
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} is missing")

    if missing_packages:
        print(f"\n📦 Install missing packages with:")
        print(f"pip install {' '.join(missing_packages)}")
        return False

    return True


def validate_azure_config():
    """Validate Azure OpenAI configuration"""
    endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    api_key = os.getenv('AZURE_OPENAI_API_KEY')

    if not endpoint:
        print("❌ AZURE_OPENAI_ENDPOINT not set")
        return False

    if not api_key:
        print("❌ AZURE_OPENAI_API_KEY not set")
        return False

    if not endpoint.startswith('https://'):
        print("❌ AZURE_OPENAI_ENDPOINT should start with https://")
        return False

    print("✅ Azure OpenAI configuration appears valid")
    return True


def create_launch_script():
    """Create convenient launch script"""

    # Windows batch file
    windows_script = """@echo off
echo Starting IT Helpdesk Chatbot...
python main.py
pause
"""

    with open('start_windows.bat', 'w') as f:
        f.write(windows_script)

    # Unix shell script
    unix_script = """#!/bin/bash
echo "Starting IT Helpdesk Chatbot..."
python3 main.py
"""

    with open('start_unix.sh', 'w') as f:
        f.write(unix_script)

    # Make Unix script executable
    os.chmod('start_unix.sh', 0o755)

    print("✅ Created launch scripts (start_windows.bat, start_unix.sh)")


def run_basic_tests():
    """Run basic functionality tests"""
    print("\n🧪 Running basic tests...")

    try:
        # Test function imports
        from functions.helpdesk_functions import reset_password, check_ticket_status
        print("✅ Function imports successful")

        # Test basic function calls
        result = reset_password("test@company.com")
        if "reset" in result.lower():
            print("✅ Password reset function working")

        result = check_ticket_status("TKT001")
        if "ticket" in result.lower():
            print("✅ Ticket status function working")

    except Exception as e:
        print(f"❌ Basic tests failed: {e}")
        return False

    return True


def main():
    """Main setup routine"""
    print("🚀 IT Helpdesk Chatbot Setup")
    print("=" * 40)

    # Create environment
    create_sample_env()

    # Validate structure
    validate_directories()
    validate_data_files()

    # Check dependencies
    if not check_dependencies():
        print("\n❌ Setup incomplete - install missing dependencies first")
        return

    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("💡 Install python-dotenv for .env file support: pip install python-dotenv")

    # Validate configuration
    azure_valid = validate_azure_config()

    # Create convenience scripts
    create_launch_script()

    # Run tests
    tests_passed = run_basic_tests()

    # Summary
    print("\n📋 SETUP SUMMARY")
    print("=" * 40)

    if azure_valid and tests_passed:
        print("✅ Setup completed successfully!")
        print("🎯 Ready to run: python main.py")
    else:
        print("⚠️  Setup completed with warnings")
        if not azure_valid:
            print("   - Configure Azure OpenAI credentials in .env")
        if not tests_passed:
            print("   - Fix test failures before running")

    print("\n📖 Next steps:")
    print("1. Configure .env file with your Azure OpenAI credentials")
    print("2. Run: python main.py")
    print("3. Test with sample queries")
    print("4. Customize data/faqs.json for your organization")


if __name__ == "__main__":
    main()
