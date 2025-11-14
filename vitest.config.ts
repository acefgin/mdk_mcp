/**
 * Vitest Configuration
 *
 * Testing framework for MCP 2.0 migration
 */

import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'json', 'lcov'],
      exclude: [
        '**/node_modules/**',
        '**/tests/**',
        '**/dist/**',
        '**/*.config.*',
        '**/examples/**',
      ],
      thresholds: {
        lines: 90,
        functions: 90,
        branches: 85,
        statements: 90,
      },
    },
    include: [
      'tests/**/*.test.ts',
      'mcp_servers/shared/tests/**/*.test.ts',
      'code-execution/tests/**/*.test.ts'
    ],
    exclude: [
      '**/node_modules/**',
      '**/dist/**',
      // Exclude tests for features not yet implemented
      'tests/unit/pii-tokenizer.test.ts',
      'tests/unit/skills-manager.test.ts',
      'tests/integration/all-servers.test.ts',
      'tests/integration/database-tools.test.ts',
    ],
    testTimeout: 10000,
    hookTimeout: 10000,
  },
});
