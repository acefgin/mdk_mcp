/**
 * PII Tokenization System
 *
 * Provides privacy-preserving tokenization for sensitive data in MCP workflows.
 *
 * Features:
 * - 6 PII pattern types (email, phone, SSN, credit card, IP address, API key)
 * - Bidirectional tokenization (tokenize/detokenize)
 * - Audit logging for compliance
 * - Export/import for distributed systems
 * - Configurable patterns and sensitivity levels
 */
/**
 * PII pattern types
 */
export declare enum PIIType {
    EMAIL = "email",
    PHONE = "phone",
    SSN = "ssn",
    CREDIT_CARD = "credit_card",
    IP_ADDRESS = "ip_address",
    API_KEY = "api_key"
}
/**
 * PII pattern definition
 */
interface PIIPattern {
    type: PIIType;
    regex: RegExp;
    description: string;
    enabled: boolean;
}
/**
 * Audit log entry
 */
interface AuditLogEntry {
    timestamp: number;
    operation: 'tokenize' | 'detokenize' | 'export' | 'import' | 'clear';
    type?: PIIType;
    count?: number;
    metadata?: Record<string, any>;
}
/**
 * PII Tokenizer configuration
 */
export interface PIITokenizerConfig {
    enableAuditLog?: boolean;
    auditLogPath?: string;
    tokenPrefix?: string;
    patterns?: Partial<Record<PIIType, PIIPattern>>;
}
/**
 * PII Tokenization System
 *
 * Detects and tokenizes sensitive data to protect privacy while maintaining
 * data utility for bioinformatics workflows.
 */
export declare class PIITokenizer {
    private tokenMap;
    private reverseMap;
    private auditLog;
    private config;
    /**
     * Default PII patterns
     */
    private readonly defaultPatterns;
    constructor(config?: PIITokenizerConfig);
    /**
     * Tokenize PII in data (string or object)
     *
     * @param data - Data to tokenize (string or object)
     * @returns Tokenized data
     *
     * @example
     * const tokenizer = new PIITokenizer();
     * const result = tokenizer.tokenize({
     *   email: 'user@example.com',
     *   phone: '555-123-4567'
     * });
     * // Returns: { email: 'PII_TOKEN_abc123', phone: 'PII_TOKEN_def456' }
     */
    tokenize(data: any): any;
    /**
     * Tokenize PII in a string
     *
     * @private
     */
    private tokenizeString;
    /**
     * Detokenize data (string or object)
     *
     * @param data - Tokenized data
     * @returns Original data with PII restored
     *
     * @example
     * const original = tokenizer.detokenize({
     *   email: 'PII_TOKEN_abc123',
     *   phone: 'PII_TOKEN_def456'
     * });
     * // Returns: { email: 'user@example.com', phone: '555-123-4567' }
     */
    detokenize(data: any): any;
    /**
     * Detokenize a string
     *
     * @private
     */
    private detokenizeString;
    /**
     * Generate a unique token
     *
     * @private
     */
    private generateToken;
    /**
     * Get statistics about tokenization
     *
     * @returns Statistics object
     */
    getStats(): {
        totalTokens: number;
        tokensByType: Record<PIIType, number>;
        oldestToken: number | null;
        newestToken: number | null;
    };
    /**
     * Export token mappings (for distributed systems)
     *
     * @returns Serialized token mappings
     */
    export(): string;
    /**
     * Import token mappings (for distributed systems)
     *
     * @param serialized - Serialized token mappings from export()
     */
    import(serialized: string): void;
    /**
     * Clear all token mappings
     */
    clear(): void;
    /**
     * Enable or disable a specific PII pattern
     *
     * @param type - PII type to enable/disable
     * @param enabled - Whether to enable the pattern
     */
    setPatternEnabled(type: PIIType, enabled: boolean): void;
    /**
     * Get audit log
     *
     * @returns Array of audit log entries
     */
    getAuditLog(): AuditLogEntry[];
    /**
     * Save audit log to file
     *
     * @param path - File path (optional, uses config path by default)
     */
    saveAuditLog(path?: string): Promise<void>;
    /**
     * Load audit log from file
     *
     * @param path - File path (optional, uses config path by default)
     */
    loadAuditLog(path?: string): Promise<void>;
    /**
     * Log an audit entry
     *
     * @private
     */
    private logAudit;
}
export declare function getDefaultTokenizer(): PIITokenizer;
export {};
//# sourceMappingURL=pii-tokenizer.d.ts.map