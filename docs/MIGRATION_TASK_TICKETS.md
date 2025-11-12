# MCP 2.0 Migration: Task Tickets

**Format**: GitHub Issues / Jira / Linear compatible
**Total Tasks**: 70+ across 8 phases
**How to Use**: Copy each ticket block into your project management tool

---

## Pre-Migration Phase (Week 0)

### PM-1: Team Preparation

```markdown
**Title**: [PM-1] Team Preparation and Kickoff

**Type**: Epic
**Priority**: P0 - Critical
**Assignee**: Tech Lead
**Estimated Time**: 2 days
**Sprint**: Week 0

**Description**:
Prepare team for MCP 2.0 migration with training, role assignment, and communication setup.

**Acceptance Criteria**:
- [ ] Kickoff meeting scheduled with all stakeholders
- [ ] All team members have read Anthropic's Code Execution guide
- [ ] Phase owners assigned (1 owner per phase)
- [ ] #mcp-migration Slack channel created
- [ ] Weekly sync meetings scheduled (Mondays 10am)

**Tasks**:
- [ ] Schedule kickoff meeting (2 hours)
- [ ] Share reading materials:
  - https://www.anthropic.com/engineering/code-execution-with-mcp
  - docs/MIGRATION_PLAN.md
  - docs/MCP_2.0_ARCHITECTURE_SUMMARY.md
- [ ] Create team assignment matrix
- [ ] Set up communication channels

**Dependencies**: None

**Definition of Done**:
Team is aligned, trained, and ready to begin implementation.

**Tags**: #pre-migration #setup #team
```

---

### PM-2: Development Environment Setup

```markdown
**Title**: [PM-2] Development Environment Setup

**Type**: Task
**Priority**: P0 - Critical
**Assignee**: DevOps Engineer
**Estimated Time**: 1 day
**Sprint**: Week 0

**Description**:
Set up Node.js 20+ development environment on all developer machines.

**Acceptance Criteria**:
- [ ] Node.js 20.x installed on all dev machines
- [ ] MCP SDK installed globally
- [ ] TypeScript compiler configured (v5.x+)
- [ ] VS Code with recommended extensions
- [ ] Migration Git branch created

**Tasks**:
```bash
# Install Node.js via nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 20
nvm use 20
node --version  # Verify v20.x.x

# Install MCP SDK
npm install -g @modelcontextprotocol/sdk

# Install TypeScript
npm install -g typescript tsx
tsc --version  # Verify 5.x+

# Clone and create branch
cd /home/raycifeng/mdk_mcp
git checkout -b migration/node-code-execution
```

**VS Code Extensions**:
- ESLint
- Prettier
- TypeScript and JavaScript Language Features

**Dependencies**: None

**Definition of Done**:
All developers can compile TypeScript and import MCP SDK without errors.

**Tags**: #pre-migration #setup #environment
```

---

### PM-3: Testing Framework Setup

```markdown
**Title**: [PM-3] Testing Framework Configuration

**Type**: Task
**Priority**: P0 - Critical
**Assignee**: QA Engineer
**Estimated Time**: 1 day
**Sprint**: Week 0

**Description**:
Configure Vitest testing framework with coverage reporting and CI/CD integration.

**Acceptance Criteria**:
- [ ] Vitest installed and configured
- [ ] Test directory structure created
- [ ] Sample test passes
- [ ] Coverage reports generate
- [ ] CI/CD pipeline runs tests automatically

**Implementation**:
```bash
# Install Vitest
npm install -D vitest @vitest/ui @vitest/coverage-v8

# Create test structure
mkdir -p tests/{unit,integration,benchmarks,fixtures}

# Create vitest.config.ts
cat > vitest.config.ts << 'EOF'
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'json'],
      exclude: ['**/node_modules/**', '**/tests/**'],
    },
  },
});
EOF

# Add scripts to package.json
npm pkg set scripts.test="vitest"
npm pkg set scripts.test:ui="vitest --ui"
npm pkg set scripts.coverage="vitest --coverage"

# Run sample test
npm test
```

**Dependencies**: PM-2

**Definition of Done**:
`npm test` runs successfully and generates coverage report.

**Tags**: #pre-migration #testing #ci-cd
```

---

### PM-4: Docker Development Environment

