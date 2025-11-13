# Code Execution Sandbox - Quick Reference Card

**Version**: 1.1 | **Date**: November 13, 2025

---

## 🚀 Getting Started

```typescript
/// <reference path="/workspace/types/sandbox.d.ts" />

// Use pre-loaded globals (NO imports needed!)
const sequences = await database.getSequences({
  taxon: "Salmo salar",
  region: "COI",
  max_results: 100
});

// Process in-code, return only summary
const stats = parseFastaStats(sequences);
return stats;
```

---

## 📦 Available Modules (Pre-loaded Globals)

| Module | Purpose | Example |
|--------|---------|---------|
| `database` | Sequence retrieval | `database.getSequences({...})` |
| `processing` | Sequence QC | `processing.fastaQc({...})` |
| `alignment` | MSA & phylogeny | `alignment.alignSequences({...})` |
| `design` | Primer design | `design.primer3Design({...})` |
| `validation` | BLAST & validation | `validation.ggetBlast({...})` |

---

## 🛠️ Helper Functions

| Function | Purpose | Token Savings |
|----------|---------|---------------|
| `parseFastaStats()` | Return stats, not sequences | 99.7% |
| `filterAndSave()` | Filter & save to file | 99.8% |
| `saveToFile()` | Save large data to disk | 99.5% |
| `summarizeAlignment()` | Return alignment metrics | 99.6% |
| `batchProcess()` | Process in batches | 99.9% |
| `cacheResult()` | Cache expensive ops | 100% (on hit) |

---

## ❌ Common Mistakes

### DON'T Use Import/Require
```typescript
// ❌ WRONG
import { database } from 'database';
const db = require('database');

// ✅ CORRECT
const sequences = await database.getSequences({...});
```

### DON'T Return Large Data
```typescript
// ❌ WRONG (50KB → context)
return sequences;

// ✅ CORRECT (~200 bytes)
return parseFastaStats(sequences);
```

---

## 📊 Output Schema

```typescript
{
  success: boolean;
  output: any;                    // Result or logs
  error?: {                       // Structured error
    message: string;
    code: 'TIMEOUT' | 'TOOL_ERROR' | 'VM_ERROR' | ...,
    phase?: string,
    context?: object
  },
  executionTime: number;          // ms
  requestId: string;              // For tracing
  truncated?: boolean;            // If output truncated
  truncationReason?: string;      // Why truncated
}
```

---

## 🔒 Error Codes

| Code | Meaning | Action |
|------|---------|--------|
| `TIMEOUT` | Execution timeout | Increase timeout or optimize code |
| `TOOL_ERROR` | MCP tool failed | Check tool arguments |
| `VM_ERROR` | Sandbox error | Check syntax, no imports |
| `OUTPUT_TOO_LARGE` | Output > 1MB | Use helpers to reduce output |
| `RATE_LIMITED` | Too many requests | Wait for `retryAfter` seconds |
| `QUEUE_FULL` | Queue saturated | Wait or optimize code |

---

## ⏱️ Timeout Guidance

| Workload | Timeout | Example |
|----------|---------|---------|
| Quick | 5-10s | Single tool, simple processing |
| Typical | 20-40s | Multi-step, moderate data |
| Heavy | 40-60s | Large datasets, batch processing |

```typescript
await execute_code({
  code: "...",
  timeout: 30000  // 30s (default)
});
```

---

## 💾 File Paths

| Directory | Purpose | Cleanup |
|-----------|---------|---------|
| `/workspace/data/` | Persistent user data | Manual |
| `/workspace/results/` | Persistent outputs | Manual |
| `/workspace/cache/` | Cached results | 24h TTL |
| `/workspace/temp/` | Temporary files | On restart |
| `/workspace/lib/` | Helper functions | Read-only |
| `/workspace/types/` | Type definitions | Read-only |

```typescript
// Save large data to file
const metadata = await saveToFile(
  sequences,
  'output.fasta',
  { ttlSeconds: 3600, compress: true }
);

return { savedTo: metadata.path, size: formatBytes(metadata.size) };
```

---

## 📈 Best Practices

### ✅ DO
- Add type reference: `/// <reference path="/workspace/types/sandbox.d.ts" />`
- Use pre-loaded globals (no imports)
- Process data in-code, return summaries
- Use helper functions for common tasks
- Cache expensive operations
- Save large data to files
- Handle errors gracefully with structured errors

### ❌ DON'T
- Import or require MCP modules
- Return large data directly
- Exceed timeout limits
- Write outside `/workspace/`
- Ignore error codes
- Skip correlation IDs for debugging

---

## 🔍 Debugging

### Use Correlation IDs
```typescript
const result = await execute_code({ code: "..." });

if (!result.success) {
  console.error(`Error in ${result.requestId}:`, result.error);
  // Share requestId with ops team
}
```

### Query Logs
```bash
# Find all logs for a request
docker logs code-execution-sandbox | grep req_abc123
docker logs ndiag-database-server | grep req_abc123
```

---

## 📚 Full Documentation

- **Complete Guide**: `docs/architecture/code_execution/GUIDE.md`
- **Developer README**: `workspace/README.md`
- **Type Definitions**: `workspace/types/sandbox.d.ts`
- **Improvements**: `docs/architecture/code_execution/IMPROVEMENTS.md`
- **Changelog**: `docs/architecture/code_execution/CHANGELOG.md`

---

## 💡 Example: Complete Workflow

```typescript
/// <reference path="/workspace/types/sandbox.d.ts" />

// Step 1: Check cache
const cacheKey = `workflow_salmo_coi`;
let result = await getCachedResult(cacheKey);

if (!result) {
  // Step 2: Retrieve sequences
  const sequences = await database.getSequences({
    taxon: "Salmo salar",
    region: "COI",
    max_results: 100
  });
  
  // Step 3: Process & save
  const metadata = await filterAndSave(
    sequences,
    (seq) => seq.length > 500 && seq.length < 800,
    '/workspace/data/filtered.fasta'
  );
  
  // Step 4: Align
  const filtered = await fs.readFile(metadata.path, 'utf-8');
  const aligned = await alignment.alignSequences({
    fasta_content: filtered,
    algorithm: 'mafft'
  });
  
  // Step 5: Summarize (not full alignment!)
  result = {
    filtered: metadata.lines / 2,
    alignment: summarizeAlignment(aligned),
    savedTo: metadata.path
  };
  
  // Step 6: Cache for 1 hour
  await cacheResult(cacheKey, result, 3600);
}

return result;
```

**Token Usage**: ~2,500 tokens (vs 162,500 traditional) = **98.5% reduction**

---

**Quick Reference v1.1** | Updated: November 13, 2025

