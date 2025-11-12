"""
Unit tests for the Validation MCP Server.

Tests cover:
- gget BLAST and BLAT integration
- Local BLAST execution
- In-silico PCR simulation
- Coverage assessment
- PubMed literature search
- Complete validation pipeline
"""

import pytest
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from validation_mcp_server import (
    gget_blast_impl,
    gget_blat_impl,
    blast_nt_impl,
    in_silico_pcr_impl,
    assess_coverage_impl,
    search_pubmed_impl,
    validate_primers_complete_impl,
    reverse_complement,
    find_primer_matches
)


# Test data
SAMPLE_PRIMER_FWD = "ATGCGATCGATCGATCGAT"
SAMPLE_PRIMER_REV = "GCTAGCTAGCTAGCTAGCT"

SAMPLE_TEMPLATE = """>target1
ATGCGATCGATCGATCGATGCTAGCTAGCTAGCTAGCTAGCTAGCT
>target2
ATGCGATCGATCGATCGATGCTAGCTAGCTAGCTAGCTAGCTAGCT
>offtarget1
TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT
"""

SAMPLE_TARGET_PANEL = """>Salmo_salar_1
ATGCGATCGATCGATCGATGCTAGCTAGCTAGCTAGCTAGCTAGCT
>Salmo_salar_2
ATGCGATCGATCGATCGATGCTAGCTAGCTAGCTAGCTAGCTAGCT
"""

SAMPLE_OFFTARGET_PANEL = """>Oncorhynchus_mykiss_1
TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT
>Thunnus_thynnus_1
CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
"""


class TestHelperFunctions:
    """Test helper functions."""

    def test_reverse_complement(self):
        """Test reverse complement calculation."""
        assert reverse_complement("ATGC") == "GCAT"
        assert reverse_complement("AAAA") == "TTTT"
        assert reverse_complement("GCGC") == "GCGC"

    def test_find_primer_matches_exact(self):
        """Test finding exact primer matches."""
        template = "ATGCGATCGATCGATCGAT"
        primer = "ATGCGATC"

        matches = find_primer_matches(primer, template, max_mismatches=0)

        # Should find forward match at position 0
        assert len(matches) > 0
        fwd_matches = [m for m in matches if m["strand"] == "+"]
        assert len(fwd_matches) >= 1
        assert fwd_matches[0]["position"] == 0
        assert fwd_matches[0]["mismatches"] == 0

    def test_find_primer_matches_with_mismatches(self):
        """Test finding matches with mismatches."""
        template = "ATGCGATCGATCGATCGAT"
        primer = "ATGCGTTC"  # One mismatch from ATGCGATC

        matches = find_primer_matches(primer, template, max_mismatches=1)

        assert len(matches) > 0
        # Should find match with 1 mismatch
        assert any(m["mismatches"] <= 1 for m in matches)

    def test_find_primer_matches_reverse(self):
        """Test finding reverse strand matches."""
        template = "ATGCGATCGATCGATCGAT"
        primer = "GATCGATC"  # Reverse complement should match

        matches = find_primer_matches(primer, template, max_mismatches=0)

        # Should find matches on reverse strand
        rev_matches = [m for m in matches if m["strand"] == "-"]
        assert len(rev_matches) > 0


class TestGgetBlast:
    """Test gget BLAST functionality."""

    @pytest.mark.asyncio
    @patch('validation_mcp_server.gget')
    async def test_gget_blast_success(self, mock_gget):
        """Test successful BLAST search."""
        import pandas as pd

        # Mock gget.blast return value
        mock_result = pd.DataFrame([
            {"description": "Test hit 1", "percent_identity": 95.0, "evalue": 1e-10},
            {"description": "Test hit 2", "percent_identity": 90.0, "evalue": 1e-8}
        ])
        mock_gget.blast = Mock(return_value=mock_result)

        result = await gget_blast_impl(
            sequence="ATGCGATCGATC",
            program="blastn",
            database="nt",
            limit=10
        )

        assert result["success"] is True
        assert result["num_hits"] == 2
        assert len(result["hits"]) == 2

    @pytest.mark.asyncio
    async def test_gget_blast_no_gget(self):
        """Test error when gget not available."""
        with patch('validation_mcp_server.gget', None):
            result = await gget_blast_impl(sequence="ATGC")

            assert result["success"] is False
            assert "gget library not available" in result["error"]

    @pytest.mark.asyncio
    @patch('validation_mcp_server.gget')
    async def test_gget_blast_no_hits(self, mock_gget):
        """Test BLAST with no hits."""
        import pandas as pd

        # Mock empty result
        mock_gget.blast = Mock(return_value=pd.DataFrame())

        result = await gget_blast_impl(sequence="ATGC")

        assert result["success"] is True
        assert result["num_hits"] == 0
        assert "No BLAST hits found" in result["message"]


