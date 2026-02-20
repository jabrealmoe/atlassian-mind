import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    
    JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
    JIRA_EMAIL = os.getenv("JIRA_EMAIL")
    JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
    
    FORGE_WEBHOOK_URL = os.getenv("FORGE_WEBHOOK_URL")
    
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
    
    FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
    FLASK_PORT = int(os.getenv("FLASK_PORT", 5005))
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
