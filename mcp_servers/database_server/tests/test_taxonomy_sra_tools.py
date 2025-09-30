"""
Unit tests for taxonomy and SRA-related MCP tools.
"""

import pytest
import json
import sys
import os
from unittest.mock import patch, Mock
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database_mcp_server import (
    get_neighbors,
    get_taxonomy,
    search_sra_studies,
    get_sra_runinfo,
    search_sra_cloud
)

pytestmark = pytest.mark.unit


class TestGetTaxonomy:
    """Tests for get_taxonomy tool."""

    @pytest.mark.asyncio
    async def test_get_taxonomy_basic(self, mock_entrez, mock_taxonomy_record):
        """Test basic taxonomy retrieval."""
        with patch('Bio.Entrez.read', return_value=mock_taxonomy_record):
            result = await get_taxonomy(query="Salmo salar")

            assert isinstance(result, str)
            data = json.loads(result)
            assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_taxonomy_by_accession(self, mock_entrez, mock_taxonomy_record):
        """Test taxonomy lookup by accession number."""
        with patch('Bio.Entrez.read', return_value=mock_taxonomy_record):
            result = await get_taxonomy(query="PV570336")

            assert isinstance(result, str)
            mock_entrez['esearch'].assert_called()

    @pytest.mark.asyncio
    async def test_get_taxonomy_no_results(self, mock_entrez):
        """Test taxonomy query with no results."""
        mock_search_result = {"IdList": []}

        with patch('Bio.Entrez.read', return_value=mock_search_result):
            result = await get_taxonomy(query="NonexistentTaxon")

            assert "No taxonomy found" in result

    @pytest.mark.asyncio
    async def test_get_taxonomy_error_handling(self):
        """Test taxonomy error handling."""
        with patch('Bio.Entrez.esearch', side_effect=Exception("API Error")):
            result = await get_taxonomy(query="Salmo salar")

            assert "Error in get_taxonomy" in result

    @pytest.mark.asyncio
    async def test_get_taxonomy_common_name(self, mock_entrez, mock_taxonomy_record):
        """Test taxonomy lookup with common name."""
        with patch('Bio.Entrez.read', return_value=mock_taxonomy_record):
            result = await get_taxonomy(query="Atlantic salmon")

            assert isinstance(result, str)


class TestGetNeighbors:
    """Tests for get_neighbors tool."""

    @pytest.mark.asyncio
    async def test_get_neighbors_basic(self, mock_entrez, mock_taxonomy_record):
        """Test basic taxonomic neighbor finding."""
        with patch('Bio.Entrez.read', return_value=mock_taxonomy_record):
            result = await get_neighbors(
                taxon="Salmo salar",
                rank="species"
            )

            assert isinstance(result, str)
            data = json.loads(result)
            assert "taxon" in data
            assert "neighbors" in data

    @pytest.mark.asyncio
    async def test_get_neighbors_genus_level(self, mock_entrez, mock_taxonomy_record):
        """Test neighbor finding at genus level."""
        with patch('Bio.Entrez.read', return_value=mock_taxonomy_record):
            result = await get_neighbors(
                taxon="Salmo",
                rank="genus",
                distance=1
            )

            assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_get_neighbors_family_level(self, mock_entrez, mock_taxonomy_record):
        """Test neighbor finding at family level."""
        with patch('Bio.Entrez.read', return_value=mock_taxonomy_record):
            result = await get_neighbors(
                taxon="Salmonidae",
                rank="family",
                distance=2
            )

            assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_get_neighbors_common_misids(self, mock_entrez, mock_taxonomy_record):
        """Test neighbor finding with common misidentifications flag."""
        with patch('Bio.Entrez.read', return_value=mock_taxonomy_record):
            result = await get_neighbors(
                taxon="Salmo salar",
                rank="species",
                common_misIDs=True
            )

            assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_get_neighbors_no_results(self, mock_entrez):
        """Test neighbor finding with no results."""
        mock_search_result = {"IdList": []}

        with patch('Bio.Entrez.read', return_value=mock_search_result):
            result = await get_neighbors(
                taxon="NonexistentTaxon",
                rank="species"
            )

            assert "No taxonomy found" in result

    @pytest.mark.asyncio
    async def test_get_neighbors_error_handling(self):
        """Test neighbor finding error handling."""
        with patch('Bio.Entrez.esearch', side_effect=Exception("Connection error")):
            result = await get_neighbors(
                taxon="Salmo salar",
                rank="species"
            )

            assert "Error in get_neighbors" in result


