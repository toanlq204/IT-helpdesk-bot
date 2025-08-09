#!/usr/bin/env python3
"""
ChromaDB Knowledge Base Manager
===============================

Manages the knowledge base using ChromaDB vector database for:
- Semantic search capabilities
- Persistent local storage
- Efficient similarity matching
- OpenAI/Azure OpenAI embedding generation
- Multi-language support

Features:
- Local ChromaDB with persistent storage
- OpenAI embeddings (Azure OpenAI compatible)
- Automatic knowledge base indexing
- Semantic similarity search
- Category-based filtering
- Multi-language content support
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import uuid

try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logging.warning("ChromaDB not available. Install with: pip install chromadb")

# Try to import sentence transformers as fallback
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning("SentenceTransformers not available. Using OpenAI or ChromaDB default embeddings.")

logger = logging.getLogger(__name__)

class ChromaKnowledgeBaseManager:
    """
    Enhanced ChromaDB-based Knowledge Base Manager with OpenAI embeddings
    
    Provides multiple embedding strategies as alternatives to sentence-transformers:
    1. OpenAI/Azure OpenAI embeddings (RECOMMENDED) - high quality, cloud-based
    2. ChromaDB Default (ONNX) - fast, reliable, no dependencies
    3. SentenceTransformers - local models for offline usage
    4. TF-IDF Hybrid - keyword matching + semantic similarity
    """
    
    def __init__(self, 
                 persist_directory: str = "chroma_db",
                 model_name: str = "text-embedding-3-small",
                 similarity_threshold: float = 0.3,
                 use_azure_openai: bool = True):  # Default to Azure OpenAI
        """
        Initialize Enhanced ChromaDB Knowledge Base Manager
        
        Args:
            persist_directory: Directory for persistent ChromaDB storage
            model_name: OpenAI embedding model name (e.g., "text-embedding-3-small")
            similarity_threshold: Minimum similarity score (lowered for better results)
            use_azure_openai: Whether to use Azure OpenAI (default) or OpenAI API
        """
        self.persist_directory = persist_directory
        self.model_name = model_name
        self.similarity_threshold = similarity_threshold
        self.use_azure_openai = use_azure_openai
        
        # Initialize state variables
        self.use_openai_embeddings = False
        self.use_sentence_transformers = False
        self.embedding_model = None
        self.embedding_function = None
        self.client = None
        self.collection = None
        self.is_initialized = False
        self.total_items = 0
        self.files_loaded = 0
        
        # Azure OpenAI configuration
        self.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        self.azure_key = os.getenv("AZURE_OPENAI_API_KEY", "")
        self.azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        # Separate deployment for embeddings (fallback to main deployment if not set)
        self.azure_embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", 
                                                   os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", ""))
        # Separate API key for embeddings (fallback to main API key if not set)
        self.azure_embedding_key = os.getenv("AZURE_OPENAI_EMBEDDING_API_KEY",
                                           os.getenv("AZURE_OPENAI_API_KEY", ""))
        
        # OpenAI configuration (fallback)
        self.openai_key = os.getenv("OPENAI_API_KEY", "")
        
        # Initialize the ChromaDB system
        self._initialize()
    
    def _initialize(self):
        """Initialize ChromaDB client and collection with OpenAI embedding function"""
        try:
            # Ensure persist directory exists
            os.makedirs(self.persist_directory, exist_ok=True)
            
            # Initialize ChromaDB client with persistent storage
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Set up embedding function priority: OpenAI > SentenceTransformers > ChromaDB Default
            if self._initialize_openai_embeddings():
                logger.info(f"✅ Using OpenAI embeddings: {self.model_name}")
            elif SENTENCE_TRANSFORMERS_AVAILABLE:
                try:
                    # Use sentence transformers as fallback
                    logger.info(f"Loading SentenceTransformer model: {self.model_name}")
                    self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")  # Fallback model
                    self.use_sentence_transformers = True
                    
                    # Get or create knowledge base collection with custom embeddings
                    self.collection = self.client.get_or_create_collection(
                        name="knowledge_base",
                        metadata={"description": "IT Helpdesk Knowledge Base with SentenceTransformer embeddings"}
                    )
                    
                    logger.info(f"✅ Using SentenceTransformer embeddings as fallback")
                    
                except Exception as e:
                    logger.error(f"Failed to load SentenceTransformer, falling back to default embeddings: {e}")
                    self.use_sentence_transformers = False
                    self._initialize_with_default_embeddings()
            else:
                # Use ChromaDB's default embedding function (final fallback)
                logger.info("Neither OpenAI nor SentenceTransformers available, using ChromaDB default embeddings")
                logger.info("ℹ️ Consider setting up OpenAI API key for better embeddings")
                self.use_sentence_transformers = False
                self._initialize_with_default_embeddings()
            
            self.is_initialized = True
            logger.info(f"✅ ChromaDB Knowledge Base initialized successfully")
            logger.info(f"📁 Persistent storage: {self.persist_directory}")
            
            embedding_type = "OpenAI" if self.use_openai_embeddings else \
                           "SentenceTransformer" if self.use_sentence_transformers else \
                           "ChromaDB Default"
            logger.info(f"🧠 Embedding type: {embedding_type}")
            logger.info(f"📊 Current collection size: {self.collection.count()}")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            self.is_initialized = False
    
    def _initialize_openai_embeddings(self) -> bool:
        """Initialize OpenAI embedding function (Azure OpenAI or OpenAI API)"""
        try:
            if self.use_azure_openai and self.azure_endpoint and self.azure_embedding_key:
                # Use Azure OpenAI
                logger.info(f"Initializing Azure OpenAI embeddings: {self.model_name}")
                
                # Check if we have a specific embedding deployment configured
                if not self.azure_embedding_deployment:
                    logger.error("No Azure OpenAI embedding deployment configured. Please set AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
                    return False
                
                # Check if the deployment seems suitable for embeddings
                is_embedding_deployment = any(embed_name in self.azure_embedding_deployment.lower() 
                                            for embed_name in ['embedding', 'ada', 'text-embed'])
                
                if not is_embedding_deployment:
                    logger.warning(f"Deployment '{self.azure_embedding_deployment}' may not be an embedding model")
                    logger.warning("Expected embedding deployments: text-embedding-ada-002, text-embedding-3-small, text-embedding-3-large")
                
                self.embedding_function = OpenAIEmbeddingFunction(
                    api_key=self.azure_embedding_key,  # Use specific embedding API key
                    api_base=self.azure_endpoint,
                    api_version=self.azure_api_version,
                    api_type="azure",
                    deployment_id=self.azure_embedding_deployment  # Use deployment_id for Azure
                )
                
                # Get or create knowledge base collection with OpenAI embeddings
                self.collection = self.client.get_or_create_collection(
                    name="knowledge_base",
                    embedding_function=self.embedding_function,
                    metadata={
                        "description": "IT Helpdesk Knowledge Base with Azure OpenAI embeddings",
                        "embedding_model": self.model_name,
                        "embedding_provider": "azure_openai",
                        "azure_deployment": self.azure_embedding_deployment
                    }
                )
                
                self.use_openai_embeddings = True
                logger.info("✅ Azure OpenAI embeddings initialized successfully")
                logger.info(f"🚀 Using Azure embedding deployment: {self.azure_embedding_deployment}")
                return True
                
            elif self.openai_key:
                # Use OpenAI API
                logger.info(f"Initializing OpenAI embeddings: {self.model_name}")
                self.embedding_function = OpenAIEmbeddingFunction(
                    model_name=self.model_name,
                    api_key=self.openai_key
                )
                
                # Get or create knowledge base collection with OpenAI embeddings
                self.collection = self.client.get_or_create_collection(
                    name="knowledge_base",
                    embedding_function=self.embedding_function,
                    metadata={
                        "description": "IT Helpdesk Knowledge Base with OpenAI embeddings",
                        "embedding_model": self.model_name,
                        "embedding_provider": "openai"
                    }
                )
                
                self.use_openai_embeddings = True
                logger.info("✅ OpenAI embeddings initialized successfully")
                return True
                
            else:
                logger.info("OpenAI API keys not available, falling back to alternative embeddings")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI embeddings: {e}")
            return False
    
    def _initialize_with_default_embeddings(self):
        """Initialize with ChromaDB's default embedding function"""
        # Get or create knowledge base collection with default embeddings
        self.collection = self.client.get_or_create_collection(
            name="knowledge_base",
            metadata={"description": "IT Helpdesk Knowledge Base with default embeddings"}
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get detailed status of the knowledge base"""
        if not self.is_initialized:
            return {
                "status": "not_initialized",
                "available": False,
                "error": "ChromaDB not available or initialization failed"
            }
        
        try:
            count = self.collection.count()
            
            # Determine embedding type and details
            if self.use_openai_embeddings:
                embedding_type = "Azure OpenAI" if self.use_azure_openai else "OpenAI"
                embedding_provider = "azure_openai" if self.use_azure_openai else "openai"
            elif self.use_sentence_transformers:
                embedding_type = "SentenceTransformer"
                embedding_provider = "sentence_transformers"
            else:
                embedding_type = "ChromaDB Default"
                embedding_provider = "chromadb_default"
            
            return {
                "status": "ready",
                "available": True,
                "collection_size": count,
                "persist_directory": self.persist_directory,
                "embedding_type": embedding_type,
                "embedding_provider": embedding_provider,
                "model_name": self.model_name,
                "use_openai_embeddings": self.use_openai_embeddings,
                "use_azure_openai": self.use_azure_openai and self.use_openai_embeddings,
                "sentence_transformers_available": SENTENCE_TRANSFORMERS_AVAILABLE,
                "azure_openai_configured": bool(self.azure_endpoint and self.azure_embedding_key),
                "azure_embedding_deployment_configured": bool(self.azure_embedding_deployment),
                "openai_configured": bool(self.openai_key),
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "available": False,
                "error": str(e)
            }
    
    def add_knowledge_items(self, items: List[Dict[str, Any]], source_file: str = "unknown") -> bool:
        """
        Add knowledge base items to ChromaDB
        
        Args:
            items: List of knowledge items (FAQs, guides, etc.)
            source_file: Source file name for tracking
            
        Returns:
            bool: Success status
        """
        if not self.is_initialized:
            logger.error("ChromaDB not initialized")
            return False
        
        try:
            documents = []
            metadatas = []
            ids = []
            
            for item in items:
                # Create searchable document text
                doc_text = self._create_document_text(item)
                
                # Create metadata
                metadata = {
                    "item_id": str(item.get("id", uuid.uuid4())),
                    "category": item.get("category", "general"),
                    "source_file": source_file,
                    "keywords": ",".join(item.get("keywords", [])),
                    "added_date": datetime.now().isoformat(),
                    "type": "faq"  # Can be extended for other types
                }
                
                # Add original question and answer to metadata for exact retrieval
                if "question" in item:
                    metadata["question"] = item["question"]
                if "answer" in item:
                    metadata["answer"] = item["answer"]
                
                documents.append(doc_text)
                metadatas.append(metadata)
                ids.append(f"{source_file}_{item.get('id', uuid.uuid4())}")
            
            # Add to collection
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"✅ Added {len(items)} knowledge items from {source_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding knowledge items: {e}")
            return False
    
    def _create_document_text(self, item: Dict[str, Any]) -> str:
        """Create searchable document text from knowledge item"""
        parts = []
        
        # Add question
        if "question" in item:
            parts.append(f"Question: {item['question']}")
        
        # Add answer
        if "answer" in item:
            parts.append(f"Answer: {item['answer']}")
        
        # Add keywords
        if "keywords" in item and item["keywords"]:
            parts.append(f"Keywords: {', '.join(item['keywords'])}")
        
        # Add category
        if "category" in item:
            parts.append(f"Category: {item['category']}")
        
        return "\n".join(parts)
    
    def search_knowledge_base(
        self, 
        query: str, 
        n_results: int = 5,
        category_filter: Optional[str] = None,
        similarity_threshold: float = 0.3  # Lowered from 0.7 to 0.3 for better recall
    ) -> List[Dict[str, Any]]:
        """
        Search knowledge base using semantic similarity
        
        Args:
            query: Search query
            n_results: Number of results to return
            category_filter: Optional category to filter by
            similarity_threshold: Minimum similarity score (0-1)
            
        Returns:
            List of matching knowledge items with similarity scores
        """
        if not self.is_initialized:
            logger.error("ChromaDB not initialized")
            return []
        
        try:
            # Prepare where clause for filtering
            where_clause = {}
            if category_filter:
                where_clause["category"] = category_filter
            
            # Perform similarity search
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_clause if where_clause else None
            )
            
            # Process results
            knowledge_items = []
            if results["documents"] and results["documents"][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0]
                )):
                    # Convert distance to similarity score (ChromaDB uses cosine distance)
                    similarity = 1 - distance
                    
                    # Filter by similarity threshold
                    if similarity >= similarity_threshold:
                        knowledge_items.append({
                            "question": metadata.get("question", ""),
                            "answer": metadata.get("answer", ""),
                            "category": metadata.get("category", "general"),
                            "keywords": metadata.get("keywords", "").split(",") if metadata.get("keywords") else [],
                            "similarity_score": round(similarity, 3),
                            "source_file": metadata.get("source_file", "unknown"),
                            "item_id": metadata.get("item_id", ""),
                            "rank": i + 1
                        })
            
            logger.info(f"🔍 Found {len(knowledge_items)} relevant items for query: '{query[:50]}...'")
            return knowledge_items
            
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return []
    
    def reload_from_directory(self, kb_directory: str) -> Dict[str, Any]:
        """
        Reload entire knowledge base from directory
        
        Args:
            kb_directory: Path to knowledge base directory
            
        Returns:
            Status dictionary with loading results
        """
        if not self.is_initialized:
            return {"success": False, "error": "ChromaDB not initialized"}
        
        try:
            # Clear existing collection by deleting and recreating it
            try:
                # Delete the old collection completely
                self.client.delete_collection(name="knowledge_base")
            except Exception as e:
                logger.warning(f"Collection may not exist yet: {e}")
            
            # Create new collection
            self.collection = self.client.get_or_create_collection(
                name="knowledge_base",
                metadata={"description": "IT Helpdesk Knowledge Base with semantic search"}
            )
            
            files_loaded = 0
            total_items = 0
            
            # Load all JSON files in the directory
            if os.path.exists(kb_directory):
                for filename in os.listdir(kb_directory):
                    if filename.endswith('.json') and not filename.startswith('backup_'):
                        file_path = os.path.join(kb_directory, filename)
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                
                                # Extract FAQs or knowledge items
                                items = []
                                if "faqs" in data and isinstance(data["faqs"], list):
                                    items.extend(data["faqs"])
                                
                                # Add other knowledge types if needed
                                # TODO: Add support for troubleshooting guides, etc.
                                
                                if items:
                                    success = self.add_knowledge_items(items, filename)
                                    if success:
                                        files_loaded += 1
                                        total_items += len(items)
                                        
                        except Exception as e:
                            logger.error(f"Error loading file {filename}: {e}")
                            continue
            
            return {
                "success": True,
                "files_loaded": files_loaded,
                "total_items": total_items,
                "collection_size": self.collection.count(),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error reloading knowledge base: {e}")
            return {"success": False, "error": str(e)}
    
    def get_categories(self) -> List[str]:
        """Get all available categories in the knowledge base"""
        if not self.is_initialized:
            return []
        
        try:
            # Get all unique categories
            results = self.collection.get()
            categories = set()
            
            if results["metadatas"]:
                for metadata in results["metadatas"]:
                    if "category" in metadata:
                        categories.add(metadata["category"])
            
            return sorted(list(categories))
            
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get detailed statistics about the knowledge base collection"""
        if not self.is_initialized:
            return {}
        
        try:
            results = self.collection.get()
            
            # Count by category
            category_counts = {}
            source_file_counts = {}
            
            if results["metadatas"]:
                for metadata in results["metadatas"]:
                    category = metadata.get("category", "unknown")
                    source = metadata.get("source_file", "unknown")
                    
                    category_counts[category] = category_counts.get(category, 0) + 1
                    source_file_counts[source] = source_file_counts.get(source, 0) + 1
            
            model_info = {
                "type": "SentenceTransformer" if self.use_sentence_transformers else "ChromaDB Default",
                "name": self.model_name if self.use_sentence_transformers else "default"
            }
            
            # Add embedding dimension if using sentence transformers
            if self.use_sentence_transformers and self.embedding_model:
                try:
                    model_info["dimension"] = self.embedding_model.get_sentence_embedding_dimension()
                except:
                    model_info["dimension"] = "unknown"
            
            return {
                "total_items": self.collection.count(),
                "categories": category_counts,
                "source_files": source_file_counts,
                "model_info": model_info,
                "persist_directory": self.persist_directory,
                "sentence_transformers_available": SENTENCE_TRANSFORMERS_AVAILABLE
            }
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {}

    def __del__(self):
        """Cleanup when manager is destroyed"""
        if self.client:
            try:
                # ChromaDB handles persistence automatically
                pass
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
