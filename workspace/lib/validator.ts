/**
 * Schema Validator
 * 
 * JSON Schema validation for tool inputs and outputs
 */

import {
  IToolSchema,
  ISchemaProperty,
  IValidationError,
  IValidationResult
} from './types/tool.schema.js';

/**
 * Schema validator implementation
 */
export class SchemaValidator {
  /**
   * Validate data against schema
   */
  validate<T = unknown>(data: unknown, schema: IToolSchema): IValidationResult<T> {
    const errors: IValidationError[] = [];
    
    // Must be an object
    if (typeof data !== 'object' || data === null || Array.isArray(data)) {
      errors.push({
        path: '$',
        message: 'Data must be an object',
        expected: 'object',
        received: data
      });
      return { valid: false, errors };
    }
    
    const dataObj = data as Record<string, unknown>;
    
    // Validate required fields
    if (schema.required) {
      for (const field of schema.required) {
        if (!(field in dataObj) || dataObj[field] === undefined) {
          errors.push({
            path: field,
            message: `Required field '${field}' is missing`,
            expected: 'defined',
            received: undefined
          });
        }
      }
    }
    
    // Validate each property
    for (const [key, value] of Object.entries(dataObj)) {
      const propSchema = schema.properties[key];
      
      // Check if property is allowed
      if (!propSchema && schema.additionalProperties === false) {
        errors.push({
          path: key,
          message: `Additional property '${key}' is not allowed`,
          expected: 'not present',
          received: value
        });
        continue;
      }
      
      // Validate property if schema exists
      if (propSchema) {
        const propErrors = this.validateProperty(value, propSchema, key);
        errors.push(...propErrors);
      }
    }
    
    if (errors.length > 0) {
      return { valid: false, errors };
    }
    
    return { valid: true, data: data as T };
  }
  
  /**
   * Validate a single property
   */
  private validateProperty(
    value: unknown,
    schema: ISchemaProperty,
    path: string
  ): IValidationError[] {
    const errors: IValidationError[] = [];
    
    // Handle union types
    if (Array.isArray(schema.type)) {
      const typeMatches = schema.type.some((type: string) => 
        this.checkType(value, type)
      );
      if (!typeMatches) {
        errors.push({
          path,
          message: `Value must be one of types: ${schema.type.join(', ')}`,
          expected: schema.type.join(' | '),
          received: value
        });
      }
      return errors;
    }
    
    // Check type
    if (!this.checkType(value, schema.type)) {
      errors.push({
        path,
        message: `Expected ${schema.type}, got ${typeof value}`,
        expected: schema.type,
        received: value
      });
      return errors;
    }
    
    // Type-specific validation
    switch (schema.type) {
      case 'string':
        errors.push(...this.validateString(value as string, schema, path));
        break;
      
      case 'number':
        errors.push(...this.validateNumber(value as number, schema, path));
        break;
      
      case 'array':
        errors.push(...this.validateArray(value as unknown[], schema, path));
        break;
      
      case 'object':
        errors.push(...this.validateObject(value as Record<string, unknown>, schema, path));
        break;
    }
    
    // Enum validation
    if (schema.enum && !schema.enum.includes(value)) {
      errors.push({
        path,
        message: `Value must be one of: ${schema.enum.join(', ')}`,
        expected: `enum: ${schema.enum.join(', ')}`,
        received: value
      });
    }
    
    return errors;
  }
  
  /**
   * Check if value matches type
   */
  private checkType(value: unknown, type: string): boolean {
    if (value === null) return type === 'null';
    
    switch (type) {
      case 'string':
        return typeof value === 'string';
      case 'number':
        return typeof value === 'number' && isFinite(value);
      case 'boolean':
        return typeof value === 'boolean';
      case 'array':
        return Array.isArray(value);
      case 'object':
        return typeof value === 'object' && value !== null && !Array.isArray(value);
      case 'null':
        return value === null;
      default:
        return false;
    }
  }
  
  /**
   * Validate string
   */
  private validateString(
    value: string,
    schema: ISchemaProperty,
    path: string
  ): IValidationError[] {
    const errors: IValidationError[] = [];
    
    if (schema.minLength !== undefined && value.length < schema.minLength) {
      errors.push({
        path,
        message: `String length must be at least ${schema.minLength}`,
        expected: `length >= ${schema.minLength}`,
        received: value.length
      });
    }
    
    if (schema.maxLength !== undefined && value.length > schema.maxLength) {
      errors.push({
        path,
        message: `String length must be at most ${schema.maxLength}`,
        expected: `length <= ${schema.maxLength}`,
        received: value.length
      });
    }
    
    if (schema.pattern) {
      const regex = new RegExp(schema.pattern);
      if (!regex.test(value)) {
        errors.push({
          path,
          message: `String must match pattern: ${schema.pattern}`,
          expected: `pattern: ${schema.pattern}`,
          received: value
        });
      }
    }
    
    return errors;
  }
  
