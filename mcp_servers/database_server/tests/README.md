# Database MCP Server Tests

Comprehensive test suite for the ndiag-database-server MCP service.

## Test Structure

```
tests/
├── conftest.py              # Pytest configuration and shared fixtures
├── test_gget_tools.py       # Tests for gget integration (search, ref, info, seq)
├── test_sequence_tools.py   # Tests for sequence retrieval and extraction
├── test_taxonomy_sra_tools.py  # Tests for taxonomy and SRA tools
├── test_integration.py      # Integration tests across components
├── test_basic.py           # Basic connectivity tests
├── test_mcp_client.py      # MCP protocol communication tests
└── README.md               # This file
```

## Running Tests

### Run All Tests
```bash
cd mcp_servers/database_server
pytest
```

### Run Specific Test Categories
```bash
# Unit tests only (fast, no external APIs)
pytest -m unit

# Integration tests
pytest -m integration

# Specific tool tests
pytest -m gget
pytest -m ncbi
pytest -m sra
pytest -m bold

# Slow tests
pytest -m slow

# With coverage report
pytest --cov --cov-report=html
```

### Run Specific Test Files
```bash
pytest tests/test_gget_tools.py
pytest tests/test_sequence_tools.py -v
pytest tests/test_integration.py::TestMCPToolIntegration -v
```

### Run Tests Requiring Network (Real API Calls)
```bash
# Set environment variable to enable real API tests
RUN_NETWORK_TESTS=1 pytest -m requires_network
```

## Test Markers

Tests are organized with pytest markers:

- `unit` - Fast unit tests with mocked dependencies
- `integration` - Integration tests verifying component interaction
- `slow` - Slow-running tests
- `requires_network` - Tests that need internet access
- `requires_api_key` - Tests that need API keys
- `gget` - gget-specific tests
- `ncbi` - NCBI-specific tests
- `sra` - SRA/BioProject tests
- `bold` - BOLD Systems tests

## Test Coverage

Current test coverage includes:

### gget Tools (test_gget_tools.py)
- ✅ `gget_search` - Gene search in Ensembl
- ✅ `gget_ref` - Reference genome retrieval
- ✅ `gget_info` - Gene information lookup
- ✅ `gget_seq` - Sequence retrieval by ID
- ✅ Error handling for all tools
- ✅ Parameter validation

### Sequence Tools (test_sequence_tools.py)
- ✅ `get_sequences` - Unified multi-source retrieval
- ✅ Source routing (gget, ncbi, bold, silva, unite)
- ✅ `extract_sequence_columns` - Metadata extraction
- ✅ FASTA header parsing
- ✅ GenBank record parsing
- ✅ Multiple output formats (JSON, CSV, TSV, table)
- ✅ Marker detection (COI, 16S, ITS, etc.)
- ✅ Geographic location extraction

### Taxonomy & SRA Tools (test_taxonomy_sra_tools.py)
- ✅ `get_taxonomy` - Taxonomic information retrieval
- ✅ `get_neighbors` - Taxonomic neighbor finding
- ✅ `search_sra_studies` - SRA/BioProject search
- ✅ `get_sra_runinfo` - Run metadata retrieval
- ✅ `search_sra_cloud` - BigQuery/Athena integration
- ✅ Filter support (organism, library_strategy, platform)
- ✅ Multiple output formats

### Integration Tests (test_integration.py)
- ✅ Complete MCP tool call workflow
- ✅ Multi-step workflows (retrieve → extract)
- ✅ Error propagation across components
- ✅ Invalid input handling
- ✅ Empty result handling

## Fixtures

Shared test fixtures are defined in `conftest.py`:

### Data Fixtures
- `sample_fasta_data` - Example FASTA sequences
- `sample_genbank_data` - Example GenBank records
- `sample_json_sequence_data` - JSON sequence metadata

### Mock Fixtures
- `mock_gget` - Mocked gget module
- `mock_entrez` - Mocked BioPython Entrez
- `mock_requests` - Mocked HTTP requests (for BOLD)
- `mock_pysradb` - Mocked pysradb library
- `mock_bigquery` - Mocked Google BigQuery client

### Helper Functions
- `create_mock_mcp_request()` - Create MCP tool requests
- `assert_valid_fasta()` - Validate FASTA format
- `assert_valid_json()` - Validate JSON format

## Writing New Tests

### Template for Unit Test
```python
import pytest
from database_mcp_server import your_function

pytestmark = pytest.mark.unit

class TestYourFunction:
    @pytest.mark.asyncio
    async def test_basic_functionality(self, mock_dependency):
        """Test basic functionality with mocked dependencies."""
        result = await your_function(arg1="value")

        assert isinstance(result, str)
        mock_dependency.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling."""
        with patch('module.function', side_effect=Exception("Error")):
            result = await your_function(arg1="bad_value")
            assert "Error" in result
```

### Template for Integration Test
```python
@pytest.mark.integration
class TestYourWorkflow:
    @pytest.mark.asyncio
    async def test_complete_workflow(self, fixtures):
        """Test complete multi-step workflow."""
        # Step 1
        result1 = await handle_call_tool("tool1", {...})
        assert len(result1) > 0

        # Step 2
        result2 = await handle_call_tool("tool2", {
            "data": result1[0].text
        })
        assert len(result2) > 0
```

## Continuous Integration

Tests are designed to run in CI/CD pipelines:

### Docker Test Execution
```bash
# Build test container
docker build -t ndiag-database-server:test .

# Run tests in container
docker run --rm ndiag-database-server:test pytest -v

# Run with coverage
docker run --rm ndiag-database-server:test pytest --cov
```

### GitHub Actions Example
```yaml
- name: Run tests
  run: |
    cd mcp_servers/database_server
    pip install -r requirements.txt
    pytest --cov --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Performance Testing

Run performance benchmarks:

```bash
# Profile test execution time
pytest --durations=10

# Run only fast tests
pytest -m "unit and not slow"

# Memory profiling
pytest --memray tests/
```

## Troubleshooting

### Common Issues

**Import Errors**
```bash
# Ensure PYTHONPATH is set
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

**Mock Not Working**
```bash
# Verify mock paths match actual imports
# Use --pdb flag to debug
pytest --pdb
```

**Async Test Failures**
```bash
# Ensure pytest-asyncio is installed
pip install pytest-asyncio

# Check pytest.ini has asyncio configuration
cat pytest.ini
```

## Test Metrics

Target metrics for Phase 1 completion:

- [ ] >80% code coverage
- [ ] All 12+ MCP tools tested
- [ ] 100+ test cases
- [ ] All error paths tested
- [ ] Integration tests passing
- [ ] < 5 seconds for unit tests
- [ ] < 30 seconds for full suite (mocked)

## Next Steps

### Additional Tests Needed
1. Performance/load testing
2. Container integration tests
3. MCP protocol compliance tests
4. Kubernetes deployment tests
5. Real API rate limiting tests

### Test Improvements
1. Add property-based testing with Hypothesis
2. Mutation testing with mutmut
3. Security testing (input sanitization)
4. Stress testing with concurrent requests