class TestGgetBlat:
    """Test gget BLAT functionality."""

    @pytest.mark.asyncio
    @patch('validation_mcp_server.gget')
    async def test_gget_blat_success(self, mock_gget):
        """Test successful BLAT search."""
        import pandas as pd

        # Mock gget.blat return value
        mock_result = pd.DataFrame([
            {"chromosome": "chr1", "start": 1000, "end": 1050, "strand": "+"}
        ])
        mock_gget.blat = Mock(return_value=mock_result)

        result = await gget_blat_impl(
            sequence="ATGCGATCGATC",
            seqtype="DNA",
            assembly="human"
        )

        assert result["success"] is True
        assert result["num_hits"] == 1

    @pytest.mark.asyncio
    async def test_gget_blat_no_gget(self):
        """Test error when gget not available."""
        with patch('validation_mcp_server.gget', None):
            result = await gget_blat_impl(sequence="ATGC")

            assert result["success"] is False
            assert "gget library not available" in result["error"]


class TestInSilicoPCR:
    """Test in-silico PCR functionality."""

    @pytest.mark.asyncio
    async def test_in_silico_pcr_success(self):
        """Test successful PCR simulation."""
        result = await in_silico_pcr_impl(
            forward_primer=SAMPLE_PRIMER_FWD,
            reverse_primer=SAMPLE_PRIMER_REV,
            template_fasta=SAMPLE_TEMPLATE,
            max_mismatches=0
        )

        assert result["success"] is True
        assert result["num_templates"] == 3
        assert "products" in result

    @pytest.mark.asyncio
    async def test_in_silico_pcr_no_templates(self):
        """Test PCR with empty FASTA."""
        result = await in_silico_pcr_impl(
            forward_primer=SAMPLE_PRIMER_FWD,
            reverse_primer=SAMPLE_PRIMER_REV,
            template_fasta=">empty\n",
            max_mismatches=0
        )

        # Should handle gracefully
        assert result.get("success") is not False or "error" in result

    @pytest.mark.asyncio
    async def test_in_silico_pcr_no_products(self):
        """Test PCR when primers don't match."""
        # Use primers that won't match the template
        result = await in_silico_pcr_impl(
            forward_primer="AAAAAAAAAAAAAAAAA",
            reverse_primer="TTTTTTTTTTTTTTTTT",
            template_fasta=SAMPLE_TEMPLATE,
            max_mismatches=0
        )

        assert result["success"] is True
        assert result["num_products"] == 0


class TestCoverageAssessment:
    """Test coverage assessment functionality."""

    @pytest.mark.asyncio
    async def test_assess_coverage_target_only(self):
        """Test coverage assessment with target panel only."""
        result = await assess_coverage_impl(
            primers={"forward": SAMPLE_PRIMER_FWD, "reverse": SAMPLE_PRIMER_REV},
            target_panel=SAMPLE_TARGET_PANEL
        )

        assert result["success"] is True
        assert "target_coverage" in result
        assert "sensitivity" in result["target_coverage"]

    @pytest.mark.asyncio
    async def test_assess_coverage_with_offtarget(self):
        """Test coverage assessment with off-target panel."""
        result = await assess_coverage_impl(
            primers={"forward": SAMPLE_PRIMER_FWD, "reverse": SAMPLE_PRIMER_REV},
            target_panel=SAMPLE_TARGET_PANEL,
            offtarget_panel=SAMPLE_OFFTARGET_PANEL
        )

        assert result["success"] is True
        assert "target_coverage" in result
        assert "offtarget_coverage" in result
        assert "specificity" in result["offtarget_coverage"]
        assert "validation_pass" in result

    @pytest.mark.asyncio
    async def test_assess_coverage_missing_primers(self):
        """Test error handling for missing primers."""
        result = await assess_coverage_impl(
            primers={"forward": SAMPLE_PRIMER_FWD},  # Missing reverse
            target_panel=SAMPLE_TARGET_PANEL
        )

        assert result["success"] is False
        assert "Both forward and reverse primers required" in result["error"]


