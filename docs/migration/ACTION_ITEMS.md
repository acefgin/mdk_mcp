# MCP 2.0 Migration Action Items

**Project**: mdk_mcp Python → Node.js with Code Execution
**Timeline**: 14 weeks (3.5 months)
**Expected Impact**: 98.7% token reduction, 10x performance improvement
**Status**: Ready to begin

---

## Executive Summary

This document provides actionable tasks for migrating from Python-based MCP servers to Node.js with code execution architecture. Tasks are organized by phase, with clear dependencies, owners, and success criteria.

### Quick Reference

| Phase | Duration | Priority | Key Deliverable |
|-------|----------|----------|-----------------|
| **Pre-Migration** | Week 0 | 🔴 Critical | Environment setup, team training |
| **Phase 1: Infrastructure** | Week 1-3 | 🔴 Critical | Code execution sandbox, tool generator |
| **Phase 2: Database Server** | Week 4-5 | 🔴 Critical | First migrated server with 11 tools |
| **Phase 3: Skills Integration** | Week 6-7 | 🟡 High | Reusable workflow system |
| **Phase 4: Processing Server** | Week 8-9 | 🟡 High | Context-efficient processing (5 tools) |
| **Phase 5: Alignment Server** | Week 10-11 | 🟢 Medium | Phylogenetic caching (5 tools) |
| **Phase 6: Design Server** | Week 12-13 | 🟢 Medium | Batch primer design (6 tools) |
| **Phase 7: Validation Server** | Week 14 | 🟢 Medium | Privacy-preserving validation (7 tools) |
| **Post-Migration** | Ongoing | 🟡 High | Production deployment, monitoring |

---

## Pre-Migration Phase (Week 0)

### PM-1: Team Preparation
**Priority**: 🔴 Critical
**Owner**: Tech Lead
**Duration**: 2 days

**Tasks**:
- [ ] Schedule kickoff meeting with all stakeholders
- [ ] Review Anthropic's [Code Execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp) guide as team
- [ ] Assign phase owners (1 owner per phase)
- [ ] Create shared Slack channel: `#mcp-migration`
- [ ] Set up weekly sync meetings (Mondays 10am)

**Success Criteria**:
- ✅ All team members understand code execution architecture
- ✅ Phase owners assigned and committed
- ✅ Communication channels established

**Blockers/Risks**:
- Team availability conflicts → Mitigation: Schedule 2 weeks in advance

---

### PM-2: Development Environment Setup
**Priority**: 🔴 Critical
**Owner**: DevOps Engineer
**Duration**: 1 day

**Tasks**:
- [ ] Install Node.js 20+ LTS on development machines
  ```bash
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
  nvm install 20
  nvm use 20
  node --version  # Should be v20.x.x
  ```
- [ ] Install MCP SDK globally
  ```bash
  npm install -g @modelcontextprotocol/sdk
  ```
- [ ] Set up TypeScript compiler
  ```bash
  npm install -g typescript tsx
  tsc --version  # Should be 5.x+
  ```
- [ ] Configure VS Code with recommended extensions:
  - ESLint
  - Prettier
  - MCP Tools (if available)
- [ ] Clone repository and create `migration` branch
  ```bash
  cd /home/raycifeng/mdk_mcp
  git checkout -b migration/node-code-execution
  ```

**Success Criteria**:
- ✅ All developers can run `node --version` → v20.x.x
- ✅ TypeScript compiles without errors
- ✅ MCP SDK imports successfully

**Dependencies**: None

---

### PM-3: Testing Framework Setup
**Priority**: 🔴 Critical
**Owner**: QA Engineer
**Duration**: 1 day

**Tasks**:
- [ ] Initialize Vitest in project
  ```bash
  npm install -D vitest @vitest/ui
  ```
- [ ] Create `tests/` directory structure
  ```
  tests/
  ├── unit/
  ├── integration/
  ├── benchmarks/
  └── fixtures/
  ```
- [ ] Configure `vitest.config.ts`
  ```typescript
  import { defineConfig } from 'vitest/config';

  export default defineConfig({
    test: {
      globals: true,
      environment: 'node',
      coverage: {
        provider: 'v8',
        reporter: ['text', 'html'],
      },
    },
  });
  ```
- [ ] Write sample test to verify setup
- [ ] Set up CI/CD pipeline for automated testing

**Success Criteria**:
- ✅ `npm test` runs successfully
- ✅ Coverage reports generate
- ✅ CI pipeline triggers on commit

**Dependencies**: PM-2 (Environment Setup)

---

### PM-4: Docker Development Environment
**Priority**: 🟡 High
**Owner**: DevOps Engineer
**Duration**: 2 days

**Tasks**:
- [ ] Create `docker-compose.migration.yml` for new Node.js services
- [ ] Set up volume mounts for workspace persistence
  ```yaml
  volumes:
    - ./workspace:/workspace
    - ./skills:/workspace/skills
    - node_modules:/workspace/node_modules
  ```
- [ ] Configure hot-reload for development
- [ ] Test parallel running of Python (old) + Node.js (new) servers
- [ ] Document Docker commands in `docs/DOCKER_MIGRATION.md`

**Success Criteria**:
- ✅ Both Python and Node.js servers run simultaneously
- ✅ File changes trigger hot-reload
- ✅ Volumes persist across restarts

**Dependencies**: PM-2

---

## Phase 1: Code Execution Infrastructure (Week 1-3)

### P1-1: Tool File Generator Implementation
**Priority**: 🔴 Critical
**Owner**: Backend Engineer
**Duration**: 5 days

**Tasks**:
- [ ] Create `mcp_servers/shared/tool-generator.ts` (see MIGRATION_PLAN.md line 146-299)
- [ ] Implement `ToolFileGenerator` class with methods:
  - `generateToolFiles()` - Main orchestrator
  - `generateToolFile()` - Individual tool file creation
  - `generateIndexFile()` - Barrel export generation
  - `generateReadme()` - Server documentation
  - `generateTypeScriptInterface()` - Type generation from JSON schema
