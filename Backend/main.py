from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from routers import ticket_router, conversation_router, chat_router, upload_router
# Load environment variables
load_dotenv()

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
os.makedirs("storage/tickets", exist_ok=True)
os.makedirs("storage/threads", exist_ok=True)
os.makedirs("storage/data", exist_ok=True)
os.makedirs("storage/chroma_db", exist_ok=True)  # For file upload service

app.include_router(ticket_router, tags=["Tickets"])
app.include_router(conversation_router, tags=["Conversations"])
app.include_router(chat_router, tags=["Chat"])
app.include_router(upload_router, tags=["File Upload"])

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