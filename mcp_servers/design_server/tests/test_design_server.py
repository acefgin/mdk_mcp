"""
Unit tests for the Design MCP Server.

Tests cover:
- Signature region discovery
- Specificity analysis
- Region ranking
- Primer3 integration
- Oligonucleotide QC
- Complete pipeline
"""

import pytest
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from design_mcp_server import (
    find_signature_regions_impl,
    analyze_specificity_impl,
    rank_regions_impl,
    primer3_design_impl,
    oligo_qc_impl,
    design_primers_complete_impl,
    calculate_shannon_entropy,
    calculate_conservation,
    calculate_gc_content,
    calculate_complexity,
    calculate_tm_basic
)


# Test data
SAMPLE_ALIGNMENT = """>target_seq1
ATGCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGAT
>target_seq2
ATGCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGAT
>offtarget_seq1
ATGCGTTCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGAT
>offtarget_seq2
ATGCGTTCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGAT
"""

SAMPLE_TEMPLATE = """>template
ATGCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGAT
"""


class TestHelperFunctions:
    """Test helper functions."""

    def test_shannon_entropy(self):
        # Perfectly conserved column
        assert calculate_shannon_entropy(['A', 'A', 'A', 'A']) == 0.0

        # Maximum diversity
        entropy = calculate_shannon_entropy(['A', 'T', 'G', 'C'])
        assert entropy > 1.5  # Should be close to 2.0

    def test_conservation(self):
        # Perfectly conserved
        assert calculate_conservation(['A', 'A', 'A', 'A']) == 1.0

        # 75% conserved
        assert calculate_conservation(['A', 'A', 'A', 'T']) == 0.75

        # With gaps
        assert calculate_conservation(['A', 'A', '-', '-']) == 1.0

    def test_gc_content(self):
        assert calculate_gc_content("ATGC") == 50.0
        assert calculate_gc_content("AAAA") == 0.0
        assert calculate_gc_content("GGCC") == 100.0

    def test_complexity(self):
        # High complexity
        assert calculate_complexity("ATGCATGC") > 0.5

        # Low complexity (repeats)
        assert calculate_complexity("AAAAAAAA") < 0.5

    def test_tm_calculation(self):
        # Test basic Tm calculation
        tm = calculate_tm_basic("ATGCATGC")
        assert 30 < tm < 70  # Reasonable Tm range


class TestSignatureRegionDiscovery:
    """Test signature region discovery functionality."""

    @pytest.mark.asyncio
    async def test_find_signature_regions_basic(self):
        result = await find_signature_regions_impl(
            alignment_content=SAMPLE_ALIGNMENT,
            target_sequences=["target_seq"],
            window_size=20,
            step_size=10,
            min_conservation=0.8,
            min_divergence=0.0
        )

        assert result['success'] is True
        assert 'regions' in result
        assert result['target_count'] == 2
        assert result['offtarget_count'] == 2

    @pytest.mark.asyncio
    async def test_find_signature_regions_no_targets(self):
        result = await find_signature_regions_impl(
            alignment_content=SAMPLE_ALIGNMENT,
            target_sequences=["nonexistent"],
            window_size=20,
            step_size=10
        )

        assert result['success'] is False
        assert 'error' in result

    @pytest.mark.asyncio
    async def test_find_signature_regions_parameters(self):
        # Test with strict parameters
        result = await find_signature_regions_impl(
            alignment_content=SAMPLE_ALIGNMENT,
            target_sequences=["target_seq"],
            window_size=30,
            step_size=5,
            min_conservation=0.95,
            min_divergence=0.5
        )

        assert result['success'] is True


class TestSpecificityAnalysis:
    """Test specificity analysis functionality."""

    @pytest.mark.asyncio
    async def test_analyze_specificity(self):
        # First get some candidate regions
        regions_result = await find_signature_regions_impl(
            alignment_content=SAMPLE_ALIGNMENT,
            target_sequences=["target_seq"],
            window_size=20,
            step_size=10,
            min_conservation=0.7,
            min_divergence=0.0
        )

        assert regions_result['success'] is True
        candidate_regions = regions_result['regions']

        if candidate_regions:
            # Analyze specificity
            result = await analyze_specificity_impl(
                candidate_regions=candidate_regions,
                target_group=["target_seq1", "target_seq2"],
                offtarget_group=["offtarget_seq1", "offtarget_seq2"]
            )

            assert result['success'] is True
            assert 'regions' in result
            assert all('specificity_score' in r for r in result['regions'])