- [ ] Add unit tests for each method
  ```typescript
  // tests/unit/tool-generator.test.ts
  describe('ToolFileGenerator', () => {
    it('should generate valid TypeScript from JSON schema', async () => {
      const generator = new ToolFileGenerator();
      const result = await generator.generateToolFile(mockTool, 'database');
      expect(result).toContain('export async function');
    });
  });
  ```
- [ ] Test with existing Python server definitions
- [ ] Generate sample output for Database Server (11 tools)
- [ ] Validate generated code compiles without errors

**Success Criteria**:
- ✅ Generator produces valid TypeScript files
- ✅ Generated code passes `tsc --noEmit` check
- ✅ All 11 Database Server tools generate successfully
- ✅ Unit test coverage ≥90%

**Acceptance Test**:
```bash
npm run generate-tools -- --server database --output workspace/servers/
ls workspace/servers/database/  # Should show 11 .ts files + index.ts + README.md
tsc --noEmit workspace/servers/database/*.ts  # Should pass
```

**Dependencies**: PM-2, PM-3

---

### P1-2: MCP Client with Code Execution
**Priority**: 🔴 Critical
**Owner**: Backend Engineer
**Duration**: 5 days

**Tasks**:
- [ ] Create `workspace/lib/mcp-client.ts` (see MIGRATION_PLAN.md line 303-526)
- [ ] Implement `MCPCodeExecutionClient` class:
  - Connection management for 5 servers
  - Request/response handling with retries
  - Error handling and exponential backoff
  - Tool search with progressive disclosure
- [ ] Implement `callMCPTool<T>()` global helper function
- [ ] Implement `searchMCPTools()` for dynamic discovery
- [ ] Add connection pooling (max 5 concurrent connections)
- [ ] Write integration tests with mock MCP servers
  ```typescript
  // tests/integration/mcp-client.test.ts
  describe('MCPCodeExecutionClient', () => {
    it('should connect to all 5 servers', async () => {
      const client = new MCPCodeExecutionClient(mockConfigs);
      await client.initialize();
      expect(client.clients.size).toBe(5);
    });

    it('should retry on transient failures', async () => {
      // Test exponential backoff
    });
  });
  ```

**Success Criteria**:
- ✅ Client connects to Python MCP servers via stdio
- ✅ Retry logic tested with simulated failures
- ✅ Tool search returns correct results
- ✅ Integration tests pass

**Dependencies**: P1-1, PM-3

---

### P1-3: PII Tokenization System
**Priority**: 🟡 High
**Owner**: Security Engineer
**Duration**: 3 days

**Tasks**:
- [ ] Implement `PIITokenizer` class in `mcp-client.ts` (line 427-500)
- [ ] Add regex patterns for:
  - Email addresses
  - Phone numbers (US format)
  - Social Security Numbers
  - Credit card numbers (optional)
  - API keys (detect by entropy)
- [ ] Implement bidirectional tokenization (tokenize + detokenize)
- [ ] Add tests for edge cases:
  - Nested objects
  - Arrays of sensitive data
  - Mixed sensitive/non-sensitive content
- [ ] Create audit logging for tokenization events
- [ ] Document PII handling policy in `docs/SECURITY.md`

**Success Criteria**:
- ✅ Email addresses tokenized as `[EMAIL_N]`
- ✅ Phone numbers tokenized as `[PHONE_N]`
- ✅ Detokenization restores original values
- ✅ No PII leaks in logs
- ✅ 100% test coverage for tokenizer

**Security Test**:
```typescript
const tokenizer = new PIITokenizer();
const input = { user: "john.doe@example.com", phone: "555-123-4567" };
const tokenized = tokenizer.tokenize(input);
expect(tokenized.user).toMatch(/\[EMAIL_\d+\]/);
expect(tokenized.user).not.toContain("john.doe");
```

**Dependencies**: P1-2

---

### P1-4: Skills Manager Implementation
**Priority**: 🟡 High
**Owner**: Backend Engineer
**Duration**: 4 days

**Tasks**:
- [ ] Create `workspace/lib/skills-manager.ts` (line 532-661)
- [ ] Implement `SkillsManager` class with methods:
  - `saveSkill()` - Persist skill to filesystem
  - `loadSkill()` - Load skill code
  - `searchSkills()` - Query by tags/description
  - `listSkills()` - List all available skills
  - `updateSkillsIndex()` - Maintain SKILLS.md
- [ ] Create `workspace/skills/` directory
- [ ] Implement SKILLS.md parser for metadata extraction
- [ ] Add version tracking for skill updates
- [ ] Write tests for skill CRUD operations
  ```typescript
  describe('SkillsManager', () => {
    it('should save and load skills', async () => {
      const skills = new SkillsManager();
      await skills.saveSkill('test-skill', code, desc, ['test']);
      const loaded = await skills.loadSkill('test-skill');
      expect(loaded).toContain(code);
    });
  });
  ```

**Success Criteria**:
- ✅ Skills persist across sessions
- ✅ SKILLS.md auto-updates on save
- ✅ Search returns relevant results
- ✅ Skills versioned with Git

**Dependencies**: P1-2

---

### P1-5: Code Execution Sandbox
**Priority**: 🔴 Critical
**Owner**: DevOps Engineer
**Duration**: 5 days

**Tasks**:
- [ ] Create `code-execution/Dockerfile` (line 1876-1907)
- [ ] Implement `code-execution/executor.ts` (line 1912-2046)
- [ ] Configure security constraints:
  - Non-root user execution
  - Read-only filesystem (except /workspace)
  - Network isolation (only MCP servers accessible)
  - Resource limits: 4GB RAM, 2 CPU cores
  - Execution timeout: 300s
- [ ] Add `execute_code` tool handler
- [ ] Implement code validation (AST parsing for dangerous patterns)
- [ ] Test with malicious code samples (injection attempts)
- [ ] Document security model in `docs/SECURITY_MODEL.md`

