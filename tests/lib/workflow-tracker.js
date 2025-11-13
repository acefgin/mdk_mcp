"use strict";
/**
 * Workflow Tracker Utility
 *
 * Tracks tool usage during workflow execution for benchmarking.
 * Helps measure progressive tool disclosure effectiveness.
 */
var __assign = (this && this.__assign) || function () {
    __assign = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign.apply(this, arguments);
};
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g = Object.create((typeof Iterator === "function" ? Iterator : Object).prototype);
    return g.next = verb(0), g["throw"] = verb(1), g["return"] = verb(2), typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.WorkflowTracker = void 0;
exports.trackWorkflow = trackWorkflow;
exports.compareWorkflows = compareWorkflows;
/**
 * Workflow Tracker
 *
 * Tracks tool usage and timing during workflow execution
 */
var WorkflowTracker = /** @class */ (function () {
    function WorkflowTracker(workflowName) {
        this.currentCalls = new Map();
        this.metrics = {
            workflowName: workflowName,
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
    WorkflowTracker.prototype.startToolCall = function (serverName, toolName) {
        var startTime = Date.now();
        var key = "".concat(serverName, ".").concat(toolName);
        this.currentCalls.set(key, startTime);
        return startTime;
    };
    /**
     * End a tool call and record metrics
     *
     * @param serverName - Server name
     * @param toolName - Tool name
     */
    WorkflowTracker.prototype.endToolCall = function (serverName, toolName) {
        var key = "".concat(serverName, ".").concat(toolName);
        var startTime = this.currentCalls.get(key);
        if (!startTime) {
            console.warn("No start time found for ".concat(key));
            return;
        }
        var endTime = Date.now();
        var callTime = endTime - startTime;
        // Get or create tool usage record
        var usage = this.metrics.toolsUsed.get(key);
        if (!usage) {
            usage = {
                toolName: toolName,
                serverName: serverName,
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
    };
    /**
     * Finish tracking and calculate final metrics
     *
     * @returns Final workflow metrics
     */
    WorkflowTracker.prototype.finish = function () {
        this.metrics.endTime = Date.now();
        this.metrics.totalTime = this.metrics.endTime - this.metrics.startTime;
        this.metrics.uniqueTools = this.metrics.toolsUsed.size;
        return this.metrics;
    };
    /**
     * Get current metrics snapshot
     *
     * @returns Current metrics
     */
    WorkflowTracker.prototype.getMetrics = function () {
        return __assign(__assign({}, this.metrics), { uniqueTools: this.metrics.toolsUsed.size });
    };
    /**
     * Get list of tool names used
     *
     * @returns Array of tool names
     */
    WorkflowTracker.prototype.getToolNames = function () {
        return Array.from(this.metrics.toolsUsed.values()).map(function (u) { return u.toolName; });
    };
    /**
     * Get list of server names used
     *
     * @returns Array of unique server names
     */
    WorkflowTracker.prototype.getServerNames = function () {
        var servers = new Set(Array.from(this.metrics.toolsUsed.values()).map(function (u) { return u.serverName; }));
        return Array.from(servers);
    };
    /**
     * Get most used tools
     *
     * @param limit - Number of tools to return
     * @returns Array of tool usage records sorted by call count
     */
    WorkflowTracker.prototype.getMostUsedTools = function (limit) {
        if (limit === void 0) { limit = 5; }
        return Array.from(this.metrics.toolsUsed.values())
            .sort(function (a, b) { return b.callCount - a.callCount; })
            .slice(0, limit);
    };
    /**
     * Print summary report
     */
    WorkflowTracker.prototype.printSummary = function () {
        var metrics = this.getMetrics();
        console.log("\n".concat('='.repeat(60)));
        console.log("Workflow: ".concat(metrics.workflowName));
        console.log("".concat('='.repeat(60)));
        console.log("Total Time:      ".concat((metrics.totalTime / 1000).toFixed(2), "s"));
        console.log("Total Calls:     ".concat(metrics.totalCalls));
        console.log("Unique Tools:    ".concat(metrics.uniqueTools));
        console.log("Servers Used:    ".concat(this.getServerNames().join(', ')));
        console.log("\nMost Used Tools:");
        this.getMostUsedTools(5).forEach(function (tool, i) {
            console.log("  ".concat(i + 1, ". ").concat(tool.serverName, ".").concat(tool.toolName, " - ").concat(tool.callCount, " calls (avg ").concat(tool.averageTime.toFixed(0), "ms)"));
        });
        console.log("".concat('='.repeat(60), "\n"));
    };
    return WorkflowTracker;
}());
exports.WorkflowTracker = WorkflowTracker;
/**
 * Create a tracked workflow wrapper
 *
 * @param workflowName - Workflow name
 * @param workflowFn - Workflow function to track
 * @returns Wrapped workflow function with tracking
 */
function trackWorkflow(workflowName, workflowFn) {
    var _this = this;
    return function () { return __awaiter(_this, void 0, void 0, function () {
        var tracker, result, metrics, error_1;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    tracker = new WorkflowTracker(workflowName);
                    _a.label = 1;
                case 1:
                    _a.trys.push([1, 3, , 4]);
                    return [4 /*yield*/, workflowFn(tracker)];
                case 2:
                    result = _a.sent();
                    metrics = tracker.finish();
                    return [2 /*return*/, { result: result, metrics: metrics }];
                case 3:
                    error_1 = _a.sent();
                    tracker.finish();
                    throw error_1;
                case 4: return [2 /*return*/];
            }
        });
    }); };
}
/**
 * Compare two workflow runs
 *
 * @param baseline - Baseline workflow metrics
 * @param optimized - Optimized workflow metrics
 * @returns Comparison report
 */
function compareWorkflows(baseline, optimized) {
    var timeReduction = ((baseline.totalTime - optimized.totalTime) / baseline.totalTime) * 100;
    var callReduction = ((baseline.totalCalls - optimized.totalCalls) / baseline.totalCalls) * 100;
    var toolReduction = ((baseline.uniqueTools - optimized.uniqueTools) / baseline.uniqueTools) * 100;
    return {
        timeReduction: timeReduction,
        callReduction: callReduction,
        toolReduction: toolReduction,
        message: "Optimized workflow is ".concat(timeReduction.toFixed(1), "% faster (").concat(baseline.totalTime, "ms \u2192 ").concat(optimized.totalTime, "ms)"),
    };
}
//# sourceMappingURL=workflow-tracker.js.map