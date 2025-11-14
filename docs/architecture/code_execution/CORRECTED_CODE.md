# Corrected Code for Salmo salar Analysis

## The Problem

Your original code used `await import('database')` which causes the error:
```
"Async not available"
```

This error occurs because **dynamic imports are not supported** in the vm2 sandbox environment used by the code-execution-sandbox.

## The Solution

All MCP tool modules are **pre-loaded** into the sandbox context. You can use them directly without importing!

## ❌ Original Code (DOESN'T WORK)

```javascript
// Import the database module
const database = await import('database');  // ❌ THIS CAUSES ERROR

// Fetch Salmo salar sequences from BOLD
const sequences = await database.getSequences({
  taxon: "Salmo salar",
  database: "bold",
  max_results: 100
});
// ... rest of code
```

## ✅ Corrected Code (WORKS)

```javascript
// No import needed - database is already available!
const sequences = await database.getSequences({
  taxon: "Salmo salar",
  database: "bold",
  max_results: 100
});

// Parse the FASTA format to count sequences and get some basic stats
const seqArray = sequences.split('\n>').filter(s => s.trim().length > 0);
const numSequences = seqArray.length;

// Get first sequence info for preview
const firstSeq = seqArray[0].replace(/^>/, '');
const firstHeader = firstSeq.split('\n')[0];
const firstSeqLength = firstSeq.split('\n').slice(1).join('').length;

// Calculate total length
let totalLength = 0;
for (const seq of seqArray) {
  const seqData = seq.replace(/^>/, '').split('\n').slice(1).join('');
  totalLength += seqData.length;
}

const avgLength = Math.round(totalLength / numSequences);

return {
  database: "BOLD",
  species: "Salmo salar",
  numSequences: numSequences,
  avgLength: avgLength,
  firstHeaderPreview: firstHeader.substring(0, 100),
  totalBaseCount: totalLength,
  sequencesRetrieved: sequences.substring(0, 500) + "..." // First 500 chars as preview
};
```

## How to Execute

### Via MCP Tool Call

Send this request to the `code-execution-sandbox` MCP server:

```json
{
  "tool": "execute_code",
  "arguments": {
    "code": "const sequences = await database.getSequences({\n  taxon: \"Salmo salar\",\n  database: \"bold\",\n  max_results: 100\n});\n\nconst seqArray = sequences.split('\\n>').filter(s => s.trim().length > 0);\nconst numSequences = seqArray.length;\n\nconst firstSeq = seqArray[0].replace(/^>/, '');\nconst firstHeader = firstSeq.split('\\n')[0];\nconst firstSeqLength = firstSeq.split('\\n').slice(1).join('').length;\n\nlet totalLength = 0;\nfor (const seq of seqArray) {\n  const seqData = seq.replace(/^>/, '').split('\\n').slice(1).join('');\n  totalLength += seqData.length;\n}\n\nconst avgLength = Math.round(totalLength / numSequences);\n\nreturn {\n  database: \"BOLD\",\n  species: \"Salmo salar\",\n  numSequences: numSequences,\n  avgLength: avgLength,\n  firstHeaderPreview: firstHeader.substring(0, 100),\n  totalBaseCount: totalLength,\n  sequencesRetrieved: sequences.substring(0, 500) + \"...\"\n};",
    "timeout": 30000
  }
}
```

### Expected Response

```json
{
  "success": true,
  "output": {
    "database": "BOLD",
    "species": "Salmo salar",
    "numSequences": 100,
    "avgLength": 650,
    "firstHeaderPreview": ">BOLD:AAA1234|Salmo salar|COI-5P|Canada|specimen-voucher:ROM:12345",
    "totalBaseCount": 65000,
    "sequencesRetrieved": ">BOLD:AAA1234|Salmo salar|COI-5P|Canada|specimen-voucher..."
  },
  "executionTime": 2345,
  "truncated": false
}
```

## Key Changes

1. **Removed** `const database = await import('database');`
2. **Changed** `await database.getSequences(...)` to use the pre-loaded `database` object directly
3. Everything else stays the same!

## Pre-loaded Modules

The following modules are always available in the sandbox:

- `database` - Database access (NCBI, BOLD, SILVA, UNITE, Ensembl, SRA)
- `processing` - Sequence processing (QC, dereplication, masking, chimera detection)
- `alignment` - Alignment and phylogeny (MAFFT, MUSCLE, FastTree, RAxML)
- `design` - Primer design (signature regions, Primer3, specificity, QC)
- `validation` - Validation (BLAST, BLAT, in silico PCR, coverage assessment)

## More Examples

### Example 1: Get Taxonomy

```javascript
const taxonomy = await database.getTaxonomy({
  taxon: "Salmo salar"
});

return {
  scientificName: taxonomy.scientific_name,
  rank: taxonomy.rank,
  lineage: taxonomy.lineage
};
```

### Example 2: Find Related Species

```javascript
const neighbors = await database.getNeighbors({
  taxon: "Salmo salar",
  rank: "genus"
});

return {
  genus: "Salmo",
  relatedSpecies: neighbors.slice(0, 10)
};
```

### Example 3: Process and Align Sequences

```javascript
// Fetch sequences
const sequences = await database.getSequences({
  taxon: "Salmo salar",
  database: "bold",
  max_results: 50
});

// Quality control
const qcResults = await processing.fastaQc({
  sequences: sequences
});

// Align sequences
const alignment = await alignment.alignSequences({
  sequences: sequences,
  method: "mafft"
});

// Build phylogenetic tree
const tree = await alignment.buildPhylogeny({
  alignment: alignment,
  method: "fasttree"
});

return {
  sequenceCount: qcResults.sequence_count,
  alignmentLength: qcResults.total_length,
  treePreview: tree.substring(0, 200)
};
```

## Troubleshooting

### Still getting "Async not available"?

Make sure you've:
1. ✅ Removed ALL `import()` or `await import()` statements
2. ✅ Rebuilt the executor: `cd /home/cxl/MDK_Design/mdk_mcp/code-execution && npm run build`
3. ✅ Restarted the code-execution-sandbox MCP server
4. ✅ Using the corrected code exactly as shown above

### How to verify modules are loaded?

You can check which modules are available:

```javascript
// Log available module names
console.log("Available modules:", Object.keys(this).filter(k => 
  ['database', 'processing', 'alignment', 'design', 'validation'].includes(k)
));

return { modulesAvailable: true };
```

## Additional Resources

- Full Usage Guide: `/home/cxl/MDK_Design/mdk_mcp/code-execution/USAGE_GUIDE.md`
- Executor Source: `/home/cxl/MDK_Design/mdk_mcp/code-execution/src/executor.ts`
- MCP Server: `/home/cxl/MDK_Design/mdk_mcp/workspace/mcp-server.ts`

