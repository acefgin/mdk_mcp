/**
 * PII Tokenization Demo
 *
 * Demonstrates privacy-preserving operations with PIITokenizer.
 *
 * Usage:
 * ```bash
 * npx tsx examples/pii-tokenization-demo.ts
 * ```
 */

import { PIITokenizer } from '../workspace/lib/mcp-client.js';

/**
 * Demo 1: Basic Email and Phone Tokenization
 */
function demo1_basicTokenization() {
  console.log('\n📧 Demo 1: Basic Email and Phone Tokenization\n');

  const tokenizer = new PIITokenizer();

  // Original data with PII
  const originalData = {
    user: 'John Doe',
    email: 'john.doe@example.com',
    phone: '555-123-4567',
    message: 'Please contact me at john.doe@example.com or 555-123-4567',
  };

  console.log('Original Data:');
  console.log(JSON.stringify(originalData, null, 2));

  // Tokenize
  const tokenized = tokenizer.tokenize(originalData);

  console.log('\n✅ Tokenized Data:');
  console.log(JSON.stringify(tokenized, null, 2));

  // Detokenize
  const detokenized = tokenizer.detokenize(tokenized);

  console.log('\n🔓 Detokenized Data:');
  console.log(JSON.stringify(detokenized, null, 2));

  // Verify
  console.log('\n✅ Verification:');
  console.log(`  Match: ${JSON.stringify(originalData) === JSON.stringify(detokenized)}`);
}

/**
 * Demo 2: Multiple PII Types
 */
function demo2_multiplePIITypes() {
  console.log('\n🔐 Demo 2: Multiple PII Types\n');

  const tokenizer = new PIITokenizer();

  const sensitiveData = {
    customer: {
      name: 'Jane Smith',
      email: 'jane.smith@company.com',
      phone: '555-987-6543',
      ssn: '123-45-6789',
      creditCard: '4532-1234-5678-9010',
    },
    server: {
      ipAddress: '192.168.1.100',
      apiKey: 'sk_live_EXAMPLE_NOT_REAL_KEY_123456',
    },
  };

  console.log('Original Sensitive Data:');
  console.log(JSON.stringify(sensitiveData, null, 2));

  const tokenized = tokenizer.tokenize(sensitiveData);

  console.log('\n✅ Tokenized (Safe to send to AI model):');
  console.log(JSON.stringify(tokenized, null, 2));

  // Statistics
  const stats = tokenizer.getStats();
  console.log('\n📊 Tokenization Statistics:');
  console.log(`  Total items tokenized: ${stats.totalTokenized}`);
  console.log('  By type:');
  Object.entries(stats.tokenizedByType).forEach(([type, count]) => {
    console.log(`    ${type}: ${count}`);
  });
}

/**
 * Demo 3: Audit Logging
 */
function demo3_auditLogging() {
  console.log('\n📋 Demo 3: Audit Logging\n');

  const tokenizer = new PIITokenizer();

  // Perform various operations
  tokenizer.tokenize('user1@example.com');
  tokenizer.tokenize('user2@example.com');
  tokenizer.tokenize('555-111-2222');

  const token1 = tokenizer.tokenize('admin@company.com');
  tokenizer.detokenize(token1);

  // Get audit log
  const log = tokenizer.getAuditLog();

  console.log('Audit Log:');
  log.forEach((entry, index) => {
    console.log(`  ${index + 1}. [${entry.timestamp.toISOString()}]`);
    console.log(`     Action: ${entry.action}`);
    console.log(`     Type: ${entry.type}`);
    console.log(`     Count: ${entry.count}`);
  });

  console.log('\n📊 Summary:');
  console.log(`  Total log entries: ${log.length}`);
  console.log(
    `  Tokenize operations: ${log.filter((e) => e.action === 'tokenize').length}`
  );
  console.log(
    `  Detokenize operations: ${log.filter((e) => e.action === 'detokenize').length}`
  );
}

/**
 * Demo 4: Persistence (Export/Import)
 */
