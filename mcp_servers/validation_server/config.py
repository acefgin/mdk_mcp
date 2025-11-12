"""Configuration settings for the validation MCP server."""

import os
from typing import Optional

class Config:
    """Configuration class for validation server settings."""

    # Server settings
    HOST: str = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("MCP_SERVER_PORT", "8004"))

    # Cache and temporary file settings
    TEMP_DIR: str = os.getenv("TEMP_DIR", "/tmp/mcp_validation")
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour default
    BLAST_CACHE_DIR: str = os.getenv("BLAST_CACHE_DIR", "/tmp/mcp_validation/blast_cache")

    # Processing limits
    MAX_SEQUENCES: int = int(os.getenv("MAX_SEQUENCES", "10000"))
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "200"))
    MAX_QUERY_LENGTH: int = int(os.getenv("MAX_QUERY_LENGTH", "10000"))

    # NCBI/Entrez settings
    NCBI_API_KEY: Optional[str] = os.getenv("NCBI_API_KEY")
    NCBI_EMAIL: str = os.getenv("NCBI_EMAIL", "user@example.com")
    NCBI_TOOL_NAME: str = os.getenv("NCBI_TOOL_NAME", "mdk_mcp_validation")

    # Rate limiting
    NCBI_REQUEST_DELAY: float = float(os.getenv("NCBI_REQUEST_DELAY", "0.34"))  # ~3 req/sec
    NCBI_REQUEST_DELAY_WITH_KEY: float = float(os.getenv("NCBI_REQUEST_DELAY_WITH_KEY", "0.11"))  # ~10 req/sec

    # BLAST tool paths
    BLASTN_PATH: str = os.getenv("BLASTN_PATH", "blastn")
    BLASTP_PATH: str = os.getenv("BLASTP_PATH", "blastp")
    BLASTX_PATH: str = os.getenv("BLASTX_PATH", "blastx")
    TBLASTN_PATH: str = os.getenv("TBLASTN_PATH", "tblastn")
    TBLASTX_PATH: str = os.getenv("TBLASTX_PATH", "tblastx")
    MAKEBLASTDB_PATH: str = os.getenv("MAKEBLASTDB_PATH", "makeblastdb")

    # BLAST database paths (following NCBI recommendations)
    # See: https://github.com/ncbi/blast_plus_docs
    BLAST_DB_DIR: Optional[str] = os.getenv("BLASTDB", os.getenv("BLAST_DB_DIR"))
    BLAST_DB_CUSTOM_DIR: Optional[str] = os.getenv("BLASTDB_CUSTOM")
    NT_DATABASE: Optional[str] = os.getenv("NT_DATABASE")  # Path to local nt database
    NR_DATABASE: Optional[str] = os.getenv("NR_DATABASE")  # Path to local nr database

    # gget BLAST defaults
    DEFAULT_BLAST_PROGRAM: str = os.getenv("DEFAULT_BLAST_PROGRAM", "blastn")
    DEFAULT_BLAST_DATABASE: str = os.getenv("DEFAULT_BLAST_DATABASE", "nt")
    DEFAULT_BLAST_LIMIT: int = int(os.getenv("DEFAULT_BLAST_LIMIT", "50"))
    DEFAULT_BLAST_EVALUE: float = float(os.getenv("DEFAULT_BLAST_EVALUE", "10.0"))
    DEFAULT_BLAST_LOW_COMP_FILT: bool = os.getenv("DEFAULT_BLAST_LOW_COMP_FILT", "false").lower() == "true"

    # Local BLAST defaults
    DEFAULT_BLAST_PERC_IDENTITY: float = float(os.getenv("DEFAULT_BLAST_PERC_IDENTITY", "90.0"))
    DEFAULT_BLAST_MAX_TARGETS: int = int(os.getenv("DEFAULT_BLAST_MAX_TARGETS", "50"))
    DEFAULT_BLAST_EVALUE_LOCAL: float = float(os.getenv("DEFAULT_BLAST_EVALUE_LOCAL", "0.001"))
    DEFAULT_BLAST_WORD_SIZE: int = int(os.getenv("DEFAULT_BLAST_WORD_SIZE", "11"))

    # BLAT defaults
    DEFAULT_BLAT_SEQTYPE: str = os.getenv("DEFAULT_BLAT_SEQTYPE", "DNA")
    DEFAULT_BLAT_ASSEMBLY: str = os.getenv("DEFAULT_BLAT_ASSEMBLY", "human")

    # In-silico PCR defaults
    DEFAULT_MAX_MISMATCHES: int = int(os.getenv("DEFAULT_MAX_MISMATCHES", "2"))
    DEFAULT_MIN_PRODUCT_SIZE: int = int(os.getenv("DEFAULT_MIN_PRODUCT_SIZE", "50"))
    DEFAULT_MAX_PRODUCT_SIZE: int = int(os.getenv("DEFAULT_MAX_PRODUCT_SIZE", "500"))
    DEFAULT_ALLOW_INTERNAL_MISMATCHES: bool = os.getenv("DEFAULT_ALLOW_INTERNAL_MISMATCHES", "true").lower() == "true"

    # Coverage assessment defaults
    DEFAULT_COVERAGE_MIN_AMPLICON: int = int(os.getenv("DEFAULT_COVERAGE_MIN_AMPLICON", "50"))
    DEFAULT_COVERAGE_MAX_AMPLICON: int = int(os.getenv("DEFAULT_COVERAGE_MAX_AMPLICON", "500"))
    DEFAULT_COVERAGE_SENSITIVITY_THRESHOLD: float = float(os.getenv("DEFAULT_COVERAGE_SENSITIVITY_THRESHOLD", "0.95"))
    DEFAULT_COVERAGE_SPECIFICITY_THRESHOLD: float = float(os.getenv("DEFAULT_COVERAGE_SPECIFICITY_THRESHOLD", "0.95"))

    # PubMed search defaults
    DEFAULT_PUBMED_MAX_RESULTS: int = int(os.getenv("DEFAULT_PUBMED_MAX_RESULTS", "20"))
    DEFAULT_PUBMED_RETMODE: str = os.getenv("DEFAULT_PUBMED_RETMODE", "xml")
    DEFAULT_PUBMED_SORT: str = os.getenv("DEFAULT_PUBMED_SORT", "relevance")  # or "pub_date"

    # Complete validation defaults
    DEFAULT_VALIDATION_BLAST_TARGET: bool = os.getenv("DEFAULT_VALIDATION_BLAST_TARGET", "true").lower() == "true"
    DEFAULT_VALIDATION_BLAST_OFFTARGET: bool = os.getenv("DEFAULT_VALIDATION_BLAST_OFFTARGET", "true").lower() == "true"
    DEFAULT_VALIDATION_IN_SILICO_PCR: bool = os.getenv("DEFAULT_VALIDATION_IN_SILICO_PCR", "true").lower() == "true"
    DEFAULT_VALIDATION_COVERAGE: bool = os.getenv("DEFAULT_VALIDATION_COVERAGE", "true").lower() == "true"
    DEFAULT_VALIDATION_LITERATURE: bool = os.getenv("DEFAULT_VALIDATION_LITERATURE", "true").lower() == "true"

    # Validation thresholds
    VALIDATION_MIN_SENSITIVITY: float = float(os.getenv("VALIDATION_MIN_SENSITIVITY", "0.90"))
    VALIDATION_MIN_SPECIFICITY: float = float(os.getenv("VALIDATION_MIN_SPECIFICITY", "0.95"))
    VALIDATION_MAX_OFFTARGET_HITS: int = int(os.getenv("VALIDATION_MAX_OFFTARGET_HITS", "5"))

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls) -> bool:
        """Validate configuration settings and create required directories."""
        # Create required directories
        os.makedirs(cls.TEMP_DIR, exist_ok=True)
        os.makedirs(cls.BLAST_CACHE_DIR, exist_ok=True)

        # Validate NCBI email
        if not cls.NCBI_EMAIL or cls.NCBI_EMAIL == "user@example.com":
            import warnings
            warnings.warn(
                "NCBI_EMAIL not set properly. Please set a valid email address "
                "to comply with NCBI's usage policies."
            )

        # Set request delay based on API key availability
        if cls.NCBI_API_KEY:
            cls.EFFECTIVE_REQUEST_DELAY = cls.NCBI_REQUEST_DELAY_WITH_KEY
        else:
            cls.EFFECTIVE_REQUEST_DELAY = cls.NCBI_REQUEST_DELAY

        return True

    @classmethod
    def get_blast_db_path(cls, db_name: str) -> Optional[str]:
        """
        Get the path to a local BLAST database.

        Args:
            db_name: Database name (e.g., 'nt', 'nr')

        Returns:
            Full path to database or None if not available locally
        """
        if db_name == "nt" and cls.NT_DATABASE:
            return cls.NT_DATABASE
        elif db_name == "nr" and cls.NR_DATABASE:
            return cls.NR_DATABASE
        elif cls.BLAST_DB_DIR:
            # Try to construct path from BLAST_DB_DIR
            return os.path.join(cls.BLAST_DB_DIR, db_name)
        return None

    @classmethod
    def use_local_blast(cls, db_name: str) -> bool:
        """
        Check if local BLAST should be used for a given database.

        Args:
            db_name: Database name

        Returns:
            True if local database is available, False otherwise
        """
        db_path = cls.get_blast_db_path(db_name)
        if db_path and os.path.exists(f"{db_path}.nin"):  # Check for nucleotide index
            return True
        if db_path and os.path.exists(f"{db_path}.pin"):  # Check for protein index
            return True
        return False