```markdown
**Title**: [PM-4] Docker Development Environment for Migration

**Type**: Task
**Priority**: P1 - High
**Assignee**: DevOps Engineer
**Estimated Time**: 2 days
**Sprint**: Week 0

**Description**:
Set up Docker Compose environment for running Python and Node.js servers in parallel.

**Acceptance Criteria**:
- [ ] docker-compose.migration.yml created
- [ ] Volume mounts configured for workspace persistence
- [ ] Hot-reload working for development
- [ ] Python (old) + Node.js (new) servers run simultaneously
- [ ] Documentation in docs/DOCKER_MIGRATION.md

**Implementation**:
Create `docker-compose.migration.yml`:
```yaml
version: '3.8'

services:
  # Existing Python servers (keep running)
  database-server-python:
    build: ./mcp_servers/database_server
    container_name: ndiag-database-server
    volumes:
      - ./results:/results

  # New Node.js servers
  database-server-node:
    build: ./mcp_servers/database_server_node
    container_name: ndiag-database-server-node
    volumes:
      - ./workspace:/workspace
      - ./results:/results
      - node_modules:/workspace/node_modules
    environment:
      - NODE_ENV=development
    ports:
      - "9000:9000"

volumes:
  node_modules:
```

**Testing**:
```bash
docker-compose -f docker-compose.migration.yml up -d
docker ps  # Should show both Python and Node containers
```

**Dependencies**: PM-2

**Definition of Done**:
Both Python and Node.js servers run simultaneously with hot-reload.

**Tags**: #pre-migration #docker #infrastructure
```

---

## Phase 1: Infrastructure (Week 1-3)

### P1-1: Tool File Generator Implementation

```markdown
**Title**: [P1-1] Tool File Generator for Filesystem-Based Tool Discovery

**Type**: Story
**Priority**: P0 - Critical
**Assignee**: Backend Engineer
**Estimated Time**: 5 days
**Sprint**: Week 1-2

**Description**:
Implement tool file generator that converts Python MCP server definitions to TypeScript filesystem API.

**Context**:
This is the core component that enables progressive tool disclosure. It generates TypeScript files from Python MCP servers, reducing token usage by 99.7%.

**Acceptance Criteria**:
- [ ] ToolFileGenerator class implemented with all methods
- [ ] Generates valid TypeScript from JSON schemas
- [ ] Creates barrel exports (index.ts)
- [ ] Generates README.md documentation
- [ ] Unit tests with ≥90% coverage
- [ ] Successfully generates all 11 Database Server tools

**Implementation**:
Create `mcp_servers/shared/tool-generator.ts`:

```typescript
import { writeFile, mkdir } from "fs/promises";
import { join } from "path";

interface ToolDefinition {
  name: string;
  description: string;
  inputSchema: any;
  outputSchema?: any;
}

export class ToolFileGenerator {
  async generateToolFiles(
    serverName: string,
    tools: ToolDefinition[],
    outputDir: string
  ): Promise<void> {
    // Implementation here
  }

  private generateToolFile(tool: ToolDefinition, serverName: string): string {
    // Generate individual tool TypeScript file
  }

  private generateIndexFile(tools: ToolDefinition[]): string {
    // Generate barrel export index.ts
  }

