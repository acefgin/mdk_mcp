"""Configuration settings for the processing MCP server."""

import os
from typing import Optional

class Config:
    """Configuration class for processing server settings."""

    # Server settings
    HOST: str = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("MCP_SERVER_PORT", "8001"))

    # Cache and temporary file settings
    TEMP_DIR: str = os.getenv("TEMP_DIR", "/tmp/mcp_processing")
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour default

    # Processing limits
    MAX_SEQUENCES: int = int(os.getenv("MAX_SEQUENCES", "10000"))
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "100"))

    # Tool paths (set to command names if in PATH, or full paths)
    SEQKIT_PATH: str = os.getenv("SEQKIT_PATH", "seqkit")
    VSEARCH_PATH: str = os.getenv("VSEARCH_PATH", "vsearch")

    # QC defaults
    DEFAULT_MIN_LENGTH: int = int(os.getenv("DEFAULT_MIN_LENGTH", "100"))
    DEFAULT_MAX_N_PERCENT: float = float(os.getenv("DEFAULT_MAX_N_PERCENT", "5.0"))

    # Dereplication defaults
    DEFAULT_IDENTITY_THRESHOLD: float = float(os.getenv("DEFAULT_IDENTITY_THRESHOLD", "0.97"))

    # Masking defaults
    DEFAULT_MIN_COMPLEXITY: float = float(os.getenv("DEFAULT_MIN_COMPLEXITY", "1.5"))

    # Chimera detection defaults
    DEFAULT_ABUNDANCE_SKEW: float = float(os.getenv("DEFAULT_ABUNDANCE_SKEW", "2.0"))

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls) -> bool:
        """Validate configuration settings and create required directories."""
        os.makedirs(cls.TEMP_DIR, exist_ok=True)
        return True
