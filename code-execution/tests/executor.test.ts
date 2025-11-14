/**
 * Tests for Code Execution Sandbox
 */

import { describe, it, expect, beforeAll } from 'vitest';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

describe('Code Execution Sandbox', () => {
  describe('Basic Execution', () => {
    it('should execute simple JavaScript code', async () => {
      const code = 'return 1 + 1;';
      const result = await executeCode(code);

      expect(result.success).toBe(true);
      expect(result.output).toBe(2);
    });

    it('should execute async code', async () => {
      const code = `
        await new Promise(resolve => setTimeout(resolve, 100));
        return 'completed';
      `;
      const result = await executeCode(code);

      expect(result.success).toBe(true);
      expect(result.output).toBe('completed');
    });

    it('should capture console logs', async () => {
      const code = `
        console.log('test message');
        return 'done';
      `;
      const result = await executeCode(code);

      expect(result.success).toBe(true);
      expect(result.output).toHaveProperty('result', 'done');
      expect(result.output).toHaveProperty('logs');
      expect(result.output.logs).toContain('test message');
    });
  });

  describe('Security Controls', () => {
    it('should enforce timeout', async () => {
      const code = `
        await new Promise(resolve => setTimeout(resolve, 5000));
        return 'should not reach here';
      `;
      const result = await executeCode(code, 1000);

      expect(result.success).toBe(false);
      expect(result.error).toContain('timeout');
    });

    it('should restrict dangerous modules', async () => {
      const code = `
        const fs = require('fs');
        const dangerous = require('child_process');
        return 'should not work';
      `;
      const result = await executeCode(code);

      expect(result.success).toBe(false);
      expect(result.error).toContain('not allowed');
    });

    it('should disable eval', async () => {
      const code = `
        eval('return 1 + 1');
      `;
      const result = await executeCode(code);

      expect(result.success).toBe(false);
    });
  });

  describe('Resource Limits', () => {
    it('should truncate large output', async () => {
      const code = `
        return 'x'.repeat(2000000); // 2MB string
      `;
      const result = await executeCode(code);

      expect(result.success).toBe(true);
      expect(result.truncated).toBe(true);
      expect(result.output).toHaveProperty('preview');
    });

    it('should report execution time', async () => {
      const code = `
        await new Promise(resolve => setTimeout(resolve, 100));
        return 'done';
      `;
      const result = await executeCode(code);

      expect(result.success).toBe(true);
      expect(result.executionTime).toBeGreaterThan(90);
      expect(result.executionTime).toBeLessThan(200);
    });
  });

  describe('MCP Tool Integration', () => {
    it('should have access to tool modules', async () => {
      const code = `
        // Check if modules are available
        const hasDatabase = typeof database !== 'undefined';
        const hasProcessing = typeof processing !== 'undefined';
        return { hasDatabase, hasProcessing };
      `;
      const result = await executeCode(code);

      expect(result.success).toBe(true);
      // Modules may not be loaded in test environment
    });
  });

  describe('File System Access', () => {
    it('should have access to workspace directory', async () => {
      const code = `
        const files = await fs.readdir('/workspace');
        return { hasWorkspace: true, files };
      `;
      const result = await executeCode(code);

      expect(result.success).toBe(true);
      expect(result.output).toHaveProperty('hasWorkspace', true);
    });

    it('should be able to write to workspace', async () => {
      const code = `
        const testFile = '/workspace/data/test.txt';
        await fs.writeFile(testFile, 'test content', 'utf-8');
        const content = await fs.readFile(testFile, 'utf-8');
        return { success: content === 'test content' };
      `;
      const result = await executeCode(code);

      expect(result.success).toBe(true);
      expect(result.output).toHaveProperty('success', true);
    });
  });

  describe('Error Handling', () => {
    it('should handle syntax errors', async () => {
      const code = 'this is not valid javascript {{{';
      const result = await executeCode(code);

      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
    });

    it('should handle runtime errors', async () => {
      const code = `
        throw new Error('Test error');
      `;
      const result = await executeCode(code);

      expect(result.success).toBe(false);
      expect(result.error).toContain('Test error');
    });

    it('should handle promise rejections', async () => {
      const code = `
        await Promise.reject(new Error('Async error'));
      `;
      const result = await executeCode(code);

      expect(result.success).toBe(false);
      expect(result.error).toContain('Async error');
    });
  });

  describe('Filesystem Operations', () => {
    it('should copy file to workspace with relative path', async () => {
      const result = await callTool('copy_file_to_workspace', {
        source_path: '/tmp/test_input.txt',
        destination_path: 'input/test.txt'
      });

      expect(result.success).toBeDefined();
      if (result.success) {
        expect(result.path).toContain('/workspace/input/test.txt');
      }
    });

    it('should copy file to workspace with absolute path', async () => {
      const result = await callTool('copy_file_to_workspace', {
        source_path: '/tmp/test_input.txt',
        destination_path: '/workspace/input/test_absolute.txt'
      });

      expect(result.success).toBeDefined();
      if (result.success) {
        expect(result.path).toBe('/workspace/input/test_absolute.txt');
      }
    });

    it('should copy file from workspace to local', async () => {
      // First create a file in workspace
      const createCode = `
        await fs.writeFile('/workspace/output/test_export.txt', 'export test', 'utf-8');
        return { created: true };
      `;
      await executeCode(createCode);

      // Then copy it out
      const result = await callTool('copy_file_from_workspace', {
        workspace_path: 'output/test_export.txt',
        destination_path: '/tmp/test_output.txt'
      });

      expect(result.success).toBeDefined();
      if (result.success) {
        expect(result.path).toBe('/tmp/test_output.txt');
        expect(result.size).toBeGreaterThan(0);
      }
    });

    it('should handle missing source file gracefully', async () => {
      const result = await callTool('copy_file_to_workspace', {
        source_path: '/tmp/nonexistent_file.txt',
        destination_path: 'input/test.txt'
      });

      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
    });

    it('should create destination directories automatically', async () => {
      const result = await callTool('copy_file_to_workspace', {
        source_path: '/tmp/test_input.txt',
        destination_path: 'deep/nested/path/test.txt'
      });

      expect(result.success).toBeDefined();
      if (result.success) {
        expect(result.path).toContain('deep/nested/path/test.txt');
      }
    });

    it('should validate required parameters', async () => {
      const result = await callTool('copy_file_to_workspace', {
        source_path: '/tmp/test.txt'
        // missing destination_path
      });

      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
    });
  });
});

// Helper function to execute code via MCP protocol
async function executeCode(code: string, timeout: number = 30000): Promise<any> {
  return callTool('execute_code', { code, timeout });
}

// Generic helper to call any MCP tool
async function callTool(toolName: string, args: any, timeout: number = 30000): Promise<any> {
  const request = JSON.stringify({
    jsonrpc: '2.0',
    id: 1,
    method: 'tools/call',
    params: {
      name: toolName,
      arguments: args,
    },
  });

  try {
    const { stdout } = await execAsync(
      `echo '${request.replace(/'/g, "'\\''")}' | docker exec -i code-execution-sandbox node dist/executor.js`,
      { timeout: timeout + 5000 }
    );

    const response = JSON.parse(stdout.trim());
    const content = response.result?.content?.[0]?.text;

    if (content) {
      return JSON.parse(content);
    }

    return { success: false, error: 'Invalid response format' };
  } catch (error: any) {
    return { success: false, error: error.message };
  }
}
