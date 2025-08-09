#!/usr/bin/env python3

import os
import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging
import re
from difflib import SequenceMatcher
import threading

# File monitoring
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    print("Watchdog not available. File monitoring disabled.")

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # If python-dotenv is not installed, continue without it
    pass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KnowledgeBaseWatcher(FileSystemEventHandler):
    """File system event handler for knowledge base changes"""
    
    def __init__(self, chatbot_instance):
        super().__init__()
        self.chatbot = chatbot_instance
        self.last_reload = datetime.now()
        self.reload_delay = 2  # seconds to wait before reloading
        
    def on_modified(self, event):
        """Handle file modification events"""
        if not event.is_directory and event.src_path.endswith('.json'):
            self._schedule_reload("modified", event.src_path)
    
    def on_created(self, event):
        """Handle file creation events"""
        if not event.is_directory and event.src_path.endswith('.json'):
            self._schedule_reload("created", event.src_path)
    
    def on_deleted(self, event):
        """Handle file deletion events"""
        if not event.is_directory and event.src_path.endswith('.json'):
            self._schedule_reload("deleted", event.src_path)
    
    def _schedule_reload(self, action, file_path):
        """Schedule knowledge base reload with debouncing"""
        now = datetime.now()
        
        # Debounce rapid file changes
        if (now - self.last_reload).total_seconds() < self.reload_delay:
            return
            
        self.last_reload = now
        filename = os.path.basename(file_path)
        
        # Skip backup files
        if filename.startswith('backup_'):
            return
        
        logger.info(f"Knowledge base file {action}: {filename}")
        
        # Schedule reload in a separate thread to avoid blocking
        threading.Timer(self.reload_delay, self._perform_reload).start()
    
    def _perform_reload(self):
        """Perform the actual knowledge base reload"""
        try:
            success = self.chatbot.reload_knowledge_base()
            if success:
                logger.info("✅ Knowledge base automatically reloaded due to file changes")
            else:
                logger.error("❌ Failed to reload knowledge base after file changes")
        except Exception as e:
            logger.error(f"Error during automatic knowledge base reload: {e}")

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # If python-dotenv is not installed, continue without it
    pass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from openai import AzureOpenAI
    AZURE_AVAILABLE = True
except ImportError:
    logger.warning("Azure OpenAI not available. Using fallback responses.")
    AZURE_AVAILABLE = False

# Import enhanced function modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from functions.helpdesk_functions import (
    route_helpdesk_function, detect_user_language, get_localized_text,
    get_user_by_username, check_permission, load_mock_data
)

# Import conversation thread management
from conversation_threads import thread_manager, ConversationThread

# Import ChromaDB Knowledge Base Manager
try:
    from .chroma_kb_manager import ChromaKnowledgeBaseManager
    CHROMA_KB_AVAILABLE = True
except ImportError:
    CHROMA_KB_AVAILABLE = False
    logger.warning("ChromaDB Knowledge Base Manager not available")
    ChromaKnowledgeBaseManager = None


