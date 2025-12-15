from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """
    Configuration management system using Pydantic for type-safe settings.
    
    This class defines the required and optional configuration fields for the application,
    with automatic loading from environment variables and .env file.
    """
    
    # Required fields
    TELEGRAM_TOKEN: str = Field(..., description="Telegram Bot API token")
    GROQ_API_KEY: str = Field(..., description="GROQ API key for LLM integration")
    
    # Optional fields with defaults
    CACHE_TTL: int = Field(default=21600, description="Cache time-to-live in seconds (default: 6 hours)")
    DATABASE_URL: str = Field(default="sqlite:///bot.db", description="Database connection URL")
    
    class Config:
        """Pydantic configuration for environment variable handling."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra environment variables not defined in the model

# Create a global settings instance
def get_settings() -> Settings:
    """
    Factory function to create and return a Settings instance.
    
    Returns:
        Settings: An instance of the Settings class with loaded configuration.
    """
    return Settings()

# Initialize settings for immediate use
settings = get_settings()