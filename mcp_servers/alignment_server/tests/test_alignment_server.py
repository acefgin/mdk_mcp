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
    calculate_alignment_stats,
    calculate_distance_matrix,
    build_phylogenetic_tree
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


class TestDistanceCalculation:
    """Test distance matrix calculation."""

    def test_calculate_distance_matrix_p_distance(self):
        """Test p-distance calculation."""
        result = calculate_distance_matrix(ALIGNED_FASTA, model="p-distance")
        
        assert result["success"] is True
        assert "distance_matrix" in result
        assert "sequence_names" in result
        assert result["model"] == "p-distance"
        assert result["num_sequences"] == 3
        
        # Check matrix is symmetric
        matrix = result["distance_matrix"]
        assert len(matrix) == 3
        for i in range(3):
            assert len(matrix[i]) == 3
            assert matrix[i][i] == 0.0  # Diagonal should be 0
            for j in range(3):
                assert matrix[i][j] == matrix[j][i]  # Symmetric

    def test_calculate_distance_matrix_jukes_cantor(self):
        """Test Jukes-Cantor distance calculation."""
        result = calculate_distance_matrix(ALIGNED_FASTA, model="jukes-cantor")
        
        assert result["success"] is True
        assert result["model"] == "jukes-cantor"
        assert "distance_matrix" in result

    def test_calculate_distance_matrix_kimura(self):
        """Test Kimura 2-parameter distance calculation."""
        result = calculate_distance_matrix(ALIGNED_FASTA, model="kimura")
        
        assert result["success"] is True
        assert result["model"] == "kimura"
        assert "distance_matrix" in result

    def test_calculate_distance_matrix_invalid_model(self):
        """Test with invalid model."""
        result = calculate_distance_matrix(ALIGNED_FASTA, model="invalid-model")
        
        assert result["success"] is False
        assert "error" in result
        assert "not supported" in result["error"].lower()

    def test_calculate_distance_matrix_invalid_fasta(self):
        """Test with invalid FASTA."""
        result = calculate_distance_matrix(INVALID_FASTA, model="p-distance")
        
        assert result["success"] is False
        assert "error" in result


class TestPhylogenyBuilding:
    """Test phylogenetic tree building."""

    def test_build_phylogeny_nj_p_distance(self):
        """Test NJ tree building with p-distance."""
        result = build_phylogenetic_tree(ALIGNED_FASTA, method="nj", model="p-distance")
        
        assert result["success"] is True
        assert "tree_newick" in result
        assert result["method"] == "neighbor_joining"
        assert result["model"] == "p-distance"
        assert result["num_taxa"] == 3
        assert result["tree_newick"].strip().endswith(";")  # Newick format ends with ;

    def test_build_phylogeny_nj_jukes_cantor(self):
        """Test NJ tree building with Jukes-Cantor."""
        result = build_phylogenetic_tree(ALIGNED_FASTA, method="nj", model="jukes-cantor")
        
        assert result["success"] is True
        assert result["model"] == "jukes-cantor"
        assert "tree_newick" in result

    def test_build_phylogeny_nj_kimura(self):
        """Test NJ tree building with Kimura."""
        result = build_phylogenetic_tree(ALIGNED_FASTA, method="nj", model="kimura")
        
        assert result["success"] is True
        assert result["model"] == "kimura"
        assert "tree_newick" in result

    def test_build_phylogeny_mp_fallback(self):
        """Test maximum parsimony falls back to NJ."""
        result = build_phylogenetic_tree(ALIGNED_FASTA, method="mp", model="kimura")
        
        assert result["success"] is True
        assert result["method"] == "neighbor_joining"  # Falls back to NJ
        assert "tree_newick" in result

    def test_build_phylogeny_ml_fallback(self):
        """Test ML method falls back to NJ."""
        result = build_phylogenetic_tree(ALIGNED_FASTA, method="ml", model="kimura")
        
        assert result["success"] is True
        assert result["method"] == "neighbor_joining"  # Falls back to NJ

    def test_build_phylogeny_invalid_method(self):
        """Test with invalid method."""
        result = build_phylogenetic_tree(ALIGNED_FASTA, method="invalid", model="kimura")
        
        assert result["success"] is False
        assert "error" in result

    def test_build_phylogeny_invalid_model(self):
        """Test with invalid model for NJ."""
        result = build_phylogenetic_tree(ALIGNED_FASTA, method="nj", model="invalid-model")
        
        assert result["success"] is False
        assert "error" in result


class TestConfiguration:
    """Test configuration loading."""

    def test_config_imports(self):
        """Test that config can be imported."""
        from config import Config
        assert Config.PORT == 8002
        assert Config.LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