function demo4_persistence() {
  console.log('\n💾 Demo 4: Mapping Persistence\n');

  // Tokenizer 1: Create and tokenize
  const tokenizer1 = new PIITokenizer();
  const original = {
    email: 'persistent@example.com',
    phone: '555-PERSIST',
  };

  console.log('Step 1: Tokenize with first instance');
  const tokenized = tokenizer1.tokenize(original);
  console.log(JSON.stringify(tokenized, null, 2));

  // Export mapping
  console.log('\nStep 2: Export mapping');
  const mapping = tokenizer1.exportMapping();
  console.log(`  Exported ${mapping.tokenMap.length} token mappings`);

  // Simulate saving to file/database
  const serialized = JSON.stringify(mapping);
  console.log(`  Serialized size: ${serialized.length} bytes`);

  // Tokenizer 2: Import and detokenize
  console.log('\nStep 3: Import mapping in new instance');
  const tokenizer2 = new PIITokenizer();
  tokenizer2.importMapping(mapping);

  console.log('\nStep 4: Detokenize with second instance');
  const detokenized = tokenizer2.detokenize(tokenized);
  console.log(JSON.stringify(detokenized, null, 2));

  console.log('\n✅ Verification:');
  console.log(`  Match: ${JSON.stringify(original) === JSON.stringify(detokenized)}`);
  console.log('  Use case: Persist tokens across API calls or sessions');
}

/**
 * Demo 5: Real-World Use Case - Database Query
 */
function demo5_realWorldUseCase() {
  console.log('\n🌍 Demo 5: Real-World Use Case - Bioinformatics Workflow\n');

  const tokenizer = new PIITokenizer();

  // Original workflow request with researcher PII
  const workflowRequest = {
    project: 'Salmon Primer Design',
    researcher: {
      name: 'Dr. Sarah Johnson',
      email: 'sarah.johnson@university.edu',
      institution: 'Marine Biology Institute',
    },
    samples: [
      {
        sampleId: 'FISH-001',
        collectedBy: 'john.field@lab.org',
        location: 'Site A',
        notes: 'Contact field team at 555-FIELD-1',
      },
      {
        sampleId: 'FISH-002',
        collectedBy: 'mary.tech@lab.org',
        location: 'Site B',
        notes: 'Lab questions: 555-LAB-HELP',
      },
    ],
    parameters: {
      taxon: 'Salmo salar',
      region: 'COI',
      primerLength: [18, 22, 25],
    },
  };

  console.log('🔬 Original Workflow Request (contains PII):');
  console.log(JSON.stringify(workflowRequest, null, 2));

  // Tokenize before sending to AI model
  const tokenizedRequest = tokenizer.tokenize(workflowRequest);

  console.log('\n✅ Tokenized Request (safe for AI processing):');
  console.log(JSON.stringify(tokenizedRequest, null, 2));

  // Simulate AI processing (AI sees tokenized data)
  console.log('\n🤖 AI processes tokenized data...');
  const aiResponse = {
    status: 'success',
    primers: ['ATCGATCGATCG', 'GCTAGCTAGCTA'],
    researcher: tokenizedRequest.researcher.email, // AI returns token
    samples: tokenizedRequest.samples.map((s) => ({
      id: s.sampleId,
      contact: s.collectedBy, // AI returns token
    })),
  };

  console.log('  AI response (still tokenized):');
  console.log(JSON.stringify(aiResponse, null, 2));

  // Detokenize before returning to user
  const detokenizedResponse = tokenizer.detokenize(aiResponse);

  console.log('\n🔓 Final Response (PII restored):');
  console.log(JSON.stringify(detokenizedResponse, null, 2));

  console.log('\n✅ Result:');
  console.log('  ✓ Researcher email never exposed to AI model');
  console.log('  ✓ Field team contacts kept private');
  console.log('  ✓ Lab phone numbers not in AI context');
  console.log('  ✓ Workflow completed successfully');

  // Statistics
  const stats = tokenizer.getStats();
  console.log('\n📊 Privacy Protection Stats:');
  console.log(`  Total PII items protected: ${stats.totalTokenized}`);
  console.log('  Breakdown:');
  Object.entries(stats.tokenizedByType).forEach(([type, count]) => {
    console.log(`    ${type}: ${count}`);
  });
}

/**
 * Demo 6: Integration with MCP Client
 */
