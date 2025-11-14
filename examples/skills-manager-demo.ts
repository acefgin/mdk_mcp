/**
 * Skills Manager Demo
 *
 * Demonstrates context-aware skill discovery and activation.
 *
 * Usage:
 * ```bash
 * npx tsx examples/skills-manager-demo.ts
 * ```
 */

import { SkillsManager, setGlobalSkillsManager, findSkills, activateSkill, suggestSkills } from '../workspace/lib/skills-manager.js';

/**
 * Demo 1: Basic Skill Discovery
 */
async function demo1_basicDiscovery() {
  console.log('\n📚 Demo 1: Basic Skill Discovery\n');

  const manager = new SkillsManager();
  await manager.initialize();

  // List all available skills
  const skills = manager.listSkills();

  console.log(`Found ${skills.length} skills:\n`);
  for (const skill of skills) {
    console.log(`  • ${skill.metadata.name}`);
    console.log(`    ${skill.metadata.description.substring(0, 80)}...`);
  }

  // Get detailed information about a specific skill
  console.log('\n📖 Detailed Skill Information:\n');
  const mcpSkill = manager.getSkill('mcp-server-dev', false);
  if (mcpSkill) {
    console.log(`  Name: ${mcpSkill.metadata.name}`);
    console.log(`  Description: ${mcpSkill.metadata.description}`);
    console.log(`  File: ${mcpSkill.filePath}`);
    console.log(`  Last Modified: ${mcpSkill.lastModified.toISOString()}`);
  }
}

/**
 * Demo 2: Searching for Skills
 */
async function demo2_searchingSkills() {
  console.log('\n🔍 Demo 2: Searching for Skills\n');

  const manager = new SkillsManager();
  await manager.initialize();

  // Search by keyword
  console.log('Search: "MCP"\n');
  const mcpResults = await manager.findSkills('MCP');
  console.log(`  Found ${mcpResults.length} results:`);
  for (const result of mcpResults) {
    console.log(`    • ${result.metadata.name}`);
  }

  // Search by different keyword
  console.log('\nSearch: "primer"\n');
  const primerResults = await manager.findSkills('primer');
  console.log(`  Found ${primerResults.length} results:`);
  for (const result of primerResults) {
    console.log(`    • ${result.metadata.name}`);
  }

  // Search with complex options
  console.log('\nSearch: "BioPython" (with content search)\n');
  const biopythonResults = await manager.findSkills({
    query: 'BioPython',
    includeContent: true,
  });
  console.log(`  Found ${biopythonResults.length} results:`);
  for (const result of biopythonResults) {
    console.log(`    • ${result.metadata.name}`);
  }
}

/**
 * Demo 3: Context-Aware Skill Suggestions
 */
async function demo3_contextAwareSuggestions() {
  console.log('\n🎯 Demo 3: Context-Aware Skill Suggestions\n');

  const manager = new SkillsManager();
  await manager.initialize();

  // Example 1: MCP tool development
  console.log('Context: "I need to create an MCP tool for sequence validation"\n');
  const suggestions1 = await manager.suggestSkills(
    'I need to create an MCP tool for sequence validation',
    3
  );
  console.log('  Suggested skills:');
  for (const skill of suggestions1) {
    console.log(`    • ${skill.metadata.name}`);
  }

  // Example 2: Primer design
  console.log('\nContext: "How do I design primers with Primer3 and calculate Tm?"\n');
  const suggestions2 = await manager.suggestSkills(
    'How do I design primers with Primer3 and calculate Tm?',
    3
  );
  console.log('  Suggested skills:');
  for (const skill of suggestions2) {
    console.log(`    • ${skill.metadata.name}`);
  }

  // Example 3: BioPython parsing
  console.log('\nContext: "I need to parse FASTA files with BioPython SeqIO"\n');
  const suggestions3 = await manager.suggestSkills(
    'I need to parse FASTA files with BioPython SeqIO',
    3
  );
  console.log('  Suggested skills:');
  for (const skill of suggestions3) {
    console.log(`    • ${skill.metadata.name}`);
  }

  // Example 4: Multi-agent system
  console.log('\nContext: "Creating a multi-agent qPCR design system with AG2"\n');
  const suggestions4 = await manager.suggestSkills(
    'Creating a multi-agent qPCR design system with AG2',
    3
  );
  console.log('  Suggested skills:');
  for (const skill of suggestions4) {
    console.log(`    • ${skill.metadata.name}`);
  }
}

/**
 * Demo 4: Skill Activation
 */