  /**
   * Validate number
   */
  private validateNumber(
    value: number,
    schema: ISchemaProperty,
    path: string
  ): IValidationError[] {
    const errors: IValidationError[] = [];
    
    if (schema.minimum !== undefined && value < schema.minimum) {
      errors.push({
        path,
        message: `Number must be at least ${schema.minimum}`,
        expected: `>= ${schema.minimum}`,
        received: value
      });
    }
    
    if (schema.maximum !== undefined && value > schema.maximum) {
      errors.push({
        path,
        message: `Number must be at most ${schema.maximum}`,
        expected: `<= ${schema.maximum}`,
        received: value
      });
    }
    
    if (schema.exclusiveMinimum !== undefined && value <= schema.exclusiveMinimum) {
      errors.push({
        path,
        message: `Number must be greater than ${schema.exclusiveMinimum}`,
        expected: `> ${schema.exclusiveMinimum}`,
        received: value
      });
    }
    
    if (schema.exclusiveMaximum !== undefined && value >= schema.exclusiveMaximum) {
      errors.push({
        path,
        message: `Number must be less than ${schema.exclusiveMaximum}`,
        expected: `< ${schema.exclusiveMaximum}`,
        received: value
      });
    }
    
    if (schema.multipleOf !== undefined && value % schema.multipleOf !== 0) {
      errors.push({
        path,
        message: `Number must be a multiple of ${schema.multipleOf}`,
        expected: `multiple of ${schema.multipleOf}`,
        received: value
      });
    }
    
    return errors;
  }
  
  /**
   * Validate array
   */
  private validateArray(
    value: unknown[],
    schema: ISchemaProperty,
    path: string
  ): IValidationError[] {
    const errors: IValidationError[] = [];
    
    if (schema.minItems !== undefined && value.length < schema.minItems) {
      errors.push({
        path,
        message: `Array must have at least ${schema.minItems} items`,
        expected: `length >= ${schema.minItems}`,
        received: value.length
      });
    }
    
    if (schema.maxItems !== undefined && value.length > schema.maxItems) {
      errors.push({
        path,
        message: `Array must have at most ${schema.maxItems} items`,
        expected: `length <= ${schema.maxItems}`,
        received: value.length
      });
    }
    
    if (schema.uniqueItems) {
      const seen = new Set();
      for (let i = 0; i < value.length; i++) {
        const item = JSON.stringify(value[i]);
        if (seen.has(item)) {
          errors.push({
            path: `${path}[${i}]`,
            message: 'Array items must be unique',
            expected: 'unique items',
            received: value[i]
          });
        }
        seen.add(item);
      }
    }
    
    // Validate items
    if (schema.items && !Array.isArray(schema.items)) {
      for (let i = 0; i < value.length; i++) {
        const itemErrors = this.validateProperty(value[i], schema.items, `${path}[${i}]`);
        errors.push(...itemErrors);
      }
    }
    
    return errors;
  }
  
  /**
   * Validate object
   */
  private validateObject(
    value: Record<string, unknown>,
    schema: ISchemaProperty,
    path: string
  ): IValidationError[] {
    const errors: IValidationError[] = [];
    
    if (schema.properties) {
      for (const [key, propSchema] of Object.entries(schema.properties)) {
        if (key in value) {
          const propErrors = this.validateProperty(
            value[key],
            propSchema,
            `${path}.${key}`
          );
          errors.push(...propErrors);
        }
      }
    }
    
    if (schema.required) {
      for (const field of schema.required) {
        if (!(field in value)) {
          errors.push({
            path: `${path}.${field}`,
            message: `Required field '${field}' is missing`,
            expected: 'defined',
            received: undefined
          });
        }
      }
    }
    
    return errors;
  }
  
  /**
   * Compile schema for faster repeated validation
   */
  compile(schema: IToolSchema): (data: unknown) => IValidationResult {
    // For now, just return a function that calls validate
    // In a production system, you might use a library like Ajv for compilation
    return (data: unknown) => this.validate(data, schema);
  }
}

/**
 * Global validator instance
 */
export const validator = new SchemaValidator();

