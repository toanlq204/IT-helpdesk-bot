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
    PINECONE_ENVIRONMENT: str = None
    PINECONE_INDEX_NAME: str = None
    
    # LangChain settings
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    CHUNK_SIZE: int = 500  
    CHUNK_OVERLAP: int = 200

    # Azure OpenAI settings (to prevent validation errors)
    AZ_OPEN_AI_CHAT_MODEL: Optional[str] = None
    AZ_OPEN_AI_CHAT_MODEL_TEMPERATURE: Optional[str] = None
    
    class Config:
        env_file = ".env"

settings = Settings()
