/**
 * Unit tests for SkillsManager
 *
 * Tests skill discovery, activation, search, and statistics tracking.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { SkillsManager, setGlobalSkillsManager, getGlobalSkillsManager, findSkills, activateSkill, suggestSkills } from '../../workspace/lib/skills-manager';
import * as fs from 'fs';
import * as path from 'path';

describe('SkillsManager', () => {
  describe('Initialization', () => {
    it('should initialize successfully with default directory', async () => {
      const manager = new SkillsManager();
      await manager.initialize();

      const skills = manager.listSkills();
      expect(skills.length).toBeGreaterThan(0);
    });

    it('should throw error if skills directory does not exist', async () => {
      const manager = new SkillsManager('/nonexistent/path');

      await expect(manager.initialize()).rejects.toThrow('Skills directory not found');
    });

    it('should only initialize once', async () => {
      const manager = new SkillsManager();
      await manager.initialize();

      const skills1 = manager.listSkills();
      await manager.initialize(); // Second call should be no-op
      const skills2 = manager.listSkills();

      expect(skills1).toEqual(skills2);
    });

    it('should throw error if methods called before initialization', () => {
      const manager = new SkillsManager();

      expect(() => manager.listSkills()).toThrow('SkillsManager not initialized');
      expect(() => manager.getStats()).toThrow('SkillsManager not initialized');
    });
  });

  describe('Skill Discovery', () => {
    let manager: SkillsManager;

    beforeEach(async () => {
      manager = new SkillsManager();
      await manager.initialize();
    });

    it('should discover all skills in .claude/skills/', () => {
      const skills = manager.listSkills();

      // Should find at least the 5 known skills
      expect(skills.length).toBeGreaterThanOrEqual(5);

      const skillNames = skills.map(s => s.metadata.name);
      expect(skillNames).toContain('mcp-server-dev');
      expect(skillNames).toContain('ag2-agent-dev');
      expect(skillNames).toContain('biopython-dev');
      expect(skillNames).toContain('primer-design-tools');
      expect(skillNames).toContain('seq-analysis-tools');
    });

    it('should parse skill metadata correctly', () => {
      const skill = manager.getSkill('mcp-server-dev');

      expect(skill).toBeDefined();
      expect(skill!.metadata.name).toBe('mcp-server-dev');
      expect(skill!.metadata.description).toContain('MCP');
      expect(skill!.metadata.description).toContain('bioinformatics');
    });

    it('should extract skill content without frontmatter', () => {
      const skill = manager.getSkill('mcp-server-dev');

      expect(skill).toBeDefined();
      expect(skill!.content).not.toContain('---');
      expect(skill!.content).not.toContain('name:');
      expect(skill!.content).toContain('MCP');
    });

    it('should include file metadata', () => {
      const skill = manager.getSkill('mcp-server-dev');

      expect(skill).toBeDefined();
      expect(skill!.filePath).toContain('mcp-server-dev');
      expect(skill!.filePath).toContain('SKILL.md');
      expect(skill!.lastModified).toBeInstanceOf(Date);
    });
  });

  describe('List Skills', () => {
    let manager: SkillsManager;

    beforeEach(async () => {
      manager = new SkillsManager();
      await manager.initialize();
    });

    it('should list all skills without content by default', () => {
      const skills = manager.listSkills();

      expect(skills.length).toBeGreaterThan(0);
      for (const skill of skills) {
        expect(skill.metadata.name).toBeDefined();
        expect(skill.metadata.description).toBeDefined();
        expect(skill.content).toBe('');
      }
    });

    it('should include content when requested', () => {
      const skills = manager.listSkills(true);

      expect(skills.length).toBeGreaterThan(0);
      for (const skill of skills) {
        expect(skill.content).not.toBe('');
        expect(skill.content.length).toBeGreaterThan(100);
      }
    });
  });

  describe('Find Skills', () => {
    let manager: SkillsManager;

    beforeEach(async () => {
      manager = new SkillsManager();
      await manager.initialize();
    });

    it('should find skills by name', async () => {
      const results = await manager.findSkills('mcp-server');

      expect(results.length).toBeGreaterThan(0);
      expect(results[0].metadata.name).toBe('mcp-server-dev');
    });

    it('should find skills by description', async () => {
      const results = await manager.findSkills('BioPython');

      expect(results.length).toBeGreaterThan(0);
      const names = results.map(s => s.metadata.name);
      expect(names).toContain('biopython-dev');
    });

    it('should support simple string query', async () => {
      const results = await manager.findSkills('primer');

      expect(results.length).toBeGreaterThan(0);
      const names = results.map(s => s.metadata.name);
      expect(names).toContain('primer-design-tools');
    });

    it('should support complex search options', async () => {
      const results = await manager.findSkills({
        query: 'MCP',
        includeContent: false,
      });

      expect(results.length).toBeGreaterThan(0);
      for (const result of results) {
        expect(result.content).toBe('');
      }
    });

    it('should search in content when includeContent is true', async () => {
      const results = await manager.findSkills({
        query: 'async',
        includeContent: true,
      });

      expect(results.length).toBeGreaterThan(0);
    });

    it('should return empty array for non-matching query', async () => {
      const results = await manager.findSkills('nonexistent-skill-xyz123');

      expect(results).toEqual([]);
    });

    it('should be case-insensitive', async () => {
      const results1 = await manager.findSkills('MCP');
      const results2 = await manager.findSkills('mcp');

      expect(results1.length).toBe(results2.length);
      expect(results1.map(s => s.metadata.name).sort()).toEqual(
        results2.map(s => s.metadata.name).sort()
      );
    });
  });

  describe('Get Skill', () => {
    let manager: SkillsManager;

    beforeEach(async () => {
      manager = new SkillsManager();
      await manager.initialize();
    });

    it('should get skill by name with content', () => {
      const skill = manager.getSkill('mcp-server-dev');

      expect(skill).toBeDefined();
      expect(skill!.metadata.name).toBe('mcp-server-dev');
      expect(skill!.content).not.toBe('');
    });

    it('should get skill without content when requested', () => {
      const skill = manager.getSkill('mcp-server-dev', false);

      expect(skill).toBeDefined();
      expect(skill!.metadata.name).toBe('mcp-server-dev');
      expect(skill!.content).toBe('');
    });

    it('should return undefined for non-existent skill', () => {
      const skill = manager.getSkill('nonexistent-skill');

      expect(skill).toBeUndefined();
    });
  });

  describe('Activate Skill', () => {
    let manager: SkillsManager;

    beforeEach(async () => {
      manager = new SkillsManager();
      await manager.initialize();
    });

    it('should activate skill and return content', async () => {
      const content = await manager.activateSkill('mcp-server-dev');

      expect(content).toBeDefined();
      expect(content.length).toBeGreaterThan(100);
      expect(content).toContain('MCP');
    });

    it('should throw error for non-existent skill', async () => {
      await expect(manager.activateSkill('nonexistent-skill')).rejects.toThrow('Skill not found');
    });

    it('should increment activation count', async () => {
      const stats1 = manager.getStats();
      const initialCount = stats1.activationsBySkill['mcp-server-dev'] || 0;

      await manager.activateSkill('mcp-server-dev');

      const stats2 = manager.getStats();
      const newCount = stats2.activationsBySkill['mcp-server-dev'] || 0;

      expect(newCount).toBe(initialCount + 1);
    });

    it('should update last activation', async () => {
      await manager.activateSkill('mcp-server-dev');

      const stats = manager.getStats();
      expect(stats.lastActivated).toBeDefined();
      expect(stats.lastActivated!.name).toBe('mcp-server-dev');
      expect(stats.lastActivated!.timestamp).toBeInstanceOf(Date);
    });

    it('should handle multiple activations', async () => {
      await manager.activateSkill('mcp-server-dev');
      await manager.activateSkill('biopython-dev');
      await manager.activateSkill('mcp-server-dev');

      const stats = manager.getStats();
      expect(stats.activationsBySkill['mcp-server-dev']).toBe(2);
      expect(stats.activationsBySkill['biopython-dev']).toBe(1);
      expect(stats.totalActivations).toBe(3);
    });
  });

  describe('Suggest Skills', () => {
    let manager: SkillsManager;

    beforeEach(async () => {
      manager = new SkillsManager();
      await manager.initialize();
    });

    it('should suggest skills based on context', async () => {
      const suggestions = await manager.suggestSkills('I need to create an MCP tool');

      expect(suggestions.length).toBeGreaterThan(0);
      expect(suggestions[0].metadata.name).toContain('mcp');
    });

    it('should respect maxSuggestions parameter', async () => {
      const suggestions = await manager.suggestSkills('bioinformatics', 2);

      expect(suggestions.length).toBeLessThanOrEqual(2);
    });

    it('should return empty array for irrelevant context', async () => {
      const suggestions = await manager.suggestSkills('xyz random unrelated text 123');

      expect(suggestions).toEqual([]);
    });

    it('should suggest primer-design-tools for primer-related context', async () => {
      const suggestions = await manager.suggestSkills('I need to design primers with Primer3');

      expect(suggestions.length).toBeGreaterThan(0);
      const names = suggestions.map(s => s.metadata.name);
      expect(names).toContain('primer-design-tools');
    });

    it('should suggest biopython-dev for BioPython context', async () => {
      const suggestions = await manager.suggestSkills('How do I parse FASTA files with BioPython?');

      expect(suggestions.length).toBeGreaterThan(0);
      const names = suggestions.map(s => s.metadata.name);
      expect(names).toContain('biopython-dev');
    });

    it('should suggest ag2-agent-dev for agent context', async () => {
      const suggestions = await manager.suggestSkills('I need to create a multi-agent system with AG2');

      expect(suggestions.length).toBeGreaterThan(0);
      const names = suggestions.map(s => s.metadata.name);
      expect(names).toContain('ag2-agent-dev');
    });

    it('should not include skill content in suggestions', async () => {
      const suggestions = await manager.suggestSkills('MCP tool development');

      for (const suggestion of suggestions) {
        expect(suggestion.content).toBe('');
      }
    });
  });

  describe('Statistics', () => {
    let manager: SkillsManager;

    beforeEach(async () => {
      manager = new SkillsManager();
      await manager.initialize();
    });

    it('should return initial statistics', () => {
      const stats = manager.getStats();

      expect(stats.totalSkills).toBeGreaterThan(0);
      expect(stats.totalActivations).toBe(0);
      expect(stats.activationsBySkill).toEqual({});
      expect(stats.lastActivated).toBeUndefined();
    });

    it('should track activations correctly', async () => {
      await manager.activateSkill('mcp-server-dev');
      await manager.activateSkill('biopython-dev');
      await manager.activateSkill('mcp-server-dev');

      const stats = manager.getStats();

      expect(stats.totalActivations).toBe(3);
      expect(stats.activationsBySkill['mcp-server-dev']).toBe(2);
      expect(stats.activationsBySkill['biopython-dev']).toBe(1);
      expect(stats.lastActivated!.name).toBe('mcp-server-dev');
    });

    it('should clear statistics', async () => {
      await manager.activateSkill('mcp-server-dev');
      manager.clearStats();

      const stats = manager.getStats();

      expect(stats.totalActivations).toBe(0);
      expect(stats.activationsBySkill).toEqual({});
      expect(stats.lastActivated).toBeUndefined();
    });
  });

  describe('Reload', () => {
    let manager: SkillsManager;

    beforeEach(async () => {
      manager = new SkillsManager();
      await manager.initialize();
    });

    it('should reload skills from disk', async () => {
      const skills1 = manager.listSkills();

      await manager.reload();

      const skills2 = manager.listSkills();

      expect(skills1.length).toBe(skills2.length);
      expect(skills1.map(s => s.metadata.name).sort()).toEqual(
        skills2.map(s => s.metadata.name).sort()
      );
    });

    it('should preserve activation statistics after reload', async () => {
      await manager.activateSkill('mcp-server-dev');
      const stats1 = manager.getStats();

      await manager.reload();

      const stats2 = manager.getStats();

      // Stats should be preserved
      expect(stats2.activationsBySkill['mcp-server-dev']).toBe(
        stats1.activationsBySkill['mcp-server-dev']
      );
    });
  });

  describe('Global Skills Manager', () => {
    let manager: SkillsManager;

    beforeEach(async () => {
      manager = new SkillsManager();
      await manager.initialize();
      setGlobalSkillsManager(manager);
    });

    afterEach(() => {
      setGlobalSkillsManager(manager); // Reset to valid manager
    });

    it('should set and get global manager', () => {
      const globalManager = getGlobalSkillsManager();

      expect(globalManager).toBe(manager);
    });

    it('should use global manager in findSkills helper', async () => {
      const results = await findSkills('MCP');

      expect(results.length).toBeGreaterThan(0);
    });

    it('should use global manager in activateSkill helper', async () => {
      const content = await activateSkill('mcp-server-dev');

      expect(content).toBeDefined();
      expect(content.length).toBeGreaterThan(100);
    });

    it('should use global manager in suggestSkills helper', async () => {
      const suggestions = await suggestSkills('MCP tool development');

      expect(suggestions.length).toBeGreaterThan(0);
    });

    it('should throw error if global manager not set', async () => {
      setGlobalSkillsManager(null as any);

      await expect(findSkills('MCP')).rejects.toThrow('Global skills manager not set');
      await expect(activateSkill('mcp-server-dev')).rejects.toThrow('Global skills manager not set');
      await expect(suggestSkills('MCP')).rejects.toThrow('Global skills manager not set');
    });
  });

  describe('Edge Cases', () => {
    it('should handle skills directory with no skills', async () => {
      // Create a temporary empty directory
      const tempDir = path.join(process.cwd(), '.test-skills-empty');
      if (!fs.existsSync(tempDir)) {
        fs.mkdirSync(tempDir);
      }

      const manager = new SkillsManager(tempDir);
      await manager.initialize();

      const skills = manager.listSkills();
      expect(skills).toEqual([]);

      // Cleanup
      fs.rmdirSync(tempDir);
    });

    it('should handle skill files with minimal metadata', async () => {
      const manager = new SkillsManager();
      await manager.initialize();

      // All our skills should have at least name and description
      const skills = manager.listSkills();
      for (const skill of skills) {
        expect(skill.metadata.name).toBeDefined();
        expect(skill.metadata.description).toBeDefined();
      }
    });

    it('should handle very long skill content', async () => {
      const manager = new SkillsManager();
      await manager.initialize();

      const skill = manager.getSkill('primer-design-tools');
      expect(skill).toBeDefined();
      expect(skill!.content.length).toBeGreaterThan(1000);
    });

    it('should handle special characters in search queries', async () => {
      const manager = new SkillsManager();
      await manager.initialize();

      const results = await manager.findSkills('C++');
      // Should not crash, even if no results
      expect(Array.isArray(results)).toBe(true);
    });
  });

  describe('Performance', () => {
    it('should initialize quickly', async () => {
      const start = Date.now();

      const manager = new SkillsManager();
      await manager.initialize();

      const elapsed = Date.now() - start;

      // Should initialize in less than 1 second
      expect(elapsed).toBeLessThan(1000);
    });

    it('should search quickly', async () => {
      const manager = new SkillsManager();
      await manager.initialize();

      const start = Date.now();

      await manager.findSkills('MCP');

      const elapsed = Date.now() - start;

      // Should search in less than 100ms
      expect(elapsed).toBeLessThan(100);
    });

    it('should activate skills quickly', async () => {
      const manager = new SkillsManager();
      await manager.initialize();

      const start = Date.now();

      await manager.activateSkill('mcp-server-dev');

      const elapsed = Date.now() - start;

      // Should activate in less than 50ms
      expect(elapsed).toBeLessThan(50);
    });
  });
});
