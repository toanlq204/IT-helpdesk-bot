import openai
import os
import json
import re


class ChatService:
    def __init__(self, chat_data_path: str = "storage/data/messages.json"):
        self.chat_data_path = chat_data_path
        os.makedirs(os.path.dirname(chat_data_path), exist_ok=True)

        # Define IT-related keywords for topic validation
        self.it_keywords = [
            'computer', 'laptop', 'desktop', 'pc', 'mac', 'windows', 'linux', 'macos',
            'software', 'hardware', 'application', 'program', 'system', 'operating',
            'internet', 'network', 'wifi', 'ethernet', 'connection', 'vpn', 'firewall',
            'email', 'outlook', 'gmail', 'exchange', 'mailbox', 'spam',
            'password', 'login', 'authentication', 'access', 'account', 'user',
            'printer', 'scanner', 'monitor', 'keyboard', 'mouse', 'usb', 'cable',
            'virus', 'malware', 'antivirus', 'security', 'firewall', 'backup',
            'server', 'database', 'cloud', 'storage', 'file', 'folder', 'share',
            'browser', 'chrome', 'firefox', 'edge', 'safari', 'website', 'url',
            'microsoft', 'office', 'word', 'excel', 'powerpoint', 'teams', 'sharepoint',
            'slow', 'freeze', 'crash', 'error', 'bug', 'troubleshoot', 'fix', 'repair',
            'install', 'uninstall', 'update', 'upgrade', 'download', 'configure',
            'helpdesk', 'support', 'ticket', 'issue', 'problem', 'technical'
        ]

        # FAQ patterns and responses
        self.faq_patterns = {
            r'(reset|forgot|change).*(password|pwd)': "To reset your password, visit the internal password reset portal at https://reset.company.com, enter your credentials, and follow the verification steps. Contact IT support at ext. 2200 if you need assistance.",

            r'(slow|freeze|frozen|hang|lag).*(computer|pc|laptop|system)|computer.*(slow|freeze|frozen|hang|lag)': "For slow computer issues: 1) Restart your computer 2) Close unnecessary applications 3) Check disk space (need 15% free) 4) Run antivirus scan 5) Update system and software. Contact IT support if issues persist.",

            r'(vpn|virtual private network).*(connect|setup|install)|connect.*(vpn|virtual private network)': "To connect to company VPN: 1) Open VPN client 2) Enter network credentials 3) Select server location 4) Click 'Connect' 5) Verify connection. Visit IT HelpDesk portal for setup instructions.",

            r'(print|printer).*(not work|fail|error|issue|problem)|printer.*(not working|broken|down)': "For printer issues: 1) Check printer power and 'Ready' status 2) Verify network connection 3) Clear print queue 4) Restart print spooler 5) Update/reinstall drivers. Contact IT support with printer model if problem persists.",

            r'(install|installation).*(software|program|application)|(need|want).*(install|new).*(software|program|application)': "For software installation: 1) Check company software center first 2) If not available, submit software request ticket 3) Provide business justification 4) Wait for IT approval 5) IT will install approved software. Unauthorized installation violates security policies.",

            r'(internet|network|wifi).*(not work|down|slow|connection|problem)|connection.*(internet|network|wifi).*(down|slow|problem)': "For internet issues: 1) Check other devices on network 2) Restart computer and network adapter 3) Check cables/WiFi status 4) Run Network Troubleshooter 5) Flush DNS cache (ipconfig /flushdns). Contact IT support if widespread issue.",

            r'(email|outlook|mail).*(not work|problem|issue|access)|can\'t.*(access|open).*(email|outlook|mail)': "For email issues: 1) Check internet connection 2) Restart email client 3) Verify account settings 4) Check storage quota 5) Clear cache/temporary files. Contact IT support at ext. 2200 for account-specific problems.",

            r'(virus|malware|security).*(scan|remove|detect)|(think|suspect).*(virus|malware)|computer.*(virus|malware|infected)': "For security concerns: 1) Run full antivirus scan immediately 2) Update antivirus definitions 3) Avoid suspicious links/downloads 4) Report suspected malware to IT security team 5) Change passwords if compromised. Contact IT security immediately for serious threats."
        }

    def load_data_messages(self) -> list:
        with open(self.chat_data_path, "r") as f:
            return json.load(f)

    def prepare_messages(self, messages: list) -> list:
        default_messages = self.load_data_messages()
        messages = default_messages + messages
        return messages

    def is_it_related(self, message: str) -> bool:
        """Check if the message is related to IT support topics"""
        message_lower = message.lower()

        # Check for IT-related keywords
        for keyword in self.it_keywords:
            if keyword in message_lower:
                return True

        # Check for common IT question patterns
        it_patterns = [
            r'how\s+(do\s+i|to|can\s+i).*(fix|install|setup|configure|troubleshoot)',
            r'(can\'t|cannot|unable).*(access|login|connect|print|open)',
            r'(my|the).*(computer|laptop|system|software|application).*(not|won\'t|doesn\'t)',
            r'(why|what).*(error|problem|issue|wrong)',
            r'(need\s+help|help\s+with).*(computer|software|system|network|email)'
        ]

        for pattern in it_patterns:
            if re.search(pattern, message_lower):
                return True

        return False

    def check_faq_response(self, message: str) -> str:
        """Check if message matches FAQ patterns and return appropriate response"""
        message_lower = message.lower()

        for pattern, response in self.faq_patterns.items():
            if re.search(pattern, message_lower):
                return response

        return None

    def get_response(self, messages: list) -> str:
        # Get the last user message to check
        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break

        # Check if the question is IT-related
        if not self.is_it_related(user_message):
            return "I'm an IT HelpDesk chatbot and I can only assist with IT-related issues such as computer problems, software troubleshooting, network issues, email problems, password resets, and other technical support matters. For non-IT questions, please contact the appropriate department or resource. How can I help you with your IT-related concerns today?"

        # Check if there's a direct FAQ response
        faq_response = self.check_faq_response(user_message)
        if faq_response:
            return faq_response

        # If IT-related but not in FAQ, use AI with enhanced prompt
        client = openai.OpenAI(
            base_url="https://aiportalapi.stu-platform.live/use",
            api_key="sk-DRKoljlUoP4FtPCOBVy71Q"
        )
        response = client.chat.completions.create(
            model="Gemini-2.5-Flash",
            messages=self.prepare_messages(messages)
        )
        return response.choices[0].message.content