**Security Tests**:
```typescript
// Should block dangerous operations
await expect(executeCode('require("child_process").exec("rm -rf /")')).rejects.toThrow();
await expect(executeCode('eval(userInput)')).rejects.toThrow();
```

**Success Criteria**:
- ✅ Sandbox blocks filesystem escape attempts
- ✅ Network access limited to MCP servers
- ✅ Memory/CPU limits enforced
- ✅ Malicious code rejected
- ✅ Security audit passes

**Dependencies**: P1-2, PM-4

---

### P1-6: Progressive Tool Disclosure Testing
**Priority**: 🟡 High
**Owner**: QA Engineer
**Duration**: 2 days

**Tasks**:
- [ ] Create benchmark test `tests/benchmarks/token-usage.bench.ts`
- [ ] Measure token usage for traditional approach (baseline)
  ```typescript
  const traditional = await loadAllTools(); // Should be ~150K tokens
  ```
- [ ] Measure token usage for code execution approach
  ```typescript
  const codeExec = await loadToolsOnDemand(['getSequences']); // Should be ~400 tokens
  ```
- [ ] Calculate reduction percentage (target: ≥95%)
- [ ] Generate comparison report
- [ ] Present findings to team

**Success Criteria**:
- ✅ Token reduction ≥95% vs baseline
- ✅ Benchmark runs reliably
- ✅ Report generated automatically

**Benchmark Output Example**:
```
Traditional Approach: 150,000 tokens
Code Execution: 2,500 tokens
Reduction: 98.3% ✅
```

**Dependencies**: P1-1, P1-2, P1-3, P1-4, P1-5

---

## Phase 2: Database Server Migration (Week 4-5)

### P2-1: Generate Database Server Tool Files
**Priority**: 🔴 Critical
**Owner**: Backend Engineer
**Duration**: 3 days

**Tasks**:
- [ ] Run tool generator on existing Python Database Server
  ```bash
  npm run generate-tools -- \
    --server database \
    --input mcp_servers/database_server/database_mcp_server.py \
    --output workspace/servers/
  ```
- [ ] Review generated files for correctness:
  - `workspace/servers/database/getSequences.ts`
  - `workspace/servers/database/ggetRef.ts`
  - `workspace/servers/database/ggetSearch.ts`
  - (... all 11 tools ...)
  - `workspace/servers/database/index.ts`
  - `workspace/servers/database/README.md`
- [ ] Fix any type generation issues
- [ ] Add JSDoc comments for better IDE support
- [ ] Compile and verify no errors
- [ ] Create example usage file `examples/database-usage.ts`

**Verification Checklist**:
```typescript
// Verify each tool exports correct interface
import * as database from './servers/database';

const seqs = await database.getSequences({
  taxon: "Salmo salar",
  region: "COI"
});
expect(typeof seqs).toBe('string');
```

**Success Criteria**:
- ✅ All 11 tools generated successfully
- ✅ TypeScript compilation passes
- ✅ Types match Python MCP server schemas
- ✅ Example usage runs without errors

**Dependencies**: P1-1, P1-2

---

### P2-2: Test gget Integration
**Priority**: 🔴 Critical
**Owner**: Backend Engineer
**Duration**: 2 days

**Tasks**:
- [ ] Test `ggetRef()` - Reference genome retrieval
  ```typescript
  const ref = await database.ggetRef({ species: 'homo_sapiens' });
  expect(ref).toHaveProperty('assembly');
  ```
- [ ] Test `ggetSearch()` - Gene search
- [ ] Test `ggetInfo()` - Gene information
- [ ] Test `ggetSeq()` - Sequence retrieval by Ensembl ID
- [ ] Verify error handling for invalid inputs
- [ ] Test rate limiting (gget has no strict limits, but verify graceful handling)
- [ ] Write integration tests

**Success Criteria**:
- ✅ All gget tools return valid data
- ✅ Error messages are user-friendly
- ✅ Integration tests pass

**Dependencies**: P2-1

---

### P2-3: NCBI E-utilities Wrapper
**Priority**: 🔴 Critical
**Owner**: Backend Engineer
**Duration**: 3 days

**Tasks**:
- [ ] Test `getSequences()` with NCBI source
  ```typescript
  const seqs = await database.getSequences({
    taxon: "Salmo salar",
    region: "COI",
    source: "ncbi",
    max_results: 10
  });
  expect(seqs).toContain('>');
  ```
- [ ] Test `getTaxonomy()` - Taxonomic lineage
- [ ] Test `getNeighbors()` - Related species
- [ ] Verify NCBI API key is used if available (env: `NCBI_API_KEY`)
- [ ] Test rate limiting (3 req/sec without key, 10 req/sec with key)
- [ ] Add retry logic for NCBI timeouts
- [ ] Write integration tests with mocked NCBI responses

**Rate Limiting Test**:
```typescript
// Should throttle requests appropriately
const start = Date.now();
await Promise.all([
  database.getTaxonomy({ taxon: 'Salmo salar' }),
  database.getTaxonomy({ taxon: 'Gadus morhua' }),
  database.getTaxonomy({ taxon: 'Thunnus albacares' }),
]);
const elapsed = Date.now() - start;
expect(elapsed).toBeGreaterThan(600); // ~3 req/sec = 200ms each
```

**Success Criteria**:
- ✅ NCBI tools return valid data
- ✅ Rate limiting enforced
- ✅ Retries work on transient failures
- ✅ Integration tests pass

**Dependencies**: P2-1

---

### P2-4: SRA/BioProject Search
**Priority**: 🟡 High
**Owner**: Backend Engineer
**Duration**: 2 days

**Tasks**:
- [ ] Test `searchSRAStudies()` - Study search
  ```typescript
  const studies = await database.searchSRAStudies({
    query: "Salmo salar transcriptome",
    max_results: 10
  });
  expect(studies.length).toBeGreaterThan(0);
  ```
- [ ] Test `getSRARuninfo()` - Run metadata
- [ ] Test `searchSRACloud()` - BigQuery/Athena queries (if credentials available)
- [ ] Handle cases where BigQuery credentials are missing (graceful fallback)
- [ ] Write integration tests

