/**
 * Logger
 * 
 * Structured logging system with log levels and context
 */

/**
 * Log levels
 */
export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3,
  NONE = 4,
}

/**
 * Log entry structure
 */
export interface ILogEntry {
  timestamp: string;
  level: LogLevel;
  levelName: string;
  component: string;
  message: string;
  context?: Record<string, unknown>;
  error?: {
    name: string;
    message: string;
    stack?: string;
    code?: number;
  };
}

/**
 * Log destination
 */
export type LogDestination = "stdout" | "stderr" | "none";

/**
 * Logger configuration
 */
export interface ILoggerConfig {
  minLevel: LogLevel;
  destination: LogDestination;
  pretty: boolean;
}

/**
 * Logger class
 */
export class Logger {
  private static globalConfig: ILoggerConfig = {
    minLevel: LogLevel.INFO,
    destination: "stderr",
    pretty: false
  };
  
  /**
   * Configure global logger settings
   */
  static configure(config: Partial<ILoggerConfig>) {
    Logger.globalConfig = {
      ...Logger.globalConfig,
      ...config
    };
  }
  
  /**
   * Get log level from environment
   */
  static getLogLevelFromEnv(): LogLevel {
    const level = process.env.LOG_LEVEL?.toUpperCase();
    switch (level) {
      case 'DEBUG': return LogLevel.DEBUG;
      case 'INFO': return LogLevel.INFO;
      case 'WARN': return LogLevel.WARN;
      case 'ERROR': return LogLevel.ERROR;
      case 'NONE': return LogLevel.NONE;
      default: return LogLevel.INFO;
    }
  }
  
  private component: string;
  private config: ILoggerConfig;
  
  constructor(component: string, config?: Partial<ILoggerConfig>) {
    this.component = component;
    this.config = {
      ...Logger.globalConfig,
      ...config
    };
  }
  
  /**
   * Log debug message
   */
  debug(message: string, context?: Record<string, unknown>) {
    this.log(LogLevel.DEBUG, message, context);
  }
  
  /**
   * Log info message
   */
  info(message: string, context?: Record<string, unknown>) {
    this.log(LogLevel.INFO, message, context);
  }
  
  /**
   * Log warning message
   */
  warn(message: string, context?: Record<string, unknown>) {
    this.log(LogLevel.WARN, message, context);
  }
  
  /**
   * Log error message
   */
  error(message: string, error?: Error, context?: Record<string, unknown>) {
    const errorData = error ? {
      name: error.name,
      message: error.message,
      stack: error.stack,
      code: (error as any).code
    } : undefined;
    
    this.log(LogLevel.ERROR, message, {
      ...context,
      error: errorData
    });
  }
  
  /**
   * Internal log method
   */
  private log(level: LogLevel, message: string, context?: Record<string, unknown>) {
    // Check if we should log this level
    if (level < this.config.minLevel) {
      return;
    }
    
    // Skip if destination is none
    if (this.config.destination === "none") {
      return;
    }
    
    const entry: ILogEntry = {
      timestamp: new Date().toISOString(),
      level,
      levelName: LogLevel[level],
      component: this.component,
      message,
      context: this.sanitizeContext(context)
    };
    
    // Format output
    const output = this.formatEntry(entry);
    
    // Write to destination
    const stream = this.config.destination === "stdout" ? process.stdout : process.stderr;
    stream.write(output + '\n');
  }
  
  /**
   * Format log entry
   */
  private formatEntry(entry: ILogEntry): string {
    if (this.config.pretty) {
      return this.formatPretty(entry);
    } else {
      return JSON.stringify(entry);
    }
  }
  
  /**
   * Format log entry in human-readable format
   */
  private formatPretty(entry: ILogEntry): string {
    const { timestamp, levelName, component, message, context } = entry;
    
    let output = `${timestamp} [${levelName}] [${component}] ${message}`;
    
    if (context && Object.keys(context).length > 0) {
      output += '\n  ' + JSON.stringify(context, null, 2).replace(/\n/g, '\n  ');
    }
    
    return output;
  }
  
  /**
   * Sanitize context to remove sensitive data
   */
  private sanitizeContext(context?: Record<string, unknown>): Record<string, unknown> | undefined {
    if (!context) return undefined;
    
    const sanitized: Record<string, unknown> = {};
    const sensitiveKeys = ['password', 'token', 'secret', 'apiKey', 'api_key'];
    
    for (const [key, value] of Object.entries(context)) {
      if (sensitiveKeys.some(k => key.toLowerCase().includes(k))) {
        sanitized[key] = '[REDACTED]';
      } else {
        sanitized[key] = value;
      }
    }
    
    return sanitized;
  }
  
  /**
   * Create a child logger with a sub-component name
   */
  child(subComponent: string): Logger {
    return new Logger(`${this.component}.${subComponent}`, this.config);
  }
}

/**
 * Performance tracking utility
 */
export class PerformanceTracker {
  private spans: Map<string, number> = new Map();
  private logger: Logger;
  
  constructor(component: string = 'Performance') {
    this.logger = new Logger(component);
  }
  
  /**
   * Start a performance span
   */
  startSpan(name: string) {
    this.spans.set(name, Date.now());
  }
  
  /**
   * End a performance span and log duration
   */
  endSpan(name: string): number {
    const start = this.spans.get(name);
    if (!start) {
      this.logger.warn(`Span '${name}' was never started`);
      return 0;
    }
    
    const duration = Date.now() - start;
    this.spans.delete(name);
    
    this.logger.debug(`Span '${name}' completed`, { duration });
    
    return duration;
  }
  
  /**
   * Measure an async function
   */
  async measureAsync<T>(name: string, fn: () => Promise<T>): Promise<T> {
    this.startSpan(name);
    try {
      return await fn();
    } finally {
      this.endSpan(name);
    }
  }
  
  /**
   * Measure a sync function
   */
  measure<T>(name: string, fn: () => T): T {
    this.startSpan(name);
    try {
      return fn();
    } finally {
      this.endSpan(name);
    }
  }
}

// Initialize global logger from environment
Logger.configure({
  minLevel: Logger.getLogLevelFromEnv(),
  destination: (process.env.LOG_DESTINATION as LogDestination) || "stderr",
  pretty: process.env.LOG_PRETTY === "true"
});

/**
 * Global logger instance
 */
export const logger = new Logger('MCP');

/**
 * Global performance tracker
 */
export const perf = new PerformanceTracker();

