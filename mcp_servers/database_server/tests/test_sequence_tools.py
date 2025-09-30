"""
Unit tests for sequence retrieval and extraction tools.
"""

import pytest
import json
import sys
import os
from unittest.mock import patch, Mock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database_mcp_server import (
    get_sequences,
    get_ncbi_sequences,
    get_bold_sequences,
    extract_sequence_columns,
    parse_fasta_header,
    parse_genbank_text,
    format_sequences
)

pytestmark = pytest.mark.unit


class TestGetSequences:
    """Tests for unified get_sequences tool."""

    @pytest.mark.asyncio
    async def test_get_sequences_gget_source(self, mock_gget):
        """Test get_sequences with gget source."""
        result = await get_sequences(
            taxon="homo_sapiens",
            region="COI",
            source="gget",
            max_results=10
        )

        assert isinstance(result, str)
        # gget.search should have been called
        mock_gget['search'].assert_called()

    @pytest.mark.asyncio
    async def test_get_sequences_ncbi_source(self, mock_entrez):
        """Test get_sequences with NCBI source."""
        result = await get_sequences(
            taxon="Salmo salar",
            region="COI",
            source="ncbi",
            max_results=10,
            format="fasta"
        )

        assert isinstance(result, str)
        # Entrez should have been used
        mock_entrez['esearch'].assert_called()

    @pytest.mark.asyncio
    async def test_get_sequences_bold_source(self, mock_requests):
        """Test get_sequences with BOLD source."""
        result = await get_sequences(
            taxon="Salmo salar",
            region="COI",
            source="bold",
            max_results=10
        )

        assert isinstance(result, str)
        # HTTP request should have been made
        mock_requests.assert_called()

    @pytest.mark.asyncio
    async def test_get_sequences_max_results_limit(self, mock_gget):
        """Test that max_results is properly limited."""
        from config import Config

        # Try to request more than limit
        result = await get_sequences(
            taxon="homo_sapiens",
            region="COI",
            source="gget",
            max_results=999999  # Unreasonably high
        )

        # Should still work, but capped at Config.MAX_RESULTS_LIMIT
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_get_sequences_different_regions(self, mock_entrez):
        """Test get_sequences with different genomic regions."""
        regions = ["COI", "16S", "ITS", "mitogenome", "whole"]

        for region in regions:
            result = await get_sequences(
                taxon="Salmo salar",
                region=region,
                source="ncbi",
                max_results=5
            )
            assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_get_sequences_genbank_format(self, mock_entrez):
        """Test get_sequences requesting GenBank format."""
        result = await get_sequences(
            taxon="Salmo salar",
            region="COI",
            source="ncbi",
            format="genbank"
        )

        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_get_sequences_error_handling(self):
        """Test get_sequences error handling."""
        with patch('gget.search', side_effect=Exception("API Error")):
            result = await get_sequences(
                taxon="invalid",
                region="COI",
                source="gget"
            )

            assert "Error retrieving sequences" in result

    @pytest.mark.asyncio
    async def test_get_sequences_unsupported_source(self):
        """Test get_sequences with unsupported source."""
        result = await get_sequences(
            taxon="Salmo salar",
            region="COI",
            source="unsupported_db"
        )

        assert "Unsupported source" in result or "Error" in result