  private generateReadme(serverName: string, tools: ToolDefinition[]): string {
    // Generate server documentation
  }
}
```

**Testing**:
```typescript
// tests/unit/tool-generator.test.ts
describe('ToolFileGenerator', () => {
  it('should generate valid TypeScript from JSON schema', async () => {
    const generator = new ToolFileGenerator();
    const result = await generator.generateToolFile(mockTool, 'database');

    expect(result).toContain('export async function');
    expect(result).toContain('export interface');
  });

  it('should generate all 11 database tools', async () => {
    await generator.generateToolFiles('database', mockTools, './test-output');
    const files = await readdir('./test-output/servers/database');
    expect(files).toHaveLength(13); // 11 tools + index.ts + README.md
  });
});
```

**Verification**:
```bash
npm run generate-tools -- --server database --output workspace/servers/
ls workspace/servers/database/  # Should show 11 .ts files
tsc --noEmit workspace/servers/database/*.ts  # Should compile
```

**Dependencies**: PM-2, PM-3

**Reference**: MIGRATION_PLAN.md lines 146-299

**Definition of Done**:
Generator produces valid TypeScript files that compile without errors and pass all tests.

**Tags**: #phase-1 #infrastructure #critical-path #tool-generator
```

---

### P1-2: MCP Client with Code Execution

```markdown
**Title**: [P1-2] MCP Client with Code Execution Support

**Type**: Story
**Priority**: P0 - Critical
**Assignee**: Backend Engineer
**Estimated Time**: 5 days
**Sprint**: Week 2

**Description**:
Implement MCP client that connects to servers via stdio and supports code execution patterns.

**Acceptance Criteria**:
- [ ] MCPCodeExecutionClient class implemented
- [ ] Connection management for 5 servers
- [ ] Request/response handling with retries
- [ ] Exponential backoff for transient failures
- [ ] Progressive tool discovery (searchTools)
- [ ] Global helper functions (callMCPTool, setMCPClient)
- [ ] Integration tests with mock servers

**Implementation**:
Create `workspace/lib/mcp-client.ts`:

```typescript
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

interface MCPServerConfig {
  command: string;
  args: string[];
  env?: Record<string, string>;
}

export class MCPCodeExecutionClient {
  private clients: Map<string, Client> = new Map();
  private tokenizer?: PIITokenizer;

  constructor(
    private serverConfigs: Map<string, MCPServerConfig>,
    enableTokenization: boolean = false
  ) {
    if (enableTokenization) {
      this.tokenizer = new PIITokenizer();
    }
  }

  async initialize(): Promise<void> {
    // Connect to all MCP servers
  }

  async callTool<T = any>(
    toolId: string,
    args: any,
    maxRetries: number = 3
  ): Promise<T> {
    // Call tool with retry logic
  }

  async searchTools(
    query: string,
    detailLevel: "name" | "description" | "full" = "description"
  ): Promise<any[]> {
    // Progressive tool discovery
  }
}

// Global helpers
let globalClient: MCPCodeExecutionClient | null = null;

export function setMCPClient(client: MCPCodeExecutionClient): void {
  globalClient = client;
}

export async function callMCPTool<T = any>(
  toolId: string,
  args: any
): Promise<T> {
  if (!globalClient) {
    throw new Error("MCP client not initialized");
  }
  return globalClient.callTool<T>(toolId, args);
}
```

**Testing**:
```typescript
// tests/integration/mcp-client.test.ts
describe('MCPCodeExecutionClient', () => {
  it('should connect to all 5 servers', async () => {
    const client = new MCPCodeExecutionClient(mockConfigs);
    await client.initialize();
    expect(client.clients.size).toBe(5);
  });

  it('should retry on transient failures', async () => {
    const mockTool = jest.fn()
      .mockRejectedValueOnce(new Error('Timeout'))
      .mockResolvedValueOnce({ result: 'success' });

    const result = await client.callTool('database__get_sequences', {});
    expect(mockTool).toHaveBeenCalledTimes(2);
    expect(result).toEqual({ result: 'success' });
  });

  it('should search tools progressively', async () => {
    const results = await client.searchTools('blast');
    expect(results.length).toBeGreaterThan(0);
    expect(results[0]).toHaveProperty('name');
  });
});
```

**Dependencies**: P1-1, PM-3

**Reference**: MIGRATION_PLAN.md lines 303-526

**Definition of Done**:
Client connects to MCP servers, handles retries, and integration tests pass.

**Tags**: #phase-1 #infrastructure #critical-path #mcp-client
```

---

### P1-3: PII Tokenization System

```markdown
**Title**: [P1-3] PII Tokenization for Privacy-Preserving Operations

**Type**: Story
**Priority**: P1 - High
**Assignee**: Security Engineer
**Estimated Time**: 3 days
**Sprint**: Week 2

**Description**:
Implement bidirectional PII tokenization to prevent sensitive data from reaching AI model.

**Acceptance Criteria**:
- [ ] PIITokenizer class implemented
- [ ] Regex patterns for email, phone, SSN, credit card
- [ ] Bidirectional tokenization (tokenize + detokenize)
- [ ] Nested object/array support
- [ ] Audit logging for tokenization events
- [ ] 100% test coverage
- [ ] Security documentation in docs/SECURITY.md

**Implementation**:
```typescript
class PIITokenizer {
  private tokenMap: Map<string, string> = new Map();
  private reverseMap: Map<string, string> = new Map();
  private tokenCounter: number = 0;

  private piiPatterns = {
    email: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g,
    phone: /\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g,
    ssn: /\b\d{3}-\d{2}-\d{4}\b/g,
    creditCard: /\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/g,
  };

  tokenize(data: any): any {
    // Replace PII with tokens
  }

  detokenize(data: any): any {
    // Restore original values
  }
}
```

**Testing**:
```typescript
describe('PIITokenizer', () => {
  it('should tokenize email addresses', () => {
    const tokenizer = new PIITokenizer();
    const input = "Contact: john.doe@example.com";
    const tokenized = tokenizer.tokenize(input);

    expect(tokenized).not.toContain("john.doe@example.com");
    expect(tokenized).toMatch(/\[EMAIL_\d+\]/);
  });

  it('should detokenize back to original', () => {
    const tokenizer = new PIITokenizer();
    const input = { user: "john.doe@example.com", phone: "555-123-4567" };

    const tokenized = tokenizer.tokenize(input);
    const detokenized = tokenizer.detokenize(tokenized);

    expect(detokenized).toEqual(input);
  });

  it('should prevent PII from reaching model', async () => {
    // Integration test with actual model call
    const logSpy = jest.spyOn(console, 'log');

    await runWorkflowWithPII({ email: "sensitive@example.com" });

    const logs = logSpy.mock.calls.join('\n');
    expect(logs).not.toContain("sensitive@example.com");
  });
});
```

**Security Checklist**:
- [ ] All PII patterns tested
- [ ] Nested data structures handled
- [ ] Audit logs cannot be disabled
- [ ] No PII in error messages
- [ ] Documentation reviewed by security team

**Dependencies**: P1-2

**Reference**: MIGRATION_PLAN.md lines 427-500

**Definition of Done**:
PII tokenization works, all tests pass, security audit approved.

**Tags**: #phase-1 #security #pii #tokenization
```

---

### P1-4: Skills Manager Implementation

```markdown
**Title**: [P1-4] Skills Manager for Reusable Agent Workflows

**Type**: Story
**Priority**: P1 - High
**Assignee**: Backend Engineer
**Estimated Time**: 4 days
**Sprint**: Week 2-3

**Description**:
Implement skills system for saving and reusing successful agent workflows.

**Acceptance Criteria**:
- [ ] SkillsManager class implemented
- [ ] Skills persist to filesystem (workspace/skills/)
- [ ] SKILLS.md auto-generated and maintained
- [ ] Search by name, description, tags
- [ ] Version tracking with Git
- [ ] CRUD tests with ≥90% coverage

**Implementation**:
```typescript
// workspace/lib/skills-manager.ts
import { readdir, readFile, writeFile, mkdir } from "fs/promises";
import { join } from "path";

export class SkillsManager {
  constructor(private skillsDir: string = "./skills") {}

  async saveSkill(
    name: string,
    code: string,
    description: string,
    tags: string[] = []
  ): Promise<void> {
    await mkdir(this.skillsDir, { recursive: true });
    const skillFile = join(this.skillsDir, `${name}.ts`);
    await writeFile(skillFile, code);
    await this.updateSkillsIndex(name, description, tags);
  }

  async loadSkill(name: string): Promise<string> {
    const skillFile = join(this.skillsDir, `${name}.ts`);
    return readFile(skillFile, "utf-8");
  }

  async searchSkills(query: string): Promise<Array<{
    name: string;
    description: string;
    tags: string[];
  }>> {
    // Search by name, description, or tags
  }
}
```

**Testing**:
```typescript
describe('SkillsManager', () => {
  it('should save and load skills', async () => {
    const skills = new SkillsManager('./test-skills');
    const code = 'export async function testSkill() { return "test"; }';

    await skills.saveSkill('test-skill', code, 'Test skill', ['test']);
    const loaded = await skills.loadSkill('test-skill');

    expect(loaded).toBe(code);
  });

  it('should update SKILLS.md index', async () => {
    await skills.saveSkill('test-skill', code, desc, ['test']);
    const index = await readFile('./test-skills/SKILLS.md', 'utf-8');

    expect(index).toContain('## test-skill');
    expect(index).toContain(desc);
  });

  it('should search by tags', async () => {
    const results = await skills.searchSkills('primer');
    expect(results.length).toBeGreaterThan(0);
  });
});
```

**Dependencies**: P1-2

**Reference**: MIGRATION_PLAN.md lines 532-661

**Definition of Done**:
Skills save, load, search correctly. Tests pass with ≥90% coverage.

**Tags**: #phase-1 #skills #learning
```

---

### P1-5: Code Execution Sandbox

```markdown
**Title**: [P1-5] Code Execution Sandbox with Security Controls

**Type**: Story
**Priority**: P0 - Critical (Security)
**Assignee**: DevOps Engineer
**Estimated Time**: 5 days
**Sprint**: Week 3

**Description**:
Create secure sandboxed environment for executing agent-generated code.

**Security Requirements**:
- [ ] Non-root user execution
- [ ] Read-only filesystem (except /workspace/temp)
- [ ] Network isolation (only MCP servers accessible)
- [ ] Resource limits: 4GB RAM, 2 CPU cores, 300s timeout
- [ ] AST-based code validation
- [ ] Malicious code rejection
- [ ] External security audit passed

**Implementation**:
Create `code-execution/Dockerfile`:
```dockerfile
FROM node:20-slim

WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git curl python3 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 sandbox && \
    chown -R sandbox:sandbox /workspace

USER sandbox

# Copy workspace template
COPY --chown=sandbox:sandbox workspace-template/ /workspace/
RUN npm ci --production

# Security hardening
ENV NODE_OPTIONS="--max-old-space-size=4096"

EXPOSE 9000
CMD ["node", "executor.js"]
```

Create `code-execution/executor.ts`:
```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { exec } from "child_process";

class CodeExecutionServer {
  async executeCode(
    code: string,
    timeout: number = 60000
  ): Promise<any> {
    // Validate code (no eval, exec, etc.)
    this.validateCode(code);

    // Execute in sandbox
    const result = await this.runSandboxed(code, timeout);

    return result;
  }

  private validateCode(code: string): void {
    const dangerousPatterns = [
      /eval\(/,
      /Function\(/,
      /require\(['"]child_process['"]\)/,
      /require\(['"]fs['"]\)\.unlink/,
    ];

    for (const pattern of dangerousPatterns) {
      if (pattern.test(code)) {
        throw new Error(`Dangerous code pattern detected: ${pattern}`);
      }
    }
  }
}
```

**Security Testing**:
```typescript
describe('Code Execution Security', () => {
  it('should block eval usage', async () => {
    const maliciousCode = 'eval("process.exit(1)")';
    await expect(executor.executeCode(maliciousCode)).rejects.toThrow();
  });

  it('should block filesystem deletion', async () => {
    const maliciousCode = 'require("fs").unlinkSync("/important-file")';
    await expect(executor.executeCode(maliciousCode)).rejects.toThrow();
  });

  it('should enforce timeout', async () => {
    const infiniteLoop = 'while(true) {}';
    await expect(
      executor.executeCode(infiniteLoop, 1000)
    ).rejects.toThrow(/timeout/);
  });

  it('should enforce memory limits', async () => {
    const memoryHog = 'const arr = []; while(true) arr.push(new Array(1e6))';
    // Should be killed by container memory limit
  });
});
```

**Security Audit Checklist**:
- [ ] Penetration testing completed
- [ ] No privilege escalation possible
- [ ] Network isolation verified
- [ ] Resource limits enforced
- [ ] Code validation comprehensive
- [ ] External audit report approved

**Dependencies**: P1-2, PM-4

**Reference**: MIGRATION_PLAN.md lines 1876-2046

**Definition of Done**:
Sandbox blocks all malicious code attempts. External security audit passed.

**Tags**: #phase-1 #security #critical #sandbox
```

---

### P1-6: Progressive Tool Disclosure Benchmark

```markdown
**Title**: [P1-6] Progressive Tool Disclosure Token Usage Benchmark

**Type**: Task
**Priority**: P1 - High
**Assignee**: QA Engineer
**Estimated Time**: 2 days
**Sprint**: Week 3

**Description**:
Measure and validate token reduction achieved through progressive tool disclosure.

**Acceptance Criteria**:
- [ ] Baseline measured (traditional approach)
- [ ] Code execution approach measured
- [ ] Reduction percentage calculated (target: ≥95%)
- [ ] Benchmark report generated
- [ ] Findings presented to team

**Implementation**:
```typescript
// tests/benchmarks/token-usage.bench.ts
import { describe, bench } from "vitest";

describe('Token Usage Benchmarks', () => {
  bench('Traditional: Load all 34 tools', async () => {
    const tools = await loadAllToolDefinitions();
    const tokens = countTokens(JSON.stringify(tools));
    console.log(`Traditional: ${tokens} tokens`);
    // Expected: ~150,000 tokens
  });

  bench('Code Execution: Progressive disclosure', async () => {
    const tools = await import('./servers/database');
    const tokens = countTokens(JSON.stringify(tools));
    console.log(`Code Execution: ${tokens} tokens`);
    // Expected: ~400 tokens
  });
});
```

**Report Template**:
```markdown
## Token Usage Benchmark Report

### Results
- **Traditional Approach**: 150,000 tokens (all tools loaded upfront)
- **Code Execution**: 2,500 tokens (loaded on demand)
- **Reduction**: 98.3% ✅

### Breakdown by Server
| Server | Traditional | Code Exec | Reduction |
|--------|-------------|-----------|-----------|
| Database | 40,000 | 400 | 99.0% |
| Processing | 25,000 | 300 | 98.8% |
| Alignment | 30,000 | 500 | 98.3% |
| Design | 35,000 | 600 | 98.3% |
| Validation | 20,000 | 700 | 96.5% |

### Recommendation
✅ Proceed with migration. Token reduction target (≥95%) achieved.
```

**Dependencies**: P1-1, P1-2, P1-5

**Reference**: MIGRATION_PLAN.md lines 1682-1708

**Definition of Done**:
Benchmark confirms ≥95% token reduction. Report approved by team.

**Tags**: #phase-1 #benchmark #validation
```

---

## Phase 2: Database Server (Week 4-5)

### P2-1: Generate Database Server Tool Files

```markdown
**Title**: [P2-1] Generate Database Server TypeScript Tool Files

**Type**: Task
**Priority**: P0 - Critical
**Assignee**: Backend Engineer
**Estimated Time**: 3 days
**Sprint**: Week 4

**Description**:
Run tool generator on Python Database Server to create TypeScript filesystem API.

**Acceptance Criteria**:
- [ ] All 11 tools generated successfully
- [ ] TypeScript compilation passes
- [ ] Type definitions match Python schemas
- [ ] Example usage file created
- [ ] Documentation reviewed

**Commands**:
```bash
# Run generator
npm run generate-tools -- \
  --server database \
  --input mcp_servers/database_server/database_mcp_server.py \
  --output workspace/servers/

# Verify output
ls workspace/servers/database/
# Expected files:
# - getSequences.ts
# - ggetRef.ts
# - ggetSearch.ts
# - ggetInfo.ts
# - ggetSeq.ts
# - getNeighbors.ts
# - getTaxonomy.ts
# - searchSRAStudies.ts
# - getSRARuninfo.ts
# - searchSRACloud.ts
# - extractSequenceColumns.ts
# - index.ts
# - README.md

# Compile
tsc --noEmit workspace/servers/database/*.ts
```

**Verification Checklist**:
```typescript
// examples/database-usage.ts
import * as database from './servers/database';

// Test each tool
const seqs = await database.getSequences({
  taxon: "Salmo salar",
  region: "COI",
  max_results: 10
});
expect(typeof seqs).toBe('string');
expect(seqs).toContain('>');

const ref = await database.ggetRef({ species: 'homo_sapiens' });
expect(ref).toHaveProperty('assembly');
```

**Dependencies**: P1-1, P1-6

**Reference**: MIGRATION_PLAN.md lines 666-740

**Definition of Done**:
All 11 tools generated, compile without errors, example runs successfully.

**Tags**: #phase-2 #database-server #code-generation
```

---

### P2-2: Database Server Integration Testing

```markdown
**Title**: [P2-2] Database Server Integration Testing (gget, NCBI, SRA)

**Type**: Task
**Priority**: P0 - Critical
**Assignee**: Backend Engineer + QA Engineer
**Estimated Time**: 4 days
**Sprint**: Week 4-5

**Description**:
Test all Database Server tools with real API calls to gget, NCBI, BOLD, and SRA.

**Test Coverage**:
- [ ] gget tools (ggetRef, ggetSearch, ggetInfo, ggetSeq)
- [ ] NCBI tools (getSequences, getTaxonomy, getNeighbors)
- [ ] SRA tools (searchSRAStudies, getSRARuninfo, searchSRACloud)
- [ ] Error handling (invalid inputs, timeouts, rate limits)
- [ ] Rate limiting verification (NCBI: 3 req/sec)

**Implementation**:
```typescript
// tests/integration/database-server.test.ts
describe('Database Server Integration', () => {
  describe('gget tools', () => {
    it('should fetch reference genome', async () => {
      const ref = await database.ggetRef({ species: 'homo_sapiens' });
      expect(ref).toHaveProperty('assembly');
      expect(ref).toHaveProperty('ensembl_release');
    });

    it('should search genes', async () => {
      const results = await database.ggetSearch({
        query: 'BRCA1',
        species: 'homo_sapiens'
      });
      expect(results.length).toBeGreaterThan(0);
    });
  });

  describe('NCBI tools', () => {
    it('should fetch sequences', async () => {
      const seqs = await database.getSequences({
        taxon: "Salmo salar",
        region: "COI",
        source: "ncbi",
        max_results: 10
      });
      expect(seqs).toContain('>');
      expect(seqs.split('>').length - 1).toBeLessThanOrEqual(10);
    });

    it('should respect rate limits', async () => {
      const start = Date.now();
      await Promise.all([
        database.getTaxonomy({ taxon: 'Salmo salar' }),
        database.getTaxonomy({ taxon: 'Gadus morhua' }),
        database.getTaxonomy({ taxon: 'Thunnus albacares' }),
      ]);
      const elapsed = Date.now() - start;
      expect(elapsed).toBeGreaterThan(600); // ~3 req/sec
    });

    it('should retry on transient failures', async () => {
      // Mock transient failure
      const mockFetch = jest.fn()
        .mockRejectedValueOnce(new Error('Timeout'))
        .mockResolvedValueOnce({ data: 'success' });

      const result = await database.getSequences({ /* ... */ });
      expect(mockFetch).toHaveBeenCalledTimes(2);
    });
  });

  describe('SRA tools', () => {
    it('should search SRA studies', async () => {
      const studies = await database.searchSRAStudies({
        query: "Salmo salar transcriptome",
        max_results: 10
      });
      expect(studies.length).toBeGreaterThan(0);
    });
  });
});
```

**Dependencies**: P2-1

**Definition of Done**:
All integration tests pass with real API calls.

**Tags**: #phase-2 #database-server #integration-testing
```

