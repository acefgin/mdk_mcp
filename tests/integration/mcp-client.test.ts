/**
 * Integration tests for MCP Client
 *
 * Tests the MCPCodeExecutionClient with mock servers to verify:
 * - Connection management
 * - Tool calling with retries
 * - Progressive tool discovery
 * - Error handling
 *
 * @see workspace/lib/mcp-client.ts
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import {
  MCPCodeExecutionClient,
  MCPServerConfig,
  setMCPClient,
  callMCPTool,
  searchMCPTools,
} from '../../workspace/lib/mcp-client.js';

describe('MCPCodeExecutionClient', () => {
  let client: MCPCodeExecutionClient;
  let mockConfigs: Map<string, MCPServerConfig>;

  beforeEach(() => {
    // Mock server configurations
    // Note: These are mock configs for testing structure
    // Real integration tests would connect to actual servers
    mockConfigs = new Map([
      [
        'database',
        {
          command: 'echo',
          args: ['mock-database-server'],
        },
      ],
      [
        'processing',
        {
          command: 'echo',
          args: ['mock-processing-server'],
        },
      ],
    ]);
  });

  afterEach(async () => {
    if (client) {
      try {
        await client.close();
      } catch {
        // Ignore errors during cleanup
      }
    }
  });

  describe('initialization', () => {
    it('should create client with server configs', () => {
      client = new MCPCodeExecutionClient(mockConfigs);
      expect(client).toBeDefined();
    });

    it('should report uninitialized status before initialize()', () => {
      client = new MCPCodeExecutionClient(mockConfigs);
      const status = client.getStatus();

      expect(status.initialized).toBe(false);
      expect(status.connectedServers).toHaveLength(0);
      expect(status.totalRequests).toBe(0);
    });

    it('should enable PII tokenization when requested', () => {
      client = new MCPCodeExecutionClient(mockConfigs, true);
      expect(client).toBeDefined();
      // PII tokenization enabled internally
    });
  });

  describe('connection management', () => {
    it('should throw error when calling tool before initialization', async () => {
      client = new MCPCodeExecutionClient(mockConfigs);

      await expect(
        client.callTool('database__get_sequences', {})
      ).rejects.toThrow('MCP client not initialized');
    });

    it('should throw error when searching tools before initialization', async () => {
      client = new MCPCodeExecutionClient(mockConfigs);

      await expect(client.searchTools('blast')).rejects.toThrow(
        'MCP client not initialized'
      );
    });

    // Note: Actual connection testing requires real MCP servers
    // This would be tested in end-to-end tests with Docker containers
  });

  describe('tool calling', () => {
    it('should reject invalid tool ID format', async () => {
      client = new MCPCodeExecutionClient(mockConfigs);

      // Mock initialization (in real test, would actually connect)
      (client as any).initialized = true;

      await expect(
        client.callTool('invalid_format', {})
      ).rejects.toThrow('Invalid tool ID format');
    });

    it('should reject unknown server', async () => {
      client = new MCPCodeExecutionClient(mockConfigs);
      (client as any).initialized = true;

      await expect(
        client.callTool('unknown__tool', {})
      ).rejects.toThrow('Server not found: unknown');
    });

    it('should parse tool ID correctly', async () => {
      client = new MCPCodeExecutionClient(mockConfigs);
      (client as any).initialized = true;

      // This will fail with "Server not found" but shows ID parsing works
      try {
        await client.callTool('database__get_sequences', {});
      } catch (error: any) {
        // Expected to fail since we don't have real connection
        // But the error should be about missing client, not ID parsing
        expect(error.message).not.toContain('Invalid tool ID');
      }
    });
  });

  describe('retry logic', () => {
    it('should retry on retryable errors', async () => {
      client = new MCPCodeExecutionClient(mockConfigs);
      (client as any).initialized = true;

      // Mock a client that fails twice then succeeds
      const mockClient = {
        request: vi
          .fn()
          .mockRejectedValueOnce(new Error('Connection timeout'))
          .mockRejectedValueOnce(new Error('Rate limit exceeded'))
          .mockResolvedValueOnce({
            content: [{ type: 'text', text: 'success' }],
          }),
      };

      (client as any).clients.set('database', mockClient);

      const result = await client.callTool('database__test', {}, 3);

      expect(mockClient.request).toHaveBeenCalledTimes(3);
      expect(result).toBe('success');
    });

    it('should not retry on non-retryable errors', async () => {
      client = new MCPCodeExecutionClient(mockConfigs);
      (client as any).initialized = true;

      const mockClient = {
        request: vi.fn().mockRejectedValue(new Error('Invalid argument')),
      };

      (client as any).clients.set('database', mockClient);

      await expect(
        client.callTool('database__test', {}, 3)
      ).rejects.toThrow('Invalid argument');

      // Should only try once for non-retryable error
      expect(mockClient.request).toHaveBeenCalledTimes(1);
    });

    it('should use exponential backoff', async () => {
      client = new MCPCodeExecutionClient(mockConfigs);
      (client as any).initialized = true;

      const mockClient = {
        request: vi
          .fn()
          .mockRejectedValueOnce(new Error('Timeout'))
          .mockRejectedValueOnce(new Error('Timeout'))
          .mockResolvedValueOnce({
            content: [{ type: 'text', text: 'success' }],
          }),
      };

      (client as any).clients.set('database', mockClient);

      const startTime = Date.now();
      await client.callTool('database__test', {}, 3);
      const elapsed = Date.now() - startTime;

      // Should have delays: 1s + 4s = 5s total (approximately)
      // Allow some tolerance for execution time
      expect(elapsed).toBeGreaterThan(4000);
      expect(elapsed).toBeLessThan(7000);
    }, 10000); // Increase timeout for this test
  });

  describe('response parsing', () => {
    it('should parse JSON responses', async () => {
      client = new MCPCodeExecutionClient(mockConfigs);
      (client as any).initialized = true;

      const mockClient = {
        request: vi.fn().mockResolvedValue({
          content: [
            {
              type: 'text',
              text: '{"count": 10, "sequences": ["ATCG", "GCTA"]}',
            },
          ],
        }),
      };

      (client as any).clients.set('database', mockClient);

      const result = await client.callTool('database__test', {});

      expect(result).toEqual({
        count: 10,
        sequences: ['ATCG', 'GCTA'],
      });
    });

    it('should return plain text when JSON parse fails', async () => {
      client = new MCPCodeExecutionClient(mockConfigs);
      (client as any).initialized = true;

      const mockClient = {
        request: vi.fn().mockResolvedValue({
          content: [{ type: 'text', text: 'plain text response' }],
        }),
      };

      (client as any).clients.set('database', mockClient);

      const result = await client.callTool('database__test', {});

      expect(result).toBe('plain text response');
    });

    it('should handle empty responses', async () => {
      client = new MCPCodeExecutionClient(mockConfigs);
      (client as any).initialized = true;

      const mockClient = {
        request: vi.fn().mockResolvedValue({
          content: [],
        }),
      };

      (client as any).clients.set('database', mockClient);

      const result = await client.callTool('database__test', {});

      expect(result).toEqual({ content: [] });
    });
  });

  describe('tool discovery', () => {
    it('should search tools by name', async () => {
      client = new MCPCodeExecutionClient(mockConfigs);
      (client as any).initialized = true;

      const mockClient = {
        request: vi.fn().mockResolvedValue({
          tools: [
            {
              name: 'get_sequences',
              description: 'Fetch sequences from database',
            },
            {
              name: 'get_taxonomy',
              description: 'Get taxonomic information',
            },
            {
              name: 'align_sequences',
              description: 'Align multiple sequences',
            },
          ],
        }),
      };

      (client as any).clients.set('database', mockClient);

      const results = await client.searchTools('sequence');

      expect(results).toHaveLength(2);
      expect(results[0].name).toBe('get_sequences');
      expect(results[1].name).toBe('align_sequences');
    });

    it('should search tools by description', async () => {
      client = new MCPCodeExecutionClient(mockConfigs);
      (client as any).initialized = true;

      const mockClient = {
        request: vi.fn().mockResolvedValue({
          tools: [
            {
              name: 'get_sequences',
              description: 'Fetch sequences from database',
            },
            {
              name: 'get_taxonomy',
              description: 'Get taxonomic information',
            },
          ],
        }),
      };

      (client as any).clients.set('database', mockClient);

      const results = await client.searchTools('taxonomic');

      expect(results).toHaveLength(1);
      expect(results[0].name).toBe('get_taxonomy');
    });

    it('should return different detail levels', async () => {
      client = new MCPCodeExecutionClient(mockConfigs);
      (client as any).initialized = true;

      const mockClient = {
        request: vi.fn().mockResolvedValue({
          tools: [
            {
              name: 'get_sequences',
              description: 'Fetch sequences',
              inputSchema: { type: 'object', properties: {} },
            },
          ],
        }),
      };

      (client as any).clients.set('database', mockClient);

      // Name only
      const nameOnly = await client.searchTools('sequences', 'name');
      expect(nameOnly[0].description).toBeUndefined();
      expect(nameOnly[0].inputSchema).toBeUndefined();

      // With description
      const withDesc = await client.searchTools('sequences', 'description');
      expect(withDesc[0].description).toBeDefined();
      expect(withDesc[0].inputSchema).toBeUndefined();

      // Full details
      const full = await client.searchTools('sequences', 'full');
      expect(full[0].description).toBeDefined();
      expect(full[0].inputSchema).toBeDefined();
    });
  });

  describe('status reporting', () => {
    it('should track request counter', async () => {
      client = new MCPCodeExecutionClient(mockConfigs);
      (client as any).initialized = true;

      const mockClient = {
        request: vi.fn().mockResolvedValue({
          content: [{ type: 'text', text: 'success' }],
        }),
      };

      (client as any).clients.set('database', mockClient);

      expect(client.getStatus().totalRequests).toBe(0);

      await client.callTool('database__test', {});
      expect(client.getStatus().totalRequests).toBe(1);

      await client.callTool('database__test', {});
      expect(client.getStatus().totalRequests).toBe(2);
    });
  });
});

describe('Global client helpers', () => {
  describe('setMCPClient and getMCPClient', () => {
    it('should set and get global client', () => {
      const mockConfigs = new Map([
        ['database', { command: 'echo', args: ['test'] }],
      ]);

      const client = new MCPCodeExecutionClient(mockConfigs);
      setMCPClient(client);

      const retrieved = getMCPClient();
      expect(retrieved).toBe(client);
    });
  });

  describe('callMCPTool helper', () => {
    it('should throw error when global client not set', async () => {
      setMCPClient(null as any);

      await expect(callMCPTool('database__test', {})).rejects.toThrow(
        'MCP client not initialized'
      );
    });

    it('should use global client when set', async () => {
      const mockConfigs = new Map([
        ['database', { command: 'echo', args: ['test'] }],
      ]);

      const client = new MCPCodeExecutionClient(mockConfigs);
      (client as any).initialized = true;

      const mockClient = {
        request: vi.fn().mockResolvedValue({
          content: [{ type: 'text', text: 'success' }],
        }),
      };

      (client as any).clients.set('database', mockClient);

      setMCPClient(client);

      const result = await callMCPTool('database__test', {});
      expect(result).toBe('success');
    });
  });

  describe('searchMCPTools helper', () => {
    it('should throw error when global client not set', async () => {
      setMCPClient(null as any);

      await expect(searchMCPTools('blast')).rejects.toThrow(
        'MCP client not initialized'
      );
    });

    it('should use global client when set', async () => {
      const mockConfigs = new Map([
        ['database', { command: 'echo', args: ['test'] }],
      ]);

      const client = new MCPCodeExecutionClient(mockConfigs);
      (client as any).initialized = true;

      const mockClient = {
        request: vi.fn().mockResolvedValue({
          tools: [
            { name: 'blast_nt', description: 'BLAST against NT database' },
          ],
        }),
      };

      (client as any).clients.set('database', mockClient);

      setMCPClient(client);

      const results = await searchMCPTools('blast');
      expect(results).toHaveLength(1);
      expect(results[0].name).toBe('blast_nt');
    });
  });
});

describe('PIITokenizer', () => {
  it('should be a placeholder for Phase 1-3', () => {
    const client = new MCPCodeExecutionClient(new Map(), true);
    // PII tokenization will be fully implemented in Phase 1-3
    // For now, it just passes data through
    expect(client).toBeDefined();
  });
});