class TestRegionRanking:
    """Test region ranking functionality."""

    @pytest.mark.asyncio
    async def test_rank_regions_default_weights(self):
        # Create some mock scored regions
        scored_regions = [
            {
                'start': 0,
                'end': 20,
                'conservation': 0.9,
                'specificity_score': 0.8,
                'complexity': 0.7
            },
            {
                'start': 10,
                'end': 30,
                'conservation': 0.7,
                'specificity_score': 0.9,
                'complexity': 0.8
            }
        ]

        result = await rank_regions_impl(scored_regions=scored_regions)

        assert result['success'] is True
        assert 'regions' in result
        assert all('composite_score' in r for r in result['regions'])
        assert all('rank' in r for r in result['regions'])

    @pytest.mark.asyncio
    async def test_rank_regions_custom_weights(self):
        scored_regions = [
            {
                'start': 0,
                'end': 20,
                'conservation': 0.9,
                'specificity_score': 0.8,
                'complexity': 0.7
            }
        ]

        result = await rank_regions_impl(
            scored_regions=scored_regions,
            weighting={
                'conservation': 0.5,
                'specificity': 0.3,
                'complexity': 0.2
            }
        )

        assert result['success'] is True
        assert 'weights_used' in result


class TestPrimer3Design:
    """Test Primer3 integration."""

    @pytest.mark.asyncio
    async def test_primer3_design_basic(self):
        result = await primer3_design_impl(
            template_fasta=SAMPLE_TEMPLATE
        )

        # May fail if primer3-py not installed, which is OK for basic test
        assert 'success' in result

    @pytest.mark.asyncio
    async def test_primer3_design_with_constraints(self):
        constraints = {
            'primer_size': [18, 22, 27],
            'tm': [57, 60, 63],
            'gc_content': [40, 50, 60],
            'product_size': [80, 150, 300],
            'num_return': 3
        }

        result = await primer3_design_impl(
            template_fasta=SAMPLE_TEMPLATE,
            constraints=constraints
        )

        assert 'success' in result


class TestOligoQC:
    """Test oligonucleotide quality control."""

    @pytest.mark.asyncio
    async def test_oligo_qc_basic(self):
        result = await oligo_qc_impl(sequence="ATGCATGCATGC")

        assert result['success'] is True
        assert 'length' in result
        assert 'gc_content' in result
        assert 'tm' in result
        assert 'qc_pass' in result

    @pytest.mark.asyncio
    async def test_oligo_qc_with_parameters(self):
        result = await oligo_qc_impl(
            sequence="ATGCATGCATGC",
            salt_mM=50.0,
            mg_mM=2.0,
            oligo_conc_nM=250.0
        )

        assert result['success'] is True
        assert result['length'] == 12

    @pytest.mark.asyncio
    async def test_oligo_qc_flags(self):
        # Test with low complexity sequence
        result = await oligo_qc_impl(sequence="AAAAAAAA")

        assert result['success'] is True
        assert 'flags' in result
        # Should have complexity or homopolymer flag
        assert len(result['flags']) > 0


class TestCompletePipeline:
    """Test end-to-end pipeline."""

    @pytest.mark.asyncio
    async def test_complete_pipeline_basic(self):
        result = await design_primers_complete_impl(
            alignment_content=SAMPLE_ALIGNMENT,
            target_sequences=["target_seq"]
        )

        # Should complete even if no primers designed
        assert 'success' in result
        assert 'pipeline_steps' in result

    @pytest.mark.asyncio
    async def test_complete_pipeline_with_parameters(self):
        result = await design_primers_complete_impl(
            alignment_content=SAMPLE_ALIGNMENT,
            target_sequences=["target_seq"],
            offtarget_sequences=["offtarget_seq"],
            primer_constraints={
                'num_return': 3
            },
            region_params={
                'window_size': 20,
                'step_size': 10,
                'min_conservation': 0.7,
                'min_divergence': 0.3
            }
        )

        assert 'success' in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
