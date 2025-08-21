import os
from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    APP_ENV: str = "dev"
    SECRET_KEY: str = "devsecret_change_me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    DB_PATH: str = "./data/app.db"
    UPLOAD_DIR: str = "./storage/uploads"
    ALLOWED_ORIGINS: str = "http://localhost:5173"
    
    # JWT settings
    ALGORITHM: str = "HS256"
    
    # File upload settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = ["pdf", "docx", "txt", "md"]
    
        # AI/RAG settings
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_API_BASE: Optional[str] = None
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_ENVIRONMENT: Optional[str] = None
    PINECONE_INDEX_NAME: Optional[str] = None
    
    # Azure OpenAI settings
    AZ_OPEN_AI_URL: Optional[str] = None
    AZ_OPEN_AI_CHAT_KEY: Optional[str] = None
    AZ_OPEN_AI_CHAT_MODEL: Optional[str] = None
    AZ_OPEN_AI_EMBEDDING_MODEL: Optional[str] = None
    AZ_OPEN_AI_EMBEDDING_KEY: Optional[str] = None
    AZ_OPEN_AI_CHAT_MODEL_TEMPERATURE: Optional[str] = None
    
    # LangChain settings
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    CHUNK_SIZE: int = 500  
    CHUNK_OVERLAP: int = 200
    
    # Chat settings
    MAX_CONVERSATION_TURNS: int = 20
    SYSTEM_PROMPT: str = """You are an expert IT Support Assistant. You help users with technical issues, troubleshooting, and IT-related questions.

Key guidelines:
- Provide clear, step-by-step solutions
- Ask clarifying questions when needed
- Use the provided context from documentation when available
- Be professional but friendly
- If you don't know something, admit it and suggest next steps
- Always prioritize user safety and data security"""
    
    class Config:
        env_file = ".env"

settings = Settings()
