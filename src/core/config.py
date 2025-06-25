"""
Configuration management for AKRIN AI Chatbot
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = Field(default="AKRIN AI Chatbot", env="APP_NAME")
    app_env: str = Field(default="development", env="APP_ENV")
    debug: bool = Field(default=True, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # API Keys
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    google_ai_api_key: Optional[str] = Field(default=None, env="GOOGLE_AI_API_KEY")
    
    # Database
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    postgres_host: str = Field(default="localhost", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    postgres_db: str = Field(default="akrin_chatbot", env="POSTGRES_DB")
    postgres_user: str = Field(default="chatbot_user", env="POSTGRES_USER")
    postgres_password: str = Field(default="", env="POSTGRES_PASSWORD")
    
    mongodb_uri: str = Field(default="mongodb://localhost:27017/akrin_chatbot", env="MONGODB_URI")
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # Vector Database
    pinecone_api_key: Optional[str] = Field(default=None, env="PINECONE_API_KEY")
    pinecone_environment: str = Field(default="us-east-1-aws", env="PINECONE_ENVIRONMENT")
    pinecone_index_name: str = Field(default="akrin-knowledge-base", env="PINECONE_INDEX_NAME")
    
    # Message Queue
    kafka_bootstrap_servers: str = Field(default="localhost:9092", env="KAFKA_BOOTSTRAP_SERVERS")
    kafka_topic_prefix: str = Field(default="akrin_chatbot_", env="KAFKA_TOPIC_PREFIX")
    
    # Authentication
    jwt_secret_key: str = Field(default="your-secret-key", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(default=24, env="JWT_EXPIRATION_HOURS")
    
    # External Services
    crm_api_url: Optional[str] = Field(default=None, env="CRM_API_URL")
    crm_api_key: Optional[str] = Field(default=None, env="CRM_API_KEY")
    ticketing_api_url: Optional[str] = Field(default=None, env="TICKETING_API_URL")
    ticketing_api_key: Optional[str] = Field(default=None, env="TICKETING_API_KEY")
    
    # Feature Flags
    enable_human_handoff: bool = Field(default=True, env="ENABLE_HUMAN_HANDOFF")
    enable_voice_support: bool = Field(default=False, env="ENABLE_VOICE_SUPPORT")
    enable_analytics: bool = Field(default=True, env="ENABLE_ANALYTICS")
    max_conversation_turns: int = Field(default=20, env="MAX_CONVERSATION_TURNS")
    
    # Rate Limiting
    rate_limit_requests_per_minute: int = Field(default=60, env="RATE_LIMIT_REQUESTS_PER_MINUTE")
    rate_limit_requests_per_hour: int = Field(default=1000, env="RATE_LIMIT_REQUESTS_PER_HOUR")
    
    # CORS
    cors_origins: List[str] = Field(default=["*"])
    
    # Model Configuration
    default_llm_model: str = Field(default="gpt-4", env="DEFAULT_LLM_MODEL")
    llm_temperature: float = Field(default=0.7, env="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=500, env="LLM_MAX_TOKENS")
    
    # Knowledge Base
    knowledge_chunk_size: int = Field(default=500, env="KNOWLEDGE_CHUNK_SIZE")
    knowledge_chunk_overlap: int = Field(default=50, env="KNOWLEDGE_CHUNK_OVERLAP")
    retrieval_top_k: int = Field(default=5, env="RETRIEVAL_TOP_K")
    
    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        if not v:
            raise ValueError("jwt_secret_key must be set")
        return v
    
    @property
    def postgres_url(self) -> str:
        """Construct PostgreSQL connection URL"""
        # Use DATABASE_URL if provided (for Supabase/Render deployment)
        if self.database_url:
            return self.database_url
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.app_env == "production"
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False
    }


# Singleton instance
settings = Settings()