"""Configuration settings for the alignment MCP server."""

import os
from typing import Optional

class Config:
    """Configuration class for alignment server settings."""

    # Server settings
    HOST: str = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("MCP_SERVER_PORT", "8002"))

    # Cache and temporary file settings
    TEMP_DIR: str = os.getenv("TEMP_DIR", "/tmp/mcp_alignment")
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour default

    # Processing limits
    MAX_SEQUENCES: int = int(os.getenv("MAX_SEQUENCES", "10000"))
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "200"))

    # Tool paths (set to command names if in PATH, or full paths)
    MAFFT_PATH: str = os.getenv("MAFFT_PATH", "mafft")
    MUSCLE_PATH: str = os.getenv("MUSCLE_PATH", "muscle")
    CLUSTALO_PATH: str = os.getenv("CLUSTALO_PATH", "clustalo")

    # Alignment defaults
    DEFAULT_MAFFT_STRATEGY: str = os.getenv("DEFAULT_MAFFT_STRATEGY", "auto")
    DEFAULT_MAX_ITERATIONS: int = int(os.getenv("DEFAULT_MAX_ITERATIONS", "1000"))
    DEFAULT_GAP_THRESHOLD: float = float(os.getenv("DEFAULT_GAP_THRESHOLD", "0.5"))

    # Phylogeny defaults
    DEFAULT_PHYLO_METHOD: str = os.getenv("DEFAULT_PHYLO_METHOD", "nj")
    DEFAULT_BOOTSTRAP: int = int(os.getenv("DEFAULT_BOOTSTRAP", "100"))
    DEFAULT_DISTANCE_MODEL: str = os.getenv("DEFAULT_DISTANCE_MODEL", "kimura")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls) -> bool:
        """Validate configuration settings and create required directories."""
        os.makedirs(cls.TEMP_DIR, exist_ok=True)
        return True
