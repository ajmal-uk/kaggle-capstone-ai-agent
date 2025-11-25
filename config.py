"""
Configuration management and API key rotation.
"""
import os
import random
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Mock mode for testing without API calls
    MOCK_MODE = os.getenv("MOCK_MODE", "True").lower() == "true"
    
    # Gemini API Keys (comma-separated list for rotation)
    GEMINI_API_KEYS = os.getenv("GEMINI_API_KEYS", "").split(",")
    GEMINI_API_KEYS = [key.strip() for key in GEMINI_API_KEYS if key.strip()]
    
    # Default model
    MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-1.5-flash-8b")
    
    # Generation config
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
    MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "2048"))
    
    @staticmethod
    def validate():
        """Validate configuration"""
        if not Config.MOCK_MODE and not Config.GEMINI_API_KEYS:
            raise ValueError("No GEMINI_API_KEYS found in environment. Set MOCK_MODE=True or add API keys.")
    
    @staticmethod
    def rotate_gemini_key():
        """Rotate through available API keys"""
        if not Config.GEMINI_API_KEYS:
            raise ValueError("No API keys available for rotation")
        return random.choice(Config.GEMINI_API_KEYS)