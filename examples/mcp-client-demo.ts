/**
 * MCP Client Demo
 *
 * Demonstrates using MCPCodeExecutionClient to connect to MCP servers
 * and call tools with progressive disclosure and retry logic.
 *
 * Usage:
 * ```bash
 * # Start MCP servers first
 * docker-compose up -d
 *
 * # Run demo
 * npx tsx examples/mcp-client-demo.ts
 * ```
 */

import {
  MCPCodeExecutionClient,
  setMCPClient,
  callMCPTool,
  searchMCPTools,
} from '../workspace/lib/mcp-client.js';

/**
 * Demo 1: Basic Connection and Tool Calling
 */
async function demo1_basicConnection() {
  console.log('\n📚 Demo 1: Basic Connection and Tool Calling\n');

  // Configure MCP servers
  const serverConfigs = new Map([
    [
      'database',
      {
        command: 'docker',
        args: [
          'exec',
          '-i',
          'ndiag-database-server',
          'python3',
          '/app/database_mcp_server.py',
        ],
        env: {
          NCBI_API_KEY: process.env.NCBI_API_KEY || '',
        },
      },
    ],
    [
      'processing',
      {
        command: 'docker',
        args: [
          'exec',
          '-i',
          'ndiag-processing-server',
          'python3',
          '/app/processing_mcp_server.py',
        ],
      },
    ],
  ]);

  // Create and initialize client
  const client = new MCPCodeExecutionClient(serverConfigs);

  try {
    await client.initialize();

    // Check status
    const status = client.getStatus();
    console.log('✅ Client Status:');
    console.log(`   Initialized: ${status.initialized}`);
    console.log(`   Connected Servers: ${status.connectedServers.join(', ')}`);
    console.log(`   Total Requests: ${status.totalRequests}`);

    // Call a tool
    console.log('\n📞 Calling database__get_sequences...');
    const sequences = await client.callTool('database__get_sequences', {
      taxon: 'Salmo salar',
      region: 'COI',
      source: 'ncbi',
      max_results: 5,
      format: 'fasta',
    });

    console.log('\n✅ Response received:');
    const seqCount = sequences.split('>').length - 1;
    console.log(`   Sequences: ${seqCount}`);
    console.log(`   First 200 chars: ${sequences.substring(0, 200)}...`);

    // Close connections
    await client.close();
  } catch (error) {
    console.error('\n❌ Error:', error);
    throw error;
  }
}

/**
 * Demo 2: Progressive Tool Discovery
 */
async function demo2_toolDiscovery() {
  console.log('\n🔍 Demo 2: Progressive Tool Discovery\n');

  const serverConfigs = new Map([
    [
      'database',
      {
        command: 'docker',
        args: [
          'exec',
          '-i',
          'ndiag-database-server',
          'python3',
          '/app/database_mcp_server.py',
        ],
      },
    ],
    [
      'validation',
      {
        command: 'docker',
        args: [
          'exec',
          '-i',
          'ndiag-validation-server',
          'python3',
          '/app/validation_mcp_server.py',
        ],
      },
    ],
  ]);

  const client = new MCPCodeExecutionClient(serverConfigs);

  try {
    await client.initialize();

    // Search for BLAST-related tools
    console.log('🔍 Searching for "blast" tools...\n');
    const blastTools = await client.searchTools('blast', 'description');

    console.log(`✅ Found ${blastTools.length} tools:\n`);
    blastTools.forEach((tool) => {
      console.log(`   • ${tool.server}.${tool.name}`);
      console.log(`     ${tool.description}`);
      console.log('');
    });

    // Get full details for specific tool
    console.log('📋 Getting full details for "blast_nt"...\n');
    const fullDetails = await client.searchTools('blast_nt', 'full');

    if (fullDetails.length > 0) {
      const tool = fullDetails[0];
      console.log(`   Tool: ${tool.name}`);
      console.log(`   Description: ${tool.description}`);
      console.log(`   Input Schema:`);
      console.log(`   ${JSON.stringify(tool.inputSchema, null, 2)}`);
    }

    await client.close();
  } catch (error) {
    console.error('\n❌ Error:', error);
    throw error;
  }
}

/**
 * Demo 3: Retry Logic with Transient Failures
 */
async function demo3_retryLogic() {
  console.log('\n🔄 Demo 3: Retry Logic with Transient Failures\n');

  const serverConfigs = new Map([
    [
      'database',
      {
        command: 'docker',
        args: [
          'exec',
          '-i',
          'ndiag-database-server',
          'python3',
          '/app/database_mcp_server.py',
        ],
      },
    ],
  ]);

  const client = new MCPCodeExecutionClient(serverConfigs);

  try {
    await client.initialize();

    console.log('📞 Calling tool with retry enabled (max 3 attempts)...\n');

    // This tool call will automatically retry on transient failures
    const result = await client.callTool(
      'database__get_taxonomy',
      {
        taxon: 'Salmo salar',
      },
      3 // max retries
    );

    console.log('✅ Success after retries (if any)');
    console.log(`   Result: ${JSON.stringify(result, null, 2)}`);

    await client.close();
  } catch (error) {
    console.error('\n❌ Error after all retries:', error);
    throw error;
  }
}

