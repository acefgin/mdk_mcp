"""
Pytest configuration and shared fixtures for database MCP server tests.
"""

import asyncio
import json
import os
import pytest
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch
import pandas as pd
from Bio import Entrez

# Set test environment variables
os.environ["LOG_LEVEL"] = "ERROR"  # Reduce noise during testing
os.environ["TEMP_DIR"] = "/tmp/test_mcp_cache"

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def sample_fasta_data():
    """Sample FASTA format data for testing."""
    return """>PV570336.1 Salmo salar mitochondrion, complete genome
GTTAACGTAGCTTAAACAAAGCAAAGCACTGAAAATGCTTAGATGGATAATTGTATCCCATAAACACA
AAGGTTTGGTCCTGGCCTTATAATTAATTGGAGGTAAGATTACACATGCAAACATCCATAAACCGGTGT
>PV570337.1 Oncorhynchus mykiss cytochrome oxidase subunit 1 (COI) gene
ATGACCAATATTCGAAAATCCCACCCGCTAGCAAACACCCCCACGGGACACAGCAGTGATAAAAATTAA
GCTATAAACGAAAGTTTGACTAAGCCATACTAATTAGGGTTGGTAAATTTCGTGCCAGCCACCGCGGTC
>AB012345.1 Thunnus thynnus isolate T123 COI gene, partial cds
TTAAGTATAAACTTCACCCACCACCCCCTAAACCAAGACATTTTTAGATAATTAAGCCGTAGGCGACAA
"""

@pytest.fixture
def sample_genbank_data():
    """Sample GenBank format data for testing."""
    return """LOCUS       PV570336               16000 bp    DNA     circular VRT 26-SEP-2024
DEFINITION  Salmo salar mitochondrion, complete genome.
ACCESSION   PV570336
VERSION     PV570336.1
KEYWORDS    .
SOURCE      mitochondrion Salmo salar (Atlantic salmon)
  ORGANISM  Salmo salar
            Eukaryota; Metazoa; Chordata; Craniata; Vertebrata; Euteleostomi;
            Actinopterygii; Salmoniformes; Salmonidae; Salmo.
REFERENCE   1  (bases 1 to 16000)
  AUTHORS   Smith,J.D. and Johnson,A.B.
  TITLE     Complete mitochondrial genome of Atlantic salmon
  JOURNAL   Marine Biology 123, 456-789 (2024)
FEATURES             Location/Qualifiers
     source          1..16000
                     /organism="Salmo salar"
                     /organelle="mitochondrion"
                     /mol_type="genomic DNA"
                     /isolate="SS2024"
                     /db_xref="taxon:8030"
                     /geo_loc_name="Norway: Bergen"
                     /collection_date="15-Mar-2024"
     gene            1..1500
                     /gene="COI"
     CDS             1..1500
                     /gene="COI"
                     /product="cytochrome c oxidase subunit I"
                     /protein_id="ABC12345.1"
ORIGIN
        1 gttaacgtag cttaaacaaa gcaaagcact gaaaatgctt agatggataa ttgtatccca
       61 taaacacaaa ggtttggtcc tggccttata attaattgga ggtaagatta cacatgcaaa
//
"""

@pytest.fixture
def sample_json_sequence_data():
    """Sample JSON sequence data for testing."""
    return json.dumps([
        {
            "Id": "PV570336.1",
            "Accession": "PV570336.1",
            "Title": "Salmo salar mitochondrion, complete genome",
            "Organism": "Salmo salar",
            "Length": 16000,
            "Database": "NCBI",
            "Marker": "mitogenome"
        },
        {
            "Id": "AB012345.1",
            "Accession": "AB012345.1",
            "Title": "Oncorhynchus mykiss COI gene",
            "Organism": "Oncorhynchus mykiss",
            "Length": 658,
            "Database": "NCBI",
            "Marker": "COI"
        }
    ])

@pytest.fixture
def mock_gget_search_result():
    """Mock result from gget.search()."""
    data = {
        "ENSG00000198804": {
            "ensembl_id": "ENSG00000198804",
            "gene_name": "MT-CO1",
            "description": "mitochondrially encoded cytochrome c oxidase I",
            "species": "homo_sapiens"
        }
    }
    return pd.DataFrame.from_dict(data, orient='index')

@pytest.fixture
def mock_gget_seq_result():
    """Mock result from gget.seq()."""
    return {
        "ENSG00000198804": "ATGTTCGCCGACCGTTGACTATTCTCAACAAACCACAAAGACATTGGAACACC"
    }

@pytest.fixture
def mock_entrez_search_result():
    """Mock result from Entrez.esearch()."""
    return {
        "Count": "10",
        "RetMax": "10",
        "IdList": ["123456789", "987654321", "555555555"]
    }

@pytest.fixture
def mock_entrez_fetch_result():
    """Mock FASTA result from Entrez.efetch()."""
    return """>gi|123456789|gb|PV570336.1| Salmo salar mitochondrion
GTTAACGTAGCTTAAACAAAGCAAAGCACTGAAAATGCTTAGATGGATAATTGTATCCCATAAACACA
>gi|987654321|gb|PV570337.1| Oncorhynchus mykiss COI
ATGACCAATATTCGAAAATCCCACCCGCTAGCAAACACCCCCACGGGACACAGCAGTGATAAAAATTAA
"""