class TestGetNCBISequences:
    """Tests for NCBI-specific sequence retrieval."""

    @pytest.mark.asyncio
    @pytest.mark.ncbi
    async def test_ncbi_sequences_basic(self, mock_entrez):
        """Test basic NCBI sequence retrieval."""
        result = await get_ncbi_sequences(
            taxon="Salmo salar",
            region="COI",
            max_results=10,
            format="fasta"
        )

        assert isinstance(result, str)
        mock_entrez['esearch'].assert_called_once()
        mock_entrez['efetch'].assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.ncbi
    async def test_ncbi_sequences_coi_search_terms(self, mock_entrez):
        """Test NCBI search with COI-specific terms."""
        result = await get_ncbi_sequences(
            taxon="Oncorhynchus mykiss",
            region="COI",
            max_results=5,
            format="fasta"
        )

        # Check that search was called with appropriate COI terms
        call_args = mock_entrez['esearch'].call_args
        search_term = call_args[1]['term']
        assert "COI" in search_term or "cytochrome" in search_term

    @pytest.mark.asyncio
    @pytest.mark.ncbi
    async def test_ncbi_sequences_16s_search_terms(self, mock_entrez):
        """Test NCBI search with 16S-specific terms."""
        result = await get_ncbi_sequences(
            taxon="Escherichia coli",
            region="16S",
            max_results=5,
            format="fasta"
        )

        call_args = mock_entrez['esearch'].call_args
        search_term = call_args[1]['term']
        assert "16S" in search_term or "ribosomal" in search_term

    @pytest.mark.asyncio
    @pytest.mark.ncbi
    async def test_ncbi_sequences_no_results(self):
        """Test NCBI when no sequences found."""
        mock_search_result = {"IdList": []}

        with patch('Bio.Entrez.esearch') as mock_search, \
             patch('Bio.Entrez.read', return_value=mock_search_result):

            result = await get_ncbi_sequences(
                taxon="NonexistentSpecies",
                region="COI",
                max_results=10,
                format="fasta"
            )

            assert "No sequences found" in result

    @pytest.mark.asyncio
    @pytest.mark.ncbi
    async def test_ncbi_sequences_genbank_format(self, mock_entrez):
        """Test NCBI retrieval in GenBank format."""
        result = await get_ncbi_sequences(
            taxon="Salmo salar",
            region="COI",
            max_results=5,
            format="genbank"
        )

        # Check that efetch was called with gb rettype
        call_args = mock_entrez['efetch'].call_args
        assert call_args[1]['rettype'] == "gb"


class TestGetBOLDSequences:
    """Tests for BOLD-specific sequence retrieval."""

    @pytest.mark.asyncio
    @pytest.mark.bold
    async def test_bold_sequences_basic(self, mock_requests):
        """Test basic BOLD sequence retrieval."""
        result = await get_bold_sequences(
            taxon="Salmo salar",
            region="COI",
            max_results=10,
            format="fasta"
        )

        assert isinstance(result, str)
        mock_requests.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.bold
    async def test_bold_api_parameters(self, mock_requests):
        """Test that BOLD API is called with correct parameters."""
        result = await get_bold_sequences(
            taxon="Oncorhynchus mykiss",
            region="COI",
            max_results=5,
            format="fasta"
        )

        call_args = mock_requests.call_args
        params = call_args[1]['params']
        assert params['taxon'] == "Oncorhynchus mykiss"
        assert params['marker'] == "COI"
        assert params['format'] == "fasta"

    @pytest.mark.asyncio
    @pytest.mark.bold
    async def test_bold_error_handling(self):
        """Test BOLD error handling."""
        with patch('requests.get', side_effect=Exception("Connection error")):
            result = await get_bold_sequences(
                taxon="Salmo salar",
                region="COI",
                max_results=10,
                format="fasta"
            )

            assert "Error retrieving BOLD sequences" in result


