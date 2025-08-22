from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain.schema import BaseMessage
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver  # dev only; use SQLite/Postgres in prod
from typing import TypedDict, List, Optional, Dict, Annotated
from operator import add
from langchain.tools import tool
from ..core.config import settings
from ..repositories.document_repository import search_documents
import logging
from sqlalchemy.orm import Session
from ..models.user import User

logger = logging.getLogger(__name__)


class GraphState(TypedDict):
    messages: Annotated[List[BaseMessage], add]
    user_info: dict
    retrieved_docs: List[dict]
    trace_ids: List[str]
    user_id: str
    loop_count: int
    llm_instance: object  # Store the LLM instance in state


def create_ticket_tool_factory(db: Session, user_info: dict):
    """Factory function to create the ticket tool with database access"""
    @tool
    def create_ticket_tool(title: str, description: str, priority: str = "medium"):
        """Create a new support ticket with title, description, and priority (low/medium/high)"""
        try:
            from ..services.ticket_service import create_ticket
            from ..schemas.ticket import TicketCreate
            
            logger.info(f"Creating ticket for user {user_info['id']}: {title}")
            
            # Create ticket data
            ticket_data = TicketCreate(
                title=title,
                description=description,
                priority=priority
            )
            
            # Create the ticket in database
            new_ticket = create_ticket(db, ticket_data, user_info['id'])
            
            if new_ticket:
                return {
                    "status": "success",
                    "message": f"Ticket #{new_ticket.id} created successfully: '{title}'",
                    "ticket_id": new_ticket.id,
                    "ticket_title": new_ticket.title,
                    "ticket_description": new_ticket.description,
                    "ticket_priority": new_ticket.priority,
                    "ticket_status": new_ticket.status
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to create ticket due to database error"
                }
                
        except Exception as e:
            logger.error(f"Error creating ticket: {e}")
            return {
                "status": "error",
                "message": f"Error creating ticket: {str(e)}"
            }
    
    return create_ticket_tool

def add_note_to_ticket_tool_factory(db: Session, user_info: dict):
    """Factory function to create the add note tool with database access"""
    @tool
    def add_note_to_ticket_tool(ticket_id: int, note: str, is_internal: bool = False):
        """Add a note to an existing support ticket with ticket_id, note content, and internal flag
        Set is_internal=True for notes only visible to technicians and admins"""
        try:
            from ..services.ticket_service import add_ticket_note
            from ..schemas.ticket import TicketNoteCreate
            
            logger.info(f"Adding note to ticket {ticket_id} by user {user_info['id']}")
            note = "AI Assistant added this note: " + note
            if user_info['role'] == "user" and is_internal:
                return {
                    "status": "error",
                    "message": "You are not authorized to add internal notes"
                }
            # Create note data
            note_data = TicketNoteCreate(
                body=note,
                is_internal=is_internal
            )
            
            # Create a simple user object for the ticket service
            from ..models.user import User
            
            # Get the user from database to ensure we have all needed fields
            user = db.query(User).filter(User.id == user_info['id']).first()
            if not user:
                return {
                    "status": "error", 
                    "message": "User not found"
                }
            
            # Add the note to the ticket
            new_note = add_ticket_note(db, ticket_id, note_data, user)
            
            if new_note:
                note_type = "internal" if new_note.is_internal else "public"
                return {
                    "status": "success",
                    "message": f"{note_type.title()} note added successfully to ticket #{ticket_id}",
                    "note_id": new_note.id,
                    "ticket_id": new_note.ticket_id,
                    "note_content": new_note.body,
                    "note_type": note_type,
                    "author_id": new_note.author_id,
                    "created_at": new_note.created_at.isoformat()
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to add note to ticket #{ticket_id}. Ticket may not exist or you may not have permission."
                }
                
        except Exception as e:
            logger.error(f"Error adding note to ticket {ticket_id}: {e}")
            return {
                "status": "error",
                "message": f"Error adding note to ticket: {str(e)}"
            }
    
    return add_note_to_ticket_tool

@tool
def query_tickets_tool(status: Optional[str] = None):
    """Query all support tickets for the user with status, title, and description
    Default is to return all tickets with status in progress, or open"""
    logger.info(f"Querying tickets with status: {status}")
    return {"status": "success", "message": "Tickets queried successfully"}

