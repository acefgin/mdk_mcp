"""Configuration settings for the design MCP server."""

import os
from typing import Optional

class Config:
    """Configuration class for design server settings."""

    # Server settings
    HOST: str = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("MCP_SERVER_PORT", "8003"))

    # Cache and temporary file settings
    TEMP_DIR: str = os.getenv("TEMP_DIR", "/tmp/mcp_design")
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour default

    # Processing limits
    MAX_SEQUENCES: int = int(os.getenv("MAX_SEQUENCES", "10000"))
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "200"))
    MAX_ALIGNMENT_LENGTH: int = int(os.getenv("MAX_ALIGNMENT_LENGTH", "50000"))

    # Tool paths (set to command names if in PATH, or full paths)
    PRIMER3_PATH: str = os.getenv("PRIMER3_PATH", "primer3_core")
    VIENNARNA_PATH: str = os.getenv("VIENNARNA_PATH", "RNAfold")

    # Signature region discovery defaults
    DEFAULT_WINDOW_SIZE: int = int(os.getenv("DEFAULT_WINDOW_SIZE", "150"))
    DEFAULT_STEP_SIZE: int = int(os.getenv("DEFAULT_STEP_SIZE", "10"))
    DEFAULT_MIN_CONSERVATION: float = float(os.getenv("DEFAULT_MIN_CONSERVATION", "0.8"))
    DEFAULT_MIN_DIVERGENCE: float = float(os.getenv("DEFAULT_MIN_DIVERGENCE", "0.3"))

    # Primer design defaults
    DEFAULT_PRIMER_SIZE_MIN: int = int(os.getenv("DEFAULT_PRIMER_SIZE_MIN", "18"))
    DEFAULT_PRIMER_SIZE_OPT: int = int(os.getenv("DEFAULT_PRIMER_SIZE_OPT", "22"))
    DEFAULT_PRIMER_SIZE_MAX: int = int(os.getenv("DEFAULT_PRIMER_SIZE_MAX", "27"))

    DEFAULT_PRIMER_TM_MIN: float = float(os.getenv("DEFAULT_PRIMER_TM_MIN", "57.0"))
    DEFAULT_PRIMER_TM_OPT: float = float(os.getenv("DEFAULT_PRIMER_TM_OPT", "60.0"))
    DEFAULT_PRIMER_TM_MAX: float = float(os.getenv("DEFAULT_PRIMER_TM_MAX", "63.0"))

    DEFAULT_PRIMER_GC_MIN: float = float(os.getenv("DEFAULT_PRIMER_GC_MIN", "40.0"))
    DEFAULT_PRIMER_GC_OPT: float = float(os.getenv("DEFAULT_PRIMER_GC_OPT", "50.0"))
    DEFAULT_PRIMER_GC_MAX: float = float(os.getenv("DEFAULT_PRIMER_GC_MAX", "60.0"))

    DEFAULT_PRODUCT_SIZE_MIN: int = int(os.getenv("DEFAULT_PRODUCT_SIZE_MIN", "80"))
    DEFAULT_PRODUCT_SIZE_OPT: int = int(os.getenv("DEFAULT_PRODUCT_SIZE_OPT", "150"))
    DEFAULT_PRODUCT_SIZE_MAX: int = int(os.getenv("DEFAULT_PRODUCT_SIZE_MAX", "300"))

    # Region ranking weights
    DEFAULT_WEIGHT_CONSERVATION: float = float(os.getenv("DEFAULT_WEIGHT_CONSERVATION", "0.4"))
    DEFAULT_WEIGHT_SPECIFICITY: float = float(os.getenv("DEFAULT_WEIGHT_SPECIFICITY", "0.4"))
    DEFAULT_WEIGHT_COMPLEXITY: float = float(os.getenv("DEFAULT_WEIGHT_COMPLEXITY", "0.2"))

    # Oligo QC defaults
    DEFAULT_SALT_CONC_MM: float = float(os.getenv("DEFAULT_SALT_CONC_MM", "50.0"))
    DEFAULT_MG_CONC_MM: float = float(os.getenv("DEFAULT_MG_CONC_MM", "2.0"))
    DEFAULT_OLIGO_CONC_NM: float = float(os.getenv("DEFAULT_OLIGO_CONC_NM", "250.0"))
    DEFAULT_MAX_HAIRPIN_TM: float = float(os.getenv("DEFAULT_MAX_HAIRPIN_TM", "47.0"))
    DEFAULT_MAX_DIMER_TM: float = float(os.getenv("DEFAULT_MAX_DIMER_TM", "47.0"))

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls) -> bool:
        """Validate configuration settings and create required directories."""
        os.makedirs(cls.TEMP_DIR, exist_ok=True)
        return True
