import os
from pydantic_settings import BaseSettings
from typing import List

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
    
    class Config:
        env_file = ".env"

settings = Settings()
