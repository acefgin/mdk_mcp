/**
 * Error Classes
 * 
 * Standard error hierarchy for consistent error handling across the system
 */

import { MCPErrorCode } from './types/client.protocol.js';
import { IValidationError } from './types/tool.schema.js';

/**
 * Base error class for all MCP errors
 */
export class MCPError extends Error {
  constructor(
    message: string,
    public code: number,
    public data?: unknown
  ) {
    super(message);
    this.name = this.constructor.name;
    
    // Maintain proper stack trace for where our error was thrown (only available on V8)
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, this.constructor);
    }
  }
  
  /**
   * Convert to JSON for serialization
   */
  toJSON() {
    return {
      name: this.name,
      message: this.message,
      code: this.code,
      data: this.data,
      stack: this.stack
    };
  }
  
  /**
   * Convert to MCP error format
   */
  toMCPError() {
    return {
      code: this.code,
      message: this.message,
      data: this.data
    };
  }
}

/**
 * Validation error - input or output doesn't match schema
 */
export class ValidationError extends MCPError {
  constructor(message: string, public validationErrors: IValidationError[]) {
    super(message, MCPErrorCode.ValidationError, { errors: validationErrors });
  }
}

/**
 * Execution error - tool execution failed
 */
export class ExecutionError extends MCPError {
  constructor(message: string, details?: string) {
    super(message, MCPErrorCode.ExecutionError, { details });
  }
}

/**
 * Timeout error - execution exceeded time limit
 */
export class TimeoutError extends MCPError {
  constructor(timeout: number, operation?: string) {
    const msg = operation 
      ? `${operation} exceeded timeout of ${timeout}ms`
      : `Execution timeout after ${timeout}ms`;
    super(msg, MCPErrorCode.ExecutionTimeout, { timeout, operation });
  }
}

/**
 * Transport error - communication with MCP server failed
 */
export class TransportError extends MCPError {
  constructor(message: string, public transportType: string, details?: unknown) {
    super(message, MCPErrorCode.TransportError, { transportType, details });
  }
}

/**
 * Container error - Docker container issue
 */
export class ContainerError extends MCPError {
  constructor(message: string, public containerName: string, details?: unknown) {
    super(message, MCPErrorCode.ContainerError, { containerName, details });
  }
}

/**
 * Security violation error
 */
export class SecurityError extends MCPError {
  constructor(message: string, details?: unknown) {
    super(message, MCPErrorCode.SecurityViolation, details);
  }
}

/**
 * Output too large error
 */
export class OutputTooLargeError extends MCPError {
  constructor(actualSize: number, maxSize: number) {
    super(
      `Output size ${actualSize} bytes exceeds maximum ${maxSize} bytes`,
      MCPErrorCode.OutputTooLarge,
      { actualSize, maxSize }
    );
  }
}

/**
 * Parse error - invalid JSON-RPC
 */
export class ParseError extends MCPError {
  constructor(message: string, details?: unknown) {
    super(message, MCPErrorCode.ParseError, details);
  }
}

/**
 * Invalid request error
 */
export class InvalidRequestError extends MCPError {
  constructor(message: string, details?: unknown) {
    super(message, MCPErrorCode.InvalidRequest, details);
  }
}

/**
 * Method not found error
 */
export class MethodNotFoundError extends MCPError {
  constructor(method: string) {
    super(`Method '${method}' not found`, MCPErrorCode.MethodNotFound, { method });
  }
}

/**
 * Invalid params error
 */
export class InvalidParamsError extends MCPError {
  constructor(message: string, details?: unknown) {
    super(message, MCPErrorCode.InvalidParams, details);
  }
}

/**
 * Internal error
 */
export class InternalError extends MCPError {
  constructor(message: string, details?: unknown) {
    super(message, MCPErrorCode.InternalError, details);
  }
}

/**
 * Error handler with retry logic
 */
export class ErrorHandler {
  /**
   * Execute function with retry logic
   */
  async withRetry<T>(
    fn: () => Promise<T>,
    options: {
      maxRetries: number;
      backoffMs: number;
      shouldRetry?: (error: Error) => boolean;
      onRetry?: (error: Error, attempt: number) => void;
    }
  ): Promise<T> {
    const {
      maxRetries,
      backoffMs,
      shouldRetry = () => true,
      onRetry
    } = options;
    
    let lastError: Error;
    
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        return await fn();
      } catch (error) {
        lastError = error as Error;
        
        // Check if we should retry
        if (attempt === maxRetries || !shouldRetry(lastError)) {
          throw lastError;
        }
        
        // Call retry callback
        if (onRetry) {
          onRetry(lastError, attempt);
        }
        
        // Exponential backoff
        const delay = backoffMs * Math.pow(2, attempt);
        await this.delay(delay);
      }
    }
    
    throw lastError!;
  }
  
  /**
   * Execute function with timeout
   */
  async withTimeout<T>(
    fn: () => Promise<T>,
    timeoutMs: number,
    operation?: string
  ): Promise<T> {
    return Promise.race([
      fn(),
      new Promise<T>((_, reject) => {
        setTimeout(() => {
          reject(new TimeoutError(timeoutMs, operation));
        }, timeoutMs);
      })
    ]);
  }
  
  /**
   * Execute function with timeout and retry
   */
  async withTimeoutAndRetry<T>(
    fn: () => Promise<T>,
    options: {
      timeoutMs: number;
      maxRetries: number;
      backoffMs: number;
      operation?: string;
    }
  ): Promise<T> {
    return this.withRetry(
      () => this.withTimeout(fn, options.timeoutMs, options.operation),
      {
        maxRetries: options.maxRetries,
        backoffMs: options.backoffMs,
        shouldRetry: (error) => error instanceof TimeoutError
      }
    );
  }
  
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

/**
 * Convert unknown error to MCPError
 */
export function toMCPError(error: unknown): MCPError {
  if (error instanceof MCPError) {
    return error;
  }
  
  if (error instanceof Error) {
    return new InternalError(error.message, {
      name: error.name,
      stack: error.stack
    });
  }
  
  return new InternalError(String(error));
}

/**
 * Check if error is retryable
 */
export function isRetryableError(error: Error): boolean {
  return error instanceof TimeoutError
    || error instanceof TransportError
    || error instanceof ContainerError;
}