class TestSearchSRAStudies:
    """Tests for search_sra_studies tool."""

    @pytest.mark.asyncio
    @pytest.mark.sra
    async def test_search_sra_entrez_basic(self, mock_entrez):
        """Test basic SRA search using Entrez."""
        result = await search_sra_studies(
            query="Salmo salar COI",
            search_method="entrez"
        )

        assert isinstance(result, str)
        data = json.loads(result)
        assert "IdList" in data or "Count" in data

    @pytest.mark.asyncio
    @pytest.mark.sra
    async def test_search_sra_with_organism_filter(self, mock_entrez):
        """Test SRA search with organism filter."""
        result = await search_sra_studies(
            query="mitochondrial genome",
            filters={"organism": "Salmo salar"},
            search_method="entrez"
        )

        assert isinstance(result, str)
        # Check that organism filter was included in search
        call_args = mock_entrez['esearch'].call_args
        search_term = call_args[1]['term']
        assert "Salmo salar" in search_term or "Organism" in search_term

    @pytest.mark.asyncio
    @pytest.mark.sra
    async def test_search_sra_with_library_strategy(self, mock_entrez):
        """Test SRA search with library strategy filter."""
        result = await search_sra_studies(
            query="salmon",
            filters={"library_strategy": "AMPLICON"},
            search_method="entrez"
        )

        assert isinstance(result, str)
        call_args = mock_entrez['esearch'].call_args
        search_term = call_args[1]['term']
        assert "AMPLICON" in search_term or "Strategy" in search_term

    @pytest.mark.asyncio
    @pytest.mark.sra
    async def test_search_sra_max_results(self, mock_entrez):
        """Test SRA search with max_results limit."""
        result = await search_sra_studies(
            query="Salmo salar",
            filters={"max_results": 50},
            search_method="entrez"
        )

        call_args = mock_entrez['esearch'].call_args
        assert call_args[1]['retmax'] == 50

    @pytest.mark.asyncio
    @pytest.mark.sra
    async def test_search_sra_cloud_sql_method(self, mock_pysradb):
        """Test SRA search using cloud SQL method."""
        result = await search_sra_studies(
            query="Salmo salar",
            search_method="cloud_sql"
        )

        assert isinstance(result, str)

    @pytest.mark.asyncio
    @pytest.mark.sra
    async def test_search_sra_error_handling(self):
        """Test SRA search error handling."""
        with patch('Bio.Entrez.esearch', side_effect=Exception("Network error")):
            result = await search_sra_studies(
                query="Salmo salar",
                search_method="entrez"
            )

            assert "Error in search_sra_studies" in result


