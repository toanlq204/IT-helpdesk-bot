import os
from typing import List, Dict, Any, Tuple, Optional
from openai import OpenAI
from dotenv import load_dotenv
import logging
from services.chroma_service import chroma_service
from services.conversation_memory_service import conversation_memory
from services.query_logging_service import query_logger

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryPipelineService:
    """Service for handling query pipeline: semantic search → build context → call OpenAI"""

    def __init__(self):
        """Initialize OpenAI client and ChromaDB service"""
        try:
            # Initialize OpenAI client
            self.openai_client = OpenAI(
                api_key=os.environ["AZOPENAI_API_KEY"],
                base_url=os.environ.get("OPENAI_BASE_URL")
            )

            # Get model settings from environment
            self.model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
            self.temperature = float(os.environ.get("OPENAI_TEMPERATURE", 0.2))
            self.max_tokens = int(os.environ.get("OPENAI_MAX_TOKENS", 500))

            # Confidence thresholds (adjust per embedding model)
            self.T_high = 0.20  # High confidence threshold
            self.T_low = 0.35   # Low confidence threshold

            logger.info("Query pipeline service initialized successfully")

        except Exception as e:
            logger.error(
                f"Failed to initialize query pipeline service: {str(e)}")
            raise

    def retrieve_from_chroma(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Retrieve relevant documents from ChromaDB"""
        try:
            # Use the existing ChromaService search method
            results = chroma_service.search_faqs(query, n_results=top_k)

            # Convert to the expected format for compatibility
            converted_results = {
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]]
            }

            if results:
                converted_results["documents"][0] = [
                    result["document"] for result in results]
                converted_results["metadatas"][0] = [
                    result["metadata"] for result in results]
                converted_results["distances"][0] = [
                    1 - result["similarity_score"] for result in results]

            return converted_results

        except Exception as e:
            logger.error(f"Failed to retrieve from ChromaDB: {str(e)}")
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

    def determine_confidence_level(self, distances: List[float]) -> Tuple[str, float, bool]:
        """Determine confidence level based on top result distance"""
        if not distances:
            return "no_results", 1.0, False

        top1_distance = distances[0]

        if top1_distance < self.T_high:
            # High confidence - use retrieved context directly
            confidence_level = "high"
            adjusted_temperature = self.temperature
            needs_human_review = False
        elif self.T_high <= top1_distance < self.T_low:
            # Medium confidence - include context but express uncertainty
            confidence_level = "medium"
            adjusted_temperature = self.temperature * \
                0.7  # Lower temperature for uncertainty
            needs_human_review = False
        else:
            # Low confidence - minimal context, general answer, flag for review
            confidence_level = "low"
            adjusted_temperature = self.temperature
            needs_human_review = True

        return confidence_level, adjusted_temperature, needs_human_review

    def build_system_prompt(self, retrieved_res: Dict[str, Any], user_query: str, confidence_level: str = "high", conversation_history: List[Dict[str, str]] = None) -> Tuple[List[Dict[str, str]], List[float]]:
        """Build system prompt with context from retrieved documents based on confidence level"""
        try:
            docs = retrieved_res["documents"][0]
            metas = retrieved_res["metadatas"][0]
            distances = retrieved_res.get("distances", [[]])[0]

            # Initialize conversation history if not provided
            if conversation_history is None:
                conversation_history = []

            if confidence_level == "high":
                # High confidence: Use full context
                context_lines = []
                for i, (d, m) in enumerate(zip(docs, metas)):
                    title = m.get("title", f"doc_{i}")
                    context_lines.append(f"{i+1}. {title}: {d}")
                context = "\n".join(context_lines)

                system_prompt = (
                    "You are an IT helpdesk assistant. Use the provided context from the knowledge base to answer user questions. "
                    "The context provided is highly relevant to the user's question. "
                    "Consider the conversation history to provide contextual responses. "
                    "If the context is insufficient, say you don't know and propose next steps (e.g., create a ticket)."
                )

                # Build messages: [system] + conversation_history + [user_with_context]
                messages = [{"role": "system", "content": system_prompt}]
                messages.extend(conversation_history)
                messages.append({
                    "role": "user",
                    "content": f"Context:\n{context}\n\nUser question: {user_query}"
                })

            elif confidence_level == "medium":
                # Medium confidence: Use context but express uncertainty
                context_lines = []
                # Limit to top 3
                for i, (d, m) in enumerate(zip(docs[:3], metas[:3])):
                    title = m.get("title", f"doc_{i}")
                    context_lines.append(f"{i+1}. {title}: {d}")
                context = "\n".join(context_lines)

                system_prompt = (
                    "You are an IT helpdesk assistant. Use the provided context from the knowledge base to answer user questions. "
                    "The context may be somewhat relevant but express some uncertainty in your response. "
                    "Consider the conversation history to provide contextual responses. "
                    "Start your answer with a phrase like 'I may be uncertain, but based on available information...' "
                    "If the context is insufficient, say you don't know and propose next steps (e.g., create a ticket)."
                )

                # Build messages: [system] + conversation_history + [user_with_context]
                messages = [{"role": "system", "content": system_prompt}]
                messages.extend(conversation_history)
                messages.append({
                    "role": "user",
                    "content": f"Context:\n{context}\n\nUser question: {user_query}"
                })

            else:  # Low confidence
                # Low confidence: Minimal or no context, general answer
                system_prompt = (
                    "You are an IT helpdesk assistant. The knowledge base doesn't contain highly relevant information for this question. "
                    "Provide a general, helpful response based on common IT practices and conversation history. "
                    "Be honest about limitations and strongly recommend creating a support ticket for personalized assistance. "
                    "Suggest that a human IT specialist should review this request."
                )

                # Build messages: [system] + conversation_history + [user_query]
                messages = [{"role": "system", "content": system_prompt}]
                messages.extend(conversation_history)
                messages.append({"role": "user", "content": user_query})

            return messages, distances

        except Exception as e:
            logger.error(f"Failed to build system prompt: {str(e)}")
            return [], []

    def ask_openai(self, messages: List[Dict[str, str]], model: str = None, temperature: float = None) -> str:
        """Call OpenAI API with the prepared messages"""
        try:
            # Use instance defaults if not provided
            model = model or self.model
            temperature = temperature or self.temperature

            response = self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=self.max_tokens
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Failed to call OpenAI: {str(e)}")
            return "I'm sorry, I'm having trouble processing your request right now. Please try again later or contact IT support directly."

    def answer_query(self, query: str, top_k: int = 5, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """Complete query pipeline: retrieve → build context → call OpenAI with confidence logic and conversation history"""
        try:
            logger.info(f"Processing query: {query}")

            # Step 1: Load conversation history if conversation_id provided
            conversation_history = []
            if conversation_id:
                conversation_history = conversation_memory.get_conversation_context(
                    conversation_id)
                logger.info(
                    f"Loaded {len(conversation_history)} messages from conversation {conversation_id}")

            # Step 2: Retrieve from ChromaDB
            retrieved = self.retrieve_from_chroma(query, top_k=top_k)
            distances = retrieved.get("distances", [[]])[0]

            # Step 3: Determine confidence level based on distances
            confidence_level, adjusted_temperature, needs_human_review = self.determine_confidence_level(
                distances)

            logger.info(
                f"Confidence level: {confidence_level}, Distance: {distances[0] if distances else 'N/A'}")

            # Step 4: Build system prompt based on confidence level with conversation history
            messages, _ = self.build_system_prompt(
                retrieved, query, confidence_level, conversation_history)

            # Step 5: Call OpenAI with adjusted temperature
            answer = self.ask_openai(
                messages, temperature=adjusted_temperature)

            # Step 6: Save conversation history if conversation_id provided
            if conversation_id:
                # Add user message
                conversation_memory.add_message(conversation_id, "user", query)
                # Add assistant response
                conversation_memory.add_message(
                    conversation_id, "assistant", answer)

            # Return comprehensive response with confidence information and conversation data
            response = {
                "answer": answer,
                "query": query,
                "conversation_id": conversation_id,
                "conversation_turns": len(conversation_history) // 2 if conversation_history else 0,
                "retrieved_count": len(retrieved["documents"][0]),
                "confidence_level": confidence_level,
                "top_distance": distances[0] if distances else 1.0,
                "needs_human_review": needs_human_review,
                "temperature_used": adjusted_temperature,
                # Count relevant results
                "context_used": len([d for d in distances if d < 1.0]),
                "sources": []
            }

            # Add source information
            docs = retrieved["documents"][0]
            metas = retrieved["metadatas"][0]
            retrieved_docs_for_logging = []

            # Top 3 sources
            for i, (doc, meta) in enumerate(zip(docs[:3], metas[:3])):
                source_info = {
                    "title": meta.get("title", f"Source {i+1}"),
                    "relevance_score": 1 - distances[i] if i < len(distances) else 0,
                    "tags": meta.get("tags", [])
                }
                response["sources"].append(source_info)

                # Prepare for logging
                retrieved_docs_for_logging.append({
                    # We don't have actual doc IDs from ChromaDB
                    "id": f"doc_{i}",
                    "metadata": meta,
                    # Truncate for logging
                    "document": doc[:200] + "..." if len(doc) > 200 else doc
                })

            # Log the query and response
            log_id = query_logger.log_query(
                user_question=query,
                retrieved_docs=retrieved_docs_for_logging,
                distances=distances,
                answer=answer,
                confidence_level=confidence_level,
                conversation_id=conversation_id,
                metadata={
                    "temperature_used": adjusted_temperature,
                    "context_used": response["context_used"],
                    "needs_human_review": needs_human_review
                }
            )

            # Add log_id to response for feedback tracking
            response["log_id"] = log_id

            logger.info(
                f"Query processed successfully. Retrieved {response['retrieved_count']} documents.")
            return response

        except Exception as e:
            logger.error(f"Failed to process query: {str(e)}")
            return {
                "answer": "I'm experiencing technical difficulties. Please contact IT support directly.",
                "query": query,
                "retrieved_count": 0,
                "context_used": 0,
                "sources": [],
                "error": str(e)
            }


# Global instance
query_pipeline = QueryPipelineService()