class EnhancedITHelpdeskBot:
    """
    Enhanced IT Helpdesk Bot with Multi-Language & Role-Based Access
    
    Provides intelligent IT support with:
    - Multi-language detection and responses
    - Role-based permission checking
    - Advanced function calling with authentication
    - Context-aware conversations with user preferences
    - Enterprise-grade ticket management
    """
    
    def __init__(self):
        """Initialize the enhanced helpdesk bot"""
        
        # Azure OpenAI Configuration
        self.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        self.azure_key = os.getenv("AZURE_OPENAI_API_KEY", "")
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        
        # Initialize Azure OpenAI client
        self.client = None
        print(f"🔍 Azure OpenAI Debug:")
        print(f"  AZURE_AVAILABLE: {AZURE_AVAILABLE}")
        print(f"  azure_endpoint: {bool(self.azure_endpoint)} ({self.azure_endpoint[:30]}...)" if self.azure_endpoint else "  azure_endpoint: False")
        print(f"  azure_key: {bool(self.azure_key)} (length: {len(self.azure_key)})" if self.azure_key else "  azure_key: False")
        
        if AZURE_AVAILABLE and self.azure_endpoint and self.azure_key:
            try:
                print(f"🔧 Attempting to create Azure OpenAI client...")
                self.client = AzureOpenAI(
                    azure_endpoint=self.azure_endpoint,
                    api_key=self.azure_key,
                    api_version=self.api_version
                )
                print("✅ Azure OpenAI client initialized successfully")
                logger.info("Enhanced Azure OpenAI client initialized successfully")
            except Exception as e:
                print(f"❌ Failed to initialize Azure OpenAI client: {e}")
                logger.error(f"Failed to initialize Azure OpenAI client: {e}")
                self.client = None
        else:
            print("❌ Azure OpenAI not available - missing configuration")
            if not AZURE_AVAILABLE:
                print("  - Azure OpenAI library not available")
            if not self.azure_endpoint:
                print("  - Missing AZURE_OPENAI_ENDPOINT")
            if not self.azure_key:
                print("  - Missing AZURE_OPENAI_API_KEY")
        
        # Multi-session conversation management with persistent threads
        self.conversations: Dict[str, List[Dict[str, Any]]] = {}  # Legacy in-memory storage
        self.user_preferences: Dict[str, Dict[str, Any]] = {}
        
        # Thread management integration
        self.thread_manager = thread_manager
        
        # Available function mappings with descriptions
        self.function_mappings = {
            "create_ticket": {
                "keywords": ["create", "new", "ticket", "issue", "problem", "report"],
                "description": "Create a new support ticket",
                "permission": "create_ticket"
            },
            "get_ticket_status": {
                "keywords": ["status", "check", "ticket", "update"],
                "description": "Check ticket status",
                "permission": "view_tickets"
            },
            "get_my_tickets": {
                "keywords": ["my", "tickets", "list", "history"],
                "description": "View user's tickets",
                "permission": "view_tickets"
            },
            "get_statistics": {
                "keywords": ["statistics", "stats", "metrics", "report", "analytics"],
                "description": "View system statistics",
                "permission": "view_statistics"
            },
            "reset_password": {
                "keywords": ["reset", "password", "forgot", "change"],
                "description": "Reset user password",
                "permission": "password_reset"
            },
            "get_contact_info": {
                "keywords": ["contact", "phone", "email", "hours", "support", "help", "reach"],
                "description": "Get IT contact information",
                "permission": "basic_access"
            },
            "search_knowledge_base": {
                "keywords": ["search", "faq", "knowledge", "how to", "help with", "solution"],
                "description": "Search knowledge base for solutions",
                "permission": "basic_access"
            }
        }
        
        # Load system prompt
        self.system_prompt = self._load_enhanced_system_prompt()
        
        # Initialize ChromaDB Knowledge Base Manager
        self.chroma_kb = None
        if CHROMA_KB_AVAILABLE and ChromaKnowledgeBaseManager:
            try:
                print("🔧 Initializing ChromaDB Knowledge Base...")
                self.chroma_kb = ChromaKnowledgeBaseManager()
                
                if self.chroma_kb.is_initialized:
                    print("✅ ChromaDB Knowledge Base initialized successfully")
                    # Load initial knowledge base into ChromaDB
                    self._initialize_chroma_knowledge_base()
                else:
                    print("❌ ChromaDB Knowledge Base failed to initialize")
                    self.chroma_kb = None
            except Exception as e:
                print(f"❌ Error initializing ChromaDB: {e}")
                logger.error(f"Error initializing ChromaDB: {e}")
                self.chroma_kb = None
        else:
            print("❌ ChromaDB not available - using legacy knowledge base")
        
        # Load legacy knowledge base (fallback)
        self.knowledge_base = self._load_knowledge_base()
        
        # Initialize file monitoring for automatic reload
        self.file_observer = None
        self.file_watcher = None
        if WATCHDOG_AVAILABLE:
            self._start_file_monitoring()
        else:
            logger.info("File monitoring not available - knowledge base will not auto-reload")
    
    def _start_file_monitoring(self):
        """Start monitoring the knowledge base directory for changes"""
        try:
            kb_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "kb")
            
            if not os.path.exists(kb_dir):
                logger.warning(f"Knowledge base directory not found for monitoring: {kb_dir}")
                return
                
            self.file_watcher = KnowledgeBaseWatcher(self)
            self.file_observer = Observer()
            self.file_observer.schedule(self.file_watcher, kb_dir, recursive=False)
            self.file_observer.start()
            
            logger.info(f"📁 Started monitoring knowledge base directory: {kb_dir}")
            
        except Exception as e:
            logger.error(f"Failed to start file monitoring: {e}")
            self.file_observer = None
            self.file_watcher = None
    
    def _stop_file_monitoring(self):
        """Stop file monitoring"""
        if self.file_observer:
            self.file_observer.stop()
            self.file_observer.join()
            self.file_observer = None
            self.file_watcher = None
            logger.info("📁 Stopped knowledge base file monitoring")
    
    def __del__(self):
        """Cleanup when bot instance is destroyed"""
        self._stop_file_monitoring()
    
    def _initialize_chroma_knowledge_base(self):
        """Initialize ChromaDB with existing knowledge base files"""
        if not self.chroma_kb or not self.chroma_kb.is_initialized:
            return
        
        try:
            kb_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "kb")
            
            if os.path.exists(kb_dir):
                logger.info("🔄 Loading knowledge base into ChromaDB...")
                result = self.chroma_kb.reload_from_directory(kb_dir)
                
                if result["success"]:
                    logger.info(f"✅ ChromaDB loaded: {result['files_loaded']} files, {result['total_items']} items")
                else:
                    logger.error(f"❌ Failed to load ChromaDB: {result.get('error', 'Unknown error')}")
            else:
                logger.warning("Knowledge base directory not found for ChromaDB initialization")
                
        except Exception as e:
            logger.error(f"Error initializing ChromaDB knowledge base: {e}")
    
    def get_chroma_status(self) -> Dict[str, Any]:
        """Get ChromaDB status information"""
        if not self.chroma_kb:
            return {
                "available": False,
                "status": "not_initialized",
                "error": "ChromaDB not available"
            }
        
        return self.chroma_kb.get_status()
    
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load all knowledge base files from data/kb folder"""
        try:
            kb_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "kb")
            
            if not os.path.exists(kb_dir):
                logger.warning(f"Knowledge base directory not found: {kb_dir}")
                return {"faqs": [], "knowledge_base": {}}
            
            # Initialize combined knowledge base
            combined_kb = {
                "faqs": [],
                "troubleshooting_guides": {},
                "quick_solutions": {},
                "emergency_contacts": {},
                "system_requirements": {},
                "security_guidelines": {},
                "escalation_guidelines": {},
                "feedback_collection": {},
                "knowledge_base": {
                    "version": "combined",
                    "last_updated": datetime.now().strftime('%Y-%m-%d'),
                    "total_files": 0,
                    "total_articles": 0
                }
            }
            
            files_loaded = 0
            total_faqs = 0
            
            # Load all JSON files in the kb directory
            for filename in os.listdir(kb_dir):
                if filename.endswith('.json') and not filename.startswith('backup_'):
                    file_path = os.path.join(kb_dir, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            kb_data = json.load(f)
                            files_loaded += 1
                            
                            # Merge FAQs
                            if "faqs" in kb_data:
                                faqs = kb_data["faqs"]
                                if isinstance(faqs, list):
                                    combined_kb["faqs"].extend(faqs)
                                    total_faqs += len(faqs)
                            
                            # Merge other knowledge base sections
                            for section in ["troubleshooting_guides", "quick_solutions", "emergency_contacts", 
                                          "system_requirements", "security_guidelines", "escalation_guidelines", "feedback_collection"]:
                                if section in kb_data:
                                    if isinstance(kb_data[section], dict):
                                        combined_kb[section].update(kb_data[section])
                                    
                            # Update knowledge_base metadata if present
                            if "knowledge_base" in kb_data:
                                kb_meta = kb_data["knowledge_base"]
                                if isinstance(kb_meta, dict):
                                    # Merge categories
                                    if "categories" in kb_meta:
                                        existing_categories = combined_kb["knowledge_base"].get("categories", [])
                                        new_categories = kb_meta["categories"]
                                        if isinstance(new_categories, list):
                                            combined_kb["knowledge_base"]["categories"] = list(set(existing_categories + new_categories))
                                    
                                    # Merge language support
                                    if "language_support" in kb_meta:
                                        existing_langs = combined_kb["knowledge_base"].get("language_support", [])
                                        new_langs = kb_meta["language_support"]
                                        if isinstance(new_langs, list):
                                            combined_kb["knowledge_base"]["language_support"] = list(set(existing_langs + new_langs))
                                    
                                    # Update other metadata
                                    for key in ["search_enabled", "auto_suggest"]:
                                        if key in kb_meta:
                                            combined_kb["knowledge_base"][key] = kb_meta[key]
                            
                            logger.info(f"Loaded knowledge base file: {filename}")
                            
                    except Exception as e:
                        logger.error(f"Error loading knowledge base file {filename}: {e}")
                        continue
            
            # Update final metadata
            combined_kb["knowledge_base"]["total_files"] = files_loaded
            combined_kb["knowledge_base"]["total_articles"] = total_faqs
            
            # Remove duplicates from FAQs based on ID
            seen_ids = set()
            unique_faqs = []
            for faq in combined_kb["faqs"]:
                faq_id = faq.get("id")
                if faq_id not in seen_ids:
                    seen_ids.add(faq_id)
                    unique_faqs.append(faq)
            combined_kb["faqs"] = unique_faqs
            combined_kb["knowledge_base"]["total_articles"] = len(unique_faqs)
            
            logger.info(f"Successfully loaded knowledge base: {files_loaded} files, {len(unique_faqs)} unique FAQs")
            return combined_kb
            
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")
            return {"faqs": [], "knowledge_base": {}}
    
    def reload_knowledge_base(self) -> bool:
        """Reload knowledge base from all files in data/kb folder (thread-safe) with ChromaDB sync"""
        try:
            # Use a lock to prevent concurrent reloads
            if not hasattr(self, '_reload_lock'):
                self._reload_lock = threading.Lock()
                
            with self._reload_lock:
                old_count = len(self.knowledge_base.get("faqs", []))
                
                # Reload legacy knowledge base
                self.knowledge_base = self._load_knowledge_base()
                new_count = len(self.knowledge_base.get("faqs", []))
                
                # Sync with ChromaDB if available
                if self.chroma_kb and self.chroma_kb.is_initialized:
                    try:
                        kb_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "kb")
                        chroma_result = self.chroma_kb.reload_from_directory(kb_dir)
                        
                        if chroma_result["success"]:
                            logger.info(f"✅ ChromaDB reloaded: {chroma_result['total_items']} items")
                        else:
                            logger.error(f"❌ ChromaDB reload failed: {chroma_result.get('error')}")
                            
                    except Exception as e:
                        logger.error(f"Error syncing with ChromaDB during reload: {e}")
                
                if new_count != old_count:
                    logger.info(f"Knowledge base reloaded: {old_count} → {new_count} FAQs")
                else:
                    logger.info("Knowledge base reloaded successfully")
                    
                return True
        except Exception as e:
            logger.error(f"Error reloading knowledge base: {e}")
            return False
    
    def force_reload_knowledge_base(self) -> Dict[str, Any]:
        """Force reload knowledge base and return detailed status"""
        try:
            kb_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "kb")
            
            # Get file information
            files_info = []
            if os.path.exists(kb_dir):
                for filename in os.listdir(kb_dir):
                    if filename.endswith('.json') and not filename.startswith('backup_'):
                        file_path = os.path.join(kb_dir, filename)
                        stat = os.stat(file_path)
                        files_info.append({
                            "filename": filename,
                            "size": stat.st_size,
                            "modified": datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                        })
            
            # Reload knowledge base
            old_info = self.get_knowledge_base_info()
            success = self.reload_knowledge_base()
            new_info = self.get_knowledge_base_info()
            
            return {
                "success": success,
                "files_found": len(files_info),
                "files_info": files_info,
                "old_stats": old_info,
                "new_stats": new_info,
                "reload_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "reload_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def get_knowledge_base_info(self) -> Dict[str, Any]:
        """Get comprehensive information about the current knowledge base including ChromaDB status"""
        kb_meta = self.knowledge_base.get("knowledge_base", {})
        
        # Base legacy information
        info = {
            "legacy_kb": {
                "total_files": kb_meta.get("total_files", 0),
                "total_faqs": len(self.knowledge_base.get("faqs", [])),
                "total_troubleshooting_guides": len(self.knowledge_base.get("troubleshooting_guides", {})),
                "total_quick_solutions": len(self.knowledge_base.get("quick_solutions", {})),
                "version": kb_meta.get("version", "unknown"),
                "last_updated": kb_meta.get("last_updated", "unknown"),
                "categories": kb_meta.get("categories", []),
                "language_support": kb_meta.get("language_support", [])
            }
        }
        
        # Add ChromaDB information if available
        if self.chroma_kb:
            info["chroma_db"] = self.chroma_kb.get_status()
            
            if self.chroma_kb.is_initialized:
                try:
                    info["chroma_db"]["stats"] = self.chroma_kb.get_collection_stats()
                    info["chroma_db"]["categories"] = self.chroma_kb.get_categories()
                except Exception as e:
                    info["chroma_db"]["stats_error"] = str(e)
        else:
            info["chroma_db"] = {
                "available": False,
                "status": "not_available",
                "error": "ChromaDB not initialized"
            }
        
        return info
    
    def _load_enhanced_system_prompt(self) -> str:
        """Load enhanced system prompt with multi-language and role awareness"""
        return """You are an Advanced IT Support Assistant for a multinational corporate environment.

