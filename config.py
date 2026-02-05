"""
Polyvuvu Configuration Module
Loads and validates environment variables from .env file.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)


class Config:
    """Application configuration loaded from environment variables."""
    
    # Telegram Configuration
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHANNEL_ID: str = os.getenv("TELEGRAM_CHANNEL_ID", "")
    
    # LLM API Configuration (OpenRouter takes priority)
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Moltbook Configuration (for AI social network posting)
    MOLTBOOK_API_KEY: str = os.getenv("MOLTBOOK_API_KEY", "").strip()
    
    # Scanning Configuration
    SCAN_INTERVAL_MINUTES: int = int(os.getenv("SCAN_INTERVAL_MINUTES", "30"))
    MIN_CONFIDENCE_THRESHOLD: int = int(os.getenv("MIN_CONFIDENCE_THRESHOLD", "7"))
    
    # Polymarket API (no auth required for read-only access)
    POLYMARKET_GAMMA_API: str = "https://gamma-api.polymarket.com"
    
    @classmethod
    def validate(cls) -> list[str]:
        """
        Validate that required configuration is present.
        Returns a list of missing configuration keys.
        """
        missing = []
        
        if not cls.TELEGRAM_BOT_TOKEN:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not cls.TELEGRAM_CHANNEL_ID:
            missing.append("TELEGRAM_CHANNEL_ID")
        if not cls.OPENROUTER_API_KEY and not cls.GEMINI_API_KEY:
            missing.append("OPENROUTER_API_KEY or GEMINI_API_KEY")
            
        return missing
    
    @classmethod
    def is_valid(cls) -> bool:
        """Check if all required configuration is present."""
        return len(cls.validate()) == 0


# Singleton instance
config = Config()
