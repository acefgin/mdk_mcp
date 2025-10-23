"""Pytest configuration and fixtures for processing server tests."""

import pytest
import tempfile
import os


@pytest.fixture
def sample_fasta():
    """Sample FASTA sequences for testing."""
    return """>seq1 Test sequence 1
ATGCATGCATGCATGCATGC
>seq2 Test sequence 2
ATGCATGCATGCNNNNATGC
>seq3 Test sequence 3 (short)
ATGC
>seq4 Test sequence 4 (duplicate of seq1)
ATGCATGCATGCATGCATGC
>seq5 Test sequence 5 (low complexity)
AAAAAAAAAAAAAAAAAAAA
"""


@pytest.fixture
def valid_fasta():
    """Valid FASTA sequences without issues."""
    return """>seq1 Good sequence 1
ATGCATGCATGCATGCATGCATGCATGCATGC
>seq2 Good sequence 2
GCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTA
>seq3 Good sequence 3
TACGTACGTACGTACGTACGTACGTACGTACG
"""


@pytest.fixture
def chimeric_fasta():
    """FASTA with potential chimeric sequences."""
    return """>seq1 Parent A
ATGCATGCATGCATGCATGCATGCATGCATGCATGCATGC
>seq2 Parent B
GCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTA
>seq3 Potential chimera (A+B)
ATGCATGCATGCATGCATGCGCTAGCTAGCTAGCTAGCTA
>seq4 Good sequence
TACGTACGTACGTACGTACGTACGTACGTACGTACGTACG
"""


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def config_override(monkeypatch, temp_dir):
    """Override configuration for tests."""
    monkeypatch.setenv("TEMP_DIR", temp_dir)
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("MAX_SEQUENCES", "1000")