**Success Criteria**:
- ✅ SRA tools return valid results
- ✅ Graceful error handling for missing credentials
- ✅ Integration tests pass

**Dependencies**: P2-1

---

### P2-5: Database Server Example Workflows
**Priority**: 🟡 High
**Owner**: Backend Engineer
**Duration**: 2 days

**Tasks**:
- [ ] Create `examples/salmon-sequences-workflow.ts` (see MIGRATION_PLAN.md line 743-825)
- [ ] Implement workflow:
  1. Fetch target sequences (Salmo salar COI)
  2. Get taxonomic neighbors
  3. Fetch off-target sequences (parallel)
  4. Combine and save
- [ ] Add logging for each step
- [ ] Measure token usage (target: <1000 tokens)
- [ ] Create `examples/README.md` with all examples
- [ ] Record demo video showing workflow execution

**Expected Output**:
```
🐟 Salmon Sequences Workflow

1. Fetching Salmo salar COI sequences...
  ✓ Retrieved 100 sequences
  ✓ Average length: 652 bp

2. Finding taxonomic neighbors...
  ✓ Found 15 neighbor taxa

3. Fetching off-target sequences (parallel)...
  ✓ Retrieved 450 off-target sequences

✅ Workflow complete!
   Total sequences: 550
   Saved to: ./data/sequences/salmon-dataset.fasta
```

**Success Criteria**:
- ✅ Workflow executes end-to-end
- ✅ Token usage <1000 tokens
- ✅ Demo video recorded

**Dependencies**: P2-1, P2-2, P2-3, P2-4

---

### P2-6: Database Server Docker Container
**Priority**: 🟡 High
**Owner**: DevOps Engineer
**Duration**: 2 days

**Tasks**:
- [ ] Create `mcp_servers/database_server_node/Dockerfile`
  ```dockerfile
  FROM node:20-slim
  WORKDIR /app
  COPY package*.json ./
  RUN npm ci --production
  COPY . .
  USER node
  CMD ["node", "database-server.js"]
  ```
- [ ] Update `docker-compose.migration.yml` to include Node.js database server
- [ ] Test parallel running (Python + Node.js)
- [ ] Verify volume mounts work correctly
- [ ] Test with MCP Inspector
  ```bash
  npx @modelcontextprotocol/inspector docker exec -i ndiag-database-server-node node /app/database-server.js
  ```

**Success Criteria**:
- ✅ Container builds successfully
- ✅ Server starts and responds to MCP requests
- ✅ MCP Inspector connects
- ✅ All 11 tools discoverable

**Dependencies**: P2-1, P2-2, P2-3, P2-4, P2-5

---

### P2-7: Database Server Unit Tests
**Priority**: 🔴 Critical
**Owner**: QA Engineer
**Duration**: 3 days

**Tasks**:
- [ ] Create `tests/unit/database/*.test.ts` for each tool
- [ ] Mock external API calls (NCBI, gget, BOLD, SRA)
- [ ] Test error handling:
  - Invalid taxon names
  - Network timeouts
  - Rate limit errors
  - Empty results
- [ ] Test edge cases:
  - Very long taxon names
  - Special characters in queries
  - Max results = 0
- [ ] Achieve ≥90% code coverage
- [ ] Run tests in CI/CD pipeline

**Test Structure**:
```typescript
// tests/unit/database/getSequences.test.ts
describe('getSequences', () => {
  it('should fetch sequences from NCBI', async () => { ... });
  it('should handle invalid taxon', async () => { ... });
  it('should respect max_results', async () => { ... });
  it('should retry on transient failures', async () => { ... });
});
```

**Success Criteria**:
- ✅ ≥90% code coverage
- ✅ All edge cases tested
- ✅ Tests pass in CI/CD

**Dependencies**: P2-1 through P2-6

---

### P2-8: Database Server Token Usage Measurement
**Priority**: 🔴 Critical
**Owner**: QA Engineer
**Duration**: 1 day

**Tasks**:
- [ ] Measure token usage for all Database Server workflows
- [ ] Create comparison report:
  - Traditional: Load all 11 tools = ~40,000 tokens
  - Code execution: Load on demand = ~400 tokens per tool
- [ ] Calculate actual reduction percentage
- [ ] Update documentation with findings
- [ ] Present to team in weekly sync

**Benchmark Script**:
```typescript
// tests/benchmarks/database-tokens.bench.ts
const traditional = countTokens(await loadAllDatabaseTools());
const codeExec = countTokens(await import('./servers/database'));
const reduction = ((traditional - codeExec) / traditional) * 100;
console.log(`Reduction: ${reduction.toFixed(2)}%`);
```

**Success Criteria**:
- ✅ Token reduction ≥95%
- ✅ Report generated
- ✅ Team agrees to proceed

**Dependencies**: P2-7

---

## Phase 3: Skills Integration (Week 6-7)

### P3-1: Salmon Primer Workflow Skill
**Priority**: 🟡 High
**Owner**: Backend Engineer
**Duration**: 3 days

**Tasks**:
- [ ] Create `workspace/skills/salmon-primer-workflow.ts`
- [ ] Implement complete workflow:
  1. Fetch sequences (database)
  2. Process and dereplicate (processing)
  3. Align sequences (alignment)
  4. Find signature regions (design)
  5. Design primers (design)
  6. Validate primers (validation)
- [ ] Add skill metadata:
  ```typescript
  /**
   * @skill salmon-primer-workflow
   * @description Complete salmon-specific qPCR primer design pipeline
   * @tags primer, salmon, qpcr, workflow
   */
  ```
- [ ] Save skill with SkillsManager
- [ ] Test end-to-end execution
- [ ] Document in SKILLS.md

**Success Criteria**:
- ✅ Workflow executes end-to-end
- ✅ Skill persists across sessions
- ✅ Token usage <3000 tokens

**Dependencies**: P2-8 (Database Server complete)

---