class TestGetSRARunInfo:
    """Tests for get_sra_runinfo tool."""

    @pytest.mark.asyncio
    @pytest.mark.sra
    async def test_get_sra_runinfo_basic(self, mock_pysradb):
        """Test basic SRA run info retrieval."""
        result = await get_sra_runinfo(
            study_accession="PRJNA123456",
            format="json"
        )

        assert isinstance(result, str)
        data = json.loads(result)
        assert isinstance(data, list)

    @pytest.mark.asyncio
    @pytest.mark.sra
    async def test_get_sra_runinfo_with_metadata(self, mock_pysradb):
        """Test SRA run info with sample metadata."""
        result = await get_sra_runinfo(
            study_accession="PRJNA123456",
            include_sample_metadata=True,
            format="json"
        )

        mock_pysradb.sra_metadata.assert_called_with("PRJNA123456", detailed=True)

    @pytest.mark.asyncio
    @pytest.mark.sra
    async def test_get_sra_runinfo_csv_format(self, mock_pysradb):
        """Test SRA run info in CSV format."""
        result = await get_sra_runinfo(
            study_accession="PRJNA123456",
            format="csv"
        )

        assert isinstance(result, str)
        # CSV should have comma-separated values
        assert "," in result or "study_accession" in result.lower()

    @pytest.mark.asyncio
    @pytest.mark.sra
    async def test_get_sra_runinfo_tsv_format(self, mock_pysradb):
        """Test SRA run info in TSV format."""
        result = await get_sra_runinfo(
            study_accession="PRJNA123456",
            format="tsv"
        )

        assert isinstance(result, str)
        # TSV should have tab-separated values
        assert "\t" in result or "study_accession" in result.lower()

    @pytest.mark.asyncio
    @pytest.mark.sra
    async def test_get_sra_runinfo_without_metadata(self, mock_pysradb):
        """Test SRA run info without detailed metadata."""
        result = await get_sra_runinfo(
            study_accession="PRJNA123456",
            include_sample_metadata=False,
            format="json"
        )

        mock_pysradb.sra_metadata.assert_called_with("PRJNA123456", detailed=False)

    @pytest.mark.asyncio
    @pytest.mark.sra
    async def test_get_sra_runinfo_error_handling(self):
        """Test SRA run info error handling."""
        with patch('pysradb.SRAweb', side_effect=Exception("Database error")):
            result = await get_sra_runinfo(
                study_accession="INVALID",
                format="json"
            )

            assert "Error in get_sra_runinfo" in result


class TestSearchSRACloud:
    """Tests for search_sra_cloud tool."""

    @pytest.mark.asyncio
    @pytest.mark.sra
    @pytest.mark.requires_api_key
    async def test_search_sra_cloud_bigquery(self, mock_bigquery):
        """Test SRA cloud search using BigQuery."""
        with patch('database_mcp_server.Config.GOOGLE_APPLICATION_CREDENTIALS', '/fake/path'):
            result = await search_sra_cloud(
                query_sql="SELECT * FROM `nih-sra-datastore.sra.metadata` LIMIT 10",
                platform="bigquery",
                max_rows=10
            )

            # Should attempt to use BigQuery
            assert isinstance(result, str)

    @pytest.mark.asyncio
    @pytest.mark.sra
    async def test_search_sra_cloud_athena_placeholder(self):
        """Test SRA cloud search with Athena (placeholder)."""
        result = await search_sra_cloud(
            query_sql="SELECT * FROM sra_metadata LIMIT 10",
            platform="athena"
        )

        # Athena is not yet implemented
        assert "not yet implemented" in result or "not configured" in result

    @pytest.mark.asyncio
    @pytest.mark.sra
    async def test_search_sra_cloud_max_rows(self, mock_bigquery):
        """Test SRA cloud search with max_rows limit."""
        with patch('database_mcp_server.Config.GOOGLE_APPLICATION_CREDENTIALS', '/fake/path'):
            result = await search_sra_cloud(
                query_sql="SELECT * FROM sra_metadata",
                platform="bigquery",
                max_rows=100
            )

            # Should limit results
            assert isinstance(result, str)

    @pytest.mark.asyncio
    @pytest.mark.sra
    async def test_search_sra_cloud_no_credentials(self):
        """Test SRA cloud search without credentials."""
        with patch('database_mcp_server.Config.GOOGLE_APPLICATION_CREDENTIALS', None):
            result = await search_sra_cloud(
                query_sql="SELECT * FROM sra_metadata",
                platform="bigquery"
            )

            assert "not configured" in result

    @pytest.mark.asyncio
    @pytest.mark.sra
    async def test_search_sra_cloud_error_handling(self):
        """Test SRA cloud search error handling."""
        with patch('database_mcp_server.Config.GOOGLE_APPLICATION_CREDENTIALS', '/fake/path'), \
             patch('google.cloud.bigquery.Client', side_effect=Exception("Query error")):

            result = await search_sra_cloud(
                query_sql="INVALID SQL",
                platform="bigquery"
            )

            assert "Error in search_sra_cloud" in result