CORE CAPABILITIES:
🌍 Multi-Language Support: Detect user language and respond appropriately (EN, ES, FR, DE, PT, ZH, JA)
👥 Role-Based Access: Respect user permissions (Staff, Manager, BOD, Admin)
🎫 Ticket Management: Create, track, and manage support tickets
📊 Analytics: Provide statistics and reports based on user role
🔐 Security: Handle password resets and user management
📁 Data Management: Admin-level data upload and system management
📚 Knowledge Base: Search and provide answers from comprehensive FAQ database

ROLE PERMISSIONS:
• Staff: Create tickets, view own tickets, basic support
• Manager: Department tickets, password resets, team statistics  
• BOD: All tickets, system statistics, advanced reporting
• Admin: Full system access, data management, user administration

LANGUAGE HANDLING:
- Detect user language from input patterns
- Respond in detected language or user preference
- Support context switching between languages
- Maintain professional tone in all languages

FUNCTION CALLING:
Use route_helpdesk_function(function_name, username, language, **kwargs) for:
- create_ticket(title, description, priority, category)
- get_ticket_status(ticket_id)
- get_my_tickets()
- get_statistics()
- reset_password(target_username)

KNOWLEDGE BASE INTEGRATION:
- Knowledge base information is provided in your context when available
- Use KB information to enhance your responses, don't just copy-paste
- Provide conversational, contextual responses that incorporate KB data naturally
- If KB has relevant solutions, present them in a helpful, personalized way
- Always offer additional assistance beyond just KB information
- Combine KB solutions with conversational guidance and follow-up options

CONVERSATION FLOW GUIDELINES:
1. ALWAYS maintain conversation context and reference previous messages when relevant
2. Use conversational continuity phrases like:
   - "Following up on your earlier request..."
   - "As we discussed..."
   - "Continuing from where we left off..."
   - "Regarding your previous question about..."
3. Remember user preferences and choices from the current conversation
4. Build upon previous information rather than starting fresh
5. Acknowledge when continuing or completing previous actions
6. Reference specific details mentioned earlier in the conversation
7. Adapt responses based on conversation history and user patterns

RESPONSE GUIDELINES:
1. Always be professional and culturally appropriate
2. Detect and adapt to user's language preference
3. Check user permissions before function calls
4. Provide role-appropriate information and options
5. Use clear, concise responses with helpful formatting
6. Escalate complex issues appropriately
7. Maintain conversation context across ALL interactions
8. Show awareness of conversation history in your responses
9. Check knowledge base first for quick self-service solutions

