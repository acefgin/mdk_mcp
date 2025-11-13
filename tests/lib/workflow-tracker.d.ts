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
export declare class WorkflowTracker {
    private metrics;
    private currentCalls;
    constructor(workflowName: string);
    /**
     * Track a tool call
     *
     * @param serverName - Server name
     * @param toolName - Tool name
     * @param startTime - Call start time
     */
    startToolCall(serverName: string, toolName: string): number;
    /**
     * End a tool call and record metrics
     *
     * @param serverName - Server name
     * @param toolName - Tool name
     */
    endToolCall(serverName: string, toolName: string): void;
    /**
     * Finish tracking and calculate final metrics
     *
     * @returns Final workflow metrics
     */
    finish(): WorkflowMetrics;
    /**
     * Get current metrics snapshot
     *
     * @returns Current metrics
     */
    getMetrics(): WorkflowMetrics;
    /**
     * Get list of tool names used
     *
     * @returns Array of tool names
     */
    getToolNames(): string[];
    /**
     * Get list of server names used
     *
     * @returns Array of unique server names
     */
    getServerNames(): string[];
    /**
     * Get most used tools
     *
     * @param limit - Number of tools to return
     * @returns Array of tool usage records sorted by call count
     */
    getMostUsedTools(limit?: number): ToolUsage[];
    /**
     * Print summary report
     */
    printSummary(): void;
}
/**
 * Create a tracked workflow wrapper
 *
 * @param workflowName - Workflow name
 * @param workflowFn - Workflow function to track
 * @returns Wrapped workflow function with tracking
 */
export declare function trackWorkflow<T>(workflowName: string, workflowFn: (tracker: WorkflowTracker) => Promise<T>): () => Promise<{
    result: T;
    metrics: WorkflowMetrics;
}>;
/**
 * Compare two workflow runs
 *
 * @param baseline - Baseline workflow metrics
 * @param optimized - Optimized workflow metrics
 * @returns Comparison report
 */
export declare function compareWorkflows(baseline: WorkflowMetrics, optimized: WorkflowMetrics): {
    timeReduction: number;
    callReduction: number;
    toolReduction: number;
    message: string;
};
//# sourceMappingURL=workflow-tracker.d.ts.map