# Code Execution Sandbox Workspace

This directory provides TypeScript definitions and linting rules for writing code that runs in the Code Execution Sandbox.

## Quick Start

### 1. Use TypeScript Definitions

Add a triple-slash reference at the top of your sandbox code:

```typescript
/// <reference path="/workspace/types/sandbox.d.ts" />

// Now you get full IntelliSense and type checking!
const sequences = await database.getSequences({
  taxon: "Salmo salar",  // ← autocomplete works here
  region: "COI",
  max_results: 100
});
```

### 2. Enable Linting

The `.eslintrc.json` file prevents common mistakes:

```bash
# Install ESLint (if not already installed)
npm install eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin

# Lint your sandbox code
npx eslint your-sandbox-code.ts
```

## Directory Structure

```
workspace/
├── README.md              # This file
├── .eslintrc.json         # ESLint rules for sandbox code
├── types/
│   └── sandbox.d.ts       # TypeScript definitions for sandbox globals
├── lib/                   # Helper functions (read-only)
├── data/                  # User data files (persistent)
├── results/               # Output files (persistent)
├── cache/                 # Cached results (TTL-based cleanup)
└── temp/                  # Temporary files (cleaned on restart)
```

## TypeScript Definitions

The `sandbox.d.ts` file provides types for:

### MCP Tool Modules (Pre-loaded Globals)
- `database` - Database access and sequence retrieval
- `processing` - Sequence processing and QC
- `alignment` - Multiple sequence alignment and phylogeny
- `design` - Primer and probe design
- `validation` - Primer validation and BLAST

### Helper Functions
- `parseFastaStats()` - Parse FASTA and return statistics
- `filterAndSave()` - Filter sequences and save to file
- `extractFields()` - Extract fields from headers
- `summarizeAlignment()` - Summarize alignment quality
- `batchProcess()` - Batch process large datasets
- `cacheResult()` / `getCachedResult()` - Cache results
- `saveToFile()` - Save data to file with metadata
- `formatBytes()` - Format byte sizes
- `truncateForContext()` - Truncate large strings
- `cleanupFiles()` - Clean up old files

### Node.js Modules (Whitelisted)
- `fs` - File system operations
- `path` - Path utilities
- `crypto` - Cryptographic functions

## Linting Rules

The ESLint configuration enforces sandbox best practices:

### ❌ Forbidden Patterns

```typescript
// ❌ WRONG - Import statements not allowed
import { database } from './database';
import * as database from './database';

// ❌ WRONG - Dynamic imports not supported
const db = await import('database');

// ❌ WRONG - Require not allowed for MCP tools
const database = require('database');
```

### ✅ Correct Patterns

```typescript
// ✅ CORRECT - Use pre-loaded globals directly
const sequences = await database.getSequences({ ... });
const qc = await processing.fastaQc({ ... });
const alignment = await alignment.alignSequences({ ... });
```

## Common Mistakes

### 1. Trying to Import MCP Modules

**Error**: `Module 'database' is not allowed in sandbox` or `Async not available`

**Fix**: Use pre-loaded globals instead:
```typescript
// ❌ DON'T DO THIS
import { getSequences } from 'database';

// ✅ DO THIS
const sequences = await database.getSequences({ ... });
```

### 2. Missing Type Reference

**Problem**: No IntelliSense or type checking

**Fix**: Add triple-slash reference:
```typescript
/// <reference path="/workspace/types/sandbox.d.ts" />
```

### 3. Returning Large Data

**Problem**: Output truncated, context bloat

**Fix**: Use helper functions:
```typescript
// ❌ DON'T DO THIS
return sequences;  // Might be 50KB+

// ✅ DO THIS
const stats = parseFastaStats(sequences);
return stats;  // ~200 bytes
```

## Examples

### Example 1: Basic Tool Call

```typescript
/// <reference path="/workspace/types/sandbox.d.ts" />

// Retrieve sequences (data stays in sandbox)
const sequences = await database.getSequences({
  taxon: "Salmo salar",
  region: "COI",
  max_results: 100
});

// Process in-code and return only summary
const stats = parseFastaStats(sequences);

return {
  count: stats.count,
  avgLength: stats.averageLength,
  gcContent: stats.gcContent
};
```

### Example 2: Multi-Tool Workflow

```typescript
/// <reference path="/workspace/types/sandbox.d.ts" />

// Step 1: Retrieve and filter
const sequences = await database.getSequences({
  taxon: "Salmo salar",
  region: "COI",
  max_results: 100
});

const metadata = await filterAndSave(
  sequences,
  (seq) => seq.length > 500 && seq.length < 800,
  '/workspace/data/filtered.fasta'
);

// Step 2: Align
const filtered = await fs.readFile(metadata.path, 'utf-8');
const aligned = await alignment.alignSequences({
  fasta_content: filtered,
  algorithm: 'mafft',
  strategy: 'auto'
});

// Step 3: Summarize (don't return full alignment)
const summary = summarizeAlignment(aligned);

return {
  filtered: metadata.lines / 2,
  alignmentLength: summary.length,
  conservation: summary.conservationScore,
  savedTo: metadata.path
};
```

### Example 3: Using Cache

```typescript
/// <reference path="/workspace/types/sandbox.d.ts" />

const cacheKey = `sequences_salmo_coi`;

// Check cache first
let stats = await getCachedResult<any>(cacheKey);

if (!stats) {
  // Not cached, fetch and process
  const sequences = await database.getSequences({
    taxon: "Salmo salar",
    region: "COI",
    max_results: 100
  });
  
  stats = parseFastaStats(sequences);
  
  // Cache for 1 hour
  await cacheResult(cacheKey, stats, 3600);
}

return stats;
```

## Best Practices

1. **Always add type reference** at the top of your sandbox code
2. **Use pre-loaded globals** - no imports needed
3. **Process data in-code** - return only summaries
4. **Use helper functions** - they're optimized for context efficiency
5. **Cache expensive operations** - avoid repeated computation
6. **Save large data to files** - keep it out of context
7. **Handle errors gracefully** - return structured errors

## Need Help?

See the main guide at `docs/architecture/code_execution/GUIDE.md` for:
- Complete architecture overview
- Security features
- Error handling
- Troubleshooting
- Production deployment

## Version

- **Sandbox API Version**: 1.0
- **Type Definitions Version**: 1.0
- **ESLint Config Version**: 1.0

