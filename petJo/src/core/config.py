from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Project Info
    PROJECT_NAME: str
    VERSION: str
    API_V1_STR: str
    ENVIRONMENT: str  # development, staging, production
    
    # Database
    DATABASE_URL: str
    POSTGRES_DB: Optional[str] = None
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_HOST: Optional[str] = None
    POSTGRES_PORT: Optional[int] = None
    
    # Redis
    REDIS_URL: Optional[str] = None
    REDIS_HOST: Optional[str] = "localhost"
    REDIS_PORT: Optional[int] = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    ALLOWED_ORIGINS: List[str]
    
    # Admin User (for initial setup)
    FIRST_SUPERUSER_EMAIL: str
    FIRST_SUPERUSER_PASSWORD: str
    
    # Logging
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FILE: Optional[str] = None  # Set to file path to enable file logging
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = False
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Cache
    CACHE_ENABLED: bool = True
    CACHE_TTL: int = 300  # seconds
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB
    UPLOAD_DIR: str = "uploads"
    
    # Storage Configuration
    STORAGE_PROVIDER: str = "r2"  # "r2" or "local"
    
    # Cloudflare R2 Configuration
    R2_ACCOUNT_ID: Optional[str] = None
    R2_ACCESS_KEY_ID: Optional[str] = None
    R2_SECRET_ACCESS_KEY: Optional[str] = None
    R2_BUCKET_NAME: str = "petjo-images"
    R2_ENDPOINT_URL: Optional[str] = None  # Will be constructed from account_id
    R2_PUBLIC_URL: Optional[str] = None  # e.g., https://pub-xyz.r2.dev or custom domain
    
    # Local Storage (for development)
    LOCAL_STORAGE_URL: str = "http://localhost:8000/uploads"
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Construct R2 endpoint URL if not provided
        if self.R2_ACCOUNT_ID and not self.R2_ENDPOINT_URL:
            self.R2_ENDPOINT_URL = f"https://{self.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="allow"
    )


settings = Settings()
