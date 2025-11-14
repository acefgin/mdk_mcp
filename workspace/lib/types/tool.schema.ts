/**
 * Tool Schema Types
 * 
 * JSON Schema definitions for tool input/output validation
 */

/**
 * JSON Schema type
 */
export type SchemaType = "string" | "number" | "boolean" | "array" | "object" | "null";

/**
 * Base schema property
 */
export interface ISchemaProperty {
  type: SchemaType | SchemaType[];
  description?: string;
  default?: unknown;
  
  // String validation
  minLength?: number;
  maxLength?: number;
  pattern?: string;
  format?: "date-time" | "date" | "email" | "uri" | "uuid";
  
  // Number validation
  minimum?: number;
  maximum?: number;
  exclusiveMinimum?: number;
  exclusiveMaximum?: number;
  multipleOf?: number;
  
  // Array validation
  items?: ISchemaProperty | ISchemaProperty[];
  minItems?: number;
  maxItems?: number;
  uniqueItems?: boolean;
  
  // Object validation
  properties?: Record<string, ISchemaProperty>;
  required?: string[];
  additionalProperties?: boolean | ISchemaProperty;
  
  // Enum
  enum?: unknown[];
  
  // Conditional
  oneOf?: ISchemaProperty[];
  anyOf?: ISchemaProperty[];
  allOf?: ISchemaProperty[];
  not?: ISchemaProperty;
  
  // Meta
  title?: string;
  examples?: unknown[];
  deprecated?: boolean;
}

/**
 * Tool schema (JSON Schema object)
 */
export interface IToolSchema {
  $schema?: string;
  $id?: string;
  type: "object";
  properties: Record<string, ISchemaProperty>;
  required?: string[];
  additionalProperties?: boolean;
  title?: string;
  description?: string;
}

/**
 * Validation error detail
 */
export interface IValidationError {
  path: string;
  message: string;
  expected: string;
  received: unknown;
}

/**
 * Validation result
 */
export interface IValidationResult<T = unknown> {
  valid: boolean;
  data?: T;
  errors?: IValidationError[];
}

/**
 * Schema validator interface
 */
export interface ISchemaValidator {
  /**
   * Validate data against schema
   */
  validate<T = unknown>(data: unknown, schema: IToolSchema): IValidationResult<T>;
  
  /**
   * Compile schema for faster repeated validation
   */
  compile(schema: IToolSchema): (data: unknown) => IValidationResult;
}