---

## (Continue with remaining phases...)

---

## How to Use These Tickets

### For GitHub Issues:

1. Copy ticket content
2. Create new issue
3. Paste content
4. Add labels from tags
5. Assign to team member
6. Add to project board

### For Jira:

1. Create Epic for each phase
2. Create Stories under Epic
3. Copy Description and Acceptance Criteria
4. Set Priority and Assignee
5. Link dependencies

### For Linear:

1. Create Project: "MCP 2.0 Migration"
2. Create Cycles for each week
3. Copy issue content
4. Set priority and estimate
5. Link related issues

---

## Quick Import Script (GitHub)

```bash
#!/bin/bash
# import-tickets.sh - Import all tickets to GitHub Issues

REPO="your-org/mdk_mcp"

# Pre-Migration
gh issue create --repo $REPO --title "[PM-1] Team Preparation" \
  --body-file tickets/pm-1.md --label "pre-migration,setup,team"

gh issue create --repo $REPO --title "[PM-2] Development Environment Setup" \
  --body-file tickets/pm-2.md --label "pre-migration,setup,environment"

# ... repeat for all tickets
```

---

**Total Tickets**: 70+
**Estimated Story Points**: 350+
**Timeline**: 14 weeks
**Team Size**: 7 people

**Next**: Import into your project management tool and begin sprint planning!
```

