from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain.schema import BaseMessage
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver  # dev only; use SQLite/Postgres in prod
from typing import TypedDict, List, Optional, Dict
from langchain.tools import tool
from ..core.config import settings
from ..repositories.document_repository import search_documents
import logging
from sqlalchemy.orm import Session
from ..models.user import User

logger = logging.getLogger(__name__)


class GraphState(TypedDict):
    messages: List[BaseMessage]
    user_info: dict
    retrieved_docs: List[dict]
    trace_ids: List[str]
    user_id: str


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
    return {"status": "success", "message": "Documents queried successfully"}

def agent_node(state: GraphState) -> GraphState:
    # The agent “thinks” one step based on dialogue history and may emit a tool call
    resp = llm.invoke(state["messages"])
    return {"messages": state["messages"] + [resp]}

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
graph.add_node("tools", tool_node)

graph.add_edge(START, "agent")
graph.add_conditional_edges(
    "agent",
    tools_condition,           # inspects last message for tool calls
    {"tools": "tools", "end": END}
)
graph.add_edge("tools", "agent")


def run_workflow(db: Session, current_user: User, user_message: str, conversation_history: List[Dict], session_id: str) -> str:
    """Run the workflow with initial messages, user info, and user ID"""
    # Convert conversation history to LangChain format
    formatted_messages = []
    for msg in conversation_history:
        if msg["role"] == "user":
            formatted_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            formatted_messages.append(AIMessage(content=msg["content"]))
    
    # Add the current user message
    formatted_messages.append(HumanMessage(content=user_message))
    
    state = GraphState(
        messages=formatted_messages,
        user_info=current_user,
        retrieved_docs=[],
        trace_ids=[],
        user_id=str(current_user.id)
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