### P3-2: Multiplex Primer Design Skill
**Priority**: 🟡 High
**Owner**: Backend Engineer
**Duration**: 4 days

**Tasks**:
- [ ] Create `workspace/skills/multiplex-primer-design.ts` (see MIGRATION_PLAN.md line 1207-1328)
- [ ] Implement multiplex workflow for N targets
- [ ] Add parallel processing for independent regions
- [ ] Implement filtering logic in code (not through model)
- [ ] Test with 3+ genomic regions
- [ ] Save skill and document

**Expected Performance**:
- **Traditional**: 3 regions × 5 taxa = 15 alignments through context = ~200K tokens
- **Code execution**: Cache + filter in code = ~5K tokens
- **Target reduction**: 97.5%

**Success Criteria**:
- ✅ Handles 3+ regions successfully
- ✅ Parallel execution works
- ✅ Token usage <5000 tokens

**Dependencies**: P3-1

---

### P3-3: Skills Search Functionality
**Priority**: 🟢 Medium
**Owner**: Backend Engineer
**Duration**: 2 days

**Tasks**:
- [ ] Implement fuzzy search in SkillsManager
- [ ] Add tag-based filtering
- [ ] Create CLI tool for skill discovery
  ```bash
  npm run skills search -- "primer"
  # Output:
  # - salmon-primer-workflow: Complete salmon-specific qPCR primer design
  # - multiplex-primer-design: Multiplex primer design for multiple targets
  ```
- [ ] Add `searchSkills()` to global exports
- [ ] Write tests for search functionality

**Success Criteria**:
- ✅ Search returns relevant results
- ✅ Tag filtering works
- ✅ CLI tool functional

**Dependencies**: P3-1, P3-2

---

### P3-4: Skills Documentation
**Priority**: 🟢 Medium
**Owner**: Technical Writer
**Duration**: 2 days

**Tasks**:
- [ ] Create comprehensive `workspace/skills/SKILLS.md`
- [ ] Document each skill with:
  - Purpose and use cases
  - Input parameters
  - Expected output
  - Token usage
  - Example invocation
- [ ] Add "How to Create a Skill" guide
- [ ] Create video tutorial on skill usage
- [ ] Review with team

**Success Criteria**:
- ✅ SKILLS.md complete with all skills
- ✅ Tutorial video recorded
- ✅ Team can create new skills

**Dependencies**: P3-1, P3-2, P3-3

---

## Phase 4: Processing Server Migration (Week 8-9)

### P4-1: Generate Processing Server Tool Files
**Priority**: 🔴 Critical
**Owner**: Backend Engineer
**Duration**: 2 days

**Tasks**:
- [ ] Run tool generator on Processing Server
  ```bash
  npm run generate-tools -- \
    --server processing \
    --input mcp_servers/processing_server/processing_mcp_server.py \
    --output workspace/servers/
  ```
- [ ] Generate 5 tools:
  - `fastaQC.ts`
  - `dereplicate.ts`
  - `maskLowComplexity.ts`
  - `detectChimeras.ts`
  - `processSequences.ts`
- [ ] Review and fix type issues
- [ ] Compile and verify

**Success Criteria**:
- ✅ All 5 tools generated
- ✅ Compilation passes
- ✅ Types correct

**Dependencies**: P3-4 (Skills complete)

---

### P4-2: seqkit and vsearch Wrappers
**Priority**: 🔴 Critical
**Owner**: Backend Engineer
**Duration**: 3 days

**Tasks**:
- [ ] Implement `fastaQC()` tool wrapper
- [ ] Test seqkit integration (stats, filtering)
- [ ] Implement `dereplicate()` with vsearch
- [ ] Test `maskLowComplexity()` (DUST algorithm)
- [ ] Test `detectChimeras()` (UCHIME)
- [ ] Verify CLI tools available in container
- [ ] Write integration tests

**Success Criteria**:
- ✅ All CLI tools accessible
- ✅ Wrappers return correct output
- ✅ Error handling works

**Dependencies**: P4-1

---

### P4-3: Context-Efficient Large Dataset Workflow
**Priority**: 🟡 High
**Owner**: Backend Engineer
**Duration**: 3 days

**Tasks**:
- [ ] Create `examples/process-large-dataset.ts` (see MIGRATION_PLAN.md line 893-983)
- [ ] Test with 10,000 sequences (5MB FASTA)
- [ ] Implement filtering in code (not through model)
- [ ] Measure token usage (target: <500 tokens)
- [ ] Compare to traditional approach (would be ~4M tokens)
- [ ] Document token savings

**Expected Results**:
- **Input**: 10,000 sequences × 500bp = 5MB
- **Traditional**: 5MB through context 3 times = ~4M tokens
- **Code execution**: Summary only = ~200 tokens
- **Reduction**: 99.995%

**Success Criteria**:
- ✅ Processes 10K sequences successfully
- ✅ Token usage <500 tokens
- ✅ 99.9%+ reduction vs traditional

**Dependencies**: P4-2

---

### P4-4: Processing Server Docker & Tests
**Priority**: 🟡 High
**Owner**: DevOps + QA Engineer
**Duration**: 3 days

**Tasks**:
- [ ] Create Dockerfile with seqkit + vsearch
- [ ] Build and test container
- [ ] Write unit tests (≥90% coverage)
- [ ] Run integration tests
- [ ] Measure token reduction

**Success Criteria**:
- ✅ Container builds
- ✅ Tests pass
- ✅ Token reduction confirmed

**Dependencies**: P4-1, P4-2, P4-3

---

## Phase 5: Alignment Server Migration (Week 10-11)

### P5-1: Generate Alignment Server Tool Files
**Priority**: 🔴 Critical
**Owner**: Backend Engineer
**Duration**: 2 days

**Tasks**:
- [ ] Generate 5 alignment tools
- [ ] Review and compile
- [ ] Create examples

**Success Criteria**:
- ✅ All 5 tools generated
- ✅ Compilation passes

**Dependencies**: P4-4

---