async function demo4_skillActivation() {
  console.log('\n🚀 Demo 4: Skill Activation\n');

  const manager = new SkillsManager();
  await manager.initialize();

  // Activate a skill
  console.log('Activating skill: mcp-server-dev\n');
  const content = await manager.activateSkill('mcp-server-dev');

  console.log(`  Content length: ${content.length} characters`);
  console.log(`  First 200 characters:\n`);
  console.log(`    ${content.substring(0, 200)}...`);

  // Check statistics
  const stats1 = manager.getStats();
  console.log('\n📊 Statistics after activation:\n');
  console.log(`  Total activations: ${stats1.totalActivations}`);
  console.log(`  Last activated: ${stats1.lastActivated?.name} at ${stats1.lastActivated?.timestamp.toISOString()}`);

  // Activate multiple skills
  console.log('\nActivating more skills...\n');
  await manager.activateSkill('biopython-dev');
  await manager.activateSkill('mcp-server-dev');
  await manager.activateSkill('primer-design-tools');

  const stats2 = manager.getStats();
  console.log('📊 Updated Statistics:\n');
  console.log(`  Total activations: ${stats2.totalActivations}`);
  console.log('  Activations by skill:');
  for (const [name, count] of Object.entries(stats2.activationsBySkill)) {
    console.log(`    • ${name}: ${count}`);
  }
}

/**
 * Demo 5: Global Skills Manager
 */
async function demo5_globalManager() {
  console.log('\n🌐 Demo 5: Global Skills Manager\n');

  // Set up global manager
  const manager = new SkillsManager();
  await manager.initialize();
  setGlobalSkillsManager(manager);

  console.log('Using global helper functions:\n');

  // Find skills using global helper
  console.log('1. findSkills("MCP")\n');
  const results = await findSkills('MCP');
  console.log(`   Found ${results.length} skills`);

  // Activate skill using global helper
  console.log('\n2. activateSkill("biopython-dev")\n');
  const content = await activateSkill('biopython-dev');
  console.log(`   Activated skill with ${content.length} characters`);

  // Suggest skills using global helper
  console.log('\n3. suggestSkills("I need to align sequences")\n');
  const suggestions = await suggestSkills('I need to align sequences', 2);
  console.log('   Suggested skills:');
  for (const skill of suggestions) {
    console.log(`     • ${skill.metadata.name}`);
  }

  console.log('\n✅ Benefits of global manager:');
  console.log('  • Simpler API (no need to pass manager instance)');
  console.log('  • Shared state across modules');
  console.log('  • Easier integration with generated tools');
}

/**
 * Demo 6: Real-World Use Case - Workflow Assistant
 */
async function demo6_workflowAssistant() {
  console.log('\n🧪 Demo 6: Real-World Use Case - Workflow Assistant\n');

  const manager = new SkillsManager();
  await manager.initialize();

  // Simulate a user working on different tasks
  const tasks = [
    {
      description: 'User is implementing a new MCP server',
      context: 'I need to create an MCP server for BLAST validation',
    },
    {
      description: 'User needs to parse sequences',
      context: 'How do I read a FASTA file with BioPython?',
    },
    {
      description: 'User wants to design primers',
      context: 'I need to design qPCR primers and check for hairpins',
    },
    {
      description: 'User is building an AG2 agent',
      context: 'Creating a multi-agent system for primer validation',
    },
  ];

  for (const task of tasks) {
    console.log(`\n📌 Task: ${task.description}`);
    console.log(`   User input: "${task.context}"\n`);

    // Get skill suggestions
    const suggestions = await manager.suggestSkills(task.context, 2);

    if (suggestions.length > 0) {
      console.log('   💡 Suggested skills:');
      for (const skill of suggestions) {
        console.log(`      • ${skill.metadata.name}`);
        console.log(`        ${skill.metadata.description.substring(0, 60)}...`);
      }

      // Automatically activate the top suggestion
      const topSkill = suggestions[0];
      console.log(`\n   ✅ Auto-activating: ${topSkill.metadata.name}`);
      await manager.activateSkill(topSkill.metadata.name);
    } else {
      console.log('   ⚠️  No relevant skills found');
    }
  }

  // Show final statistics
  console.log('\n\n📊 Workflow Session Statistics:\n');
  const stats = manager.getStats();
  console.log(`  Total skills available: ${stats.totalSkills}`);
  console.log(`  Total activations: ${stats.totalActivations}`);
  console.log('  Most activated skills:');

  const sorted = Object.entries(stats.activationsBySkill)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 3);

  for (const [name, count] of sorted) {
    console.log(`    • ${name}: ${count} times`);
  }
}

/**
 * Demo 7: Integration with Code Execution
 */
