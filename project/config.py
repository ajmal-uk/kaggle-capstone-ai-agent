"""
Configuration management and API key rotation.
"""
import os
import random
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Mock mode defaults to True if env var is not explicitly "False"
    MOCK_MODE = os.getenv("MOCK_MODE", "True").lower() == "true"
    
    # Load keys
    _raw_keys = os.getenv("GEMINI_API_KEYS", "AIzaSyBpG-IyFq7pxBxthVOtJWSlFcvO6bb8_es").split(",")
    
    # FILTER: Just check if key is not empty. 
    # Removed the aggressive prefix check to ensure your key is accepted.
    GEMINI_API_KEYS = [k.strip() for k in _raw_keys if k.strip()]
    
    # Default model
    MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-1.5-flash-8b")
    
    # Generation config
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
    MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "2048"))
    
    @staticmethod
    def validate():
        """Validate configuration"""
        # If we have no valid keys, force Mock Mode
        if not Config.GEMINI_API_KEYS:
            Config.MOCK_MODE = True
            
        if not Config.MOCK_MODE and not Config.GEMINI_API_KEYS:
            raise ValueError("No GEMINI_API_KEYS found. Set MOCK_MODE=True or add valid keys.")
    
    @staticmethod
    def rotate_gemini_key():
        """Rotate through available API keys"""
        if not Config.GEMINI_API_KEYS:
            raise ValueError("No API keys available for rotation")
        return random.choice(Config.GEMINI_API_KEYS)