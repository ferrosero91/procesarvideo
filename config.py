import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration"""
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    PORT = int(os.getenv("PORT", 9000))
    HOST = "0.0.0.0"
    
    # Audio processing settings
    AUDIO_SAMPLE_RATE = "16000"
    AUDIO_CHANNELS = "1"
    
    # AI Model settings (optimized for speed and reliability)
    GROQ_TRANSCRIPTION_MODEL = "whisper-large-v3-turbo"  # Faster transcription
    GROQ_CHAT_MODEL = "llama-3.3-70b-versatile"  # Better quality, still fast
    GEMINI_MODEL = "gemini-1.5-flash"  # Stable model with good quota
    GEMINI_FALLBACK_MODEL = "gemini-1.5-flash-8b"
    HUGGINGFACE_MODEL = "meta-llama/Llama-3.2-3B-Instruct"
    OPENROUTER_MODEL = "meta-llama/llama-3.2-3b-instruct:free"
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    
    # Performance settings
    REQUEST_TIMEOUT = 60  # seconds
    MAX_RETRIES = 2
    ENABLE_CACHE = True
    ENABLE_FALLBACK = True  # Auto fallback to other services on error
    
    # MongoDB settings
    MONGODB_HOST = os.getenv("MONGODB_HOST", "localhost")
    MONGODB_PORT = os.getenv("MONGODB_PORT", "27017")
    MONGODB_USERNAME = os.getenv("MONGODB_USERNAME", "")
    MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD", "")
    # Full connection string (Atlas) - if set, this takes precedence
    MONGODB_URI = os.getenv("MONGODB_URI", "")
    MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "video_profile_extractor")
    MONGODB_AUTH_DATABASE = os.getenv("MONGODB_AUTH_DATABASE", "admin")
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not any([cls.GROQ_API_KEY, cls.GEMINI_API_KEY, cls.HUGGINGFACE_API_KEY, cls.OPENROUTER_API_KEY]):
            raise ValueError("At least one API key must be set")