### P5-2: Phylogenetic Caching Implementation
**Priority**: 🟡 High
**Owner**: Backend Engineer
**Duration**: 3 days

**Tasks**:
- [ ] Implement caching in `buildPhylogeny.ts` (see MIGRATION_PLAN.md line 1073-1112)
- [ ] Use SHA256 hash of alignment as cache key
- [ ] Store cached trees in `workspace/data/cache/`
- [ ] Test cache hit/miss scenarios
- [ ] Measure performance improvement (expect 10x speedup on cache hits)

**Caching Logic**:
```typescript
const cacheKey = createHash('sha256')
  .update(alignment_content + JSON.stringify(params))
  .digest('hex');
const cachePath = `./data/cache/phylo-${cacheKey}.json`;

// Check cache first
if (await fileExists(cachePath)) {
  return JSON.parse(await readFile(cachePath));
}

// Cache miss - compute and save
const tree = await callMCPTool('alignment__build_phylogeny', input);
await writeFile(cachePath, JSON.stringify(tree));
return tree;
```

**Success Criteria**:
- ✅ Cache hits return instantly
- ✅ Cache persists across sessions
- ✅ 10x speedup on repeated alignments

**Dependencies**: P5-1

---

### P5-3: MAFFT/MUSCLE Wrappers and Tests
**Priority**: 🟡 High
**Owner**: Backend Engineer + QA
**Duration**: 4 days

**Tasks**:
- [ ] Test MAFFT strategies (auto, linsi, ginsi, einsi)
- [ ] Test MUSCLE v5 integration
- [ ] Test Clustal Omega
- [ ] Write unit and integration tests
- [ ] Build Docker container
- [ ] Measure token reduction

**Success Criteria**:
- ✅ All alignment algorithms work
- ✅ Tests pass
- ✅ Container functional

**Dependencies**: P5-1, P5-2

---

## Phase 6: Design Server Migration (Week 12-13)

### P6-1: Generate Design Server Tool Files
**Priority**: 🔴 Critical
**Owner**: Backend Engineer
**Duration**: 2 days

**Tasks**:
- [ ] Generate 6 design tools
- [ ] Review and compile
- [ ] Create examples

**Success Criteria**:
- ✅ All 6 tools generated
- ✅ Compilation passes

**Dependencies**: P5-3

---

### P6-2: Primer3 Integration and Batch Processing
**Priority**: 🔴 Critical
**Owner**: Backend Engineer
**Duration**: 4 days

**Tasks**:
- [ ] Implement `primer3Design()` wrapper
- [ ] Test with various constraint sets
- [ ] Implement batch processing for multiple regions
- [ ] Add ViennaRNA for secondary structure prediction
- [ ] Test `oligoQC()` tool
- [ ] Write integration tests

**Success Criteria**:
- ✅ Primer3 generates valid primers
- ✅ Batch processing works
- ✅ QC checks functional

**Dependencies**: P6-1

---

### P6-3: Multiplex Design Workflow and Tests
**Priority**: 🟡 High
**Owner**: Backend Engineer + QA
**Duration**: 4 days

**Tasks**:
- [ ] Create multiplex primer design workflow (see MIGRATION_PLAN.md line 1207-1328)
- [ ] Test with 3+ regions
- [ ] Implement filtering in code
- [ ] Write tests
- [ ] Build Docker container
- [ ] Measure token reduction (target: 97.5%)

**Success Criteria**:
- ✅ Multiplex design works
- ✅ Token reduction ≥95%
- ✅ Tests pass

**Dependencies**: P6-1, P6-2

---

## Phase 7: Validation Server Migration (Week 14)

### P7-1: Generate Validation Server Tool Files
**Priority**: 🔴 Critical
**Owner**: Backend Engineer
**Duration**: 1 day

**Tasks**:
- [ ] Generate 7 validation tools
- [ ] Review and compile
- [ ] Create examples

**Success Criteria**:
- ✅ All 7 tools generated
- ✅ Compilation passes

**Dependencies**: P6-3

---

### P7-2: BLAST Integration with Result Filtering
**Priority**: 🔴 Critical
**Owner**: Backend Engineer
**Duration**: 3 days

