/**
 * Configuration Manager
 * 
 * Centralized configuration management for the MCP system
 */

import { LogLevel } from './logger.js';
import { TransportType } from './types/mcp.bridge.js';

/**
 * Server configuration
 */
export interface IServerConfig {
  name: string;
  container: string;
  entrypoint: string;
  port?: number;
  timeout: number;
  retries: number;
  healthCheck: {
    enabled: boolean;
    interval: number;
    timeout: number;
  };
}

/**
 * System configuration
 */
export interface ISystemConfig {
  execution: {
    timeout: number;
    maxOutputSize: number;
    allowedModules: string[];
  };
  transport: {
    type: TransportType;
    timeout: number;
  };
  logging: {
    level: LogLevel;
    destination: "stdout" | "stderr" | "none";
    pretty: boolean;
  };
  cache: {
    enabled: boolean;
    schemaTTL: number;
    toolListTTL: number;
  };
  servers: Record<string, IServerConfig>;
}

/**
 * Configuration manager singleton
 */
export class ConfigManager {
  private static instance: ConfigManager;
  private config: ISystemConfig;
  
  private constructor() {
    this.config = this.loadConfig();
  }
  
  /**
   * Get singleton instance
   */
  static getInstance(): ConfigManager {
    if (!ConfigManager.instance) {
      ConfigManager.instance = new ConfigManager();
    }
    return ConfigManager.instance;
  }
  
  /**
   * Load configuration from environment variables
   */
  private loadConfig(): ISystemConfig {
    return {
      execution: {
        timeout: this.getEnvNumber('EXECUTION_TIMEOUT', 30000),
        maxOutputSize: this.getEnvNumber('MAX_OUTPUT_SIZE', 1048576),
        allowedModules: this.getEnvArray('ALLOWED_MODULES', [
          'path', 'util', 'crypto', 'stream'
        ])
      },
      transport: {
        type: this.getEnv('TRANSPORT_TYPE', 'docker-exec') as TransportType,
        timeout: this.getEnvNumber('TRANSPORT_TIMEOUT', 30000)
      },
      logging: {
        level: this.getLogLevel(),
        destination: this.getEnv('LOG_DESTINATION', 'stderr') as any,
        pretty: this.getEnvBoolean('LOG_PRETTY', false)
      },
      cache: {
        enabled: this.getEnvBoolean('CACHE_ENABLED', true),
        schemaTTL: this.getEnvNumber('CACHE_SCHEMA_TTL', 300000), // 5 minutes
        toolListTTL: this.getEnvNumber('CACHE_TOOL_LIST_TTL', 600000) // 10 minutes
      },
      servers: {
        database: {
          name: 'database',
          container: this.getEnv('DATABASE_CONTAINER', 'ndiag-database-server'),
          entrypoint: this.getEnv('DATABASE_ENTRYPOINT', 'python3 /app/database_mcp_server.py'),
          timeout: this.getEnvNumber('DATABASE_TIMEOUT', 30000),
          retries: this.getEnvNumber('DATABASE_RETRIES', 3),
          healthCheck: {
            enabled: this.getEnvBoolean('DATABASE_HEALTH_CHECK', true),
            interval: this.getEnvNumber('DATABASE_HEALTH_INTERVAL', 60000),
            timeout: this.getEnvNumber('DATABASE_HEALTH_TIMEOUT', 5000)
          }
        },
        processing: {
          name: 'processing',
          container: this.getEnv('PROCESSING_CONTAINER', 'ndiag-processing-server'),
          entrypoint: this.getEnv('PROCESSING_ENTRYPOINT', 'python3 /app/processing_mcp_server.py'),
          timeout: this.getEnvNumber('PROCESSING_TIMEOUT', 60000),
          retries: this.getEnvNumber('PROCESSING_RETRIES', 3),
          healthCheck: {
            enabled: this.getEnvBoolean('PROCESSING_HEALTH_CHECK', true),
            interval: this.getEnvNumber('PROCESSING_HEALTH_INTERVAL', 60000),
            timeout: this.getEnvNumber('PROCESSING_HEALTH_TIMEOUT', 5000)
          }
        },
        alignment: {
          name: 'alignment',
          container: this.getEnv('ALIGNMENT_CONTAINER', 'ndiag-alignment-server'),
          entrypoint: this.getEnv('ALIGNMENT_ENTRYPOINT', 'python3 /app/alignment_mcp_server.py'),
          timeout: this.getEnvNumber('ALIGNMENT_TIMEOUT', 120000),
          retries: this.getEnvNumber('ALIGNMENT_RETRIES', 3),
          healthCheck: {
            enabled: this.getEnvBoolean('ALIGNMENT_HEALTH_CHECK', true),
            interval: this.getEnvNumber('ALIGNMENT_HEALTH_INTERVAL', 60000),
            timeout: this.getEnvNumber('ALIGNMENT_HEALTH_TIMEOUT', 5000)
          }
        },
        design: {
          name: 'design',
          container: this.getEnv('DESIGN_CONTAINER', 'ndiag-design-server'),
          entrypoint: this.getEnv('DESIGN_ENTRYPOINT', 'python3 /app/design_mcp_server.py'),
          timeout: this.getEnvNumber('DESIGN_TIMEOUT', 60000),
          retries: this.getEnvNumber('DESIGN_RETRIES', 3),
          healthCheck: {
            enabled: this.getEnvBoolean('DESIGN_HEALTH_CHECK', true),
            interval: this.getEnvNumber('DESIGN_HEALTH_INTERVAL', 60000),
            timeout: this.getEnvNumber('DESIGN_HEALTH_TIMEOUT', 5000)
          }
        },
        validation: {
          name: 'validation',
          container: this.getEnv('VALIDATION_CONTAINER', 'ndiag-validation-server'),
          entrypoint: this.getEnv('VALIDATION_ENTRYPOINT', 'python3 /app/validation_mcp_server.py'),
          timeout: this.getEnvNumber('VALIDATION_TIMEOUT', 60000),
          retries: this.getEnvNumber('VALIDATION_RETRIES', 3),
          healthCheck: {
            enabled: this.getEnvBoolean('VALIDATION_HEALTH_CHECK', true),
            interval: this.getEnvNumber('VALIDATION_HEALTH_INTERVAL', 60000),
            timeout: this.getEnvNumber('VALIDATION_HEALTH_TIMEOUT', 5000)
          }
        }
      }
    };
  }
  
