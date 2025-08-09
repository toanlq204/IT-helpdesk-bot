from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from routers import ticket_router, conversation_router, chat_router
import chromadb
from chromadb.config import Settings

load_dotenv()

# Environment variables
CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "helpdesk_kb")

# Create ChromaDB client
chroma_client = chromadb.Client(
    Settings(
        chroma_db_impl="duckdb+parquet",
        persist_directory=CHROMA_PERSIST_DIRECTORY
    )
)

# Create or get collection
if CHROMA_COLLECTION_NAME in [c.name for c in chroma_client.list_collections()]:
    collection = chroma_client.get_collection(CHROMA_COLLECTION_NAME)
else:
    collection = chroma_client.create_collection(
        name=CHROMA_COLLECTION_NAME,
        metadata={"description": "IT HelpDesk chatbot knowledge base"}
    )

def get_collection():
    """Return active ChromaDB collection"""
    return collection

# Create FastAPI app
app = FastAPI(title="IT HelpDesk Chatbot API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create necessary directories
os.makedirs("tickets", exist_ok=True)
os.makedirs("threads", exist_ok=True)
os.makedirs("data", exist_ok=True)
app.include_router(ticket_router, tags=["Tickets"])
app.include_router(conversation_router, tags=["Conversations"])
app.include_router(chat_router, tags=["Chat"])
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "IT HelpDesk Chatbot API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "OK"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 