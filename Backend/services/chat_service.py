from fastapi import Query
from models.ticket_models import TicketCreate
import openai
import os
import json
import chromadb
from services.ticket_service import TicketService


class ChatService:
    def __init__(
        self,
        chat_data_path: str = "storage/data/messages.json",
        ticket_service: TicketService = TicketService(),
    ):
        self.chat_data_path = chat_data_path
        self.ticket_service = ticket_service
        self.chroma_client = chromadb.PersistentClient(path="storage/chroma_db")
        self.collection = self.chroma_client.get_or_create_collection("files")
        self.openai_client_emb = openai.OpenAI(
            api_key=os.getenv("AZOPENAI_EMBEDDING_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
        )
        os.makedirs(os.path.dirname(chat_data_path), exist_ok=True)
        
        # Check collection health on initialization
        self._check_collection_health()

    def _check_collection_health(self):
        """Check if the collection exists and has compatible embeddings"""
        try:
            # Try to get collection info to see if it has data
            collection_count = self.collection.count()
            print(f"ChromaDB collection 'files' has {collection_count} documents")
            
            if collection_count > 0:
                # Test a simple query to see if embeddings are compatible
                test_embedding = self.openai_client_emb.embeddings.create(
                    input="test query",
                    model=os.getenv("AZOPENAI_EMBEDDING_MODEL")
                ).data[0].embedding
                
                # Try a test query to verify embedding compatibility
                try:
                    self.collection.query(
                        query_embeddings=[test_embedding],
                        n_results=1,
                        include=["distances"]
                    )
                    print("ChromaDB collection embeddings are compatible")
                except Exception as embedding_error:
                    print(f"ChromaDB embedding compatibility issue: {embedding_error}")
                    print("Consider clearing the collection or checking embedding model consistency")
                    
        except Exception as e:
            print(f"ChromaDB collection health check failed: {e}")

    def reset_collection_if_needed(self):
        """Reset the ChromaDB collection to fix embedding dimension mismatches"""
        try:
            print("Resetting ChromaDB collection due to embedding incompatibility...")
            # Delete the existing collection
            self.chroma_client.delete_collection("files")
            # Recreate the collection
            self.collection = self.chroma_client.get_or_create_collection("files")
            print("ChromaDB collection reset successfully")
            return True
        except Exception as e:
            print(f"Failed to reset ChromaDB collection: {e}")
            return False

    def ticket_to_friendly_message(self, ticket: dict) -> str:
        """Transform a ticket dictionary into a user-friendly message."""
        if not ticket:
            return "Ticket not found."
        message = (
            f"Ticket ID: {ticket.get('id', 'N/A')}\n"
            f"Title: {ticket.get('title', 'N/A')}\n"
            f"Description: {ticket.get('description', 'N/A')}\n"
            f"Priority: {ticket.get('priority', 'N/A')}\n"
            f"Status: {ticket.get('status', 'N/A')}\n"
            f"Assignee: {ticket.get('assignee', 'Unassigned')}\n"
            f"Created At: {ticket.get('created_at', 'N/A')}\n"
            f"Last Updated: {ticket.get('updated_at', 'N/A')}\n"
        )
        return message

    def get_system_prompt(self) -> str:
        return [
            {
                "role": "system",
                "content": "You are an IT HelpDesk chatbot assistant. You only provide support for IT-related questions including: computer issues, network problems, software troubleshooting, email problems, printer issues, password resets, VPN connection, hardware malfunctions, system performance, security concerns, and software installation. If a user asks about topics unrelated to IT support (such as general conversation, personal matters, non-IT business questions, weather, etc.), politely inform them that you only assist with IT-related issues and direct them to contact the appropriate department or resource. Always provide clear, helpful, and professional responses for IT support topics. Limit your response to 500 tokens.",
            }
        ]

    def load_data_messages(self) -> list:
        with open(self.chat_data_path, "r") as f:
            return json.load(f)

    def prepare_messages(self, messages: list, context: str) -> list:
        default_messages = self.get_system_prompt()
        if context and context.strip():
            default_messages.append({"role": "user", "content": f"Relevant context from knowledge base: {context}"})
        messages = default_messages + messages
        return messages
    
    def format_chroma_results(self, results) -> str:
        """Format ChromaDB results into a readable context string"""
        if not results or not results.get('documents') or not results['documents'][0]:
            return ""
        
        context_parts = []
        documents = results['documents'][0]  # First query result
        for document in documents:  
            context_parts.append(document)
        return "\n\n".join(context_parts) if context_parts else ""

    def get_metadata(self, message: str) -> dict:
        client = openai.OpenAI(
            base_url=os.getenv("OPENAI_BASE_URL"), api_key=os.getenv("AZOPENAI_API_KEY")
        )
        prompt = f"""
            Analyze the following message and provide metadata in JSON format. Do not include markdown, code fences, or any text before/after the JSON:
            
            Message: {message}
            
            Please provide the following metadata for this chunk:
            {{
                "summary": "Brief summary of this chunk's content",
                "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
                "topics": ["topic1", "topic2", "topic3"],
                "content_type": "",
                "topic_category": "IT/HR/Finance/Security/Network/Hardware/Software/General",
                "difficulty_level": "beginner/intermediate/advanced",
                "key_concepts": ["concept1", "concept2", "concept3"],
                "action_items": ["action1", "action2"] or null if none,
                "technical_terms": ["term1", "term2", "term3"] or null if none
            }}
            
            Return only valid JSON. If chunk is too short or irrelevant, return null values for optional fields.
            """
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL"),
            max_tokens=int(os.getenv("OPENAI_MAX_TOKENS")),
            temperature=float(os.getenv("OPENAI_TEMPERATURE")),
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        try:
            metadata = json.loads(response.choices[0].message.content)
            # Convert list metadata to strings for ChromaDB compatibility
            if metadata:
                if isinstance(metadata.get("keywords"), list):
                    metadata["keywords"] = metadata["keywords"][0]
                if isinstance(metadata.get("topics"), list):
                    metadata["topics"] = metadata["topics"][0]
                if isinstance(metadata.get("key_concepts"), list):
                    metadata["key_concepts"] = metadata["key_concepts"][0]
                if isinstance(metadata.get("action_items"), list):
                    metadata["action_items"] = metadata["action_items"][0]
                if isinstance(metadata.get("technical_terms"), list):
                    metadata["technical_terms"] = metadata["technical_terms"][0]
            return metadata
        except Exception as e:
            print(e)
            return None

    def _build_where_clause(self, metadata: dict) -> dict:
        """Build a proper ChromaDB where clause with operators"""
        if not metadata:
            return {}
        
        # ChromaDB supports logical operators like $and, $or and comparison operators like $eq, $in
        # For this use case, we'll use $or to match any of the metadata fields
        conditions = []
        
        # Build individual conditions for each metadata field
        if metadata.get("topic_category") and metadata["topic_category"] != "unknown":
            conditions.append({"topic_category": {"$eq": metadata["topic_category"]}})
        
        if metadata.get("difficulty_level") and metadata["difficulty_level"] != "unknown":
            conditions.append({"difficulty_level": {"$eq": metadata["difficulty_level"]}})
        
        # For string fields that might contain the search terms
        if metadata.get("keywords"):
            conditions.append({"keywords": {"$eq": metadata["keywords"]}})
        
        if metadata.get("topics"):
            conditions.append({"topics": {"$eq": metadata["topics"]}})
        
        # If we have conditions, combine them with $or
        if conditions:
            if len(conditions) == 1:
                return conditions[0]
            else:
                return {"$or": conditions}
        
        return {}        

    def query_chroma(self, message: str, metadata: dict) -> str:
        """Query ChromaDB for relevant documents using embeddings to match storage format"""
        try:
            # Generate embedding for the query message using the same model as upload service
            embedding_response = self.openai_client_emb.embeddings.create(
                input=message,
                model=os.getenv("AZOPENAI_EMBEDDING_MODEL")
            )
            query_embedding = embedding_response.data[0].embedding
            
            # Use embedding-based query for better semantic search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=3,  # Get top 3 results for better context
                include=["distances", "documents", "metadatas"],
                where=self._build_where_clause(metadata) if metadata else None
            )
            return results
        except Exception as e:
            print(f"Error in query_chroma with embeddings: {e}")
            # Fallback to text-based query if embedding generation fails
            try:
                results = self.collection.query(
                    query_texts=[message],
                    n_results=3,
                    include=["distances", "documents", "metadatas"]
                    # Don't use where clause in fallback to avoid further errors
                )
                return results
            except Exception as fallback_error:
                print(f"Fallback text query also failed: {fallback_error}")
                # Return empty structure if all queries fail
                return {"documents": [[]], "distances": [[]], "metadatas": [[]]}

    # sk-DRKoljlUoP4FtPCOBVy71Q
    def get_response(self, messages: list, message: str) -> str:
        # Query ChromaDB for relevant context
        chroma_results = self.query_chroma(message, self.get_metadata(message))
        # Format the results into a readable context string
        context = self.format_chroma_results(chroma_results)
        
        client = openai.OpenAI(
            base_url=os.getenv("OPENAI_BASE_URL"), api_key=os.getenv("AZOPENAI_API_KEY")
        )

        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL"),
            max_tokens=int(os.getenv("OPENAI_MAX_TOKENS")),
            temperature=float(os.getenv("OPENAI_TEMPERATURE")),
            messages=self.prepare_messages(messages, context),
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "get_ticket_status",
                        "description": "Get the status of a ticket",
                        "parameters": {
                            "type": "object",
                            "properties": {"ticket_id": {"type": "string"}},
                        },
                        "required": ["ticket_id"],
                    },
                },
                {
                    "type": "function",
                    "function": {
                        "name": "create_ticket",
                        "description": "Create a ticket",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "description": {"type": "string"},
                            },
                        },
                        "required": ["title", "description"],
                    },
                },
            ],
        )
        tool_calls = response.choices[0].message.tool_calls
        if tool_calls is not None:
            for tool_call in tool_calls:
                if tool_call.function.name == "get_ticket_status":
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                        ticket_id = arguments["ticket_id"]
                        ticket = self.ticket_service.find_ticket_by_partial_id(
                            ticket_id
                        )
                        return self.ticket_to_friendly_message(ticket)
                    except Exception as e:
                        return None
                elif tool_call.function.name == "create_ticket":
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                        title = arguments["title"]
                        description = arguments["description"]
                        priority = (
                            arguments["priority"]
                            if "priority" in arguments
                            else "medium"
                        )

                        ticket = self.ticket_service.create_ticket(
                            TicketCreate(
                                title=title,
                                description=description,
                                priority=priority,
                                status="open",
                            )
                        )
                        return self.ticket_to_friendly_message(ticket)
                    except Exception as e:
                        return None
        if response.choices[0].message.content is not None:
            return response.choices[0].message.content
        else:
            return None
