"""Configuration module for Story-Book application."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-prod')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = 2592000  # 30 days
    
    # Database
    MONGO_URI = os.getenv('MONGO_URI')
    
    # AI APIs
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
    FREEPIK_API_KEY = os.getenv('FREEPIK_API_KEY')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    # Models
    TEXT_MODEL = "google/gemini-2.0-flash-exp:free"
    MODEL_LIST = [
        "gemini-2.0-flash-exp",
        "gemini-1.5-flash",
        "gemini-1.5-flash-8b",
        "google/gemini-2.0-flash-exp:free",
        "meta-llama/llama-3.2-3b-instruct:free",
        "mistralai/mistral-7b-instruct:free",
        "microsoft/phi-3-mini-128k-instruct:free"
    ]
    
    # Redis
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Rate Limiting
    RATE_LIMIT_STORIES_PER_DAY = int(os.getenv('RATE_LIMIT_STORIES_PER_DAY', '5'))
    
    # Monitoring
    SENTRY_DSN = os.getenv('SENTRY_DSN')
    
    # File Storage
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    @classmethod
    def validate(cls):
        """Validate required environment variables."""
        required_vars = {
            'MONGO_URI': cls.MONGO_URI,
            'OPENROUTER_API_KEY': cls.OPENROUTER_API_KEY,
            'FREEPIK_API_KEY': cls.FREEPIK_API_KEY,
        }
        
        missing = [key for key, value in required_vars.items() if not value]
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        return True


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
