/**
 * Base Tool Wrapper
 * 
 * Abstract base class for tool wrappers
 */

import {
  IToolWrapper,
  IToolMetadata,
  IToolSchema,
  IValidationResult
} from './types/index.js';
import { validator } from './validator.js';
import { InputSanitizer } from './sanitizer.js';
import { ValidationError } from './errors.js';
import { logger } from './logger.js';

/**
 * Abstract base class for tool wrappers
 */
export abstract class ToolWrapperBase<TInput = unknown, TOutput = unknown>
  implements IToolWrapper<TInput, TOutput> {
  
  /**
   * Tool name (must be implemented by subclass)
   */
  abstract readonly toolName: string;
  
  /**
   * Server name (must be implemented by subclass)
   */
  abstract readonly serverName: string;
  
  /**
   * Input schema (must be implemented by subclass)
   */
  abstract readonly inputSchema: IToolSchema;
  
  /**
   * Output schema (must be implemented by subclass)
   */
  abstract readonly outputSchema: IToolSchema;
  
  /**
   * Tool metadata (optional, can be overridden)
   */
  readonly metadata?: IToolMetadata;
  
  /**
   * Get full tool ID
   */
  get toolId(): string {
    return `${this.serverName}__${this.toolName}`;
  }
  
  /**
   * Execute the tool (must be implemented by subclass)
   */
  abstract execute(input: TInput): Promise<TOutput>;
  
  /**
   * Validate input against schema
   */
  validateInput(input: unknown): IValidationResult<TInput> {
    logger.debug(`Validating input for ${this.toolId}`, {
      input,
      schema: this.inputSchema
    });
    
    const result = validator.validate<TInput>(input, this.inputSchema);
    
    if (!result.valid) {
      logger.warn(`Input validation failed for ${this.toolId}`, {
        errors: result.errors
      });
    }
    
    return result;
  }
  
  /**
   * Validate output against schema
   */
  validateOutput(output: unknown): IValidationResult<TOutput> {
    logger.debug(`Validating output for ${this.toolId}`, {
      schema: this.outputSchema
    });
    
    const result = validator.validate<TOutput>(output, this.outputSchema);
    
    if (!result.valid) {
      logger.warn(`Output validation failed for ${this.toolId}`, {
        errors: result.errors
      });
    }
    
    return result;
  }
  
  /**
   * Sanitize input
   * 
   * Default implementation:
   * 1. Clone input
   * 2. Sanitize strings
   * 3. Coerce types based on schema
   */
  sanitizeInput(input: unknown): TInput {
    if (!input || typeof input !== 'object') {
      return input as TInput;
    }
    
    // Clone to avoid mutating original
    const sanitized = InputSanitizer.clone(input);
    
    if (Array.isArray(sanitized)) {
      return sanitized as TInput;
    }
    
    // Sanitize based on schema
    const result: any = {};
    
    for (const [key, value] of Object.entries(sanitized)) {
      const propSchema = this.inputSchema.properties[key];
      
      if (!propSchema) {
        result[key] = value;
        continue;
      }
      
      // Get expected type
      const expectedType = Array.isArray(propSchema.type)
        ? propSchema.type[0]
        : propSchema.type;
      
      // Coerce value to expected type if type is defined
      if (expectedType) {
        result[key] = InputSanitizer.coerceToSchema(value, expectedType);
      } else {
        result[key] = value;
      }
    }
    
    return result as TInput;
  }
  
  /**
   * Execute with full validation pipeline
   */
  async executeWithValidation(input: unknown): Promise<TOutput> {
    // 1. Sanitize input
    const sanitized = this.sanitizeInput(input);
    
    // 2. Validate input
    const inputValidation = this.validateInput(sanitized);
    if (!inputValidation.valid) {
      throw new ValidationError(
        `Invalid input for ${this.toolId}`,
        inputValidation.errors!
      );
    }
    
    // 3. Execute
    logger.info(`Executing ${this.toolId}`);
    const startTime = Date.now();
    
    try {
      const result = await this.execute(inputValidation.data!);
      
      const duration = Date.now() - startTime;
      logger.info(`${this.toolId} completed in ${duration}ms`);
      
      // 4. Validate output
      const outputValidation = this.validateOutput(result);
      if (!outputValidation.valid) {
        logger.error(`Output validation failed for ${this.toolId}`, undefined, {
          errors: outputValidation.errors
        });
        throw new ValidationError(
          `Invalid output from ${this.toolId}`,
          outputValidation.errors!
        );
      }
      
      return outputValidation.data!;
    } catch (error) {
      const duration = Date.now() - startTime;
      logger.error(`${this.toolId} failed after ${duration}ms`, error as Error);
      throw error;
    }
  }
}

/**
 * Create a tool wrapper instance
 */
export function createToolWrapper<TInput, TOutput>(
  definition: {
    toolName: string;
    serverName: string;
    inputSchema: IToolSchema;
    outputSchema: IToolSchema;
    metadata?: IToolMetadata;
    execute: (input: TInput) => Promise<TOutput>;
  }
): IToolWrapper<TInput, TOutput> {
  return new (class extends ToolWrapperBase<TInput, TOutput> {
    override readonly toolName = definition.toolName;
    override readonly serverName = definition.serverName;
    override readonly inputSchema = definition.inputSchema;
    override readonly outputSchema = definition.outputSchema;
    override readonly metadata = definition.metadata;
    
    override async execute(input: TInput): Promise<TOutput> {
      return definition.execute(input);
    }
  })();
}