@tool
def query_documents_tool(query: str):
    """Query the knowledge base for documents matching the query about the user's issue, technical issue or question or guidance
    Return the documents that are most relevant to the user's issue, technical issue or question

    """
    logger.info(f"Querying documents with query: {query}")
    try:
        relevant_chunks = search_documents(query, limit=3)
        
        if not relevant_chunks:
            return {
                "status": "success", 
                "message": "No relevant documents found in knowledge base.",
                "documents": []
            }
        
        documents = []
        for i, chunk in enumerate(relevant_chunks, 1):
            filename = chunk["metadata"].get("filename", "Unknown")
            content = chunk["content"]
            score = chunk.get("score", 0)
            
            documents.append({
                "document_id": i,
                "filename": filename,
                "content": content,
                "relevance_score": round(score, 3)
            })
        
        # Format response for the LLM
        response_text = f"Found {len(documents)} relevant documents:\n\n"
        for doc in documents:
            response_text += f"{doc['content']}\n\n"
        
        return {"status": "success", "message": response_text, "documents": documents}
        
    except Exception as e:
        logger.error(f"Error querying documents: {e}")
        return {
            "status": "error",
            "message": f"Error retrieving documents from knowledge base: {str(e)}",
            "documents": []
        }

def should_continue(state: GraphState) -> str:
    """Decide whether to continue with tools or end the conversation"""
    # Check for loop limit
    loop_count = state.get("loop_count", 0)
    if loop_count >= 3:  # Maximum 3 tool calls
        logger.info("Reached maximum loop count, ending conversation")
        return "end"
    
    # Check if the last message has tool calls
    messages = state["messages"]
    if messages and hasattr(messages[-1], 'tool_calls') and messages[-1].tool_calls:
        return "tools"
    else:
        return "end"

def agent_node(state: GraphState) -> GraphState:
    # The agent "thinks" one step based on dialogue history and may emit a tool call
    # Extract tool results and include them in the system context for Azure OpenAI compatibility
    messages_for_llm = []
    tool_context_parts = []
    last_message = state["messages"][-1]
    if isinstance(last_message, ToolMessage):
        if (last_message.name == "create_ticket_tool"):
            messages_for_llm.append(SystemMessage(content=f"""
                You are an IT Support Assistant. You have created a new ticket:
                Reponse all ticket information to the user in a friendly and helpful manner.
                {last_message.content}
            """))
            current_llm = state.get("llm_instance", llm)
            resp = current_llm.invoke(messages_for_llm)
            return {"messages": [resp]}
        elif (last_message.name == "add_note_to_ticket_tool"):
            messages_for_llm.append(SystemMessage(content=f"""
                You are an IT Support Assistant. You have helped to add a note to a ticket:
                Response with the note information to the user in a friendly and helpful manner.
                Include the note details and confirm it was added successfully or not.
                {last_message.content}
            """))
            current_llm = state.get("llm_instance", llm)
            resp = current_llm.invoke(messages_for_llm)
            return {"messages": [resp]} 

    for msg in state["messages"]:
        if isinstance(msg, ToolMessage):
            # Extract tool result content to use as context
            messages_for_llm.append(AIMessage(content=msg.content))
        elif isinstance(msg, (SystemMessage, HumanMessage, AIMessage)) and msg.content != "":
            messages_for_llm.append(msg)
    
    if messages_for_llm:
        # Use the LLM instance from state (with tools bound)
        current_llm = state.get("llm_instance", llm)
        resp = current_llm.invoke(messages_for_llm)
        return {"messages": [resp]}  # Only return the new message, LangGraph will add it to existing
    
    return {"messages": []}

def tool_node_wrapper(state: GraphState) -> GraphState:
    """Wrapper around tool node to increment loop count"""
    # Increment loop count
    current_count = state.get("loop_count", 0)
    new_count = current_count + 1
    
    # Call the actual tool node
    result = tool_node.invoke(state)
    
    # Add the loop count to the result
    result["loop_count"] = new_count
    logger.info(f"Tool execution complete, loop count: {new_count}")
    
    return result

