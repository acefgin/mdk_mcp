"""
Integration tests for database MCP server.

These tests verify the integration between different components
and may make real API calls (when API keys are available).
"""

import pytest
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database_mcp_server import handle_call_tool

pytestmark = pytest.mark.integration


class TestMCPToolIntegration:
    """Integration tests for MCP tool call handling."""

    @pytest.mark.asyncio
    async def test_tool_call_gget_search(self, mock_gget):
        """Test complete tool call workflow for gget_search."""
        result = await handle_call_tool(
            name="gget_search",
            arguments={
                "searchwords": ["COI"],
                "species": "homo_sapiens"
            }
        )

        assert len(result) > 0
        assert result[0].type == "text"
        assert isinstance(result[0].text, str)

    @pytest.mark.asyncio
    async def test_tool_call_get_sequences_gget(self, mock_gget):
        """Test get_sequences tool with gget source."""
        result = await handle_call_tool(
            name="get_sequences",
            arguments={
                "taxon": "homo_sapiens",
                "region": "COI",
                "source": "gget",
                "max_results": 5
            }
        )

        assert len(result) > 0
        assert isinstance(result[0].text, str)

    @pytest.mark.asyncio
    async def test_tool_call_get_sequences_ncbi(self, mock_entrez):
        """Test get_sequences tool with NCBI source."""
        result = await handle_call_tool(
            name="get_sequences",
            arguments={
                "taxon": "Salmo salar",
                "region": "COI",
                "source": "ncbi",
                "max_results": 5,
                "format": "fasta"
            }
        )

        assert len(result) > 0
        assert isinstance(result[0].text, str)

    @pytest.mark.asyncio
    async def test_tool_call_extract_sequence_columns(self, sample_fasta_data):
        """Test extract_sequence_columns tool."""
        result = await handle_call_tool(
            name="extract_sequence_columns",
            arguments={
                "sequence_data": sample_fasta_data,
                "columns": ["Id", "Accession", "Organism"],
                "output_format": "json"
            }
        )

        assert len(result) > 0
        text = result[0].text
        data = json.loads(text)
        assert isinstance(data, list)
        assert len(data) > 0

    @pytest.mark.asyncio
    async def test_tool_call_get_taxonomy(self, mock_entrez, mock_taxonomy_record):
        """Test get_taxonomy tool."""
        from unittest.mock import patch

        with patch('Bio.Entrez.read', return_value=mock_taxonomy_record):
            result = await handle_call_tool(
                name="get_taxonomy",
                arguments={"query": "Salmo salar"}
            )

            assert len(result) > 0
            assert isinstance(result[0].text, str)

    @pytest.mark.asyncio
    async def test_tool_call_search_sra_studies(self, mock_entrez):
        """Test search_sra_studies tool."""
        result = await handle_call_tool(
            name="search_sra_studies",
            arguments={
                "query": "Salmo salar",
                "search_method": "entrez"
            }
        )

        assert len(result) > 0
        assert isinstance(result[0].text, str)

    @pytest.mark.asyncio
    async def test_tool_call_unknown_tool(self):
        """Test calling unknown tool."""
        result = await handle_call_tool(
            name="nonexistent_tool",
            arguments={}
        )

        assert len(result) > 0
        assert "Unknown tool" in result[0].text or "Error" in result[0].text

    @pytest.mark.asyncio
    async def test_tool_call_invalid_arguments(self):
        """Test tool call with invalid arguments."""
        result = await handle_call_tool(
            name="gget_search",
            arguments={
                "invalid_param": "value"
            }
        )

        # Should handle gracefully
        assert len(result) > 0
        assert isinstance(result[0].text, str)


