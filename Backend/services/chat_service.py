from fastapi import Query
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from models.ticket_models import TicketCreate
import openai
import os
import json
from pinecone import ServerlessSpec, Pinecone
from services.ticket_service import TicketService
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain.chains import create_retrieval_chain


class ChatService:
    def __init__(
        self,
        chat_data_path: str = "storage/data/messages.json",
        ticket_service: TicketService = TicketService(),
    ):
        self.chat_data_path = chat_data_path
        self.ticket_service = ticket_service
        self.pinecone_client = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index_name = "helpdesk-kb"
        self.openai_client_emb = openai.OpenAI(
            api_key=os.getenv("AZOPENAI_EMBEDDING_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
        )
        os.makedirs(os.path.dirname(chat_data_path), exist_ok=True)

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
                "content": """You are an IT HelpDesk chatbot assistant. 
                You only provide support for IT-related questions including: computer issues, network problems, software troubleshooting, email problems, printer issues, password resets, VPN connection, hardware malfunctions, system performance, security concerns, and software installation. 
                If a user asks about topics unrelated to IT support (such as general conversation, personal matters, non-IT business questions, weather, etc.), politely inform them that you only assist with IT-related issues and direct them to contact the appropriate department or resource.
                 Always provide clear, helpful, and professional responses for IT support topics. Limit your response to 500 tokens.""",
            }
        ]

    def load_data_messages(self) -> list:
        with open(self.chat_data_path, "r") as f:
            return json.load(f)

    def prepare_messages(self, messages: list, context: str) -> list:
        default_messages = self.get_system_prompt()
        if context and context.strip():
            default_messages.append(
                {
                    "role": "user",
                    "content": f"Relevant context from knowledge base: {context}",
                }
            )
        messages = default_messages + messages
        return messages

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

        """Build a proper ChromaDB where clause with operators"""
        if not metadata:
            return {}

        # ChromaDB supports logical operators like $and, $or and comparison operators like $eq, $in
        # For this use case, we'll use $or to match any of the metadata fields
        conditions = []

        # Build individual conditions for each metadata field
        if metadata.get("topic_category") and metadata["topic_category"] != "unknown":
            conditions.append(
                {"topic_category": {"$eq": metadata["topic_category"]}})

        if (
            metadata.get("difficulty_level")
            and metadata["difficulty_level"] != "unknown"
        ):
            conditions.append(
                {"difficulty_level": {"$eq": metadata["difficulty_level"]}}
            )

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

        """Query ChromaDB for relevant documents using embeddings to match storage format"""
        try:
            # Generate embedding for the query message using the same model as upload service
            embedding_response = self.openai_client_emb.embeddings.create(
                input=message, model=os.getenv("AZOPENAI_EMBEDDING_MODEL")
            )
            query_embedding = embedding_response.data[0].embedding

            # Use embedding-based query for better semantic search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=3,  # Get top 3 results for better context
                include=["distances", "documents", "metadatas"],
                where=self._build_where_clause(metadata) if metadata else None,
            )
            return results
        except Exception as e:
            print(f"Error in query_chroma with embeddings: {e}")
            # Fallback to text-based query if embedding generation fails
            try:
                results = self.collection.query(
                    query_texts=[message],
                    n_results=3,
                    include=["distances", "documents", "metadatas"],
                    # Don't use where clause in fallback to avoid further errors
                )
                return results
            except Exception as fallback_error:
                print(f"Fallback text query also failed: {fallback_error}")
                # Return empty structure if all queries fail
                return {"documents": [[]], "distances": [[]], "metadatas": [[]]}

    def query_pinecone(self, message: str, metadata: dict) -> str:
        """Query Pinecone for relevant documents using embeddings to match storage format"""
        try:
            # Generate embedding for the query message using the same model as upload service
            embedding_response = self.openai_client_emb.embeddings.create(
                input=message, model=os.getenv("AZOPENAI_EMBEDDING_MODEL")
            )
            query_embedding = embedding_response.data[0].embedding

            # Use embedding-based query for better semantic search
            results = self.pinecone_client.Index(self.index_name).query(
                vector=query_embedding, top_k=1, include_metadata=True
            )
            return results
        except Exception as e:
            print(f"Error in query_pinecone with embeddings: {e}")
            return None

    def query_by_vector(self, message: str) -> str:
        index = self.pinecone_client.Index(self.index_name)
        embeddings = OpenAIEmbeddings(
            api_key=os.getenv("AZOPENAI_EMBEDDING_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
            model=os.getenv("AZOPENAI_EMBEDDING_MODEL"),
        )
        vector_store = PineconeVectorStore(index=index, embedding=embeddings)
        retriever = vector_store.as_retriever(
            search_kwargs={
                "k": 4,
                # Pinecone metadata filter example:
                # "filter": {"source": {"$eq": "kb"}},
                # MMR (diversity) example:
                # "search_type": "mmr", "lambda_mult": 0.5
            }
        )
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            api_key=os.getenv("AZOPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
        )
        rewrite_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You rewrite the user question into a standalone query for retrieval. "
                    "Use the chat history for context, but do not answer.",
                ),
                MessagesPlaceholder("chat_history"),
                ("user", "{input}"),
            ]
        )
        history_aware_retriever = create_history_aware_retriever(
            llm=llm, retriever=retriever, prompt=rewrite_prompt
        )
        answer_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an IT HelpDesk chatbot assistant. 
                You only provide support for IT-related questions including: computer issues, network problems, software troubleshooting, email problems, printer issues, password resets, VPN connection, hardware malfunctions, system performance, security concerns, and software installation. 
                If a user asks about topics unrelated to IT support (such as general conversation, personal matters, non-IT business questions, weather, etc.), politely inform them that you only assist with IT-related issues and direct them to contact the appropriate department or resource.
                 Always provide clear, helpful, and professional responses for IT support topics. Limit your response to 500 tokens.""",
                ),
                MessagesPlaceholder("chat_history"),
                ("user", """Question: {input}
                            Context:\n{context}"""),
            ]
        )
        combine_chain = create_stuff_documents_chain(llm, answer_prompt)
        rag_chain = create_retrieval_chain(
            retriever=history_aware_retriever,  # uses history to rewrite the query
            combine_docs_chain=combine_chain,    # then answers with retrieved context
        )

        return rag_chain.invoke({"input": message})

    # sk-DRKoljlUoP4FtPCOBVy71Q
    def get_response(self, messages: list, message: str) -> str:
        # Query ChromaDB for relevant context
        vector_results = self.query_pinecone(message, None)
        context = ""
        if len(vector_results.matches) > 0 and vector_results.matches[0].score > 0.44:
            context = vector_results.matches[0].metadata.get("text")

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
        elif response.choices[0].message.content is not None:
            if context != "":
                return response.choices[0].message.content
            else:
                return "Sorry, I don't have any information on that topic."
        else:
            return None

    def get_enhanced_response(self, user_message: str, conversation_id: str = None) -> dict:
        """Get enhanced response using ChromaDB knowledge base + OpenAI with confidence logic and conversation history"""
        try:
            # Use the query pipeline for semantic search and AI response with conversation context
            result = query_pipeline.answer_query(
                user_message, conversation_id=conversation_id)

            # Add confidence-based metadata
            confidence_level = result.get("confidence_level", "unknown")
            needs_review = result.get("needs_human_review", False)

            response = {
                "response": result["answer"],
                "sources": result.get("sources", []),
                "retrieved_count": result.get("retrieved_count", 0),
                "confidence_level": confidence_level,
                "needs_human_review": needs_review,
                "top_distance": result.get("top_distance", 1.0),
                "conversation_id": result.get("conversation_id"),
                "conversation_turns": result.get("conversation_turns", 0),
                "log_id": result.get("log_id"),  # For feedback tracking
                "type": "enhanced"
            }

            # Add confidence-based recommendations
            if confidence_level == "low" or needs_review:
                response["recommendation"] = "This query may need human review. Consider creating a support ticket."
            elif confidence_level == "medium":
                response["recommendation"] = "Answer provided with some uncertainty. Verify if this resolves your issue."

            return response

        except Exception as e:
            # Fallback to regular response if enhanced fails
            fallback_response = self.get_response(
                [{"role": "user", "content": user_message}])
            return {
                "response": fallback_response or "I'm having trouble processing your request.",
                "sources": [],
                "retrieved_count": 0,
                "confidence_level": "fallback",
                "needs_human_review": True,
                "type": "fallback",
                "error": str(e),
                "recommendation": "System encountered an error. Please create a support ticket."
            }