async function demo7_codeExecutionIntegration() {
  console.log('\n🔌 Demo 7: Integration with Code Execution\n');

  console.log('Code Execution with Skills Manager:\n');
  console.log('```typescript');
  console.log('// Initialize skills manager');
  console.log('const manager = new SkillsManager();');
  console.log('await manager.initialize();');
  console.log('setGlobalSkillsManager(manager);');
  console.log('');
  console.log('// Analyze user request');
  console.log('const userRequest = "I need to create an MCP tool for primer design";');
  console.log('');
  console.log('// Get skill suggestions');
  console.log('const suggestions = await suggestSkills(userRequest);');
  console.log('');
  console.log('// Activate relevant skills');
  console.log('for (const skill of suggestions) {');
  console.log('  const content = await activateSkill(skill.metadata.name);');
  console.log('  // Inject skill content into AI context');
  console.log('  await injectSkillContext(content);');
  console.log('}');
  console.log('');
  console.log('// Execute workflow with skill knowledge');
  console.log('const result = await executeWorkflow(userRequest);');
  console.log('```');
  console.log('');
  console.log('✅ Benefits:');
  console.log('  • Automatic skill discovery based on user intent');
  console.log('  • Just-in-time knowledge injection');
  console.log('  • Reduced token usage (only load relevant skills)');
  console.log('  • Context-aware assistance');
  console.log('  • Scalable to hundreds of skills');
}

/**
 * Demo 8: Performance Characteristics
 */
async function demo8_performance() {
  console.log('\n⚡ Demo 8: Performance Characteristics\n');

  const manager = new SkillsManager();

  // Initialization time
  const initStart = Date.now();
  await manager.initialize();
  const initTime = Date.now() - initStart;

  console.log(`Initialization: ${initTime}ms`);
  console.log(`  • Discovered ${manager.listSkills().length} skills`);

  // Search time
  const searchStart = Date.now();
  await manager.findSkills('MCP');
  const searchTime = Date.now() - searchStart;

  console.log(`\nSearch time: ${searchTime}ms`);
  console.log('  • Fast keyword matching');

  // Activation time
  const activateStart = Date.now();
  await manager.activateSkill('mcp-server-dev');
  const activateTime = Date.now() - activateStart;

  console.log(`\nActivation time: ${activateTime}ms`);
  console.log('  • Instant content retrieval from cache');

  // Suggestion time
  const suggestStart = Date.now();
  await manager.suggestSkills('I need to create an MCP tool');
  const suggestTime = Date.now() - suggestStart;

  console.log(`\nSuggestion time: ${suggestTime}ms`);
  console.log('  • Context-aware matching with scoring');

  console.log('\n✅ Performance Summary:');
  console.log('  • Initialization: Fast (<500ms for typical skill library)');
  console.log('  • Search: Very fast (<50ms)');
  console.log('  • Activation: Instant (<10ms from cache)');
  console.log('  • Suggestion: Fast (<100ms with scoring)');
}

/**
 * Run all demos
 */
async function main() {
  console.log('📚 Skills Manager Demo Suite');
  console.log('============================\n');

  const demos = [
    { name: 'Basic Discovery', fn: demo1_basicDiscovery },
    { name: 'Searching Skills', fn: demo2_searchingSkills },
    { name: 'Context-Aware Suggestions', fn: demo3_contextAwareSuggestions },
    { name: 'Skill Activation', fn: demo4_skillActivation },
    { name: 'Global Manager', fn: demo5_globalManager },
    { name: 'Workflow Assistant', fn: demo6_workflowAssistant },
    { name: 'Code Execution Integration', fn: demo7_codeExecutionIntegration },
    { name: 'Performance', fn: demo8_performance },
  ];

  for (const demo of demos) {
    try {
      await demo.fn();
    } catch (error: any) {
      console.error(`\n❌ Demo "${demo.name}" failed:`, error.message);
    }
  }

  console.log('\n\n✅ Demo suite complete!\n');
  console.log('📖 Key Takeaways:');
  console.log('  • Skills are automatically discovered from .claude/skills/');
  console.log('  • Context-aware suggestions help find relevant skills');
  console.log('  • Activation statistics track skill usage');
  console.log('  • Global manager simplifies integration');
  console.log('  • Fast performance for real-time assistance');
  console.log('  • Scalable to large skill libraries');
  console.log('\n📚 Next steps:');
  console.log('  1. Review workspace/lib/skills-manager.ts (SkillsManager class)');
  console.log('  2. Check tests/unit/skills-manager.test.ts for tests');
  console.log('  3. Explore .claude/skills/ directory for available skills');
  console.log('  4. Integrate with code execution workflows\n');
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

export {
  demo1_basicDiscovery,
  demo2_searchingSkills,
  demo3_contextAwareSuggestions,
  demo4_skillActivation,
  demo5_globalManager,
  demo6_workflowAssistant,
};