function demo6_mcpIntegration() {
  console.log('\n🔌 Demo 6: Integration with MCP Client\n');

  console.log('MCP Client with PII Tokenization:');
  console.log('');
  console.log('// Enable tokenization when creating client');
  console.log('const client = new MCPCodeExecutionClient(');
  console.log('  serverConfigs,');
  console.log('  true  // ← Enable PII tokenization');
  console.log(');');
  console.log('');
  console.log('await client.initialize();');
  console.log('');
  console.log('// Call tool with PII (will be tokenized automatically)');
  console.log("const result = await client.callTool('database__search', {");
  console.log("  researcher_email: 'researcher@university.edu',  // ← Tokenized");
  console.log("  contact_phone: '555-123-4567',  // ← Tokenized");
  console.log("  query: 'Salmo salar primers'");
  console.log('});');
  console.log('');
  console.log('// Result is automatically detokenized before returning');
  console.log('console.log(result);  // PII restored');
  console.log('');
  console.log('✅ Benefits:');
  console.log('  • Automatic PII protection');
  console.log('  • No manual tokenization needed');
  console.log('  • Transparent to tool implementations');
  console.log('  • Audit logging included');
  console.log('  • Zero PII leakage to AI models');
}

/**
 * Demo 7: Security Best Practices
 */
function demo7_securityBestPractices() {
  console.log('\n🔒 Demo 7: Security Best Practices\n');

  const tokenizer = new PIITokenizer();

  console.log('1. Tokenize before logging:');
  const sensitiveLog = {
    event: 'user_login',
    user_email: 'user@example.com',
    timestamp: new Date().toISOString(),
  };
  const safeLog = tokenizer.tokenize(sensitiveLog);
  console.log(`   Original: ${JSON.stringify(sensitiveLog)}`);
  console.log(`   Safe log: ${JSON.stringify(safeLog)}`);

  console.log('\n2. Consistent tokenization:');
  const email = 'same@example.com';
  const token1 = tokenizer.tokenize(email);
  const token2 = tokenizer.tokenize(email);
  console.log(`   Same email → same token: ${token1 === token2}`);

  console.log('\n3. Export mapping for distributed systems:');
  const mapping = tokenizer.exportMapping();
  console.log(`   Mapping size: ${JSON.stringify(mapping).length} bytes`);
  console.log('   Use case: Share across microservices');

  console.log('\n4. Audit trail:');
  const log = tokenizer.getAuditLog(5);
  console.log(`   Recent operations: ${log.length}`);
  console.log('   Use case: Compliance reporting');

  console.log('\n5. Clear sensitive data:');
  console.log(`   Before clear: ${tokenizer.getStats().totalTokenized} tokens`);
  tokenizer.clear();
  console.log(`   After clear: ${tokenizer.getStats().totalTokenized} tokens`);
  console.log('   Use case: Session cleanup');
}

/**
 * Run all demos
 */
function main() {
  console.log('🔐 PII Tokenization Demo Suite');
  console.log('==============================\n');

  const demos = [
    { name: 'Basic Tokenization', fn: demo1_basicTokenization },
    { name: 'Multiple PII Types', fn: demo2_multiplePIITypes },
    { name: 'Audit Logging', fn: demo3_auditLogging },
    { name: 'Persistence', fn: demo4_persistence },
    { name: 'Real-World Use Case', fn: demo5_realWorldUseCase },
    { name: 'MCP Integration', fn: demo6_mcpIntegration },
    { name: 'Security Best Practices', fn: demo7_securityBestPractices },
  ];

  for (const demo of demos) {
    try {
      demo.fn();
    } catch (error: any) {
      console.error(`\n❌ Demo "${demo.name}" failed:`, error.message);
    }
  }

  console.log('\n\n✅ Demo suite complete!\n');
  console.log('📖 Key Takeaways:');
  console.log('  • PII is automatically detected and tokenized');
  console.log('  • Bidirectional: tokenize → process → detokenize');
  console.log('  • Supports emails, phones, SSN, credit cards, IPs, API keys');
  console.log('  • Nested objects and arrays handled recursively');
  console.log('  • Audit logging for compliance');
  console.log('  • Mapping persistence for distributed systems');
  console.log('  • Zero PII exposure to AI models');
  console.log('\n📚 Next steps:');
  console.log('  1. Review workspace/lib/mcp-client.ts (PIITokenizer class)');
  console.log('  2. Check tests/unit/pii-tokenizer.test.ts for tests');
  console.log('  3. Enable tokenization in MCP client');
  console.log('  4. Review docs/SECURITY.md for security guidelines\n');
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

export {
  demo1_basicTokenization,
  demo2_multiplePIITypes,
  demo3_auditLogging,
  demo4_persistence,
  demo5_realWorldUseCase,
};
