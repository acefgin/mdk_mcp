"""Configuration settings for the database MCP server."""

import os
from typing import Optional

class Config:
    """Configuration class for database server settings."""
    
    # Server settings
    HOST: str = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("MCP_SERVER_PORT", "8000"))
    
    # API Keys and credentials
    NCBI_API_KEY: Optional[str] = os.getenv("NCBI_API_KEY")
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
    
    # Cache and temporary file settings
    TEMP_DIR: str = os.getenv("TEMP_DIR", "/tmp/mcp_cache")
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour default
    
    # Rate limiting
    MAX_REQUESTS_PER_MINUTE: int = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "60"))
    MAX_RESULTS_DEFAULT: int = int(os.getenv("MAX_RESULTS_DEFAULT", "100"))
    MAX_RESULTS_LIMIT: int = int(os.getenv("MAX_RESULTS_LIMIT", "10000"))
    
    # Database specific settings
    BOLD_BASE_URL: str = "http://www.boldsystems.org/index.php/API_Public"
    SILVA_BASE_URL: str = "https://www.arb-silva.de/search"
    UNITE_BASE_URL: str = "https://unite.ut.ee/sh_files"
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration settings."""
        os.makedirs(cls.TEMP_DIR, exist_ok=True)
        return True
