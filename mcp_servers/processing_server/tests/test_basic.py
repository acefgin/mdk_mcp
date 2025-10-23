"""Basic tests for processing server functionality."""

import pytest
from Bio import SeqIO
from io import StringIO


def test_sample_fasta_fixture(sample_fasta):
    """Test that sample FASTA fixture is valid."""
    assert sample_fasta.startswith('>')
    assert sample_fasta.count('>') == 5  # 5 sequences


def test_fasta_parsing(valid_fasta):
    """Test BioPython FASTA parsing works."""
    records = list(SeqIO.parse(StringIO(valid_fasta), "fasta"))
    assert len(records) == 3
    assert all(len(str(rec.seq)) > 0 for rec in records)


def test_config_override(config_override, temp_dir):
    """Test configuration override for tests."""
    import os
    assert os.environ.get("LOG_LEVEL") == "DEBUG"
    assert os.path.exists(temp_dir)


@pytest.mark.asyncio
async def test_count_sequences(sample_fasta):
    """Test sequence counting helper."""
    count = sample_fasta.count('>')
    assert count == 5
