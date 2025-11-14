/**
 * Workflow Tracker Utility
 *
 * Tracks tool usage during workflow execution for benchmarking.
 * Helps measure progressive tool disclosure effectiveness.
 */

export interface ToolUsage {
  toolName: string;
  serverName: string;
  callCount: number;
  firstCalled: number;
  lastCalled: number;
  totalTime: number;
  averageTime: number;
}

export interface WorkflowMetrics {
  workflowName: string;
  startTime: number;
  endTime: number;
  totalTime: number;
  toolsUsed: Map<string, ToolUsage>;
  totalCalls: number;
  uniqueTools: number;
}

/**
 * Workflow Tracker
 *
 * Tracks tool usage and timing during workflow execution
 */
export class WorkflowTracker {
  private metrics: WorkflowMetrics;
  private currentCalls: Map<string, number> = new Map();

  constructor(workflowName: string) {
    this.metrics = {
      workflowName,
      startTime: Date.now(),
      endTime: 0,
      totalTime: 0,
      toolsUsed: new Map(),
      totalCalls: 0,
      uniqueTools: 0,
    };
  }

  /**
   * Track a tool call
   *
   * @param serverName - Server name
   * @param toolName - Tool name
   * @param startTime - Call start time
   */
  startToolCall(serverName: string, toolName: string): number {
    const startTime = Date.now();
    const key = `${serverName}.${toolName}`;
    this.currentCalls.set(key, startTime);
    return startTime;
  }

  /**
   * End a tool call and record metrics
   *
   * @param serverName - Server name
   * @param toolName - Tool name
   */
  endToolCall(serverName: string, toolName: string): void {
    const key = `${serverName}.${toolName}`;
    const startTime = this.currentCalls.get(key);

    if (!startTime) {
      console.warn(`No start time found for ${key}`);
      return;
    }

    const endTime = Date.now();
    const callTime = endTime - startTime;

    // Get or create tool usage record
    let usage = this.metrics.toolsUsed.get(key);
    if (!usage) {
      usage = {
        toolName,
        serverName,
        callCount: 0,
        firstCalled: startTime,
        lastCalled: endTime,
        totalTime: 0,
        averageTime: 0,
      };
      this.metrics.toolsUsed.set(key, usage);
    }

    // Update usage metrics
    usage.callCount++;
    usage.lastCalled = endTime;
    usage.totalTime += callTime;
    usage.averageTime = usage.totalTime / usage.callCount;

    this.metrics.totalCalls++;
    this.currentCalls.delete(key);
  }

  /**
   * Finish tracking and calculate final metrics
   *
   * @returns Final workflow metrics
   */
  finish(): WorkflowMetrics {
    this.metrics.endTime = Date.now();
    this.metrics.totalTime = this.metrics.endTime - this.metrics.startTime;
    this.metrics.uniqueTools = this.metrics.toolsUsed.size;
    return this.metrics;
  }

  /**
   * Get current metrics snapshot
   *
   * @returns Current metrics
   */
  getMetrics(): WorkflowMetrics {
    return {
      ...this.metrics,
      uniqueTools: this.metrics.toolsUsed.size,
    };
  }

  /**
   * Get list of tool names used
   *
   * @returns Array of tool names
   */
  getToolNames(): string[] {
    return Array.from(this.metrics.toolsUsed.values()).map((u) => u.toolName);
  }

  /**
   * Get list of server names used
   *
   * @returns Array of unique server names
   */
  getServerNames(): string[] {
    const servers = new Set(
      Array.from(this.metrics.toolsUsed.values()).map((u) => u.serverName)
    );
    return Array.from(servers);
  }

  /**
   * Get most used tools
   *
   * @param limit - Number of tools to return
   * @returns Array of tool usage records sorted by call count
   */
  getMostUsedTools(limit: number = 5): ToolUsage[] {
    return Array.from(this.metrics.toolsUsed.values())
      .sort((a, b) => b.callCount - a.callCount)
      .slice(0, limit);
  }

  /**
   * Print summary report
   */
  printSummary(): void {
    const metrics = this.getMetrics();

    console.log(`\n${'='.repeat(60)}`);
    console.log(`Workflow: ${metrics.workflowName}`);
    console.log(`${'='.repeat(60)}`);
    console.log(`Total Time:      ${(metrics.totalTime / 1000).toFixed(2)}s`);
    console.log(`Total Calls:     ${metrics.totalCalls}`);
    console.log(`Unique Tools:    ${metrics.uniqueTools}`);
    console.log(`Servers Used:    ${this.getServerNames().join(', ')}`);

    console.log(`\nMost Used Tools:`);
    this.getMostUsedTools(5).forEach((tool, i) => {
      console.log(
        `  ${i + 1}. ${tool.serverName}.${tool.toolName} - ${tool.callCount} calls (avg ${tool.averageTime.toFixed(0)}ms)`
      );
    });

    console.log(`${'='.repeat(60)}\n`);
  }
}

/**
 * Create a tracked workflow wrapper
 *
 * @param workflowName - Workflow name
 * @param workflowFn - Workflow function to track
 * @returns Wrapped workflow function with tracking
 */
export function trackWorkflow<T>(
  workflowName: string,
  workflowFn: (tracker: WorkflowTracker) => Promise<T>
): () => Promise<{ result: T; metrics: WorkflowMetrics }> {
  return async () => {
    const tracker = new WorkflowTracker(workflowName);

    try {
      const result = await workflowFn(tracker);
      const metrics = tracker.finish();
      return { result, metrics };
    } catch (error) {
      tracker.finish();
      throw error;
    }
  };
}

/**
 * Compare two workflow runs
 *
 * @param baseline - Baseline workflow metrics
 * @param optimized - Optimized workflow metrics
 * @returns Comparison report
 */
export function compareWorkflows(
  baseline: WorkflowMetrics,
  optimized: WorkflowMetrics
): {
  timeReduction: number;
  callReduction: number;
  toolReduction: number;
  message: string;
} {
  const timeReduction =
    ((baseline.totalTime - optimized.totalTime) / baseline.totalTime) * 100;
  const callReduction =
    ((baseline.totalCalls - optimized.totalCalls) / baseline.totalCalls) * 100;
  const toolReduction =
    ((baseline.uniqueTools - optimized.uniqueTools) / baseline.uniqueTools) * 100;

  return {
    timeReduction,
    callReduction,
    toolReduction,
    message: `Optimized workflow is ${timeReduction.toFixed(1)}% faster (${baseline.totalTime}ms → ${optimized.totalTime}ms)`,
  };
}
