"""
Configuration settings for the CLM Automation system.
"""
import os

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded from .env file")
except ImportError:
    print("⚠️  python-dotenv not installed. Using system environment variables only.")
except FileNotFoundError:
    print("⚠️  .env file not found. Using system environment variables only.")

class Config:
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    
    # Email Configuration
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    EMAIL_USERNAME = os.getenv("EMAIL_USERNAME", "")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
    REPORT_RECIPIENT = os.getenv("REPORT_RECIPIENT", "admin@company.com")
    
    # Vector Database Configuration
    CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
    
    # Application Settings
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Document Processing
    DOCUMENTS_DIRECTORY = "./documents"
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    
    # Similarity Search
    SIMILARITY_THRESHOLD = 0.7
    MAX_SIMILAR_DOCS = 5
    
    # Contract Monitoring
    EXPIRATION_ALERT_DAYS = 30