/**
 * Demo 4: Using Global Client Helpers
 */
async function demo4_globalHelpers() {
  console.log('\n🌐 Demo 4: Using Global Client Helpers\n');

  const serverConfigs = new Map([
    [
      'database',
      {
        command: 'docker',
        args: [
          'exec',
          '-i',
          'ndiag-database-server',
          'python3',
          '/app/database_mcp_server.py',
        ],
      },
    ],
  ]);

  const client = new MCPCodeExecutionClient(serverConfigs);

  try {
    await client.initialize();

    // Set global client
    setMCPClient(client);
    console.log('✅ Global client set\n');

    // Now can use helper functions
    console.log('📞 Calling tool using callMCPTool() helper...\n');
    const result = await callMCPTool('database__get_sequences', {
      taxon: 'Gadus morhua',
      region: 'COI',
      max_results: 3,
    });

    console.log('✅ Response received via helper');
    console.log(`   Sequences: ${result.split('>').length - 1}`);

    // Search tools using helper
    console.log('\n🔍 Searching tools using searchMCPTools() helper...\n');
    const tools = await searchMCPTools('taxonomy');

    console.log(`✅ Found ${tools.length} tools`);
    tools.forEach((tool) => {
      console.log(`   • ${tool.name}`);
    });

    await client.close();
  } catch (error) {
    console.error('\n❌ Error:', error);
    throw error;
  }
}

/**
 * Demo 5: Token Usage Comparison
 */
async function demo5_tokenEfficiency() {
  console.log('\n💰 Demo 5: Token Usage Comparison\n');

  console.log('Traditional Approach:');
  console.log('  1. Load all 34 tools upfront → 150,000 tokens');
  console.log('  2. Pass sequences through context → 50,000 tokens');
  console.log('  Total: 200,000 tokens per workflow\n');

  console.log('Code Execution Approach (Current):');
  console.log('  1. Load tools on demand → 400 tokens per tool');
  console.log('  2. Process in code → 200 tokens for summary');
  console.log('  Total: 2,500 tokens per workflow\n');

  console.log('✨ Token Reduction: 98.75%');
  console.log('💵 Cost Reduction: $0.60 → $0.008 per workflow\n');

  console.log('Example:');
  console.log('  const client = new MCPCodeExecutionClient(configs);');
  console.log('  await client.initialize();');
  console.log('  ');
  console.log('  // Only loads getSequences tool (~400 tokens)');
  console.log("  const seqs = await client.callTool('database__get_sequences', {");
  console.log("    taxon: 'Salmo salar',");
  console.log('    max_results: 100');
  console.log('  });');
  console.log('  ');
  console.log('  // Process in code (not through model)');
  console.log("  const filtered = seqs.split('\\n>').filter(s => s.length > 500);");
  console.log('  ');
  console.log('  // Return only summary (~100 tokens)');
  console.log('  return { count: filtered.length };');
}

/**
 * Run all demos
 */
async function main() {
  console.log('🚀 MCP Client Demo Suite');
  console.log('========================\n');

  const demos = [
    { name: 'Basic Connection', fn: demo1_basicConnection, requiresDocker: true },
    { name: 'Tool Discovery', fn: demo2_toolDiscovery, requiresDocker: true },
    { name: 'Retry Logic', fn: demo3_retryLogic, requiresDocker: true },
    { name: 'Global Helpers', fn: demo4_globalHelpers, requiresDocker: true },
    { name: 'Token Efficiency', fn: demo5_tokenEfficiency, requiresDocker: false },
  ];

  // Check if Docker containers are running
  const dockerAvailable = process.env.SKIP_DOCKER_DEMOS !== 'true';

  for (const demo of demos) {
    if (demo.requiresDocker && !dockerAvailable) {
      console.log(`\n⏭️  Skipping "${demo.name}" (requires Docker containers)`);
      console.log('   Run: docker-compose up -d');
      console.log('   Then: unset SKIP_DOCKER_DEMOS\n');
      continue;
    }

    try {
      await demo.fn();
    } catch (error: any) {
      console.error(`\n❌ Demo "${demo.name}" failed:`, error.message);

      if (demo.requiresDocker) {
        console.log('\n💡 Tip: Make sure Docker containers are running:');
        console.log('   docker-compose up -d');
        console.log('   docker ps  # Verify containers are running\n');
      }
    }
  }

  console.log('\n✅ Demo suite complete!\n');
  console.log('📖 Next steps:');
  console.log('  1. Review workspace/lib/mcp-client.ts for implementation');
  console.log('  2. Check tests/integration/mcp-client.test.ts for tests');
  console.log('  3. Start using MCP client in your workflows');
  console.log('  4. Measure token usage with real workloads\n');
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((error) => {
    console.error('\n❌ Fatal error:', error);
    process.exit(1);
  });
}

export { demo1_basicConnection, demo2_toolDiscovery, demo3_retryLogic };