**Tasks**:
- [ ] Implement `ggetBlast()`, `ggetBlat()`, `blastNT()` wrappers
- [ ] Add result filtering in code (don't pass all hits through model)
- [ ] Test with sample primers
- [ ] Write integration tests

**Filtering Example**:
```typescript
// Fetch 1000 BLAST hits
const allHits = await validation.ggetBlast({ sequence: primer, limit: 1000 });

// Filter in code (not through model)
const targetHits = allHits.filter(hit =>
  hit.description.includes(targetTaxon) && hit.identity > 95
);
const offTargetHits = allHits.filter(hit =>
  !hit.description.includes(targetTaxon) && hit.identity > 90
);

// Return only summary (not 1000 hits)
return {
  target_count: targetHits.length,
  offtarget_count: offTargetHits.length,
  top_target: targetHits[0],
  worst_offtarget: offTargetHits[0]
};  // Only ~500 tokens vs 50K for all hits
```

**Success Criteria**:
- ✅ BLAST tools work
- ✅ Filtering reduces tokens by 99%
- ✅ Tests pass

**Dependencies**: P7-1

---

### P7-3: PII Tokenization Testing and Validation Pipeline
**Priority**: 🔴 Critical
**Owner**: Backend Engineer + Security
**Duration**: 3 days

**Tasks**:
- [ ] Enable PII tokenization for validation server
  ```typescript
  const client = new MCPCodeExecutionClient(configs, true); // Enable tokenization
  ```
- [ ] Test with sample data containing emails, phones
- [ ] Verify no PII in logs
- [ ] Create comprehensive validation workflow (see MIGRATION_PLAN.md line 1405-1548)
- [ ] Test end-to-end primer validation
- [ ] Write security audit tests
- [ ] Document PII handling

**Security Audit**:
```typescript
// Run validation with PII
const result = await validatePrimersComprehensive({
  primers: { forward: "ATCG...", reverse: "GCTA..." },
  taxon: "Salmo salar",
  region: "COI",
  researcher_email: "sensitive@example.com"
});

// Verify logs don't contain actual email
const logs = capturedLogs.join('\n');
expect(logs).not.toContain("sensitive@example.com");
expect(logs).toMatch(/\[EMAIL_\d+\]/);
```

**Success Criteria**:
- ✅ PII tokenized correctly
- ✅ No PII leaks
- ✅ Validation pipeline functional
- ✅ Security audit passes

**Dependencies**: P7-1, P7-2

---

### P7-4: Final Integration and Docker Build
**Priority**: 🔴 Critical
**Owner**: DevOps Engineer
**Duration**: 2 days

**Tasks**:
- [ ] Build validation server Docker container
- [ ] Test all 7 tools
- [ ] Run full integration tests
- [ ] Measure final token reduction across all 5 servers

**Final Benchmark**:
```
Traditional (Python): 150,000 tokens
Code Execution (Node): 2,500 tokens
Reduction: 98.3% ✅
```

**Success Criteria**:
- ✅ All 5 servers running
- ✅ 34 tools functional
- ✅ Token reduction ≥98%
- ✅ All tests pass

**Dependencies**: P7-1, P7-2, P7-3

---

## Post-Migration Phase (Ongoing)

### POST-1: Production Deployment
**Priority**: 🔴 Critical
**Owner**: DevOps Engineer
**Duration**: 3 days

**Tasks**:
- [ ] Create production `docker-compose.prod.yml`
- [ ] Set up monitoring (Prometheus + Grafana)
  - Token usage per workflow
  - Execution time per tool
  - Error rates
  - Cache hit rates
- [ ] Configure alerts:
  - Error rate >5%
  - Token usage >5000 per workflow
  - Execution time >60s
- [ ] Deploy to staging environment
- [ ] Run smoke tests
- [ ] Deploy to production
- [ ] Monitor for 48 hours

**Success Criteria**:
- ✅ Production deployment successful
- ✅ Monitoring dashboards functional
- ✅ No critical alerts in first 48h
- ✅ Token usage <3000 tokens/workflow

**Dependencies**: P7-4

---

### POST-2: Performance Monitoring and Optimization
**Priority**: 🟡 High
**Owner**: Backend Engineer
**Duration**: Ongoing

**Tasks**:
- [ ] Create weekly performance reports
- [ ] Track key metrics:
  - Average token usage per workflow
  - Average execution time
  - Cache hit rates
  - Error rates
  - Cost savings (API costs)
- [ ] Identify optimization opportunities
- [ ] Implement improvements
- [ ] Share findings with team

**Weekly Report Template**:
```markdown
## Weekly Performance Report (Week XX)

### Token Usage
- Average: 2,345 tokens/workflow (-98.2% vs baseline)
- Min: 1,200 tokens
- Max: 4,500 tokens

### Execution Time
- Average: 15.3 seconds (-89% vs baseline)
- Cache hit rate: 67%

### Cost Savings
- Traditional cost: $1,800/month
- Current cost: $28/month
- Savings: $1,772/month (98.4%)

### Top Issues
1. PubMed timeout in 3% of validation calls → Add retry
2. Cache misses on similar alignments → Improve hash key
```

**Success Criteria**:
- ✅ Weekly reports generated
- ✅ Optimization backlog maintained
- ✅ Continuous improvement

**Dependencies**: POST-1

---

### POST-3: Skills Repository Growth
**Priority**: 🟡 High
**Owner**: Backend Engineer
**Duration**: Ongoing

**Tasks**:
- [ ] Set target: 50 skills in first 3 months
- [ ] Encourage team to save successful workflows as skills
- [ ] Review and refactor skills monthly
- [ ] Create skills leaderboard (most used skills)
- [ ] Host monthly "Skill Showcase" meeting
- [ ] Document best practices for skill creation

**Monthly Metrics**:
- Total skills count
- New skills this month
- Most used skills
- Average skill token savings

**Target**: 50 skills by Month 3

**Dependencies**: POST-1

---

### POST-4: Documentation and Training
**Priority**: 🟡 High
**Owner**: Technical Writer
**Duration**: 2 weeks

**Tasks**:
- [ ] Update all documentation:
  - README.md
  - CLAUDE.md
  - DEPLOYMENT.md
  - MIGRATION_PLAN.md
  - MCP_2.0_ARCHITECTURE_SUMMARY.md
- [ ] Create migration retrospective document
- [ ] Record training videos:
  - "How to use the new system"
  - "How to create skills"
  - "Debugging code execution"
- [ ] Host training session for team
- [ ] Create FAQ document
- [ ] Update onboarding docs

**Success Criteria**:
- ✅ All docs updated
- ✅ Training videos recorded
- ✅ Team trained

**Dependencies**: POST-1

---

### POST-5: Rollback Plan (Contingency)
**Priority**: 🔴 Critical
**Owner**: DevOps Engineer
**Duration**: 1 day

**Tasks**:
- [ ] Document rollback procedure
- [ ] Keep Python servers running for 2 weeks after migration
- [ ] Create rollback script
  ```bash
  #!/bin/bash
  # Rollback to Python servers
  docker-compose -f docker-compose.yml up -d
  docker-compose -f docker-compose.migration.yml down
  ```
- [ ] Test rollback in staging
- [ ] Define rollback criteria:
  - Error rate >10%
  - Token usage >10,000 per workflow
  - Critical bugs unfixable within 24h
- [ ] Assign rollback decision maker

**Rollback Checklist**:
- [ ] Notify team in #mcp-migration
- [ ] Stop Node.js containers
- [ ] Start Python containers
- [ ] Verify all tools functional
- [ ] Update monitoring dashboards
- [ ] Post-mortem within 48h

**Success Criteria**:
- ✅ Rollback procedure documented
- ✅ Rollback tested
- ✅ Decision criteria clear

**Dependencies**: POST-1

---

## Risk Management

### High-Priority Risks

| Risk | Probability | Impact | Mitigation | Owner |
|------|-------------|--------|------------|-------|
| **Code execution security breach** | Low | Critical | Sandboxing, audits, penetration testing | Security Engineer |
| **Token reduction <95%** | Medium | High | Continuous benchmarking, optimization | Backend Engineer |
| **Python library incompatibility** | Medium | Medium | Hybrid approach (Python subprocess when needed) | Backend Engineer |
| **Team learning curve** | High | Medium | Training, documentation, pair programming | Tech Lead |
| **Timeline delays** | Medium | Medium | Buffer weeks, agile sprints, daily standups | Project Manager |

### Mitigation Actions

1. **Security**: Schedule external security audit after P1-5
2. **Performance**: Daily token usage tracking starting P2-1
3. **Training**: Weekly "MCP Migration 101" sessions
4. **Timeline**: 2-week buffer built into schedule

---

## Success Metrics

### Primary KPIs

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| **Token Usage** | 200,000/workflow | <3,000/workflow | Prometheus counter |
| **Execution Time** | 120s | <15s | Latency histogram |
| **Cost per Workflow** | $0.60 | <$0.01 | API billing |
| **Error Rate** | 5% | <2% | Error logs |
| **Skills Count** | 0 | 50 (3 months) | Skills repository |
| **Cache Hit Rate** | N/A | >60% | Cache metrics |
| **Code Coverage** | 0% | >90% | Vitest report |

### Weekly Checkpoints

**Every Monday 10am**: Review previous week's metrics, adjust plan as needed

**Milestone Reviews**:
- End of Phase 1 (Week 3): Infrastructure ready?
- End of Phase 2 (Week 5): Database server functional?
- End of Phase 4 (Week 9): Processing complete?
- End of Phase 6 (Week 13): Design complete?
- End of Phase 7 (Week 14): Migration complete?

---

## Communication Plan

### Stakeholders

| Stakeholder | Role | Communication Frequency |
|-------------|------|------------------------|
| **Development Team** | Implementation | Daily standup (9am) |
| **QA Team** | Testing | Daily + ad-hoc |
| **DevOps Team** | Infrastructure | Weekly sync |
| **Security Team** | Audits | Bi-weekly reviews |
| **Product Owner** | Decisions | Weekly update |
| **Executive Team** | Oversight | Monthly report |

### Channels

- **Slack #mcp-migration**: Daily updates, blockers, questions
- **Weekly Sync**: Mondays 10am - 1 hour
- **Demo Sessions**: End of each phase (recorded)
- **Retrospectives**: End of each phase
- **Documentation**: `docs/MIGRATION_LOG.md` (daily updates)

---

## Appendix

### A. Tool Inventory

**Total Tools to Migrate**: 34 across 5 servers

| Server | Tools | Priority | Phase |
|--------|-------|----------|-------|
| Database | 11 | 🔴 Critical | Phase 2 |
| Processing | 5 | 🟡 High | Phase 4 |
| Alignment | 5 | 🟡 High | Phase 5 |
| Design | 6 | 🟢 Medium | Phase 6 |
| Validation | 7 | 🟢 Medium | Phase 7 |

### B. Reference Documents

- [MIGRATION_PLAN.md](./MIGRATION_PLAN.md) - Detailed technical plan
- [MCP_2.0_ARCHITECTURE_SUMMARY.md](./MCP_2.0_ARCHITECTURE_SUMMARY.md) - Architecture overview
- [Anthropic Code Execution Guide](https://www.anthropic.com/engineering/code-execution-with-mcp) - Official guide
- [MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk) - SDK documentation

### C. Timeline Visualization

```
Week 0:  [Pre-Migration: Setup & Training]
Week 1-3: [Phase 1: Infrastructure]
           ├── Tool Generator
           ├── MCP Client
           ├── PII Tokenization
           ├── Skills Manager
           └── Code Execution Sandbox

Week 4-5: [Phase 2: Database Server]
           ├── Generate Tools (11)
           ├── Test Integrations
           └── Docker + Tests

Week 6-7: [Phase 3: Skills]
           ├── Salmon Workflow
           ├── Multiplex Design
           └── Documentation

Week 8-9: [Phase 4: Processing Server]
           ├── Generate Tools (5)
           ├── CLI Wrappers
           └── Large Dataset Tests

Week 10-11: [Phase 5: Alignment Server]
            ├── Generate Tools (5)
            ├── Phylogenetic Caching
            └── Docker + Tests

Week 12-13: [Phase 6: Design Server]
            ├── Generate Tools (6)
            ├── Primer3 Integration
            └── Multiplex Workflows

Week 14: [Phase 7: Validation Server]
         ├── Generate Tools (7)
         ├── BLAST + PII
         └── Final Integration

Week 15+: [Post-Migration: Production]
          ├── Deploy
          ├── Monitor
          └── Optimize
```

### D. Contact Information

| Role | Name | Email | Slack |
|------|------|-------|-------|
| **Project Lead** | TBD | TBD | @TBD |
| **Tech Lead** | TBD | TBD | @TBD |
| **Backend Engineer** | TBD | TBD | @TBD |
| **DevOps Engineer** | TBD | TBD | @TBD |
| **QA Engineer** | TBD | TBD | @TBD |
| **Security Engineer** | TBD | TBD | @TBD |

---

**Document Version**: 1.0
**Last Updated**: November 12, 2025
**Next Review**: End of Pre-Migration Phase
**Status**: Ready for Kickoff

---

## Quick Start Checklist

Ready to begin? Complete these first steps:

- [ ] Read this document completely
- [ ] Review MIGRATION_PLAN.md
- [ ] Review MCP_2.0_ARCHITECTURE_SUMMARY.md
- [ ] Assign phase owners
- [ ] Schedule kickoff meeting
- [ ] Create #mcp-migration Slack channel
- [ ] Set up development environment (PM-2)
- [ ] Run first team standup
- [ ] Begin Phase 1!

**Questions?** Ask in #mcp-migration or contact the Project Lead.

**Let's build something amazing! 🚀**
