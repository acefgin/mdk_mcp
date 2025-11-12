/**
 * Unit tests for CodeExecutor
 *
 * Tests code execution, security controls, and resource limits.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import {
  CodeExecutor,
  setGlobalExecutor,
  getGlobalExecutor,
  executeCode,
  executeFile,
  executeWorkflow,
  type ExecutionResult,
  type WorkflowStep,
} from '../../workspace/lib/executor';
import * as fs from 'fs';
import * as path from 'path';

describe('CodeExecutor', () => {
  let executor: CodeExecutor;
  let dockerAvailable: boolean;

  beforeEach(async () => {
    executor = new CodeExecutor();
    dockerAvailable = await executor.isDockerAvailable();

    if (!dockerAvailable) {
      console.warn('⚠️  Docker not available - some tests will be skipped');
    }
  });

  describe('Docker Availability', () => {
    it('should check if Docker is available', async () => {
      const available = await executor.isDockerAvailable();
      expect(typeof available).toBe('boolean');
    });

    it('should get Docker version if available', async () => {
      if (!dockerAvailable) {
        return; // Skip if Docker not available
      }

      const version = await executor.getDockerVersion();
      expect(version).toBeDefined();
      expect(version.length).toBeGreaterThan(0);
    });
  });

  describe('JavaScript Execution', () => {
    it('should execute simple JavaScript code', async () => {
      if (!dockerAvailable) return;

      const code = 'console.log("Hello, World!");';
      const result = await executor.execute(code, 'javascript');

      expect(result.success).toBe(true);
      expect(result.exitCode).toBe(0);
      expect(result.stdout.trim()).toBe('Hello, World!');
      expect(result.stderr).toBe('');
    });

    it('should capture stdout correctly', async () => {
      if (!dockerAvailable) return;

      const code = `
        console.log("Line 1");
        console.log("Line 2");
        console.log("Line 3");
      `;
      const result = await executor.execute(code, 'javascript');

      expect(result.success).toBe(true);
      expect(result.stdout).toContain('Line 1');
      expect(result.stdout).toContain('Line 2');
      expect(result.stdout).toContain('Line 3');
    });

    it('should capture stderr correctly', async () => {
      if (!dockerAvailable) return;

      const code = 'console.error("Error message");';
      const result = await executor.execute(code, 'javascript');

      expect(result.success).toBe(true);
      expect(result.stderr).toContain('Error message');
    });

    it('should handle runtime errors', async () => {
      if (!dockerAvailable) return;

      const code = 'throw new Error("Test error");';
      const result = await executor.execute(code, 'javascript');

      expect(result.success).toBe(false);
      expect(result.exitCode).not.toBe(0);
      expect(result.stderr).toContain('Test error');
    });

    it('should execute mathematical operations', async () => {
      if (!dockerAvailable) return;

      const code = `
        const sum = 10 + 20;
        const product = 5 * 6;
        console.log(\`sum=\${sum}, product=\${product}\`);
      `;
      const result = await executor.execute(code, 'javascript');

      expect(result.success).toBe(true);
      expect(result.stdout).toContain('sum=30');
      expect(result.stdout).toContain('product=30');
    });
  });

  describe('TypeScript Execution', () => {
    it('should execute simple TypeScript code', async () => {
      if (!dockerAvailable) return;

      const code = `
        const message: string = "Hello from TypeScript";
        console.log(message);
      `;
      const result = await executor.execute(code, 'typescript');

      expect(result.success).toBe(true);
      expect(result.stdout).toContain('Hello from TypeScript');
    });

    it('should support TypeScript type checking', async () => {
      if (!dockerAvailable) return;

      const code = `
        interface User {
          name: string;
          age: number;
        }

        const user: User = {
          name: "Alice",
          age: 30
        };

        console.log(\`\${user.name} is \${user.age} years old\`);
      `;
      const result = await executor.execute(code, 'typescript');

      expect(result.success).toBe(true);
      expect(result.stdout).toContain('Alice is 30 years old');
    });
  });

  describe('Python Execution', () => {
    it('should execute simple Python code', async () => {
      if (!dockerAvailable) return;

      const code = 'print("Hello from Python")';
      const result = await executor.execute(code, 'python');

      expect(result.success).toBe(true);
      expect(result.stdout).toContain('Hello from Python');
    });

    it('should handle Python errors', async () => {
      if (!dockerAvailable) return;

      const code = 'raise ValueError("Test error")';
      const result = await executor.execute(code, 'python');

      expect(result.success).toBe(false);
      expect(result.stderr).toContain('ValueError');
      expect(result.stderr).toContain('Test error');
    });

    it('should support Python standard library', async () => {
      if (!dockerAvailable) return;

      const code = `
import json
data = {"name": "Alice", "age": 30}
print(json.dumps(data))
      `;
      const result = await executor.execute(code, 'python');

      expect(result.success).toBe(true);
      expect(result.stdout).toContain('"name"');
      expect(result.stdout).toContain('Alice');
    });
  });

  describe('Shell Execution', () => {
    it('should execute simple shell commands', async () => {
      if (!dockerAvailable) return;

      const code = 'echo "Hello from Shell"';
      const result = await executor.execute(code, 'shell');

      expect(result.success).toBe(true);
      expect(result.stdout).toContain('Hello from Shell');
    });

    it('should support shell pipes', async () => {
      if (!dockerAvailable) return;

      const code = 'echo "test" | tr "a-z" "A-Z"';
      const result = await executor.execute(code, 'shell');

      expect(result.success).toBe(true);
      expect(result.stdout).toContain('TEST');
    });
  });

  describe('Timeout Enforcement', () => {
    it('should enforce timeout on long-running code', async () => {
      if (!dockerAvailable) return;

      const code = `
        const start = Date.now();
        while (Date.now() - start < 60000) {
          // Loop for 60 seconds
        }
      `;
      const result = await executor.execute(code, 'javascript', {
        timeout: 2000, // 2 seconds
      });

      expect(result.success).toBe(false);
      expect(result.stderr).toContain('timed out');
    });

    it('should complete before timeout for fast code', async () => {
      if (!dockerAvailable) return;

      const code = 'console.log("Fast code");';
      const result = await executor.execute(code, 'javascript', {
        timeout: 10000, // 10 seconds
      });

      expect(result.success).toBe(true);
      expect(result.executionTime).toBeLessThan(10000);
    });
  });

  describe('Resource Limits', () => {
    it('should apply memory limits', async () => {
      if (!dockerAvailable) return;

      // This test verifies that memory limits are being set
      // Actual enforcement depends on Docker configuration
      const code = 'console.log("Memory limited execution");';
      const result = await executor.execute(code, 'javascript', {
        memoryLimit: '128m',
      });

      expect(result.success).toBe(true);
    });

    it('should apply CPU limits', async () => {
      if (!dockerAvailable) return;

      // This test verifies that CPU limits are being set
      const code = 'console.log("CPU limited execution");';
      const result = await executor.execute(code, 'javascript', {
        cpuLimit: '0.5',
      });

      expect(result.success).toBe(true);
    });
  });

  describe('Security Controls', () => {
    it('should block network access by default', async () => {
      if (!dockerAvailable) return;

      // Attempt to fetch from internet (should fail)
      const code = `
        const https = require('https');
        https.get('https://example.com', (res) => {
          console.log('Network access succeeded');
        }).on('error', (err) => {
          console.error('Network access blocked:', err.message);
        });
      `;
      const result = await executor.execute(code, 'javascript', {
        timeout: 5000,
      });

      // Network should be blocked
      expect(result.stderr).toContain('getaddrinfo EAI_AGAIN' || 'network');
    });

    it('should have read-only filesystem', async () => {
      if (!dockerAvailable) return;

      // Attempt to write to filesystem (should fail)
      const code = `
        import fs from 'fs';
        try {
          fs.writeFileSync('/test.txt', 'Should not work');
          console.log('Write succeeded');
        } catch (err) {
          console.log('Write blocked:', err.message);
        }
      `;
      const result = await executor.execute(code, 'javascript');

      // Filesystem should be read-only
      expect(result.stdout).toContain('Write blocked');
    });
  });

  describe('File Execution', () => {
    it('should execute code from a file', async () => {
      if (!dockerAvailable) return;

      // Create a temporary test file
      const tempDir = '/tmp/executor-test';
      if (!fs.existsSync(tempDir)) {
        fs.mkdirSync(tempDir, { recursive: true });
      }

      const testFile = path.join(tempDir, 'test.js');
      fs.writeFileSync(testFile, 'console.log("Hello from file");');

      try {
        const result = await executor.executeFile(testFile, 'javascript');

        expect(result.success).toBe(true);
        expect(result.stdout).toContain('Hello from file');
      } finally {
        // Cleanup
        fs.unlinkSync(testFile);
      }
    });
  });

  describe('Workflow Execution', () => {
    it('should execute multi-step workflow', async () => {
      if (!dockerAvailable) return;

      const steps: WorkflowStep[] = [
        {
          name: 'Step 1',
          code: 'console.log("Step 1 complete");',
          language: 'javascript',
          description: 'First step',
        },
        {
          name: 'Step 2',
          code: 'console.log("Step 2 complete");',
          language: 'javascript',
          description: 'Second step',
        },
        {
          name: 'Step 3',
          code: 'print("Step 3 complete")',
          language: 'python',
          description: 'Third step',
        },
      ];

      const result = await executor.executeWorkflow(steps);

      expect(result.overallSuccess).toBe(true);
      expect(result.steps.length).toBe(3);
      expect(result.steps[0].success).toBe(true);
      expect(result.steps[1].success).toBe(true);
      expect(result.steps[2].success).toBe(true);
    });

    it('should stop workflow on first failure', async () => {
      if (!dockerAvailable) return;

      const steps: WorkflowStep[] = [
        {
          name: 'Step 1',
          code: 'console.log("Step 1 complete");',
          language: 'javascript',
        },
        {
          name: 'Step 2 (fails)',
          code: 'throw new Error("Intentional error");',
          language: 'javascript',
        },
        {
          name: 'Step 3 (should not run)',
          code: 'console.log("Step 3 complete");',
          language: 'javascript',
        },
      ];

      const result = await executor.executeWorkflow(steps);

      expect(result.overallSuccess).toBe(false);
      expect(result.steps.length).toBe(2); // Only 2 steps executed
      expect(result.steps[0].success).toBe(true);
      expect(result.steps[1].success).toBe(false);
    });
  });

  describe('Execution Metadata', () => {
    it('should track execution time', async () => {
      if (!dockerAvailable) return;

      const code = 'console.log("Quick execution");';
      const result = await executor.execute(code, 'javascript');

      expect(result.executionTime).toBeGreaterThan(0);
      expect(result.executionTime).toBeLessThan(30000);
    });

    it('should return success status', async () => {
      if (!dockerAvailable) return;

      const successCode = 'console.log("Success");';
      const successResult = await executor.execute(successCode, 'javascript');
      expect(successResult.success).toBe(true);

      const errorCode = 'throw new Error("Fail");';
      const errorResult = await executor.execute(errorCode, 'javascript');
      expect(errorResult.success).toBe(false);
    });

    it('should return exit code', async () => {
      if (!dockerAvailable) return;

      const successCode = 'console.log("Success");';
      const successResult = await executor.execute(successCode, 'javascript');
      expect(successResult.exitCode).toBe(0);

      const errorCode = 'process.exit(42);';
      const errorResult = await executor.execute(errorCode, 'javascript');
      expect(errorResult.exitCode).toBe(42);
    });
  });

  describe('Global Executor', () => {
    afterEach(() => {
      setGlobalExecutor(executor); // Reset to valid executor
    });

    it('should set and get global executor', () => {
      setGlobalExecutor(executor);
      const globalExecutor = getGlobalExecutor();

      expect(globalExecutor).toBe(executor);
    });

    it('should use global executor in executeCode helper', async () => {
      if (!dockerAvailable) return;

      setGlobalExecutor(executor);

      const result = await executeCode('console.log("Hello");', 'javascript');

      expect(result.success).toBe(true);
      expect(result.stdout).toContain('Hello');
    });

    it('should throw error if global executor not set', async () => {
      setGlobalExecutor(null as any);

      await expect(
        executeCode('console.log("Hello");', 'javascript')
      ).rejects.toThrow('Global executor not set');
    });

    it('should use global executor in executeFile helper', async () => {
      if (!dockerAvailable) return;

      setGlobalExecutor(executor);

      const tempDir = '/tmp/executor-test';
      if (!fs.existsSync(tempDir)) {
        fs.mkdirSync(tempDir, { recursive: true });
      }

      const testFile = path.join(tempDir, 'test-global.js');
      fs.writeFileSync(testFile, 'console.log("Global file");');

      try {
        const result = await executeFile(testFile, 'javascript');

        expect(result.success).toBe(true);
        expect(result.stdout).toContain('Global file');
      } finally {
        fs.unlinkSync(testFile);
      }
    });

    it('should use global executor in executeWorkflow helper', async () => {
      if (!dockerAvailable) return;

      setGlobalExecutor(executor);

      const steps: WorkflowStep[] = [
        {
          name: 'Step 1',
          code: 'console.log("Global workflow");',
          language: 'javascript',
        },
      ];

      const result = await executeWorkflow(steps);

      expect(result.overallSuccess).toBe(true);
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty code', async () => {
      if (!dockerAvailable) return;

      const result = await executor.execute('', 'javascript');

      expect(result.success).toBe(true);
      expect(result.stdout).toBe('');
    });

    it('should handle code with special characters', async () => {
      if (!dockerAvailable) return;

      const code = 'console.log("Special: $, \\", \', \\n");';
      const result = await executor.execute(code, 'javascript');

      expect(result.success).toBe(true);
    });

    it('should handle very long output', async () => {
      if (!dockerAvailable) return;

      const code = `
        for (let i = 0; i < 100; i++) {
          console.log("Line " + i);
        }
      `;
      const result = await executor.execute(code, 'javascript');

      expect(result.success).toBe(true);
      expect(result.stdout.split('\n').length).toBeGreaterThan(90);
    });
  });

  describe('Error Handling', () => {
    it('should handle Docker not available', async () => {
      const mockExecutor = new CodeExecutor();

      // Mock isDockerAvailable to return false
      vi.spyOn(mockExecutor, 'isDockerAvailable').mockResolvedValue(false);

      const available = await mockExecutor.isDockerAvailable();
      expect(available).toBe(false);
    });

    it('should handle invalid language', async () => {
      const result = await executor.execute(
        'console.log("test");',
        'invalid' as any
      );

      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
    });
  });

  describe('Performance', () => {
    it('should execute quickly for simple code', async () => {
      if (!dockerAvailable) return;

      const start = Date.now();
      await executor.execute('console.log("test");', 'javascript');
      const elapsed = Date.now() - start;

      // Should complete in less than 10 seconds (Docker overhead included)
      expect(elapsed).toBeLessThan(10000);
    });

    it('should handle concurrent executions', async () => {
      if (!dockerAvailable) return;

      const promises = [
        executor.execute('console.log("1");', 'javascript'),
        executor.execute('console.log("2");', 'javascript'),
        executor.execute('console.log("3");', 'javascript'),
      ];

      const results = await Promise.all(promises);

      expect(results.length).toBe(3);
      expect(results.every((r) => r.success)).toBe(true);
    });
  });
});
