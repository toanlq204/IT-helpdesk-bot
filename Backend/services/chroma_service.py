import chromadb
import json
import os
from typing import List, Dict, Any, Optional
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
import uuid
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChromaService:
    """Service for managing ChromaDB operations for IT helpdesk FAQs"""

    def __init__(self):
        """Initialize ChromaDB client and collection"""
        try:
            # Persistent client
            self.client = chromadb.PersistentClient(path="chroma_db")

            # Use default embedding function instead of OpenAI to avoid API key issues
            # For production, you'd use OpenAI embeddings, but for testing we'll use default
            try:
                # Try OpenAI first
                self.openai_ef = embedding_functions.OpenAIEmbeddingFunction(
                    api_key=os.environ.get("AZOPENAI_API_KEY", ""),
                    api_base=os.environ.get("OPENAI_BASE_URL", ""),
                    model_name="text-embedding-ada-002"
                )
                # Test with a simple embedding
                test_embed = self.openai_ef(["test"])
                logger.info("Using OpenAI embeddings")
                embedding_function = self.openai_ef
            except Exception as e:
                logger.warning(
                    f"OpenAI embeddings failed: {str(e)}, falling back to default")
                # Use default sentence transformer embeddings
                embedding_function = embedding_functions.DefaultEmbeddingFunction()

            # Create collection (or get if exists)
            self.collection = self.client.get_or_create_collection(
                name="it_faq",
                embedding_function=embedding_function,
                metadata={"description": "IT Helpdesk FAQ knowledge base"}
            )

            logger.info("ChromaDB service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB service: {str(e)}")
            raise

    def add_faq(self, faq_id: str, title: str, text: str, tags: List[str] = None) -> bool:
        """Add a single FAQ to the ChromaDB collection"""
        try:
            # Combine title and text for better search results
            combined_text = f"{title}\n{text}"

            # Prepare metadata (ChromaDB doesn't support lists, so join tags as string)
            metadata = {
                "title": title,
                # Convert list to comma-separated string
                "tags": ",".join(tags) if tags else "",
                "text_length": len(text)
            }

            # Add to collection (ChromaDB will handle embedding automatically)
            self.collection.add(
                ids=[faq_id],
                documents=[combined_text],
                metadatas=[metadata]
            )

            logger.info(f"Added FAQ: {faq_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to add FAQ {faq_id}: {str(e)}")
            return False

    def add_faqs_bulk(self, faqs: List[Dict[str, Any]]) -> int:
        """Add multiple FAQs to the collection"""
        successful_adds = 0

        for faq in faqs:
            faq_id = faq.get("id", str(uuid.uuid4()))
            title = faq.get("title", "")
            text = faq.get("text", "")
            tags = faq.get("tags", [])

            if self.add_faq(faq_id, title, text, tags):
                successful_adds += 1

        logger.info(f"Successfully added {successful_adds}/{len(faqs)} FAQs")
        return successful_adds

    def search_faqs(self, query: str, n_results: int = 5, filter_tags: List[str] = None) -> List[Dict[str, Any]]:
        """Search for relevant FAQs based on query"""
        try:
            # Prepare where clause for filtering
            where_clause = None
            if filter_tags:
                where_clause = {"tags": {"$in": filter_tags}}

            # Search in collection (ChromaDB will handle query embedding automatically)
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_clause,
                include=["documents", "metadatas", "distances"]
            )

            # Format results
            formatted_results = []
            if results["ids"] and results["ids"][0]:
                for i in range(len(results["ids"][0])):
                    formatted_results.append({
                        "id": results["ids"][0][i],
                        "document": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        # Convert distance to similarity
                        "similarity_score": 1 - results["distances"][0][i],
                        "title": results["metadatas"][0][i].get("title", ""),
                        # Convert back to list
                        "tags": results["metadatas"][0][i].get("tags", "").split(",") if results["metadatas"][0][i].get("tags") else []
                    })

            logger.info(
                f"Found {len(formatted_results)} results for query: {query}")
            return formatted_results

        except Exception as e:
            logger.error(f"Failed to search FAQs: {str(e)}")
            return []

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the FAQ collection"""
        try:
            count = self.collection.count()
            return {
                "total_faqs": count,
                "collection_name": self.collection.name,
                "status": "healthy" if count > 0 else "empty"
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {str(e)}")
            return {"status": "error", "error": str(e)}

    def delete_faq(self, faq_id: str) -> bool:
        """Delete a FAQ by ID"""
        try:
            self.collection.delete(ids=[faq_id])
            logger.info(f"Deleted FAQ: {faq_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete FAQ {faq_id}: {str(e)}")
            return False

    def update_faq(self, faq_id: str, title: str, text: str, tags: List[str] = None) -> bool:
        """Update an existing FAQ"""
        try:
            # Delete old version
            self.delete_faq(faq_id)
            # Add new version
            return self.add_faq(faq_id, title, text, tags)
        except Exception as e:
            logger.error(f"Failed to update FAQ {faq_id}: {str(e)}")
            return False

    def load_mock_data(self, file_path: str = "data/mock_faq_data.json") -> bool:
        """Load mock FAQ data into ChromaDB collection"""
        try:
            # Load FAQ items from JSON file
            with open(file_path, 'r', encoding='utf-8') as f:
                faq_items = json.load(f)

            # Prepare data for bulk insert as per the example
            ids = [item["id"] for item in faq_items]
            documents = [item["text"] for item in faq_items]
            metadatas = [{"title": item["title"], "tags": ",".join(
                item.get("tags", []))} for item in faq_items]

            # Add to collection in bulk
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )

            logger.info(
                f"Successfully loaded {len(faq_items)} FAQ items into ChromaDB")
            return True

        except FileNotFoundError:
            logger.error(f"Mock data file not found: {file_path}")
            return False
        except Exception as e:
            logger.error(f"Failed to load mock data: {str(e)}")
            return False


# Global instance
chroma_service = ChromaService()
