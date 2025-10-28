#!/usr/bin/env python3
"""
Basic tests for alignment MCP server.
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from alignment_mcp_server import (
    validate_fasta,
    count_sequences,
    calculate_alignment_stats
)


# Test data
VALID_FASTA = """>seq1
ATCGATCGATCG
>seq2
ATCGATCGTTTT
>seq3
ATCGGGGGGGGG
"""

ALIGNED_FASTA = """>seq1
ATCG-ATCGATCG
>seq2
ATCG-ATCGTTTT
>seq3
ATCG-GGGGGGGG
"""

INVALID_FASTA = "not a fasta file"


class TestHelperFunctions:
    """Test helper functions."""

    def test_validate_fasta_valid(self):
        """Test validation with valid FASTA."""
        assert validate_fasta(VALID_FASTA) is True

    def test_validate_fasta_invalid(self):
        """Test validation with invalid FASTA."""
        assert validate_fasta(INVALID_FASTA) is False

    def test_validate_fasta_empty(self):
        """Test validation with empty string."""
        assert validate_fasta("") is False

    def test_count_sequences(self):
        """Test sequence counting."""
        assert count_sequences(VALID_FASTA) == 3

    def test_count_sequences_empty(self):
        """Test counting with empty string."""
        assert count_sequences("") == 0


class TestAlignmentStats:
    """Test alignment statistics calculation."""

    def test_calculate_alignment_stats(self):
        """Test basic alignment statistics."""
        stats = calculate_alignment_stats(ALIGNED_FASTA)

        assert "num_sequences" in stats
        assert stats["num_sequences"] == 3

        assert "alignment_length" in stats
        assert stats["alignment_length"] == 13

        assert "average_gaps_per_sequence" in stats
        assert stats["average_gaps_per_sequence"] == 1.0

        assert "average_conservation" in stats


class TestConfiguration:
    """Test configuration loading."""

    def test_config_imports(self):
        """Test that config can be imported."""
        from config import Config
        assert Config.PORT == 8002
        assert Config.LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
