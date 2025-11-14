# Changelog - Code Execution Sandbox

## Version 1.1.0 - Filesystem Operations

### New Features

Added two new MCP tools for filesystem operations:

#### 1. `copy_file_to_workspace`
- **Purpose**: Copy files from local filesystem into container workspace
- **Parameters**:
  - `source_path`: Absolute path to source file on local filesystem
  - `destination_path`: Destination path in workspace (relative or absolute)
- **Use Cases**: Import data files, configuration files, reference databases

#### 2. `copy_file_from_workspace`
- **Purpose**: Copy files from container workspace to local filesystem
- **Parameters**:
  - `workspace_path`: Path to file in workspace (relative or absolute)
  - `destination_path`: Absolute path on local filesystem
- **Use Cases**: Export results, save processed data, extract reports

### Documentation Updates

- Added `docs.filesystem` with usage examples and use cases
- Updated `docs.quickStart` with filesystem operation examples
- Updated `docs.help()` to include filesystem operations
- Added comprehensive FILESYSTEM_OPERATIONS.md guide

### Code Changes

**Modified Files**:
- `src/executor.ts`: Added `copyFileToWorkspace()` and `copyFileFromWorkspace()` functions
- `src/executor.ts`: Added tool definitions and handlers for both operations
- `src/docs.ts`: Added filesystem documentation section
- `src/docs.ts`: Updated quick start guide and help text

### Path Resolution

**Workspace Paths** (relative to `/workspace`):
- Relative: `"input/data.fasta"` → `/workspace/input/data.fasta`
- Absolute: `"/workspace/input/data.fasta"` → `/workspace/input/data.fasta`

**Local Paths** (must be absolute):
- Example: `"/home/user/data/sequences.fasta"`

### Response Format

Success:
```json
{
  "success": true,
  "path": "/workspace/input/sequences.fasta",
  "size": 1024000  // copy_from_workspace only
}
```

Error:
```json
{
  "success": false,
  "error": "Error message"
}
```

### Example Workflow

```typescript
// 1. Copy data into workspace
copy_file_to_workspace({
  source_path: "/home/user/sequences.fasta",
  destination_path: "input/sequences.fasta"
});

// 2. Process in sandbox
execute_code({
  code: `
    const fs = require('fs').promises;
    const data = await fs.readFile('/workspace/input/sequences.fasta', 'utf-8');
    const processed = await processing.fastaQc({ sequences: data });
    await fs.writeFile('/workspace/output/results.fasta', processed);
    return { status: 'complete' };
  `
});

// 3. Export results
copy_file_from_workspace({
  workspace_path: "output/results.fasta",
  destination_path: "/home/user/results.fasta"
});
```

### Building

```bash
npm run build
```

### Testing

The tools are available immediately after building. Test via MCP tool calls:

```json
{
  "tool": "copy_file_to_workspace",
  "arguments": {
    "source_path": "/absolute/path/to/source.txt",
    "destination_path": "input/destination.txt"
  }
}
```

---

## Version 1.0.0 - Initial Release

- Code execution sandbox with security sandboxing
- MCP tool integration (database, processing, alignment, design, validation)
- Comprehensive documentation system
- Helper functions for context efficiency
- Timeout enforcement and resource limits