class TestPubMedSearch:
    """Test PubMed search functionality."""

    @pytest.mark.asyncio
    async def test_search_pubmed_mock(self):
        """Test PubMed search with mocked Entrez."""
        with patch('validation_mcp_server.Entrez') as mock_entrez:
            # Mock esearch
            mock_esearch_handle = Mock()
            mock_esearch_handle.read = Mock(return_value={"IdList": ["12345", "67890"]})
            mock_entrez.esearch = Mock(return_value=mock_esearch_handle)

            # Mock efetch
            mock_efetch_handle = Mock()
            mock_efetch_handle.read = Mock(return_value={
                "PubmedArticle": [
                    {
                        "MedlineCitation": {
                            "PMID": "12345",
                            "Article": {
                                "ArticleTitle": "Test Article 1",
                                "Abstract": {"AbstractText": ["Test abstract"]},
                                "AuthorList": [],
                                "Journal": {"JournalIssue": {"PubDate": {"Year": "2023"}}}
                            }
                        }
                    }
                ]
            })
            mock_entrez.efetch = Mock(return_value=mock_efetch_handle)

            result = await search_pubmed_impl(
                query="qPCR primers salmon",
                max_results=10
            )

            assert result["success"] is True
            assert result["num_results"] >= 0
            if result["num_results"] > 0:
                assert "articles" in result

    @pytest.mark.asyncio
    async def test_search_pubmed_no_results(self):
        """Test PubMed search with no results."""
        with patch('validation_mcp_server.Entrez') as mock_entrez:
            # Mock empty esearch
            mock_handle = Mock()
            mock_handle.read = Mock(return_value={"IdList": []})
            mock_entrez.esearch = Mock(return_value=mock_handle)

            result = await search_pubmed_impl(query="nonexistent12345")

            assert result["success"] is True
            assert result["num_results"] == 0
            assert "No PubMed articles found" in result["message"]


class TestCompleteValidation:
    """Test complete validation pipeline."""

    @pytest.mark.asyncio
    @patch('validation_mcp_server.gget_blast_impl')
    @patch('validation_mcp_server.in_silico_pcr_impl')
    @patch('validation_mcp_server.assess_coverage_impl')
    async def test_validate_primers_complete_success(
        self,
        mock_coverage,
        mock_pcr,
        mock_blast
    ):
        """Test complete validation pipeline."""
        # Mock successful results for each step
        mock_blast.return_value = {
            "success": True,
            "num_hits": 10,
            "hits": []
        }

        mock_pcr.return_value = {
            "success": True,
            "num_products": 2,
            "products": []
        }

        mock_coverage.return_value = {
            "success": True,
            "validation_pass": True,
            "target_coverage": {"sensitivity": 0.95},
            "offtarget_coverage": {"specificity": 0.98},
            "issues": []
        }

        result = await validate_primers_complete_impl(
            primers={"forward": SAMPLE_PRIMER_FWD, "reverse": SAMPLE_PRIMER_REV},
            target_panel=SAMPLE_TARGET_PANEL,
            offtarget_panel=SAMPLE_OFFTARGET_PANEL,
            include_literature=False
        )

        assert result["success"] is True
        assert "validation_steps" in result
        assert "summary" in result
        assert result["summary"]["validation_pass"] is True

    @pytest.mark.asyncio
    async def test_validate_primers_missing_primers(self):
        """Test validation with missing primers."""
        result = await validate_primers_complete_impl(
            primers={"forward": SAMPLE_PRIMER_FWD},  # Missing reverse
            target_panel=SAMPLE_TARGET_PANEL
        )

        assert result["success"] is False
        assert "Both forward and reverse primers required" in result["error"]


class TestBlastNT:
    """Test local BLAST functionality."""

    @pytest.mark.asyncio
    async def test_blast_nt_not_configured(self):
        """Test error when local BLAST not configured."""
        with patch('validation_mcp_server.Config.use_local_blast', return_value=False):
            result = await blast_nt_impl(
                query_fasta=">test\nATGC"
            )

            assert result["success"] is False
            assert "Local BLAST database not configured" in result["error"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
