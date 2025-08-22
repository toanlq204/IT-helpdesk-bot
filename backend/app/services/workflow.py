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


@tool
def create_ticket_tool(title: str, description: str):
    """Create a new support ticket with title and description"""
    logger.info(f"Creating ticket with title: {title} and description: {description}")
    return {"status": "success", "message": "Ticket created successfully"}

@tool
def add_note_to_ticket_tool(ticket_id: str, note: str):
    """Add a note to an existing support ticket with ticket_id and note
    Techinician and Admin can add internal notes to a ticket"""
    logger.info(f"Adding note to ticket with ticket_id: {ticket_id} and note: {note}")
    return {"status": "success", "message": "Note added successfully"}

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
    
    for msg in state["messages"]:
        if isinstance(msg, ToolMessage):
            # Extract tool result content to use as context
            messages_for_llm.append(AIMessage(content=msg.content))
        elif isinstance(msg, (SystemMessage, HumanMessage, AIMessage)) and msg.content != "":
            messages_for_llm.append(msg)
    
    if messages_for_llm:
        resp = llm.invoke(messages_for_llm)
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

tools = [create_ticket_tool, add_note_to_ticket_tool, query_tickets_tool, query_documents_tool]
llm = llm.bind_tools(tools)
tool_node = ToolNode(tools)

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
- Be helpful, professional, and provide step-by-step guidance when possible
- If you can't find relevant information, ask clarifying questions or suggest contacting IT support directly
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
    
    # Convert User object to serializable dictionary
    user_dict = {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role
    }
    
    state = GraphState(
        messages=formatted_messages,
        user_info=user_dict,
        retrieved_docs=[],
        trace_ids=[],
        user_id=str(current_user.id),
        loop_count=0
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

