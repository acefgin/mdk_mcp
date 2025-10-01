"""
Unit tests for gget-related MCP tools.
"""

import pytest
import json
import pandas as pd
from unittest.mock import patch, Mock, AsyncMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database_mcp_server import (
    gget_search, gget_ref, gget_info, gget_seq
)

pytestmark = pytest.mark.unit


class TestGgetSearch:
    """Tests for gget_search tool."""

    @pytest.mark.asyncio
    @pytest.mark.gget
    async def test_gget_search_basic(self, mock_gget):
        """Test basic gget_search functionality."""
        result = await gget_search(
            searchwords=["COI"],
            species="homo_sapiens"
        )

        # Verify gget.search was called with correct arguments
        mock_gget['search'].assert_called_once()
        call_args = mock_gget['search'].call_args

        # Result should be JSON string
        assert isinstance(result, str)
        assert_valid_json(result)

        # Parse and check content
        data = json.loads(result)
        assert isinstance(data, list)

    @pytest.mark.asyncio
    @pytest.mark.gget
    async def test_gget_search_multiple_terms(self, mock_gget):
        """Test gget_search with multiple search terms."""
        result = await gget_search(
            searchwords=["cytochrome", "oxidase"],
            species="salmo_salar",
            id_type="gene",
            andor="and"
        )

        assert isinstance(result, str)
        mock_gget['search'].assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.gget
    async def test_gget_search_transcript_type(self, mock_gget):
        """Test gget_search with transcript id_type."""
        result = await gget_search(
            searchwords=["COI"],
            species="homo_sapiens",
            id_type="transcript"
        )

        assert isinstance(result, str)

    @pytest.mark.asyncio
    @pytest.mark.gget
    async def test_gget_search_error_handling(self):
        """Test gget_search error handling."""
        with patch('gget.search', side_effect=Exception("API Error")):
            result = await gget_search(
                searchwords=["COI"],
                species="invalid_species"
            )

            assert "Error in gget_search" in result
            assert "API Error" in result

    @pytest.mark.asyncio
    @pytest.mark.gget
    async def test_gget_search_empty_result(self):
        """Test gget_search with empty result."""
        with patch('gget.search', return_value=pd.DataFrame()):
            result = await gget_search(
                searchwords=["nonexistent_gene"],
                species="homo_sapiens"
            )

            assert isinstance(result, str)
            data = json.loads(result)
            assert data == []


class TestGgetRef:
    """Tests for gget_ref tool."""

    @pytest.mark.asyncio
    @pytest.mark.gget
    async def test_gget_ref_basic(self, mock_gget):
        """Test basic gget_ref functionality."""
        result = await gget_ref(species="homo_sapiens")

        mock_gget['ref'].assert_called_once_with(
            species="homo_sapiens",
            which="all",
            release=None
        )
        assert isinstance(result, str)

    @pytest.mark.asyncio
    @pytest.mark.gget
    async def test_gget_ref_fasta_only(self, mock_gget):
        """Test gget_ref requesting only FASTA."""
        result = await gget_ref(
            species="salmo_salar",
            which="fasta"
        )

        mock_gget['ref'].assert_called_once()
        call_args = mock_gget['ref'].call_args
        assert call_args[1]['which'] == "fasta"

    @pytest.mark.asyncio
    @pytest.mark.gget
    async def test_gget_ref_specific_release(self, mock_gget):
        """Test gget_ref with specific Ensembl release."""
        result = await gget_ref(
            species="homo_sapiens",
            release=109
        )

        call_args = mock_gget['ref'].call_args
        assert call_args[1]['release'] == 109

    @pytest.mark.asyncio
    @pytest.mark.gget
    async def test_gget_ref_gtf_only(self, mock_gget):
        """Test gget_ref requesting only GTF."""
        result = await gget_ref(
            species="mus_musculus",
            which="gtf"
        )

        call_args = mock_gget['ref'].call_args
        assert call_args[1]['which'] == "gtf"

    @pytest.mark.asyncio
    @pytest.mark.gget
    async def test_gget_ref_error_handling(self):
        """Test gget_ref error handling."""
        with patch('gget.ref', side_effect=Exception("Species not found")):
            result = await gget_ref(species="invalid_species")

            assert "Error in gget_ref" in result
            assert "Species not found" in result


