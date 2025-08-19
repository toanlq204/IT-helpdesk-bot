from fastapi import Query
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from models.ticket_models import TicketCreate
import openai
import os
import json
from pinecone import Pinecone  # Removed unused ServerlessSpec import
from services.ticket_service import TicketService
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain.chains import create_retrieval_chain
from langchain_pinecone import PineconeVectorStore


class ChatService:
    def __init__(
        self,
        chat_data_path: str = "storage/data/messages.json",
        ticket_service: TicketService = TicketService(),
    ):
        self.chat_data_path = chat_data_path
        self.ticket_service = ticket_service
        # Lazy / safe initialization for Pinecone
        self.index_name = "helpdesk-kb"
        self.pinecone_client = None
        pinecone_key = os.getenv("PINECONE_API_KEY")
        if pinecone_key:
            try:
                self.pinecone_client = Pinecone(api_key=pinecone_key)
            except Exception as e:
                print(f"[ChatService] Failed to init Pinecone client: {e}")
                self.pinecone_client = None
        # Embedding client (may be optional)
        try:
            self.openai_client_emb = openai.OpenAI(
                api_key=os.getenv("AZOPENAI_EMBEDDING_API_KEY") or os.getenv(
                    "AZOPENAI_API_KEY"),
                base_url=os.getenv("OPENAI_BASE_URL"),
            )
        except Exception as e:
            print(f"[ChatService] Failed to init embedding client: {e}")
            self.openai_client_emb = None
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

    def get_system_prompt(self) -> list:  # corrected type hint
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

    def query_pinecone(self, message: str, metadata: dict) -> str:
        """Query Pinecone for relevant documents using embeddings to match storage format"""
        if not self.pinecone_client or not self.openai_client_emb:
            return None
        try:
            embedding_response = self.openai_client_emb.embeddings.create(
                input=message, model=os.getenv(
                    "AZOPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
            )
            query_embedding = embedding_response.data[0].embedding
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
        # Fast failure if no OpenAI API key
        if not os.getenv("AZOPENAI_API_KEY"):
            return "OpenAI API key not configured on server. Please set AZOPENAI_API_KEY."

        # Try vector context (ignore failures)
        context = ""
        try:
            vector_results = self.query_pinecone(message, None)
            if (
                vector_results
                and getattr(vector_results, "matches", None)
                and len(vector_results.matches) > 0
                and getattr(vector_results.matches[0], "score", 0) > 0.44
            ):
                context = vector_results.matches[0].metadata.get(
                    "text", "") or ""
        except Exception as e:
            print(f"[ChatService] Context retrieval failed: {e}")

        try:
            client = openai.OpenAI(
                base_url=os.getenv("OPENAI_BASE_URL"), api_key=os.getenv("AZOPENAI_API_KEY")
            )
            response = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "512")),
                temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.1")),
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
                                    "priority": {"type": "string"},
                                },
                            },
                            "required": ["title", "description"],
                        },
                    },
                ],
            )
        except Exception as e:
            print(f"[ChatService] OpenAI request failed: {e}")
            # English fallback
            return "Sorry, the AI system is not responding right now. Please try again later."

        try:
            tool_calls = response.choices[0].message.tool_calls
        except Exception:
            tool_calls = None

        if tool_calls:
            for tool_call in tool_calls:
                if tool_call.function.name == "get_ticket_status":
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                        ticket_id = arguments.get("ticket_id")
                        ticket = self.ticket_service.find_ticket_by_partial_id(
                            ticket_id) if ticket_id else None
                        return self.ticket_to_friendly_message(ticket)
                    except Exception as e:
                        print(f"[ChatService] get_ticket_status error: {e}")
                        return "Unable to retrieve the ticket information."
                elif tool_call.function.name == "create_ticket":
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                        title = arguments.get("title")
                        description = arguments.get("description")
                        priority = arguments.get("priority", "medium")
                        if not title or not description:
                            return "Missing title or description to create a ticket."
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
                        print(f"[ChatService] create_ticket error: {e}")
                        return "Unable to create a ticket at this time."
        else:
            content = getattr(response.choices[0].message, "content", None)
            if content:
                return content
            return "Sorry, I cannot process this request."  # final fallback
