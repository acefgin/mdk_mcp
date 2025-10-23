# MCP Testing Quick Reference

Quick commands for testing MCP servers with Inspector.

## 🚀 Quick Start

### Test Database Server
```bash
cd mcp_servers/database_server
pip install -r requirements.txt
npx @modelcontextprotocol/inspector python3 database_mcp_server.py
# Open http://localhost:6274
```

### Test Processing Server
```bash
cd mcp_servers/processing_server
pip install -r requirements.txt
# Requires seqkit + vsearch OR use Docker:
docker-compose up --build
```

### Automated Test Script
```bash
# Test database server
./test_mcp_server.sh database

# Test processing server
./test_mcp_server.sh processing
```

---

## 📋 Common Commands

### List All Tools
```bash
npx @modelcontextprotocol/inspector \
  --method tools/list \
  python3 <server>.py
```

### Call a Tool (CLI)
```bash
npx @modelcontextprotocol/inspector \
  --method tools/call \
  --tool-name <tool_name> \
  python3 <server>.py <<EOF
{"param": "value"}
EOF
```

### Launch UI Mode
```bash
npx @modelcontextprotocol/inspector python3 <server>.py
# Opens at http://localhost:6274
```

---

## 🔧 Database Server Tools

### get_sequences
```json
{
  "taxon": "Salmo salar",
  "region": "COI",
  "source": "ncbi",
  "max_results": 10
}
```

### gget_search
```json
{
  "searchwords": ["COI", "cytochrome"],
  "species": "homo_sapiens"
}
```

### get_taxonomy
```json
{
  "query": "Salmo salar"
}
```

### search_sra_studies
```json
{
  "query": "Salmo salar amplicon",
  "filters": {
    "library_strategy": "AMPLICON",
    "max_results": 20
  }
}
```

---

## ⚙️ Processing Server Tools

### fasta_qc
```json
{
  "fasta_content": ">seq1\nATGC...",
  "min_length": 100,
  "max_n_percent": 5.0,
  "remove_duplicates": true
}
```

### dereplicate_sequences
```json
{
  "fasta_content": ">seq1\nATGC...",
  "identity_threshold": 0.97,
  "per_species": true
}
```

### mask_low_complexity
```json
{
  "fasta_content": ">seq1\nATGC...",
  "mask_repeats": true,
  "mask_homopolymers": true
}
```

### detect_chimeras
```json
{
  "fasta_content": ">seq1\nATGC...",
  "reference_db": "auto",
  "abundance_threshold": 2.0
}
```

### process_sequences (Pipeline)
```json
{
  "fasta_content": ">seq1\nATGC...",
  "pipeline": ["qc", "dereplicate", "mask"],
  "qc_params": {"min_length": 150},
  "derep_params": {"identity_threshold": 0.95}
}
```

---

## 🐛 Troubleshooting

### "Module not found"
```bash
pip install -r requirements.txt
```

### "Connection failed"
```bash
python3 -m py_compile <server>.py
LOG_LEVEL=DEBUG python3 <server>.py
```

### "seqkit/vsearch not found"
```bash
# Use Docker instead
cd mcp_servers/processing_server
docker-compose up --build
```

### "Port 6274 in use"
```bash
lsof -ti:6274 | xargs kill -9
```

---

## 📚 Full Documentation

- **Complete Guide**: `docs/MCP_TESTING_GUIDE.md` (741 lines)
- **Database README**: `mcp_servers/database_server/README.md`
- **Processing README**: `mcp_servers/processing_server/README.md`
- **MCP Inspector**: https://github.com/modelcontextprotocol/inspector

---

## 🧪 Example Test Workflow

```bash
# 1. Test database server
cd mcp_servers/database_server
npx @modelcontextprotocol/inspector python3 database_mcp_server.py

# 2. In UI (http://localhost:6274):
#    - Select "get_sequences"
#    - Enter: {"taxon": "Salmo salar", "region": "COI", "max_results": 5}
#    - Click "Run Tool"
#    - Copy FASTA output

# 3. Test processing server (new terminal)
cd mcp_servers/processing_server
npx @modelcontextprotocol/inspector python3 processing_mcp_server.py

# 4. In UI (http://localhost:6274):
#    - Select "fasta_qc"
#    - Paste FASTA from step 2
#    - Set min_length: 100
#    - Click "Run Tool"
#    - Verify cleaned sequences and stats
```

---

**Pro Tip**: Use UI mode for exploration, CLI mode for automation!
