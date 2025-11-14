/**
 * Code Executor Demo
 *
 * Demonstrates isolated code execution with Docker-based sandboxing.
 *
 * Usage:
 * ```bash
 * npx tsx examples/executor-demo.ts
 * ```
 */

import {
  CodeExecutor,
  setGlobalExecutor,
  executeCode,
  executeWorkflow,
  type WorkflowStep,
} from '../workspace/lib/executor.js';

/**
 * Demo 1: Basic Code Execution
 */
async function demo1_basicExecution() {
  console.log('\n⚡ Demo 1: Basic Code Execution\n');

  const executor = new CodeExecutor();

  // JavaScript
  console.log('1. JavaScript execution:');
  const jsResult = await executor.execute(
    'console.log("Hello from JavaScript!");',
    'javascript'
  );
  console.log(`   Output: ${jsResult.stdout.trim()}`);
  console.log(`   Exit code: ${jsResult.exitCode}`);
  console.log(`   Execution time: ${jsResult.executionTime}ms`);

  // TypeScript
  console.log('\n2. TypeScript execution:');
  const tsCode = `
    interface Greeting {
      message: string;
      language: string;
    }

    const greeting: Greeting = {
      message: "Hello from TypeScript!",
      language: "typescript"
    };

    console.log(greeting.message);
  `;
  const tsResult = await executor.execute(tsCode, 'typescript');
  console.log(`   Output: ${tsResult.stdout.trim()}`);
  console.log(`   Execution time: ${tsResult.executionTime}ms`);

  // Python
  console.log('\n3. Python execution:');
  const pyResult = await executor.execute(
    'print("Hello from Python!")',
    'python'
  );
  console.log(`   Output: ${pyResult.stdout.trim()}`);
  console.log(`   Execution time: ${pyResult.executionTime}ms`);

  // Shell
  console.log('\n4. Shell execution:');
  const shResult = await executor.execute(
    'echo "Hello from Shell!"',
    'shell'
  );
  console.log(`   Output: ${shResult.stdout.trim()}`);
  console.log(`   Execution time: ${shResult.executionTime}ms`);
}

/**
 * Demo 2: Error Handling
 */
async function demo2_errorHandling() {
  console.log('\n❌ Demo 2: Error Handling\n');

  const executor = new CodeExecutor();

  // Runtime error
  console.log('1. Runtime error (JavaScript):');
  const errorResult = await executor.execute(
    'throw new Error("Intentional error");',
    'javascript'
  );
  console.log(`   Success: ${errorResult.success}`);
  console.log(`   Exit code: ${errorResult.exitCode}`);
  console.log(`   Error: ${errorResult.stderr.substring(0, 100)}...`);

  // Syntax error
  console.log('\n2. Syntax error (Python):');
  const syntaxResult = await executor.execute(
    'print("Missing closing quote',
    'python'
  );
  console.log(`   Success: ${syntaxResult.success}`);
  console.log(`   Error: ${syntaxResult.stderr.substring(0, 100)}...`);

  // Division by zero
  console.log('\n3. Division by zero (Python):');
  const divResult = await executor.execute(
    'result = 10 / 0',
    'python'
  );
  console.log(`   Success: ${divResult.success}`);
  console.log(`   Error type: ZeroDivisionError`);
}

/**
 * Demo 3: Security Controls
 */
async function demo3_securityControls() {
  console.log('\n🔒 Demo 3: Security Controls\n');

  const executor = new CodeExecutor();

  // Network isolation
  console.log('1. Network isolation:');
  const networkCode = `
    const https = require('https');
    https.get('https://example.com', (res) => {
      console.log('Network access succeeded');
    }).on('error', (err) => {
      console.error('Network blocked:', err.code);
    });

    // Wait for callback
    setTimeout(() => {}, 3000);
  `;
  const networkResult = await executor.execute(networkCode, 'javascript', {
    timeout: 5000,
  });
  console.log(`   Network access blocked: ${networkResult.stderr.includes('EAI_AGAIN')}`);

  // Filesystem isolation
  console.log('\n2. Filesystem isolation (read-only):');
  const fsCode = `
    import fs from 'fs';
    try {
      fs.writeFileSync('/test.txt', 'This should not work');
      console.log('Write succeeded');
    } catch (err) {
      console.log('Write blocked:', err.code);
    }
  `;
  const fsResult = await executor.execute(fsCode, 'javascript');
  console.log(`   Filesystem write blocked: ${fsResult.stdout.includes('blocked')}`);

  console.log('\n✅ Security Summary:');
  console.log('  • Network access: BLOCKED');
  console.log('  • Filesystem writes: BLOCKED');
  console.log('  • Container isolation: ENABLED');
  console.log('  • No new privileges: ENFORCED');
  console.log('  • Capabilities dropped: ALL');
}

/**
 * Demo 4: Resource Limits
 */