class TestSequenceRetrievalWorkflow:
    """Integration tests for complete sequence retrieval workflows."""

    @pytest.mark.asyncio
    async def test_retrieve_and_extract_workflow(self, mock_entrez, sample_fasta_data):
        """Test workflow: retrieve sequences then extract columns."""
        # Step 1: Retrieve sequences from NCBI
        sequences = await handle_call_tool(
            name="get_sequences",
            arguments={
                "taxon": "Salmo salar",
                "region": "COI",
                "source": "ncbi",
                "max_results": 5,
                "format": "fasta"
            }
        )

        assert len(sequences) > 0
        fasta_data = sequences[0].text

        # Step 2: Extract columns from retrieved sequences
        extracted = await handle_call_tool(
            name="extract_sequence_columns",
            arguments={
                "sequence_data": fasta_data,
                "columns": ["Id", "Organism", "Marker"],
                "output_format": "json"
            }
        )

        assert len(extracted) > 0
        data = json.loads(extracted[0].text)
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_taxonomy_then_sequences_workflow(self, mock_entrez, mock_taxonomy_record):
        """Test workflow: get taxonomy info then retrieve sequences."""
        from unittest.mock import patch

        # Step 1: Get taxonomy information
        with patch('Bio.Entrez.read', return_value=mock_taxonomy_record):
            taxonomy = await handle_call_tool(
                name="get_taxonomy",
                arguments={"query": "Salmo salar"}
            )

            assert len(taxonomy) > 0

        # Step 2: Retrieve sequences for that organism
        sequences = await handle_call_tool(
            name="get_sequences",
            arguments={
                "taxon": "Salmo salar",
                "region": "COI",
                "source": "ncbi",
                "max_results": 5
            }
        )

        assert len(sequences) > 0


class TestErrorHandlingIntegration:
    """Integration tests for error handling across components."""

    @pytest.mark.asyncio
    async def test_network_error_handling(self):
        """Test handling of network errors."""
        from unittest.mock import patch

        with patch('gget.search', side_effect=Exception("Connection timeout")):
            result = await handle_call_tool(
                name="gget_search",
                arguments={
                    "searchwords": ["COI"],
                    "species": "homo_sapiens"
                }
            )

            assert len(result) > 0
            assert "Error" in result[0].text or "timeout" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_invalid_data_error_handling(self):
        """Test handling of invalid input data."""
        result = await handle_call_tool(
            name="extract_sequence_columns",
            arguments={
                "sequence_data": "not valid sequence data",
                "columns": ["Id"],
                "output_format": "json"
            }
        )

        # Should handle gracefully without crashing
        assert len(result) > 0
        assert isinstance(result[0].text, str)

    @pytest.mark.asyncio
    async def test_empty_result_handling(self):
        """Test handling of queries that return no results."""
        from unittest.mock import patch
        import pandas as pd

        with patch('gget.search', return_value=pd.DataFrame()):
            result = await handle_call_tool(
                name="get_sequences",
                arguments={
                    "taxon": "nonexistent_species",
                    "region": "COI",
                    "source": "gget"
                }
            )

            assert len(result) > 0
            assert isinstance(result[0].text, str)


@pytest.mark.slow
@pytest.mark.requires_network
class TestRealAPIIntegration:
    """
    Integration tests that make real API calls.
    Only run when explicitly requested with: pytest -m requires_network
    """

    @pytest.mark.skipif(
        not os.getenv("RUN_NETWORK_TESTS"),
        reason="Real API tests disabled. Set RUN_NETWORK_TESTS=1 to enable"
    )
    @pytest.mark.asyncio
    async def test_real_gget_search(self):
        """Test real gget API call (requires network)."""
        result = await handle_call_tool(
            name="gget_search",
            arguments={
                "searchwords": ["COI"],
                "species": "homo_sapiens"
            }
        )

        assert len(result) > 0
        # Should get real results
        data = json.loads(result[0].text)
        assert len(data) > 0

    @pytest.mark.skipif(
        not os.getenv("RUN_NETWORK_TESTS"),
        reason="Real API tests disabled"
    )
    @pytest.mark.asyncio
    async def test_real_ncbi_taxonomy(self):
        """Test real NCBI taxonomy call (requires network)."""
        result = await handle_call_tool(
            name="get_taxonomy",
            arguments={"query": "Homo sapiens"}
        )

        assert len(result) > 0
        data = json.loads(result[0].text)
        assert len(data) > 0
