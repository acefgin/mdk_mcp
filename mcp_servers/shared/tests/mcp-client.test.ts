/**
 * Tests for Enhanced MCP Client with Progressive Tool Disclosure
 */

import { describe, it, expect, beforeAll, afterEach } from 'vitest';
import { MCPClient } from '../mcp-client';

describe('MCPClient - Progressive Tool Disclosure', () => {
  let client: MCPClient;

  beforeAll(() => {
    client = new MCPClient({
      servers: {
        database: {
          container: 'ndiag-database-server',
          enabled: true,
        },
        processing: {
          container: 'ndiag-processing-server',
          enabled: true,
        },
        alignment: {
          container: 'ndiag-alignment-server',
          enabled: true,
        },
      },
      cacheSchemas: true,
    });
  });

  afterEach(() => {
    client.clearCache();
  });

  describe('Tool Discovery', () => {
    it('should search for tools by name with minimal detail', async () => {
      const results = await client.searchTools('sequence', 'name');

      expect(results).toBeInstanceOf(Array);
      expect(results.length).toBeGreaterThan(0);

      const firstResult = results[0];
      expect(firstResult).toHaveProperty('server');
      expect(firstResult).toHaveProperty('tools');

      const firstTool = firstResult.tools[0];
      expect(firstTool).toHaveProperty('name');
      expect(firstTool.description).toBeUndefined();
      expect(firstTool.inputSchema).toBeUndefined();
    });

    it('should search for tools with descriptions', async () => {
      const results = await client.searchTools('align', 'description');

      expect(results).toBeInstanceOf(Array);

      if (results.length > 0) {
        const firstTool = results[0].tools[0];
        expect(firstTool).toHaveProperty('name');
        expect(firstTool).toHaveProperty('description');
        expect(firstTool.inputSchema).toBeUndefined();
      }
    });

    it('should search for tools with full schema', async () => {
      const results = await client.searchTools('get_sequences', 'full');

      expect(results).toBeInstanceOf(Array);

      if (results.length > 0) {
        const firstTool = results[0].tools[0];
        expect(firstTool).toHaveProperty('name');
        expect(firstTool).toHaveProperty('description');
        expect(firstTool).toHaveProperty('inputSchema');
        expect(firstTool.inputSchema).toHaveProperty('type');
        expect(firstTool.inputSchema).toHaveProperty('properties');
      }
    });

    it('should handle regex patterns in search', async () => {
      const results = await client.searchTools('^get_', 'name');

      expect(results).toBeInstanceOf(Array);

      if (results.length > 0) {
        const allTools = results.flatMap(r => r.tools);
        allTools.forEach(tool => {
          expect(tool.name).toMatch(/^get_/);
        });
      }
    });
  });

  describe('Server-Specific Queries', () => {
    it('should get all tool names from a server', async () => {
      const names = await client.getToolNames('database');

      expect(names).toBeInstanceOf(Array);
      expect(names.length).toBeGreaterThan(0);
      expect(names).toContain('get_sequences');
    });

    it('should get tool descriptions from a server', async () => {
      const tools = await client.getToolDescriptions('database');

      expect(tools).toBeInstanceOf(Array);
      expect(tools.length).toBeGreaterThan(0);

      const firstTool = tools[0];
      expect(firstTool).toHaveProperty('name');
      expect(firstTool).toHaveProperty('description');
    });

    it('should get full tool schema from a server', async () => {
      const tools = await client.getToolSchema('database');

      expect(tools).toBeInstanceOf(Array);
      expect(tools.length).toBeGreaterThan(0);

      const firstTool = tools[0];
      expect(firstTool).toHaveProperty('name');
      expect(firstTool).toHaveProperty('description');
      expect(firstTool).toHaveProperty('inputSchema');
    });

    it('should get specific tool schema by name', async () => {
      const tools = await client.getToolSchema('database', 'get_sequences');

      expect(tools).toBeInstanceOf(Array);
      expect(tools.length).toBe(1);

      const tool = tools[0];
      expect(tool.name).toBe('get_sequences');
      expect(tool).toHaveProperty('inputSchema');
    });

    it('should throw error for unknown server', async () => {
      await expect(
        client.getToolNames('unknown_server')
      ).rejects.toThrow('not found');
    });
  });

  describe('Caching', () => {
    it('should cache tool names', async () => {
      // First call
      const names1 = await client.getToolNames('database');
      const stats1 = client.getCacheStats();
      expect(stats1.namesCached).toBe(1);

      // Second call (should use cache)
      const names2 = await client.getToolNames('database');
      expect(names2).toEqual(names1);

      const stats2 = client.getCacheStats();
      expect(stats2.namesCached).toBe(1); // Still 1, not incremented
    });

    it('should cache tool descriptions', async () => {
      const desc1 = await client.getToolDescriptions('processing');
      const stats1 = client.getCacheStats();
      expect(stats1.descriptionsCached).toBe(1);

      const desc2 = await client.getToolDescriptions('processing');
      expect(desc2).toEqual(desc1);
    });

    it('should cache full schemas', async () => {
      const schema1 = await client.getToolSchema('alignment');
      const stats1 = client.getCacheStats();
      expect(stats1.schemasCached).toBe(1);

      const schema2 = await client.getToolSchema('alignment');
      expect(schema2).toEqual(schema1);
    });

    it('should clear all caches', async () => {
      await client.getToolNames('database');
      await client.getToolDescriptions('processing');
      await client.getToolSchema('alignment');

      const statsBefore = client.getCacheStats();
      expect(statsBefore.namesCached).toBeGreaterThan(0);
      expect(statsBefore.descriptionsCached).toBeGreaterThan(0);
      expect(statsBefore.schemasCached).toBeGreaterThan(0);

      client.clearCache();

      const statsAfter = client.getCacheStats();
      expect(statsAfter.namesCached).toBe(0);
      expect(statsAfter.descriptionsCached).toBe(0);
      expect(statsAfter.schemasCached).toBe(0);
    });

    it('should respect cache configuration', async () => {
      const noCacheClient = new MCPClient({
        servers: {
          database: {
            container: 'ndiag-database-server',
          },
        },
        cacheSchemas: false,
      });

      await noCacheClient.getToolNames('database');
      await noCacheClient.getToolNames('database');

      const stats = noCacheClient.getCacheStats();
      expect(stats.namesCached).toBe(0);
    });
  });

  describe('Tool Calling', () => {
    it('should call a tool successfully', async () => {
      const result = await client.callTool('database', 'get_taxonomy', {
        taxon: 'Homo sapiens',
      });

      expect(result).toBeDefined();
      // Result format depends on the tool
    });

    it('should handle tool errors', async () => {
      await expect(
        client.callTool('database', 'invalid_tool', {})
      ).rejects.toThrow();
    });

    it('should handle timeout', async () => {
      // This would need a tool that takes longer than timeout
      // For now, just verify the timeout parameter is accepted
      await expect(
        client.callTool('database', 'get_sequences', { taxon: 'test' }, 100)
      ).rejects.toThrow();
    });
  });

  describe('Cache Statistics', () => {
    it('should provide accurate cache statistics', async () => {
      const stats = client.getCacheStats();

      expect(stats).toHaveProperty('servers');
      expect(stats).toHaveProperty('namesCached');
      expect(stats).toHaveProperty('descriptionsCached');
      expect(stats).toHaveProperty('schemasCached');

      expect(stats.servers).toBe(3); // database, processing, alignment
    });
  });

  describe('Token Reduction', () => {
    it('should demonstrate token reduction with progressive loading', async () => {
      // Scenario 1: Load only tool names (minimal tokens)
      const names = await client.getToolNames('database');
      const nameTokens = JSON.stringify(names).length;

      // Scenario 2: Load with descriptions (moderate tokens)
      const descriptions = await client.getToolDescriptions('database');
      const descTokens = JSON.stringify(descriptions).length;

      // Scenario 3: Load full schemas (maximum tokens)
      const schemas = await client.getToolSchema('database');
      const schemaTokens = JSON.stringify(schemas).length;

      // Verify progressive increase
      expect(nameTokens).toBeLessThan(descTokens);
      expect(descTokens).toBeLessThan(schemaTokens);

      // Log for visibility
      console.log('Token usage comparison:');
      console.log(`  Names only: ${nameTokens} chars (~${Math.ceil(nameTokens / 4)} tokens)`);
      console.log(`  With descriptions: ${descTokens} chars (~${Math.ceil(descTokens / 4)} tokens)`);
      console.log(`  Full schemas: ${schemaTokens} chars (~${Math.ceil(schemaTokens / 4)} tokens)`);
      console.log(`  Reduction: ${Math.round((1 - nameTokens / schemaTokens) * 100)}%`);
    });
  });
});