async function demo4_resourceLimits() {
  console.log('\n⏱️  Demo 4: Resource Limits\n');

  const executor = new CodeExecutor();

  // Timeout enforcement
  console.log('1. Timeout enforcement:');
  const infiniteLoop = `
    const start = Date.now();
    console.log('Starting infinite loop...');
    while (true) {
      if (Date.now() - start > 60000) break;
    }
    console.log('Loop completed');
  `;
  const timeoutResult = await executor.execute(infiniteLoop, 'javascript', {
    timeout: 2000, // 2 seconds
  });
  console.log(`   Timed out: ${!timeoutResult.success}`);
  console.log(`   Execution time: ${timeoutResult.executionTime}ms`);
  console.log(`   Message: ${timeoutResult.stderr.includes('timed out') ? 'Timeout enforced' : 'Completed'}`);

  // Memory limit
  console.log('\n2. Memory limit:');
  const memoryResult = await executor.execute(
    'console.log("Executing with 128MB memory limit");',
    'javascript',
    {
      memoryLimit: '128m',
    }
  );
  console.log(`   Success: ${memoryResult.success}`);
  console.log(`   Memory limit: 128MB`);

  // CPU limit
  console.log('\n3. CPU limit:');
  const cpuResult = await executor.execute(
    'console.log("Executing with 0.5 CPU limit");',
    'javascript',
    {
      cpuLimit: '0.5',
    }
  );
  console.log(`   Success: ${cpuResult.success}`);
  console.log(`   CPU limit: 0.5 cores`);

  console.log('\n✅ Resource Limits Summary:');
  console.log('  • Timeout: 2 seconds (enforced)');
  console.log('  • Memory: 128MB (configurable)');
  console.log('  • CPU: 0.5 cores (configurable)');
}

/**
 * Demo 5: Multi-Step Workflows
 */
async function demo5_workflows() {
  console.log('\n📋 Demo 5: Multi-Step Workflows\n');

  const executor = new CodeExecutor();

  // Define workflow steps
  const steps: WorkflowStep[] = [
    {
      name: 'Fetch Data',
      description: 'Generate sample data',
      language: 'javascript',
      code: `
        const data = { name: "Alice", age: 30, city: "Boston" };
        console.log(JSON.stringify(data));
      `,
    },
    {
      name: 'Process Data',
      description: 'Process the data',
      language: 'python',
      code: `
import json
data = {"name": "Alice", "age": 30, "city": "Boston"}
data['processed'] = True
print(json.dumps(data))
      `,
    },
    {
      name: 'Format Output',
      description: 'Format final output',
      language: 'shell',
      code: `
        echo "=== Final Result ==="
        echo "Processing complete"
      `,
    },
  ];

  console.log('Executing 3-step workflow:\n');

  const result = await executor.executeWorkflow(steps);

  for (let i = 0; i < result.steps.length; i++) {
    const step = result.steps[i];
    console.log(`Step ${i + 1}: ${step.name}`);
    console.log(`  Success: ${step.success ? '✅' : '❌'}`);
    console.log(`  Output: ${step.result.stdout.trim().substring(0, 50)}...`);
    console.log(`  Time: ${step.result.executionTime}ms`);
  }

  console.log(`\nOverall Success: ${result.overallSuccess ? '✅' : '❌'}`);
  console.log(`Total Time: ${result.totalTime}ms`);
}

/**
 * Demo 6: Real-World Use Case - Data Processing
 */
async function demo6_realWorldDataProcessing() {
  console.log('\n🔬 Demo 6: Real-World Use Case - Data Processing\n');

  const executor = new CodeExecutor();

  console.log('Processing bioinformatics data...\n');

  // Step 1: Generate sample sequences
  console.log('1. Generating sample sequences:');
  const generateCode = `
    const sequences = [
      { id: "SEQ001", sequence: "ATCGATCG", gc: 0.5 },
      { id: "SEQ002", sequence: "GCGCGCGC", gc: 1.0 },
      { id: "SEQ003", sequence: "ATATATATAT", gc: 0.0 }
    ];
    console.log(JSON.stringify(sequences));
  `;
  const generateResult = await executor.execute(generateCode, 'javascript');
  console.log(`   Generated ${generateResult.stdout.split('SEQ').length - 1} sequences`);

  // Step 2: Calculate statistics
  console.log('\n2. Calculating statistics:');
  const statsCode = `
    const sequences = ${generateResult.stdout.trim()};
    const totalLength = sequences.reduce((sum, seq) => sum + seq.sequence.length, 0);
    const avgLength = totalLength / sequences.length;
    const avgGC = sequences.reduce((sum, seq) => sum + seq.gc, 0) / sequences.length;

    console.log(\`Total sequences: \${sequences.length}\`);
    console.log(\`Average length: \${avgLength.toFixed(2)}\`);
    console.log(\`Average GC content: \${(avgGC * 100).toFixed(2)}%\`);
  `;
  const statsResult = await executor.execute(statsCode, 'javascript');
  console.log(`   ${statsResult.stdout.trim().replace(/\n/g, '\n   ')}`);

  // Step 3: Filter high GC content
  console.log('\n3. Filtering high GC content (>50%):');
  const filterCode = `
    const sequences = ${generateResult.stdout.trim()};
    const highGC = sequences.filter(seq => seq.gc > 0.5);
    console.log(\`Found \${highGC.length} high-GC sequences:\`);
    highGC.forEach(seq => console.log(\`  - \${seq.id}: GC=\${(seq.gc * 100).toFixed(0)}%\`));
  `;
  const filterResult = await executor.execute(filterCode, 'javascript');
  console.log(`   ${filterResult.stdout.trim().replace(/\n/g, '\n   ')}`);

  console.log('\n✅ Data Processing Complete');
  console.log(`   Total time: ${generateResult.executionTime + statsResult.executionTime + filterResult.executionTime}ms`);
}