class TestGgetInfo:
    """Tests for gget_info tool."""

    @pytest.mark.asyncio
    @pytest.mark.gget
    async def test_gget_info_single_id(self, mock_gget):
        """Test gget_info with single Ensembl ID."""
        result = await gget_info(ens_ids=["ENSG00000198804"])

        mock_gget['info'].assert_called_once_with(
            ["ENSG00000198804"],
            expand=False
        )
        assert isinstance(result, str)
        assert_valid_json(result)

    @pytest.mark.asyncio
    @pytest.mark.gget
    async def test_gget_info_multiple_ids(self, mock_gget):
        """Test gget_info with multiple Ensembl IDs."""
        ids = ["ENSG00000198804", "ENSG00000198712", "ENSG00000198899"]
        result = await gget_info(ens_ids=ids)

        call_args = mock_gget['info'].call_args
        assert call_args[0][0] == ids

    @pytest.mark.asyncio
    @pytest.mark.gget
    async def test_gget_info_expand_true(self, mock_gget):
        """Test gget_info with expand parameter."""
        result = await gget_info(
            ens_ids=["ENSG00000198804"],
            expand=True
        )

        call_args = mock_gget['info'].call_args
        assert call_args[1]['expand'] is True

    @pytest.mark.asyncio
    @pytest.mark.gget
    async def test_gget_info_error_handling(self):
        """Test gget_info error handling."""
        with patch('gget.info', side_effect=Exception("Invalid ID")):
            result = await gget_info(ens_ids=["INVALID_ID"])

            assert "Error in gget_info" in result
            assert "Invalid ID" in result

    @pytest.mark.asyncio
    @pytest.mark.gget
    async def test_gget_info_empty_list(self, mock_gget):
        """Test gget_info with empty ID list."""
        result = await gget_info(ens_ids=[])

        # Should still call the function
        mock_gget['info'].assert_called_once()


class TestGgetSeq:
    """Tests for gget_seq tool."""

    @pytest.mark.asyncio
    @pytest.mark.gget
    async def test_gget_seq_basic(self, mock_gget):
        """Test basic gget_seq functionality."""
        result = await gget_seq(ens_ids=["ENSG00000198804"])

        mock_gget['seq'].assert_called_once_with(
            ["ENSG00000198804"],
            translate=False,
            seqtype="transcript"
        )
        assert isinstance(result, str)

    @pytest.mark.asyncio
    @pytest.mark.gget
    async def test_gget_seq_translate(self, mock_gget):
        """Test gget_seq with translation."""
        result = await gget_seq(
            ens_ids=["ENSG00000198804"],
            translate=True
        )

        call_args = mock_gget['seq'].call_args
        assert call_args[1]['translate'] is True

    @pytest.mark.asyncio
    @pytest.mark.gget
    async def test_gget_seq_genomic(self, mock_gget):
        """Test gget_seq requesting genomic sequence."""
        result = await gget_seq(
            ens_ids=["ENSG00000198804"],
            seqtype="genomic"
        )

        call_args = mock_gget['seq'].call_args
        assert call_args[1]['seqtype'] == "genomic"

    @pytest.mark.asyncio
    @pytest.mark.gget
    async def test_gget_seq_protein(self, mock_gget):
        """Test gget_seq requesting protein sequence."""
        result = await gget_seq(
            ens_ids=["ENSG00000198804"],
            seqtype="protein"
        )

        call_args = mock_gget['seq'].call_args
        assert call_args[1]['seqtype'] == "protein"

    @pytest.mark.asyncio
    @pytest.mark.gget
    async def test_gget_seq_multiple_ids(self, mock_gget):
        """Test gget_seq with multiple IDs."""
        ids = ["ENSG00000198804", "ENSG00000198712"]
        result = await gget_seq(ens_ids=ids)

        call_args = mock_gget['seq'].call_args
        assert call_args[0][0] == ids

    @pytest.mark.asyncio
    @pytest.mark.gget
    async def test_gget_seq_error_handling(self):
        """Test gget_seq error handling."""
        with patch('gget.seq', side_effect=Exception("Sequence not found")):
            result = await gget_seq(ens_ids=["INVALID_ID"])

            assert "Error in gget_seq" in result
            assert "Sequence not found" in result


def assert_valid_json(json_str: str) -> bool:
    """Helper to validate JSON string."""
    try:
        json.loads(json_str)
        return True
    except json.JSONDecodeError:
        return False