  /**
   * Get environment variable as string
   */
  private getEnv(key: string, defaultValue: string): string {
    return process.env[key] || defaultValue;
  }
  
  /**
   * Get environment variable as number
   */
  private getEnvNumber(key: string, defaultValue: number): number {
    const value = process.env[key];
    if (!value) return defaultValue;
    const parsed = parseInt(value, 10);
    return isNaN(parsed) ? defaultValue : parsed;
  }
  
  /**
   * Get environment variable as boolean
   */
  private getEnvBoolean(key: string, defaultValue: boolean): boolean {
    const value = process.env[key];
    if (!value) return defaultValue;
    return value.toLowerCase() === 'true' || value === '1';
  }
  
  /**
   * Get environment variable as array
   */
  private getEnvArray(key: string, defaultValue: string[]): string[] {
    const value = process.env[key];
    if (!value) return defaultValue;
    return value.split(',').map(s => s.trim()).filter(s => s.length > 0);
  }
  
  /**
   * Get log level from environment
   */
  private getLogLevel(): LogLevel {
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
  
  /**
   * Get server configuration
   */
  getServerConfig(serverName: string): IServerConfig {
    const config = this.config.servers[serverName];
    if (!config) {
      throw new Error(`Server '${serverName}' not configured`);
    }
    return config;
  }
  
  /**
   * Get all server names
   */
  getServerNames(): string[] {
    return Object.keys(this.config.servers);
  }
  
  /**
   * Check if server exists
   */
  hasServer(serverName: string): boolean {
    return serverName in this.config.servers;
  }
  
  /**
   * Get execution configuration
   */
  get executionConfig() {
    return this.config.execution;
  }
  
  /**
   * Get transport configuration
   */
  get transportConfig() {
    return this.config.transport;
  }
  
  /**
   * Get logging configuration
   */
  get loggingConfig() {
    return this.config.logging;
  }
  
  /**
   * Get cache configuration
   */
  get cacheConfig() {
    return this.config.cache;
  }
  
  /**
   * Get full configuration
   */
  getConfig(): Readonly<ISystemConfig> {
    return this.config;
  }
  
  /**
   * Update configuration (for testing)
   */
  updateConfig(updates: Partial<ISystemConfig>) {
    this.config = {
      ...this.config,
      ...updates
    };
  }
}

/**
 * Global configuration instance
 */
export const config = ConfigManager.getInstance();