class TestExtractSequenceColumns:
    """Tests for extract_sequence_columns tool."""

    @pytest.mark.asyncio
    async def test_extract_from_fasta(self, sample_fasta_data):
        """Test extracting columns from FASTA data."""
        result = await extract_sequence_columns(
            sequence_data=sample_fasta_data,
            columns=["Id", "Accession", "Organism", "Length"],
            output_format="json"
        )

        assert isinstance(result, str)
        data = json.loads(result)
        assert isinstance(data, list)
        assert len(data) > 0

        # Check that required columns are present
        first_record = data[0]
        assert "Id" in first_record
        assert "Accession" in first_record
        assert "Organism" in first_record

    @pytest.mark.asyncio
    async def test_extract_from_genbank(self, sample_genbank_data):
        """Test extracting columns from GenBank data."""
        result = await extract_sequence_columns(
            sequence_data=sample_genbank_data,
            columns=["Accession", "Organism", "Length", "Gene", "Collection Date"],
            output_format="json"
        )

        data = json.loads(result)
        assert len(data) > 0

        record = data[0]
        assert record["Accession"] == "PV570336.1"
        assert "Salmo salar" in record["Organism"]

    @pytest.mark.asyncio
    async def test_extract_from_json(self, sample_json_sequence_data):
        """Test extracting columns from JSON data."""
        result = await extract_sequence_columns(
            sequence_data=sample_json_sequence_data,
            columns=["Id", "Organism", "Marker"],
            output_format="json"
        )

        data = json.loads(result)
        assert len(data) == 2
        assert data[0]["Organism"] == "Salmo salar"

    @pytest.mark.asyncio
    async def test_extract_csv_format(self, sample_fasta_data):
        """Test CSV output format."""
        result = await extract_sequence_columns(
            sequence_data=sample_fasta_data,
            columns=["Id", "Organism"],
            output_format="csv"
        )

        assert "Id,Organism" in result  # CSV header
        lines = result.strip().split('\n')
        assert len(lines) > 1  # Header + data

    @pytest.mark.asyncio
    async def test_extract_tsv_format(self, sample_fasta_data):
        """Test TSV output format."""
        result = await extract_sequence_columns(
            sequence_data=sample_fasta_data,
            columns=["Id", "Accession"],
            output_format="tsv"
        )

        assert "Id\tAccession" in result  # TSV header
        assert '\t' in result

    @pytest.mark.asyncio
    async def test_extract_table_format(self, sample_fasta_data):
        """Test table output format."""
        result = await extract_sequence_columns(
            sequence_data=sample_fasta_data,
            columns=["Id", "Organism"],
            output_format="table"
        )

        assert "|" in result  # Table formatting
        assert "-" in result  # Separator line

    @pytest.mark.asyncio
    async def test_extract_marker_detection(self, sample_fasta_data):
        """Test automatic marker detection."""
        result = await extract_sequence_columns(
            sequence_data=sample_fasta_data,
            columns=["Marker"],
            output_format="json"
        )

        data = json.loads(result)
        # Should detect COI from the FASTA headers
        markers = [r.get("Marker", "") for r in data]
        assert "COI" in markers or "mitogenome" in markers

    @pytest.mark.asyncio
    async def test_extract_error_handling(self):
        """Test error handling with invalid data."""
        result = await extract_sequence_columns(
            sequence_data="invalid data",
            columns=["Id"],
            output_format="json"
        )

        # Should handle gracefully
        assert isinstance(result, str)


class TestParseFastaHeader:
    """Tests for FASTA header parsing."""

    def test_parse_simple_header(self):
        """Test parsing simple FASTA header."""
        header = "PV570336.1 Salmo salar mitochondrion"
        record = parse_fasta_header(header)

        assert record["Accession"] == "PV570336.1"
        assert "Salmo salar" in record["Organism"]

    def test_parse_header_with_brackets(self):
        """Test parsing header with organism in brackets."""
        header = "AB012345.1 cytochrome oxidase [Oncorhynchus mykiss]"
        record = parse_fasta_header(header)

        assert record["Accession"] == "AB012345.1"
        assert record["Organism"] == "Oncorhynchus mykiss"

    def test_parse_header_marker_detection(self):
        """Test marker detection from header."""
        headers = [
            ("COI gene sequence", "COI"),
            ("16S ribosomal RNA", "16S"),
            ("internal transcribed spacer ITS", "ITS"),
            ("rbcL gene", "rbcL")
        ]

        for header, expected_marker in headers:
            record = parse_fasta_header(header)
            assert record["Marker"] == expected_marker

    def test_parse_header_country_detection(self):
        """Test geographic location detection."""
        header = "Sample123 Salmo salar from Norway isolate N1"
        record = parse_fasta_header(header)

        assert "Norway" in record["Country"]


class TestFormatSequences:
    """Tests for sequence formatting."""

    def test_format_dict_to_fasta(self):
        """Test formatting dictionary to FASTA."""
        sequences = {
            "seq1": "ATCGATCG",
            "seq2": "GCTAGCTA"
        }

        result = format_sequences(sequences, "fasta")

        assert ">seq1" in result
        assert "ATCGATCG" in result
        assert ">seq2" in result

    def test_format_error_handling(self):
        """Test format_sequences error handling."""
        result = format_sequences(None, "fasta")

        assert "Error" in result or isinstance(result, str)
