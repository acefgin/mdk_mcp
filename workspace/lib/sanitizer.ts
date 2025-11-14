/**
 * Input Sanitizer
 * 
 * Utilities for sanitizing and coercing input data
 */

/**
 * Input sanitizer class
 */
export class InputSanitizer {
  /**
   * Remove dangerous characters from strings
   */
  static sanitizeString(input: string): string {
    return input
      .replace(/[<>]/g, '') // Remove HTML tags
      .replace(/[`$\\]/g, '') // Remove shell metacharacters
      .replace(/\0/g, '') // Remove null bytes
      .trim();
  }
  
  /**
   * Coerce string numbers to actual numbers
   */
  static coerceNumber(input: unknown): number | undefined {
    if (typeof input === 'number') {
      return isNaN(input) || !isFinite(input) ? undefined : input;
    }
    
    if (typeof input === 'string') {
      const trimmed = input.trim();
      if (trimmed === '') return undefined;
      
      const num = Number(trimmed);
      return isNaN(num) || !isFinite(num) ? undefined : num;
    }
    
    return undefined;
  }
  
  /**
   * Coerce to boolean
   */
  static coerceBoolean(input: unknown): boolean | undefined {
    if (typeof input === 'boolean') {
      return input;
    }
    
    if (typeof input === 'string') {
      const lower = input.toLowerCase().trim();
      if (lower === 'true' || lower === '1' || lower === 'yes') return true;
      if (lower === 'false' || lower === '0' || lower === 'no') return false;
    }
    
    if (typeof input === 'number') {
      return input !== 0;
    }
    
    return undefined;
  }
  
  /**
   * Coerce to array
   */
  static coerceArray(input: unknown): unknown[] | undefined {
    if (Array.isArray(input)) {
      return input;
    }
    
    if (typeof input === 'string') {
      // Try to parse as JSON array
      try {
        const parsed = JSON.parse(input);
        if (Array.isArray(parsed)) {
          return parsed;
        }
      } catch {
        // Not JSON, try comma-separated
        return input.split(',').map(s => s.trim());
      }
    }
    
    return undefined;
  }
  
  /**
   * Sanitize entire input object recursively
   */
  static sanitize<T extends Record<string, unknown>>(input: T): T {
    const result: any = {};
    
    for (const [key, value] of Object.entries(input)) {
      result[key] = this.sanitizeValue(value);
    }
    
    return result;
  }
  
  /**
   * Sanitize a single value
   */
  private static sanitizeValue(value: unknown): unknown {
    if (value === null || value === undefined) {
      return value;
    }
    
    if (typeof value === 'string') {
      return this.sanitizeString(value);
    }
    
    if (Array.isArray(value)) {
      return value.map(v => this.sanitizeValue(v));
    }
    
    if (typeof value === 'object') {
      return this.sanitize(value as Record<string, unknown>);
    }
    
    return value;
  }
  
  /**
   * Coerce types based on schema
   */
  static coerceToSchema(input: unknown, expectedType: string): unknown {
    switch (expectedType) {
      case 'string':
        return input == null ? undefined : String(input);
      
      case 'number':
        return this.coerceNumber(input);
      
      case 'boolean':
        return this.coerceBoolean(input);
      
      case 'array':
        return this.coerceArray(input);
      
      case 'object':
        return typeof input === 'object' && input !== null ? input : undefined;
      
      default:
        return input;
    }
  }
  
  /**
   * Deep clone an object (safe for JSON-serializable objects)
   */
  static clone<T>(input: T): T {
    if (input === null || input === undefined) {
      return input;
    }
    
    if (typeof input !== 'object') {
      return input;
    }
    
    try {
      return JSON.parse(JSON.stringify(input));
    } catch {
      // Fallback for non-serializable objects
      return input;
    }
  }
  
  /**
   * Merge objects deeply
   */
  static merge<T extends Record<string, unknown>>(
    target: T,
    ...sources: Partial<T>[]
  ): T {
    const result = this.clone(target);
    
    for (const source of sources) {
      for (const [key, value] of Object.entries(source)) {
        if (value === undefined) continue;
        
        if (
          typeof value === 'object' &&
          value !== null &&
          !Array.isArray(value) &&
          typeof result[key] === 'object' &&
          result[key] !== null &&
          !Array.isArray(result[key])
        ) {
          const merged = this.merge(
            result[key] as Record<string, unknown>,
            value as Record<string, unknown>
          );
          (result as any)[key] = merged;
        } else {
          (result as any)[key] = value;
        }
      }
    }
    
    return result;
  }
  
  /**
   * Remove undefined and null values
   */
  static removeEmpty<T extends Record<string, unknown>>(input: T): Partial<T> {
    const result: any = {};
    
    for (const [key, value] of Object.entries(input)) {
      if (value !== undefined && value !== null) {
        result[key] = value;
      }
    }
    
    return result;
  }
}