@pytest.fixture
def mock_sra_metadata():
    """Mock SRA metadata from pysradb."""
    data = {
        "study_accession": ["PRJNA123456", "PRJNA123456"],
        "run_accession": ["SRR12345678", "SRR87654321"],
        "experiment_accession": ["SRX1234567", "SRX7654321"],
        "sample_accession": ["SRS1234567", "SRS7654321"],
        "organism": ["Salmo salar", "Salmo salar"],
        "library_strategy": ["AMPLICON", "AMPLICON"],
        "platform": ["ILLUMINA", "ILLUMINA"],
        "instrument": ["Illumina MiSeq", "Illumina MiSeq"]
    }
    return pd.DataFrame(data)

@pytest.fixture
def mock_bold_response():
    """Mock response from BOLD API."""
    return """>BOLD:AAA1234|Salmo salar|COI-5P
AACTTTATACTTTATTTTTGGAGCTTGAGCAGGAATAGTAGGAACTTCTTTAAGAATTTTAATTCGAGCTGAATTAGGTCAACCTGGAGCTTTAATTGGAGATGATCAAATTTATAATGTAATTGTTACAGCTCATGCTTTTATTATAATTTTTTTTATAGTTATACCTATTATAATTGGAGGATTTGGTAATTGACTTGTACCTTTAATATTAGGAGCCCCTGATATAGCTTTCCCTCGAATAAATAATATAAGATTTTGA
>BOLD:AAA5678|Oncorhynchus mykiss|COI-5P
AACCTGTATTTAATTTTTGGGGCTTGAGCTGGTATAGTGGGAACTTCTTTAAGAATTTTAATTCGAGCTGAATTAGGTCAACCTGGATCATTAATTGGAGATGATCAAATTTATAATGTAATTGTTACAGCTCATGCTTTTATTATAATTTTTTTTATAGTTATACCTATTATAATTGGAGGATTTGGTAATTGACTTGTACCATTAATATTAGGAGCCCCTGATATAGCTTTTCCTCGAATAAATAATATAAGATTTTGA
"""

@pytest.fixture
def mock_taxonomy_record():
    """Mock taxonomy record from NCBI."""
    return [{
        "TaxId": "8030",
        "ScientificName": "Salmo salar",
        "Lineage": "Eukaryota; Metazoa; Chordata; Craniata; Vertebrata; Euteleostomi; Actinopterygii; Salmoniformes; Salmonidae; Salmo",
        "Rank": "species"
    }]

# Mock patches for external dependencies
@pytest.fixture
def mock_gget(mock_gget_search_result, mock_gget_seq_result):
    """Mock gget module functions."""
    with patch('gget.search') as mock_search, \
         patch('gget.seq') as mock_seq, \
         patch('gget.ref') as mock_ref, \
         patch('gget.info') as mock_info:

        mock_search.return_value = mock_gget_search_result
        mock_seq.return_value = mock_gget_seq_result
        mock_ref.return_value = pd.DataFrame({"ftp": ["ftp://example.com/file.fa.gz"]})
        mock_info.return_value = pd.DataFrame({"gene_name": ["MT-CO1"]})

        yield {
            'search': mock_search,
            'seq': mock_seq,
            'ref': mock_ref,
            'info': mock_info
        }

@pytest.fixture
def mock_entrez(mock_entrez_search_result, mock_entrez_fetch_result):
    """Mock BioPython Entrez functions."""
    with patch('Bio.Entrez.esearch') as mock_search, \
         patch('Bio.Entrez.efetch') as mock_fetch, \
         patch('Bio.Entrez.read') as mock_read:

        # Configure mock search
        mock_search_handle = Mock()
        mock_search.return_value = mock_search_handle
        mock_read.return_value = mock_entrez_search_result

        # Configure mock fetch
        mock_fetch_handle = Mock()
        mock_fetch_handle.read.return_value = mock_entrez_fetch_result
        mock_fetch.return_value = mock_fetch_handle

        yield {
            'esearch': mock_search,
            'efetch': mock_fetch,
            'read': mock_read
        }

@pytest.fixture
def mock_requests(mock_bold_response):
    """Mock requests library for HTTP calls."""
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = mock_bold_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        yield mock_get

@pytest.fixture
def mock_pysradb(mock_sra_metadata):
    """Mock pysradb library."""
    with patch('pysradb.SRAweb') as mock_sraweb:
        mock_db = Mock()
        mock_db.sra_metadata.return_value = mock_sra_metadata
        mock_db.search_sra.return_value = mock_sra_metadata
        mock_sraweb.return_value = mock_db

        yield mock_db

@pytest.fixture
def mock_bigquery():
    """Mock Google BigQuery client."""
    with patch('google.cloud.bigquery.Client') as mock_client:
        mock_bq = Mock()
        mock_job = Mock()
        mock_results = Mock()
        mock_results.to_dataframe.return_value = pd.DataFrame({
            "run_accession": ["SRR12345678"],
            "organism": ["Salmo salar"]
        })
        mock_job.result.return_value = mock_results
        mock_bq.query.return_value = mock_job
        mock_client.return_value = mock_bq

        yield mock_bq

# Helper functions for tests
def create_mock_mcp_request(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Create a mock MCP tool request."""
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }

def assert_valid_fasta(fasta_text: str) -> bool:
    """Validate FASTA format."""
    lines = fasta_text.strip().split('\n')
    if not lines:
        return False

    has_header = False
    for line in lines:
        if line.startswith('>'):
            has_header = True
        elif has_header and line and not line.startswith('>'):
            # Check if sequence line contains valid characters
            if not all(c in 'ACGTNacgtn' for c in line.strip()):
                return False

    return has_header

def assert_valid_json(json_text: str) -> bool:
    """Validate JSON format."""
    try:
        json.loads(json_text)
        return True
    except json.JSONDecodeError:
        return False