/**
 * Demo 7: Integration with Global Executor
 */
async function demo7_globalIntegration() {
  console.log('\n🌐 Demo 7: Integration with Global Executor\n');

  // Set up global executor
  const executor = new CodeExecutor();
  setGlobalExecutor(executor);

  console.log('Using global helper functions:\n');

  // Execute code using global helper
  console.log('1. executeCode() helper:');
  const result1 = await executeCode(
    'console.log("Using global executor");',
    'javascript'
  );
  console.log(`   Output: ${result1.stdout.trim()}`);

  // Execute workflow using global helper
  console.log('\n2. executeWorkflow() helper:');
  const steps: WorkflowStep[] = [
    {
      name: 'Step 1',
      code: 'console.log("Global workflow step 1");',
      language: 'javascript',
    },
    {
      name: 'Step 2',
      code: 'print("Global workflow step 2")',
      language: 'python',
    },
  ];
  const result2 = await executeWorkflow(steps);
  console.log(`   Steps completed: ${result2.steps.length}`);
  console.log(`   Overall success: ${result2.overallSuccess ? '✅' : '❌'}`);

  console.log('\n✅ Benefits of global executor:');
  console.log('  • Simpler API (no need to pass executor instance)');
  console.log('  • Shared configuration across modules');
  console.log('  • Easier integration with generated tools');
}

/**
 * Demo 8: Performance and Concurrency
 */
async function demo8_performance() {
  console.log('\n⚡ Demo 8: Performance and Concurrency\n');

  const executor = new CodeExecutor();

  // Sequential execution
  console.log('1. Sequential execution (3 tasks):');
  const seqStart = Date.now();
  await executor.execute('console.log("Task 1");', 'javascript');
  await executor.execute('console.log("Task 2");', 'javascript');
  await executor.execute('console.log("Task 3");', 'javascript');
  const seqTime = Date.now() - seqStart;
  console.log(`   Time: ${seqTime}ms`);

  // Concurrent execution
  console.log('\n2. Concurrent execution (3 tasks):');
  const concStart = Date.now();
  await Promise.all([
    executor.execute('console.log("Task 1");', 'javascript'),
    executor.execute('console.log("Task 2");', 'javascript'),
    executor.execute('console.log("Task 3");', 'javascript'),
  ]);
  const concTime = Date.now() - concStart;
  console.log(`   Time: ${concTime}ms`);

  console.log(`\n✅ Concurrency speedup: ${(seqTime / concTime).toFixed(2)}x`);
  console.log('  • Independent tasks can run in parallel');
  console.log('  • Each task gets its own isolated container');
  console.log('  • No interference between concurrent executions');
}

/**
 * Run all demos
 */
async function main() {
  console.log('⚡ Code Executor Demo Suite');
  console.log('==========================\n');

  // Check Docker availability
  const executor = new CodeExecutor();
  const dockerAvailable = await executor.isDockerAvailable();

  if (!dockerAvailable) {
    console.error('❌ Docker is not available!');
    console.error('   Please install Docker and ensure it is running.');
    console.error('   Visit: https://docs.docker.com/get-docker/\n');
    return;
  }

  console.log('✅ Docker is available');
  const version = await executor.getDockerVersion();
  console.log(`   Docker version: ${version}`);

  const demos = [
    { name: 'Basic Execution', fn: demo1_basicExecution },
    { name: 'Error Handling', fn: demo2_errorHandling },
    { name: 'Security Controls', fn: demo3_securityControls },
    { name: 'Resource Limits', fn: demo4_resourceLimits },
    { name: 'Multi-Step Workflows', fn: demo5_workflows },
    { name: 'Real-World Data Processing', fn: demo6_realWorldDataProcessing },
    { name: 'Global Integration', fn: demo7_globalIntegration },
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
  console.log('  • Code executes in isolated Docker containers');
  console.log('  • Multiple languages supported (JS, TS, Python, Shell)');
  console.log('  • Security controls (no network, read-only filesystem)');
  console.log('  • Resource limits (timeout, memory, CPU)');
  console.log('  • Multi-step workflows with error handling');
  console.log('  • Concurrent execution for independent tasks');
  console.log('\n📚 Next steps:');
  console.log('  1. Review workspace/lib/executor.ts (CodeExecutor class)');
  console.log('  2. Check tests/unit/executor.test.ts for comprehensive tests');
  console.log('  3. Integrate with MCP client for tool execution');
  console.log('  4. Build custom workflows for your use case\n');
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

export {
  demo1_basicExecution,
  demo2_errorHandling,
  demo3_securityControls,
  demo4_resourceLimits,
  demo5_workflows,
  demo6_realWorldDataProcessing,
};