llm = ChatOpenAI(
    api_key=settings.AZ_OPEN_AI_CHAT_KEY,
    base_url=settings.AZ_OPEN_AI_URL,
    model=settings.AZ_OPEN_AI_CHAT_MODEL,
    temperature=float(settings.AZ_OPEN_AI_CHAT_MODEL_TEMPERATURE or "0.7"),
    max_tokens=1000,
    timeout=30,
)

# Tools will be initialized in run_workflow with database access
tools = []
llm_with_tools = None
tool_node = None

graph = StateGraph(GraphState)
 
graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node_wrapper)

graph.add_edge(START, "agent")
graph.add_conditional_edges(
    "agent",
    should_continue,           # Use our custom condition with loop control
    {"tools": "tools", "end": END}
)
graph.add_edge("tools", "agent")


def run_workflow(db: Session, current_user: User, user_message: str, conversation_history: List[Dict], session_id: str) -> str:
    """Run the workflow with initial messages, user info, and user ID"""
    
    # Convert User object to serializable dictionary
    user_dict = {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role
    }
    
    # Initialize tools with database access
    create_ticket_tool = create_ticket_tool_factory(db, user_dict)
    add_note_tool = add_note_to_ticket_tool_factory(db, user_dict)
    workflow_tools = [create_ticket_tool, add_note_tool, query_tickets_tool, query_documents_tool]
    
    # Bind tools to LLM and create tool node
    llm_with_tools = llm.bind_tools(workflow_tools)
    workflow_tool_node = ToolNode(workflow_tools)
    
    # Update global tool_node for this workflow execution
    global tool_node
    tool_node = workflow_tool_node
    
    # Convert conversation history to LangChain format
    formatted_messages = []
    
    # Add system prompt for the agent
    system_prompt = """You are an IT Support Assistant. You have access to the following tools:

1. query_documents_tool: Search the knowledge base for relevant documentation and solutions
2. create_ticket_tool: Create new support tickets for issues that need tracking
3. add_note_to_ticket_tool: Add notes to existing tickets (for technicians/admins)
4. query_tickets_tool: Search and retrieve existing support tickets

Guidelines:
- Always search the knowledge base first using query_documents_tool when users ask technical questions
- Use the retrieved documents to provide accurate, helpful responses
- Create tickets for issues that require follow-up or cannot be resolved immediately
- Always reponse with ticket information: ticket_id, ticket_title, ticket_description, ticket notes, ticket_priority, ticket_status when user ask for ticket information or after creating a ticket
- Be helpful, professional, and provide step-by-step guidance when possible
- IMPORTANT: If you can't find relevant information, DO NOT reponse with common guide, ask user to contact IT support directly
"""
    formatted_messages.append(SystemMessage(content=system_prompt))
    
    # Only include user and assistant messages from history, skip any tool messages
    for msg in conversation_history:
        if msg["role"] == "user":
            formatted_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            formatted_messages.append(AIMessage(content=msg["content"]))
        # Skip any other roles like 'tool' that might cause issues
    
    # Add the current user message
    formatted_messages.append(HumanMessage(content=user_message))
    
    # Debug logging
    logger.info(f"Initializing workflow with {len(formatted_messages)} messages")
    for i, msg in enumerate(formatted_messages):
        msg_type = getattr(msg, 'type', 'unknown')
        content_preview = str(msg.content)[:100] + "..." if len(str(msg.content)) > 100 else str(msg.content)
        logger.info(f"Initial message {i}: type={msg_type}, content={content_preview}")
    
    state = GraphState(
        messages=formatted_messages,
        user_info=user_dict,
        retrieved_docs=[],
        trace_ids=[],
        user_id=str(current_user.id),
        loop_count=0,
        llm_instance=llm_with_tools
    )
    app = graph.compile(checkpointer=MemorySaver())
    result = app.invoke(state, config={"configurable": {"thread_id": session_id}})
    
    # Extract the last AI message from the result
    if result and "messages" in result and result["messages"]:
        last_message = result["messages"][-1]
        if hasattr(last_message, 'content'):
            return last_message.content
        else:
            return str(last_message)
    
    return "I'm sorry, I couldn't generate a response at this time."

