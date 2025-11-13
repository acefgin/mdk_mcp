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
import crypto from 'crypto';
import { promises as fs } from 'fs';
/**
 * PII pattern types
 */
export var PIIType;
(function (PIIType) {
    PIIType["EMAIL"] = "email";
    PIIType["PHONE"] = "phone";
    PIIType["SSN"] = "ssn";
    PIIType["CREDIT_CARD"] = "credit_card";
    PIIType["IP_ADDRESS"] = "ip_address";
    PIIType["API_KEY"] = "api_key";
})(PIIType || (PIIType = {}));
/**
 * PII Tokenization System
 *
 * Detects and tokenizes sensitive data to protect privacy while maintaining
 * data utility for bioinformatics workflows.
 */
export class PIITokenizer {
    tokenMap = new Map();
    reverseMap = new Map();
    auditLog = [];
    config;
    /**
     * Default PII patterns
     */
    defaultPatterns = {
        [PIIType.EMAIL]: {
            type: PIIType.EMAIL,
            regex: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g,
            description: 'Email address',
            enabled: true,
        },
        [PIIType.PHONE]: {
            type: PIIType.PHONE,
            regex: /\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b/g,
            description: 'Phone number (US format)',
            enabled: true,
        },
        [PIIType.SSN]: {
            type: PIIType.SSN,
            regex: /\b\d{3}-\d{2}-\d{4}\b/g,
            description: 'Social Security Number',
            enabled: true,
        },
        [PIIType.CREDIT_CARD]: {
            type: PIIType.CREDIT_CARD,
            regex: /\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b/g,
            description: 'Credit card number',
            enabled: true,
        },
        [PIIType.IP_ADDRESS]: {
            type: PIIType.IP_ADDRESS,
            regex: /\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b/g,
            description: 'IPv4 address',
            enabled: true,
        },
        [PIIType.API_KEY]: {
            type: PIIType.API_KEY,
            regex: /\b(?:api[_-]?key|apikey|access[_-]?token)[\s:=]+['"]?([a-zA-Z0-9_\-]{32,})['"]?/gi,
            description: 'API key or access token',
            enabled: true,
        },
    };
    constructor(config = {}) {
        this.config = {
            enableAuditLog: config.enableAuditLog ?? true,
            auditLogPath: config.auditLogPath ?? '/workspace/cache/pii-audit.log',
            tokenPrefix: config.tokenPrefix ?? 'PII_TOKEN_',
            patterns: { ...this.defaultPatterns, ...config.patterns },
        };
    }
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
    tokenize(data) {
        if (typeof data === 'string') {
            return this.tokenizeString(data);
        }
        else if (Array.isArray(data)) {
            return data.map(item => this.tokenize(item));
        }
        else if (data !== null && typeof data === 'object') {
            const result = {};
            for (const [key, value] of Object.entries(data)) {
                result[key] = this.tokenize(value);
            }
            return result;
        }
        return data;
    }
    /**
     * Tokenize PII in a string
     *
     * @private
     */
    tokenizeString(text) {
        let result = text;
        let count = 0;
        for (const pattern of Object.values(this.config.patterns)) {
            if (!pattern.enabled)
                continue;
            result = result.replace(pattern.regex, (match) => {
                // Check if already tokenized
                if (match.startsWith(this.config.tokenPrefix)) {
                    return match;
                }
                // Generate token
                const token = this.generateToken();
                const mapping = {
                    token,
                    originalValue: match,
                    type: pattern.type,
                    timestamp: Date.now(),
                };
                // Store mapping
                this.tokenMap.set(token, mapping);
                this.reverseMap.set(match, token);
                count++;
                return token;
            });
        }
        // Log tokenization
        if (count > 0 && this.config.enableAuditLog) {
            this.logAudit({
                timestamp: Date.now(),
                operation: 'tokenize',
                count,
            });
        }
        return result;
    }
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
    detokenize(data) {
        if (typeof data === 'string') {
            return this.detokenizeString(data);
        }
        else if (Array.isArray(data)) {
            return data.map(item => this.detokenize(item));
        }
        else if (data !== null && typeof data === 'object') {
            const result = {};
            for (const [key, value] of Object.entries(data)) {
                result[key] = this.detokenize(value);
            }
            return result;
        }
        return data;
    }
    /**
     * Detokenize a string
     *
     * @private
     */
    detokenizeString(text) {
        let result = text;
        let count = 0;
        // Replace all tokens with original values
        for (const [token, mapping] of this.tokenMap.entries()) {
            if (result.includes(token)) {
                result = result.replace(new RegExp(token, 'g'), mapping.originalValue);
                count++;
            }
        }
        // Log detokenization
        if (count > 0 && this.config.enableAuditLog) {
            this.logAudit({
                timestamp: Date.now(),
                operation: 'detokenize',
                count,
            });
        }
        return result;
    }
    /**
     * Generate a unique token
     *
     * @private
     */
    generateToken() {
        const hash = crypto.randomBytes(16).toString('hex');
        return `${this.config.tokenPrefix}${hash}`;
    }
    /**
     * Get statistics about tokenization
     *
     * @returns Statistics object
     */
    getStats() {
        const tokensByType = {
            [PIIType.EMAIL]: 0,
            [PIIType.PHONE]: 0,
            [PIIType.SSN]: 0,
            [PIIType.CREDIT_CARD]: 0,
            [PIIType.IP_ADDRESS]: 0,
            [PIIType.API_KEY]: 0,
        };
        let oldestToken = null;
        let newestToken = null;
        for (const mapping of this.tokenMap.values()) {
            tokensByType[mapping.type]++;
            if (oldestToken === null || mapping.timestamp < oldestToken) {
                oldestToken = mapping.timestamp;
            }
            if (newestToken === null || mapping.timestamp > newestToken) {
                newestToken = mapping.timestamp;
            }
        }
        return {
            totalTokens: this.tokenMap.size,
            tokensByType,
            oldestToken,
            newestToken,
        };
    }
    /**
     * Export token mappings (for distributed systems)
     *
     * @returns Serialized token mappings
     */
    export() {
        const data = {
            version: '1.0',
            timestamp: Date.now(),
            tokens: Array.from(this.tokenMap.entries()).map(([, mapping]) => ({
                ...mapping,
            })),
        };
        if (this.config.enableAuditLog) {
            this.logAudit({
                timestamp: Date.now(),
                operation: 'export',
                count: this.tokenMap.size,
            });
        }
        return JSON.stringify(data, null, 2);
    }
    /**
     * Import token mappings (for distributed systems)
     *
     * @param serialized - Serialized token mappings from export()
     */
    import(serialized) {
        try {
            const data = JSON.parse(serialized);
            if (!data.version || !data.tokens) {
                throw new Error('Invalid export format');
            }
            // Clear existing mappings
            this.tokenMap.clear();
            this.reverseMap.clear();
            // Import tokens
            for (const tokenData of data.tokens) {
                const mapping = {
                    token: tokenData.token,
                    originalValue: tokenData.originalValue,
                    type: tokenData.type,
                    timestamp: tokenData.timestamp,
                };
                this.tokenMap.set(tokenData.token, mapping);
                this.reverseMap.set(tokenData.originalValue, tokenData.token);
            }
            if (this.config.enableAuditLog) {
                this.logAudit({
                    timestamp: Date.now(),
                    operation: 'import',
                    count: this.tokenMap.size,
                });
            }
        }
        catch (error) {
            throw new Error(`Failed to import token mappings: ${error.message}`);
        }
    }
    /**
     * Clear all token mappings
     */
    clear() {
        const count = this.tokenMap.size;
        this.tokenMap.clear();
        this.reverseMap.clear();
        if (this.config.enableAuditLog) {
            this.logAudit({
                timestamp: Date.now(),
                operation: 'clear',
                count,
            });
        }
    }
    /**
     * Enable or disable a specific PII pattern
     *
     * @param type - PII type to enable/disable
     * @param enabled - Whether to enable the pattern
     */
    setPatternEnabled(type, enabled) {
        if (this.config.patterns[type]) {
            this.config.patterns[type].enabled = enabled;
        }
    }
    /**
     * Get audit log
     *
     * @returns Array of audit log entries
     */
    getAuditLog() {
        return [...this.auditLog];
    }
    /**
     * Save audit log to file
     *
     * @param path - File path (optional, uses config path by default)
     */
    async saveAuditLog(path) {
        const logPath = path || this.config.auditLogPath;
        try {
            // Ensure directory exists
            await fs.mkdir(require('path').dirname(logPath), { recursive: true });
            // Write log
            const logData = JSON.stringify(this.auditLog, null, 2);
            await fs.writeFile(logPath, logData, 'utf-8');
        }
        catch (error) {
            console.error(`Failed to save audit log: ${error.message}`);
        }
    }
    /**
     * Load audit log from file
     *
     * @param path - File path (optional, uses config path by default)
     */
    async loadAuditLog(path) {
        const logPath = path || this.config.auditLogPath;
        try {
            const logData = await fs.readFile(logPath, 'utf-8');
            this.auditLog = JSON.parse(logData);
        }
        catch (error) {
            // File doesn't exist or is invalid - start with empty log
            this.auditLog = [];
        }
    }
    /**
     * Log an audit entry
     *
     * @private
     */
    logAudit(entry) {
        if (this.config.enableAuditLog) {
            this.auditLog.push(entry);
            // Keep only last 1000 entries
            if (this.auditLog.length > 1000) {
                this.auditLog = this.auditLog.slice(-1000);
            }
        }
    }
}
/**
 * Create a singleton PII tokenizer instance
 */
let defaultTokenizer = null;
export function getDefaultTokenizer() {
    if (!defaultTokenizer) {
        defaultTokenizer = new PIITokenizer();
    }
    return defaultTokenizer;
}
//# sourceMappingURL=pii-tokenizer.js.map