Current datetime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    def search_knowledge_base(self, query: str, max_results: int = 3, category_filter: str = None) -> List[Dict[str, Any]]:
        """
        Search knowledge base for relevant FAQs using ChromaDB (with legacy fallback)
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            category_filter: Optional category filter
            
        Returns:
            List of relevant FAQs with similarity scores
        """
        # Try ChromaDB first (semantic search)
        if self.chroma_kb and self.chroma_kb.is_initialized:
            try:
                logger.info(f"🔍 Searching ChromaDB for: '{query[:50]}...'")
                results = self.chroma_kb.search_knowledge_base(
                    query=query,
                    n_results=max_results,
                    category_filter=category_filter,
                    similarity_threshold=0.3  # Lower threshold for better recall
                )
                
                if results:
                    logger.info(f"✅ ChromaDB found {len(results)} relevant items")
                    return results
                else:
                    logger.info("ℹ️ No relevant items found in ChromaDB, trying legacy search")
                    
            except Exception as e:
                logger.error(f"Error searching ChromaDB: {e}")
                logger.info("🔄 Falling back to legacy knowledge base search")
        
        # Fallback to legacy search
        logger.info(f"🔍 Using legacy search for: '{query[:50]}...'")
        return self._legacy_search_knowledge_base(query, max_results, category_filter)
    
    def _legacy_search_knowledge_base(self, query: str, max_results: int = 3, category_filter: str = None) -> List[Dict[str, Any]]:
        """Legacy keyword-based knowledge base search (fallback)"""
        if not self.knowledge_base or not self.knowledge_base.get("faqs"):
            return []
        
        query_lower = query.lower()
        faqs = self.knowledge_base.get("faqs", [])
        scored_results = []
        
        for faq in faqs:
            # Skip if category filter doesn't match
            if category_filter and faq.get("category", "").lower() != category_filter.lower():
                continue
                
            score = 0
            
            # Check question similarity
            question_similarity = SequenceMatcher(None, query_lower, faq.get("question", "").lower()).ratio()
            score += question_similarity * 100
            
            # Check keywords
            keywords = faq.get("keywords", [])
            for keyword in keywords:
                if keyword.lower() in query_lower:
                    score += 20
            
            # Check category relevance
            category = faq.get("category", "")
            if category.lower() in query_lower:
                score += 15
            
            # Check answer content
            answer = faq.get("answer", "")
            answer_words = answer.lower().split()
            query_words = query_lower.split()
            common_words = set(answer_words) & set(query_words)
            score += len(common_words) * 5
            
            if score > 10:  # Minimum relevance threshold
                # Add similarity score and rank for consistency with ChromaDB results
                result_faq = faq.copy()
                result_faq["similarity_score"] = round(score / 100, 3)  # Normalize to 0-1
                result_faq["source_file"] = "legacy"
                result_faq["rank"] = len(scored_results) + 1
                scored_results.append((score, result_faq))
        
        # Sort by score and return top results
        scored_results.sort(key=lambda x: x[0], reverse=True)
        return [faq for score, faq in scored_results[:max_results]]
    
    def get_quick_solution(self, query: str) -> Optional[str]:
        """Get quick solution from knowledge base if available"""
        if not self.knowledge_base or not self.knowledge_base.get("quick_solutions"):
            return None
        
        query_lower = query.lower()
        quick_solutions = self.knowledge_base.get("quick_solutions", {})
        
        # Check for direct keyword matches
        for key, solution in quick_solutions.items():
            keywords = key.split("_")
            if all(keyword in query_lower for keyword in keywords):
                return solution
        
        return None
    
    def format_knowledge_base_response(self, faqs: List[Dict[str, Any]], query: str) -> str:
        """Format knowledge base search results into a helpful response (supports both ChromaDB and legacy results)"""
        if not faqs:
            return None
        
        if len(faqs) == 1:
            faq = faqs[0]
            response = f"""💡 **I found this solution for you:**

**{faq.get('question', 'Solution')}**

{faq.get('answer', 'No answer available')}

⏱️ **Estimated time:** {faq.get('resolution_time_minutes', 15)} minutes
📂 **Category:** {faq.get('category', 'general').title()}"""
            
            # Add similarity score if available (ChromaDB)
            if 'similarity_score' in faq:
                response += f"\n🎯 **Relevance:** {int(faq['similarity_score'] * 100)}%"
            
            if faq.get('priority') == 'high' or faq.get('priority') == 'critical':
                response += f"\n🚨 **Priority:** {faq.get('priority', 'medium').title()}"
            
            response += "\n\n💬 **Need more help?** If this doesn't solve your issue, I can create a support ticket for you."
            return response
        
        else:
            response = f"💡 **I found {len(faqs)} solutions that might help:**\n\n"
            
            for i, faq in enumerate(faqs, 1):
                response += f"**{i}. {faq.get('question', 'Solution')}**\n"
                # Truncate long answers for multiple results
                answer = faq.get('answer', '')
                if len(answer) > 200:
                    answer = answer[:197] + "..."
                response += f"{answer}\n"
                
                # Add metadata line
                metadata_parts = []
                metadata_parts.append(f"⏱️ {faq.get('resolution_time_minutes', 15)} min")
                metadata_parts.append(f"📂 {faq.get('category', 'general').title()}")
                
                # Add similarity score if available (ChromaDB)
                if 'similarity_score' in faq:
                    metadata_parts.append(f"🎯 {int(faq['similarity_score'] * 100)}%")
                
                response += f"*{' | '.join(metadata_parts)}*\n\n"
            
            response += "💬 **Want more details on any solution?** Ask me about a specific item, or I can create a support ticket if needed."
            return response
    
    def get_emergency_contacts(self) -> str:
        """Get emergency contact information from knowledge base"""
        if not self.knowledge_base or not self.knowledge_base.get("emergency_contacts"):
            return """📞 **IT Emergency Contacts:**

🏢 **IT Helpdesk:** +1-555-0199
📧 **Email:** helpdesk@company.com  
🕐 **Hours:** 24/7 for critical issues"""
        
        contacts = self.knowledge_base.get("emergency_contacts", {})
        response = "📞 **IT Emergency Contacts:**\n\n"
        
        for contact_type, info in contacts.items():
            name = contact_type.replace("_", " ").title()
            response += f"**{name}:**\n"
            response += f"📞 Phone: {info.get('phone', 'N/A')}\n"
            response += f"📧 Email: {info.get('email', 'N/A')}\n"
            response += f"🕐 Hours: {info.get('hours', 'Business hours')}\n\n"
        
        return response.strip()
    
    def get_user_session_key(self, username: str, session_id: str = "default") -> str:
        """Generate unique session key for user (legacy method)"""
        return f"{username}:{session_id}"
    
    def create_new_thread(self, username: str, title: str = None) -> ConversationThread:
        """Create a new conversation thread for the user"""
        return self.thread_manager.create_thread(username, title)
    
    def get_or_create_active_thread(self, username: str) -> ConversationThread:
        """Get user's active thread or create a new one"""
        active_thread = self.thread_manager.get_user_active_thread(username)
        if not active_thread:
            active_thread = self.thread_manager.create_thread(username)
        return active_thread
    
    def get_user_threads(self, username: str, limit: int = 10) -> List[ConversationThread]:
        """Get user's conversation threads"""
        return self.thread_manager.get_user_threads(username)[:limit]
    
    def switch_to_thread(self, username: str, thread_id: str) -> Optional[ConversationThread]:
        """Switch to a specific conversation thread"""
        thread = self.thread_manager.get_thread(thread_id)
        if thread and thread.username == username:
            return thread
        return None
    
    def add_to_conversation(self, username: str, role: str, content: str, 
                          language: str = "en", thread_id: str = None):
        """Add message to user's conversation thread with enhanced tracking"""
        
        # Get or create thread
        if thread_id:
            thread = self.thread_manager.get_thread(thread_id)
            if not thread or thread.username != username:
                thread = self.get_or_create_active_thread(username)
        else:
            thread = self.get_or_create_active_thread(username)
        
        # Extract metadata for better conversation tracking
        metadata = {}
        if role == "user":
            metadata["intent"] = self._extract_user_intent(content)
        elif role == "assistant":
            metadata["functions_used"] = self._extract_functions_from_response(content)
        
        # Add message to thread
        thread.add_message(role, content, language, metadata)
        
        # Also maintain legacy in-memory conversation for backward compatibility
        session_key = self.get_user_session_key(username, thread.thread_id)
        if session_key not in self.conversations:
            self.conversations[session_key] = []
        
        message_entry = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "language": language,
            "metadata": metadata
        }
        
        self.conversations[session_key].append(message_entry)
        
        # Keep last 20 messages in memory for performance
        if len(self.conversations[session_key]) > 20:
            self.conversations[session_key] = self.conversations[session_key][-20:]
        
        return thread.thread_id
    
    def _extract_user_intent(self, content: str) -> str:
        """Extract basic user intent for conversation tracking"""
        content_lower = content.lower()
        
        # Common intents
        if any(word in content_lower for word in ["ticket", "create", "new", "issue", "problem"]):
            return "ticket_creation"
        elif any(word in content_lower for word in ["status", "check", "my ticket", "progress"]):
            return "ticket_inquiry"
        elif any(word in content_lower for word in ["password", "reset", "login", "access"]):
            return "password_help"
        elif any(word in content_lower for word in ["hello", "hi", "help", "assistance"]):
            return "general_help"
        elif any(word in content_lower for word in ["thank", "thanks", "bye", "goodbye"]):
            return "closing"
        else:
            return "other"
    
    def _extract_functions_from_response(self, response: str) -> List[str]:
        """Extract functions mentioned in bot response for tracking"""
        functions = []
        if "reset_password" in response.lower():
            functions.append("password_reset")
        if "create_ticket" in response.lower():
            functions.append("ticket_creation")
        if "ticket_status" in response.lower():
            functions.append("ticket_status")
        return functions
    
    def get_user_preferences(self, username: str) -> Dict[str, Any]:
        """Get or initialize user preferences"""
        if username not in self.user_preferences:
            user_data = get_user_by_username(username)
            self.user_preferences[username] = {
                "language": user_data.get("preferred_language", "en") if user_data else "en",
                "role": user_data.get("role", "staff") if user_data else "staff",
                "department": user_data.get("department", "Unknown") if user_data else "Unknown",
                "notification_preference": "email",
                "timezone": "UTC"
            }
        return self.user_preferences[username]
    
    def update_user_language_preference(self, username: str, language: str):
        """Update user's language preference"""
        prefs = self.get_user_preferences(username)
        prefs["language"] = language
        self.user_preferences[username] = prefs
    
    def _prepare_enhanced_messages(self, user_input: str, username: str, 
                                 thread_id: str = None) -> List[Dict[str, str]]:
        """Prepare messages with user context and conversation history from thread"""
        
        # Get thread for conversation history
        if thread_id:
            thread = self.thread_manager.get_thread(thread_id)
        else:
            thread = self.get_or_create_active_thread(username)
        
        user_prefs = self.get_user_preferences(username)
        
        # Enhanced system prompt with user context and conversation awareness
        user_context = f"""
USER CONTEXT:
- Username: {username}
- Role: {user_prefs['role'].title()}
- Department: {user_prefs['department']}
- Preferred Language: {user_prefs['language']}
- Thread: {thread.thread_id if thread else 'new'}
- Thread Title: {thread.title if thread else 'New Conversation'}

CONVERSATION GUIDELINES:
- Maintain context from previous messages in this thread
- Reference earlier topics when relevant (e.g., "As we discussed earlier...")
- Follow up on previous actions or requests
- Remember user preferences and choices from this conversation
- If continuing a previous topic, acknowledge it explicitly
- Use conversational flow markers like "Following up on your earlier request..."
- Build upon previous information rather than starting fresh each time
"""
        
        messages = [
            {"role": "system", "content": self.system_prompt + user_context}
        ]
        
        # Add conversation history from thread
        if thread and thread.messages:
            conversation_history = thread.messages[-10:]  # Last 10 messages for better context
            
            # Add conversation summary if there's history
            if len(conversation_history) > 0:
                messages.append({
                    "role": "system", 
                    "content": f"CONVERSATION CONTEXT: This is a continuation of thread '{thread.title}'. Previous topics and actions should be remembered and referenced appropriately."
                })
            
            # Add actual conversation messages
            for msg in conversation_history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # Add current user input
        messages.append({"role": "user", "content": user_input})
        
        return messages
    
    def _prepare_enhanced_messages_with_kb(self, user_input: str, username: str, thread_id: str = None):
        """Prepare messages for OpenAI with knowledge base context"""
        # Get user preferences and thread
        user_prefs = self.get_user_preferences(username)
        thread = self.thread_manager.get_thread(thread_id) if thread_id else None
        
        # Search knowledge base for relevant information
        kb_results = self.search_knowledge_base(user_input, max_results=2)
        quick_solution = self.get_quick_solution(user_input)
        
        # Build knowledge base context
        kb_context = ""
        if quick_solution:
            kb_context += f"\nQUICK SOLUTION AVAILABLE: {quick_solution}"
        
        if kb_results:
            kb_context += f"\nRELEVANT KNOWLEDGE BASE ENTRIES:"
            for i, faq in enumerate(kb_results, 1):
                kb_context += f"\n{i}. Q: {faq.get('question', '')}"
                kb_context += f"\n   A: {faq.get('answer', '')[:200]}..."
                kb_context += f"\n   Category: {faq.get('category', 'general')}, Time: {faq.get('resolution_time_minutes', 15)} min"
        
        # Enhanced system prompt with user context and knowledge base
        user_context = f"""
USER CONTEXT:
- Username: {username}
- Role: {user_prefs['role'].title()}
- Department: {user_prefs['department']}
- Preferred Language: {user_prefs['language']}
- Thread: {thread.thread_id if thread else 'new'}
- Thread Title: {thread.title if thread else 'New Conversation'}

KNOWLEDGE BASE CONTEXT:{kb_context}

CONVERSATION GUIDELINES:
- Use the knowledge base information to provide accurate, helpful responses
- If there's a quick solution, you can mention it but provide conversational context
- If there are relevant FAQs, incorporate that information naturally into your response
- Always maintain a conversational, helpful tone
- Don't just copy-paste knowledge base content - integrate it conversationally
- If knowledge base has the answer, provide it but also offer to help further
- If knowledge base doesn't have the answer, offer to create a support ticket
- Maintain context from previous messages in this thread
- Reference earlier topics when relevant (e.g., "As we discussed earlier...")
- Follow up on previous actions or requests
- Remember user preferences and choices from this conversation
- If continuing a previous topic, acknowledge it explicitly
- Use conversational flow markers like "Following up on your earlier request..."
- Build upon previous information rather than starting fresh each time
"""
        
        messages = [
            {"role": "system", "content": self.system_prompt + user_context}
        ]
        
        # Add conversation history from thread
        if thread and thread.messages:
            conversation_history = thread.messages[-10:]  # Last 10 messages for better context
            
            # Add conversation summary if there's history
            if len(conversation_history) > 0:
                messages.append({
                    "role": "system", 
                    "content": f"CONVERSATION CONTEXT: This is a continuation of thread '{thread.title}'. Previous topics and actions should be remembered and referenced appropriately."
                })
            
            # Add actual conversation messages
            for msg in conversation_history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # Add current user input
        messages.append({"role": "user", "content": user_input})
        
        return messages
    
    def _extract_enhanced_function_call(self, response_text: str, user_input: str) -> Optional[Dict[str, Any]]:
        """Enhanced function call extraction with NLP understanding - but prompt for ticket details instead of auto-creating"""
        try:
            user_lower = user_input.lower()
            
            # Intent detection patterns
            intent_patterns = {
                "get_ticket_status": [
                    r"get.*ticket.*status",
                    r"check.*ticket",
                    r"status.*ticket",
                    r"ticket.*status",
                    r"update.*ticket"
                ],
                "get_my_tickets": [
                    r"my.*tickets",
                    r"show.*tickets",
                    r"list.*tickets",
                    r"ticket.*history"
                ],
                "get_statistics": [
                    r"statistics",
                    r"stats",
                    r"metrics",
                    r"reports?",
                    r"analytics",
                    r"system.*status",
                    r"current.*status", 
                    r"system.*health",
                    r"ongoing.*issues",
                    r"system.*issues",
                    r"dashboard",
                    r"overview",
                    r"system.*information",
                    r"show.*status",
                    r"status.*report"
                ],
                "reset_password": [
                    r"reset.*password",
                    r"forgot.*password",
                    r"change.*password",
                    r"password.*reset"
                ],
                "get_contact_info": [
                    r"contact.*it",
                    r"it.*contact",
                    r"phone.*number",
                    r"email.*address",
                    r"support.*hours",
                    r"office.*hours",
                    r"how.*reach",
                    r"get.*help",
                    r"contact.*information",
                    r"support.*information",
                    r"help.*desk.*number",
                    r"it.*department.*contact"
                ]
            }
            
            # Check for structured ticket information (Title: ... Description: ... etc.)
            has_structured_ticket_info = (
                (("title:" in user_lower or "tittle:" in user_lower) and "description:" in user_lower) or
                (("title:" in user_lower or "tittle:" in user_lower) and "priority:" in user_lower) or
                ("description:" in user_lower and "category:" in user_lower) or
                ("priority:" in user_lower and "category:" in user_lower) or
                # Handle "Create a ticket: Title: ... Description: ..." format
                ("create" in user_lower and "ticket" in user_lower and ("title:" in user_lower or "tittle:" in user_lower))
            )
            
            # For ticket creation, check if we have sufficient details
            create_ticket_patterns = [
                r"create.*ticket",
                r"new.*ticket", 
                r"report.*issue",
                r"submit.*problem",
                r"i have.*problem",
                r"need help with"
            ]
            
            # Check if it's a ticket creation request
            is_ticket_request = any(re.search(pattern, user_lower) for pattern in create_ticket_patterns)
            
            # If we have structured ticket info, treat as ticket creation
            if has_structured_ticket_info:
                params = self._extract_parameters("create_ticket", user_input)
                if params:  # Only proceed if we successfully extracted parameters
                    return {
                        "function": "create_ticket",
                        "parameters": params,
                        "confidence": 0.9
                    }
            
            if is_ticket_request:
                # Check if we have detailed information
                has_detailed_info = (
                    len(user_input.split()) > 8 and  # More than 8 words
                    any(word in user_lower for word in ["problem", "issue", "not working", "broken", "error", "can't", "cannot", "unable"]) and
                    any(word in user_lower for word in ["computer", "laptop", "printer", "email", "network", "software", "application", "password"])
                )
                
                if has_detailed_info:
                    # Only create ticket if we have enough details
                    params = self._extract_parameters("create_ticket", user_input)
                    return {
                        "function": "create_ticket",
                        "parameters": params,
                        "confidence": 0.8
                    }
                else:
                    # Return None to trigger guidance response instead of auto-creation
                    return None
            
            # Check for other intent matches
            for intent, patterns in intent_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, user_lower):
                        # Extract parameters based on intent
                        params = self._extract_parameters(intent, user_input)
                        return {
                            "function": intent,
                            "parameters": params,
                            "confidence": 0.8
                        }
            
            # Check if response mentions function calls
            for func_name in self.function_mappings.keys():
                if func_name in response_text.lower() and func_name != "create_ticket":
                    return {
                        "function": func_name,
                        "parameters": {},
                        "confidence": 0.6
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting enhanced function call: {e}")
            return None
    
    def _extract_parameters(self, intent: str, user_input: str) -> Dict[str, Any]:
        """Extract parameters for specific function intents - require good details for ticket creation"""
        params = {}
        user_lower = user_input.lower()
        
        if intent == "create_ticket":
            # Check for structured format first (Title: ... Description: ... Priority: ... Category: ...)
            # Handle common typos like "Tittle" for "Title"
            title_match = re.search(r"(?:title|tittle):\s*([^:\n]+?)(?:\s+(?:description|desc):|$)", user_input, re.IGNORECASE)
            desc_match = re.search(r"(?:description|desc):\s*([^:\n]+?)(?:\s+(?:priority|prio):|$)", user_input, re.IGNORECASE)
            priority_match = re.search(r"(?:priority|prio):\s*(\w+)", user_input, re.IGNORECASE)
            category_match = re.search(r"category:\s*(\w+)", user_input, re.IGNORECASE)
            
            # Also handle the format: "Create a ticket: Title: ... Description: ..."
            if not title_match:
                title_match = re.search(r"create.*ticket.*?(?:title|tittle):\s*([^:\n]+?)(?:\s+(?:description|desc):|$)", user_input, re.IGNORECASE)
            if not desc_match:
                desc_match = re.search(r"create.*ticket.*?(?:description|desc):\s*([^:\n]+?)(?:\s+(?:priority|prio):|$)", user_input, re.IGNORECASE)
            
            # Extract structured information
            if title_match:
                params["title"] = title_match.group(1).strip()
            
            if desc_match:
                params["description"] = desc_match.group(1).strip()
            elif not desc_match and title_match:
                # If no separate description, use remaining text after title
                remaining_text = user_input[title_match.end():].strip()
                # Remove other structured fields to get description
                remaining_text = re.sub(r"(?:priority|prio):\s*\w+", "", remaining_text, flags=re.IGNORECASE)
                remaining_text = re.sub(r"category:\s*\w+", "", remaining_text, flags=re.IGNORECASE)
                params["description"] = remaining_text.strip() if remaining_text.strip() else params.get("title", "")
            
            if priority_match:
                params["priority"] = priority_match.group(1).lower()
            
            if category_match:
                params["category"] = category_match.group(1).lower()
            
            # If no structured format, try legacy extraction
            if not title_match:
                # Legacy title extraction
                issue_match = re.search(r"(?:create ticket:?\s*|new ticket:?\s*|issue:?\s*|problem:?\s*)(.+?)(?:\.|$)", user_input, re.IGNORECASE)
                if issue_match:
                    params["title"] = issue_match.group(1).strip()[:100]
                else:
                    # Extract first meaningful sentence
                    sentences = user_input.split('.')
                    if sentences:
                        params["title"] = sentences[0].strip()[:100]
                    else:
                        params["title"] = user_input[:100]
                
                # Legacy description
                if not desc_match:
                    params["description"] = user_input.strip()
            
            # Ensure we have meaningful content
            if not params.get("title") or len(params["title"].strip()) < 3:
                return {}  # Trigger guidance instead
            
            # Set default description if missing
            if not params.get("description"):
                params["description"] = params.get("title", "No description provided")
            
            # Extract priority with better detection (if not already found)
            if not params.get("priority"):
                if any(word in user_lower for word in ["urgent", "critical", "emergency", "asap", "immediately", "can't work"]):
                    params["priority"] = "critical"
                elif any(word in user_lower for word in ["high", "important", "soon", "blocking"]):
                    params["priority"] = "high"
                elif any(word in user_lower for word in ["low", "minor", "when possible", "eventually"]):
                    params["priority"] = "low"
                else:
                    params["priority"] = "medium"
                
            # Extract category with better detection (if not already found)
            if not params.get("category"):
                if any(word in user_lower for word in ["computer", "laptop", "pc", "desktop", "hardware", "device", "monitor", "keyboard", "mouse"]):
                    params["category"] = "hardware"
                elif any(word in user_lower for word in ["software", "application", "program", "app", "excel", "word", "browser", "chrome"]):
                    params["category"] = "software"
                elif any(word in user_lower for word in ["network", "internet", "wifi", "connection", "vpn", "connectivity"]):
                    params["category"] = "network"
                elif any(word in user_lower for word in ["email", "outlook", "mail", "inbox", "send", "receive"]):
                    params["category"] = "email"
                elif any(word in user_lower for word in ["password", "login", "account", "access", "authentication"]):
                    params["category"] = "account"
                else:
                    params["category"] = "general"
        
        elif intent == "get_ticket_status":
            # Extract ticket ID - improved pattern to get actual ticket numbers
            # Try multiple patterns to capture ticket IDs
            patterns = [
                r"(\d{14})",  # Direct 14-digit timestamp format
                r"(?:ticket\s+id[\s:]*|id[\s:]*|ticket[\s:]+)(\d+)",  # ticket id: 123 or ticket 123
                r"(?:status\s+)(\d+)",  # status 123
                r"([A-Z0-9]{10,})"  # Any long alphanumeric ID
            ]
            
            for pattern in patterns:
                ticket_match = re.search(pattern, user_input, re.IGNORECASE)
                if ticket_match:
                    params["ticket_id"] = ticket_match.group(1)
                    break
        
        elif intent == "reset_password":
            # Extract username (including usernames with dots like john.doe)
            # Try multiple patterns to catch different formats
            patterns = [
                r"(?:user|username)[\s:]+([a-zA-Z0-9._-]+)",  # "user john.doe" or "username: john.doe"
                r"for\s+([a-zA-Z0-9._-]+)",                    # "reset password for john.doe"
                r"password\s+for\s+([a-zA-Z0-9._-]+)",        # "reset john.doe password"
                r"([a-zA-Z0-9._-]+)(?:'s)?\s+password"        # "john.doe's password"
            ]
            
            for pattern in patterns:
                user_match = re.search(pattern, user_input, re.IGNORECASE)
                if user_match:
                    params["target_username"] = user_match.group(1)
                    break
        
        return params
    
    def _execute_enhanced_function(self, function_call: Dict[str, Any], 
                                 username: str, language: str) -> str:
        """Execute function with enhanced error handling and permissions"""
        try:
            func_name = function_call["function"]
            params = function_call.get("parameters", {})
            
            # Check if function exists
            if func_name not in self.function_mappings:
                return get_localized_text("error", language) + f": Unknown function {func_name}"
            
            # Execute function through router
            result = route_helpdesk_function(
                function_name=func_name,
                username=username,
                language=language,
                **params
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing enhanced function {func_name}: {e}")
            error_msg = get_localized_text("error", language)
            return f"{error_msg}: {str(e)}"
    
    def get_response(self, user_input: str, username: str = "user", 
                         thread_id: str = None) -> tuple[str, str]:
        """
        Get enhanced response with multi-language and thread-based conversations
        
        Args:
            user_input: User's message
            username: Username for context and permissions
            thread_id: Optional specific thread ID, or creates/uses active thread
            
        Returns:
            Tuple of (bot_response, thread_id)
        """
        try:
            # Detect user language
            detected_language = detect_user_language(user_input)
            user_prefs = self.get_user_preferences(username)
            
            # Use detected language or user preference
            response_language = detected_language if detected_language != "en" else user_prefs.get("language", "en")
            
            # Update language preference if changed
            if response_language != user_prefs.get("language"):
                self.update_user_language_preference(username, response_language)
            
            # Get or create thread
            if thread_id:
                thread = self.thread_manager.get_thread(thread_id)
                if not thread or thread.username != username:
                    thread = self.get_or_create_active_thread(username)
                    thread_id = thread.thread_id
            else:
                thread = self.get_or_create_active_thread(username)
                thread_id = thread.thread_id
            
            # Add to conversation history
            self.add_to_conversation(username, "user", user_input, response_language, thread_id)
            
            # Check if user exists and get role info
            user_data = get_user_by_username(username)
            if not user_data:
                error_msg = get_localized_text("user_not_found", response_language)
                return error_msg, thread_id
            
            # Try Azure OpenAI first
            if self.client:
                try:
                    # Prepare messages with knowledge base context
                    messages = self._prepare_enhanced_messages_with_kb(user_input, username, thread_id)
                    
                    response = self.client.chat.completions.create(
                        model=self.deployment_name,
                        messages=messages,
                        max_tokens=1000,
                        temperature=0.7,
                        timeout=30  # Add 30 second timeout
                    )
                    
                    bot_response = response.choices[0].message.content
                    
                    # Check for function calls based on user input (prioritize user intent over bot response)
                    function_call = self._extract_enhanced_function_call("", user_input)
                    if function_call:
                        function_result = self._execute_enhanced_function(
                            function_call, username, response_language
                        )
                        
                        # Replace bot response with function result if successful
                        if "error" not in function_result.lower():
                            bot_response = function_result
                        else:
                            bot_response = f"{bot_response}\n\n{function_result}"
                    
                except Exception as e:
                    logger.error(f"Azure OpenAI API error: {e}")
                    bot_response = self._get_enhanced_fallback_response(
                        user_input, username, response_language, thread_id
                    )
            else:
                # Use enhanced fallback
                bot_response = self._get_enhanced_fallback_response(
                    user_input, username, response_language, thread_id
                )
            
            # Add bot response to conversation
            self.add_to_conversation(username, "assistant", bot_response, response_language, thread_id)
            
            return bot_response, thread_id
            
        except Exception as e:
            logger.error(f"Error getting enhanced response: {e}")
            error_msg = get_localized_text("error", response_language)
            return f"{error_msg}: {str(e)}", thread_id or "error"
    
    def _get_enhanced_fallback_response(self, user_input: str, username: str, 
                                      language: str, thread_id: str = None) -> str:
        """Enhanced fallback with conversation context and multi-language responses"""
        user_input_lower = user_input.lower()
        user_data = get_user_by_username(username)
        user_role = user_data.get("role", "staff") if user_data else "staff"
        
        # Get conversation history for context
        thread = self.thread_manager.get_thread(thread_id) if thread_id else None
        has_conversation_history = thread and len(thread.messages) > 1
        
        # First, check for explicit function calls
        function_call = self._extract_enhanced_function_call("", user_input)
        if function_call:
            return self._execute_enhanced_function(function_call, username, language)
        
        # For very specific, simple queries, provide quick solutions
        # But for conversational queries, let the fallback logic handle it with context
        simple_queries = ["password reset", "reset password", "contact info", "contact information"]
        if any(query in user_input_lower for query in simple_queries):
            quick_solution = self.get_quick_solution(user_input)
            if quick_solution:
                return f"💡 **Quick Solution:** {quick_solution}\n\n💬 If this doesn't help, I can create a support ticket for you."
        
        # Context-aware responses based on conversation history
        if has_conversation_history:
            recent_messages = thread.messages[-5:]  # Last 5 messages
            
            # Check for follow-up patterns
            if any(word in user_input_lower for word in ["slow", "slowly", "performance", "running"]):
                if any("computer" in msg.get("content", "").lower() for msg in recent_messages if msg.get("role") == "user"):
                    return f"""I understand your computer is running slowly. Following up on our conversation, here are some steps to help:

**Immediate Steps:**
🔄 **Restart your computer** - This often resolves temporary slowdowns
📂 **Close unused programs** - Check Task Manager for memory usage
🧹 **Clear temporary files** - Run Disk Cleanup utility

**I can also help you:**
• 🎫 Create a ticket for IT investigation: "Create ticket for slow computer performance"
• 📞 Get immediate help: "Contact IT support"
• 📋 Check your other tickets: "Show my tickets"

Would you like me to create a support ticket for this performance issue?"""
        
        # Enhanced ticket creation guidance
        if any(word in user_input_lower for word in ["create", "new", "ticket", "issue", "problem", "report", "help"]) or \
           (("title:" in user_input_lower or "tittle:" in user_input_lower) and "description:" in user_input_lower):
            # Check if user provided enough detail already OR structured format
            has_good_detail = (
                len(user_input.split()) > 8 and
                any(word in user_input_lower for word in ["not working", "broken", "error", "can't", "cannot", "unable", "problem with"]) and
                any(word in user_input_lower for word in ["computer", "laptop", "printer", "email", "network", "software", "application", "password", "system"])
            )
            
            # Check for structured format
            has_structured_format = (
                (("title:" in user_input_lower or "tittle:" in user_input_lower) and "description:" in user_input_lower) or
                (("title:" in user_input_lower or "tittle:" in user_input_lower) and "priority:" in user_input_lower) or
                ("description:" in user_input_lower and "category:" in user_input_lower) or
                # Handle "Create a ticket: Title: ... Description: ..." format
                ("create" in user_input_lower and "ticket" in user_input_lower and ("title:" in user_input_lower or "tittle:" in user_input_lower))
            )
            
            if has_good_detail or has_structured_format:
                # User provided good details, try to create the ticket
                function_call = self._extract_enhanced_function_call("", user_input)
                if function_call:
                    return self._execute_enhanced_function(function_call, username, language)
            
            # Guide user through ticket creation process
            return f"""I'll help you create a support ticket! To provide the best assistance, I need some information:

**🎫 Ticket Creation Guide:**

**1. What's the problem?** 
   • Describe what's not working
   • Include any error messages you see
   
**2. What type of issue is this?**
   • 💻 Hardware (computer, printer, monitor)
   • 📱 Software (applications, programs)
   • 🌐 Network (internet, wifi, connectivity)
   • 📧 Email (Outlook, mail issues)
   • 🔐 Account/Password problems

**3. How urgent is this?**
   • 🔴 Critical - Blocking all work
   • 🟡 High - Significantly impacting work  
   • 🟢 Medium - Some impact on work
   • ⚪ Low - Minor inconvenience

**Examples of good ticket requests:**
• "Create ticket: My computer won't start this morning, getting blue screen error"
• "Create ticket: Printer in conference room is jammed and won't print any documents"
• "Create ticket: Can't access email on my phone, getting authentication error"

**Quick Template:**
"Create ticket: [What's broken] - [Brief description of the problem]"

What issue would you like to report?"""
        
        # Greeting responses
        if any(word in user_input_lower for word in ["hello", "hi", "hola", "bonjour", "help"]):
            greeting = get_localized_text("greeting", language)
            role_name = get_localized_text(f"role_{user_role}", language)
            
            context_msg = ""
            if has_conversation_history:
                context_msg = "\n\n💬 **Continuing our conversation...** How else can I help you?"
            
            return f"""{greeting}

👤 **Welcome {username}** ({role_name})
🏢 **Department:** {user_data.get('department', 'Unknown') if user_data else 'Unknown'}

**Available Services:**
🎫 **Ticket Management:** Create, track, and manage support requests
🔐 **Password Services:** Reset and manage account passwords  
📊 **System Information:** View statistics and system status
🌍 **Multi-Language:** I can help in multiple languages

**Quick Commands:**
• "Create ticket" - Submit new support request
• "My tickets" - View your tickets
• "Reset password" - Password assistance
• "System stats" - View metrics (if permitted){context_msg}

How can I assist you today?"""
        
        # Context-aware default response
        role_name = get_localized_text(f"role_{user_role}", language)
        
        context_prefix = ""
        if has_conversation_history:
            context_prefix = "Continuing our conversation, "
        
        return f"""{context_prefix}I'm here to help you with IT support, {username} ({role_name}).

**I can assist with:**
• 🎫 Creating and managing support tickets
• 🔐 Password resets and account issues
• 📊 System statistics and reports
• 🌍 Support in multiple languages

**For your request:** "{user_input}"

Please specify what you'd like me to help with:
- Create a ticket: "Create ticket for [issue]"
- Check tickets: "Show my tickets" 
- Password help: "Reset password"
- System info: "Show statistics"

What would you like me to do?"""
    
    def get_conversation_summary(self, username: str, thread_id: str = None) -> Dict[str, Any]:
        """Get enhanced conversation summary with thread context"""
        user_prefs = self.get_user_preferences(username)
        
        if thread_id:
            thread = self.thread_manager.get_thread(thread_id)
        else:
            thread = self.thread_manager.get_user_active_thread(username)
        
        if thread:
            return {
                "username": username,
                "thread_id": thread.thread_id,
                "thread_title": thread.title,
                "message_count": thread.get_message_count(),
                "user_message_count": thread.get_user_message_count(),
                "created_date": thread.created_date,
                "last_updated": thread.last_updated,
                "user_role": user_prefs.get("role", "staff"),
                "preferred_language": user_prefs.get("language", "en"),
                "azure_available": self.client is not None,
                "thread_active": thread.is_active,
                "thread_summary": thread.get_summary()
            }
        else:
            return {
                "username": username,
                "thread_id": None,
                "thread_title": "No active conversation",
                "message_count": 0,
                "user_message_count": 0,
                "user_role": user_prefs.get("role", "staff"),
                "preferred_language": user_prefs.get("language", "en"),
                "azure_available": self.client is not None,
                "thread_active": False
            }
    
    def get_user_thread_list(self, username: str) -> List[Dict[str, Any]]:
        """Get formatted list of user's threads"""
        threads = self.thread_manager.get_user_threads(username)
        return [
            {
                "thread_id": thread.thread_id,
                "title": thread.title,
                "message_count": thread.get_message_count(),
                "user_message_count": thread.get_user_message_count(),
                "last_updated": thread.last_updated,
                "created_date": thread.created_date,
                "is_active": thread.is_active,
                "summary": thread.get_summary()
            }
            for thread in threads
        ]
    
    def clear_conversation(self, username: str, thread_id: str = None):
        """Clear specific thread or create new active thread"""
        if thread_id:
            # Archive the specific thread
            self.thread_manager.archive_thread(thread_id)
        else:
            # Archive current active thread and create new one
            active_thread = self.thread_manager.get_user_active_thread(username)
            if active_thread:
                self.thread_manager.archive_thread(active_thread.thread_id)
        
        # Clear legacy in-memory conversation
        if thread_id:
            session_key = self.get_user_session_key(username, thread_id)
            if session_key in self.conversations:
                del self.conversations[session_key]
        
        logger.info(f"Conversation cleared for {username}, thread: {thread_id}")


# Example usage and testing
if __name__ == "__main__":
    async def test_enhanced_bot():
        bot = EnhancedITHelpdeskBot()
        
        # Test with different user roles and languages
        test_scenarios = [
            ("john.doe", "Hello, I need help", "en"),
            ("maria.garcia", "Hola, necesito ayuda", "es"),
            ("john.doe", "Create a ticket for computer issues", "en"),
            ("david.bod", "Show me system statistics", "en"),
            ("admin.user", "Reset password for john.doe", "en")
        ]
        
        for username, query, lang in test_scenarios:
            print(f"\nUser ({username}): {query}")
            response = await bot.get_response(query, username)
            print(f"Bot: {response}")
            print("-" * 80)
    
    # Run test
    asyncio.run(test_enhanced_bot())
