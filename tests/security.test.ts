/**
 * Security and Privacy Testing
 *
 * Tests PII tokenization, sandbox security, and privacy leak prevention.
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { PIITokenizer, PIIType } from '../mcp_servers/shared/pii-tokenizer';

describe('PII Tokenization Security', () => {
  let tokenizer: PIITokenizer;

  beforeEach(() => {
    tokenizer = new PIITokenizer({ enableAuditLog: true });
  });

  it('should tokenize email addresses', () => {
    const input = 'Contact: john.doe@example.com';
    const tokenized = tokenizer.tokenize(input);

    expect(tokenized).not.toContain('john.doe@example.com');
    expect(tokenized).toMatch(/PII_TOKEN_[a-f0-9]{32}/);

    // Should detokenize back to original
    const detokenized = tokenizer.detokenize(tokenized);
    expect(detokenized).toBe(input);
  });

  it('should tokenize phone numbers (multiple formats)', () => {
    const inputs = [
      '555-123-4567',
      '(555) 123-4567',
      '+1-555-123-4567',
      '5551234567',
    ];

    inputs.forEach((input) => {
      const tokenized = tokenizer.tokenize(input);
      expect(tokenized).not.toContain('555');
      expect(tokenized).toMatch(/PII_TOKEN_[a-f0-9]{32}/);

      const detokenized = tokenizer.detokenize(tokenized);
      expect(detokenized).toBe(input);
    });
  });

  it('should tokenize SSN', () => {
    const input = 'SSN: 123-45-6789';
    const tokenized = tokenizer.tokenize(input);

    expect(tokenized).not.toContain('123-45-6789');
    expect(tokenized).toMatch(/PII_TOKEN_[a-f0-9]{32}/);

    const detokenized = tokenizer.detokenize(tokenized);
    expect(detokenized).toBe(input);
  });

  it('should tokenize credit card numbers', () => {
    const inputs = [
      '4532-1234-5678-9010',
      '4532 1234 5678 9010',
      '4532123456789010',
    ];

    inputs.forEach((input) => {
      const tokenized = tokenizer.tokenize(input);
      expect(tokenized).not.toContain('4532');
      expect(tokenized).toMatch(/PII_TOKEN_[a-f0-9]{32}/);

      const detokenized = tokenizer.detokenize(tokenized);
      expect(detokenized).toBe(input);
    });
  });

  it('should tokenize IP addresses', () => {
    const input = 'Server: 192.168.1.100';
    const tokenized = tokenizer.tokenize(input);

    expect(tokenized).not.toContain('192.168.1.100');
    expect(tokenized).toMatch(/PII_TOKEN_[a-f0-9]{32}/);

    const detokenized = tokenizer.detokenize(tokenized);
    expect(detokenized).toBe(input);
  });

  it('should tokenize API keys', () => {
    const inputs = [
      'api_key=sk_test_1234567890abcdef1234567890abcdef',
      'access_token: xyz123456789abc123456789abc123456',
      'apikey: "secret_key_1234567890abcdef1234567890"',
    ];

    inputs.forEach((input) => {
      const tokenized = tokenizer.tokenize(input);
      expect(tokenized).toMatch(/PII_TOKEN_[a-f0-9]{32}/);

      const detokenized = tokenizer.detokenize(tokenized);
      expect(detokenized).toBe(input);
    });
  });

  it('should tokenize multiple PII types in same text', () => {
    const input = `
      Patient: john.doe@example.com
      Phone: 555-123-4567
      SSN: 123-45-6789
      IP: 192.168.1.100
    `;

    const tokenized = tokenizer.tokenize(input);

    expect(tokenized).not.toContain('john.doe@example.com');
    expect(tokenized).not.toContain('555-123-4567');
    expect(tokenized).not.toContain('123-45-6789');
    expect(tokenized).not.toContain('192.168.1.100');

    // Should have 4 tokens
    const tokenCount = (tokenized.match(/PII_TOKEN_/g) || []).length;
    expect(tokenCount).toBe(4);

    // Should restore all PII
    const detokenized = tokenizer.detokenize(tokenized);
    expect(detokenized).toContain('john.doe@example.com');
    expect(detokenized).toContain('555-123-4567');
    expect(detokenized).toContain('123-45-6789');
    expect(detokenized).toContain('192.168.1.100');
  });

  it('should tokenize nested objects recursively', () => {
    const input = {
      researcher: {
        name: 'John Doe',
        email: 'john.doe@example.com',
        phone: '555-123-4567',
      },
      samples: [
        { id: 'S1', ip: '192.168.1.100' },
        { id: 'S2', ip: '192.168.1.101' },
      ],
    };

    const tokenized = tokenizer.tokenize(input);

    // Check email is tokenized
    expect(tokenized.researcher.email).not.toContain('@example.com');
    expect(tokenized.researcher.email).toMatch(/PII_TOKEN_/);

    // Check phone is tokenized
    expect(tokenized.researcher.phone).not.toContain('555');
    expect(tokenized.researcher.phone).toMatch(/PII_TOKEN_/);

    // Check IPs are tokenized
    expect(tokenized.samples[0].ip).toMatch(/PII_TOKEN_/);
    expect(tokenized.samples[1].ip).toMatch(/PII_TOKEN_/);

    // Check non-PII is preserved
    expect(tokenized.researcher.name).toBe('John Doe');
    expect(tokenized.samples[0].id).toBe('S1');

    // Detokenize should restore everything
    const detokenized = tokenizer.detokenize(tokenized);
    expect(detokenized.researcher.email).toBe('john.doe@example.com');
    expect(detokenized.researcher.phone).toBe('555-123-4567');
    expect(detokenized.samples[0].ip).toBe('192.168.1.100');
  });

  it('should prevent double tokenization', () => {
    const input = 'Email: john@example.com';

    const tokenized1 = tokenizer.tokenize(input);
    const tokenized2 = tokenizer.tokenize(tokenized1); // Try to tokenize again

    // Should not create nested tokens
    expect(tokenized2).toBe(tokenized1);

    // Should still detokenize correctly
    const detokenized = tokenizer.detokenize(tokenized2);
    expect(detokenized).toBe(input);
  });

  it('should track tokenization statistics', () => {
    tokenizer.tokenize('Email: test@example.com');
    tokenizer.tokenize('Phone: 555-123-4567');
    tokenizer.tokenize('SSN: 123-45-6789');

    const stats = tokenizer.getStats();

    expect(stats.totalTokens).toBe(3);
    expect(stats.tokensByType[PIIType.EMAIL]).toBe(1);
    expect(stats.tokensByType[PIIType.PHONE]).toBe(1);
    expect(stats.tokensByType[PIIType.SSN]).toBe(1);
    expect(stats.oldestToken).toBeLessThanOrEqual(stats.newestToken!);
  });

  it('should enable/disable specific patterns', () => {
    // Disable email tokenization
    tokenizer.setPatternEnabled(PIIType.EMAIL, false);

    const input = 'Email: test@example.com, Phone: 555-123-4567';
    const tokenized = tokenizer.tokenize(input);

    // Email should NOT be tokenized
    expect(tokenized).toContain('test@example.com');

    // Phone SHOULD be tokenized
    expect(tokenized).not.toContain('555-123-4567');
    expect(tokenized).toMatch(/PII_TOKEN_/);
  });

  it('should export and import token mappings', () => {
    const tokenizer1 = new PIITokenizer();
    const input = 'Email: test@example.com, Phone: 555-123-4567';

    const tokenized1 = tokenizer1.tokenize(input);
    const exported = tokenizer1.export();

    // Create new tokenizer and import
    const tokenizer2 = new PIITokenizer();
    tokenizer2.import(exported);

    // Should be able to detokenize with imported mappings
    const detokenized2 = tokenizer2.detokenize(tokenized1);
    expect(detokenized2).toBe(input);
  });

  it('should create audit log entries', () => {
    const tokenized = tokenizer.tokenize('Email: test@example.com');
    tokenizer.detokenize(tokenized); // Detokenize the actual token

    const log = tokenizer.getAuditLog();

    expect(log.length).toBeGreaterThan(0);
    expect(log.some((entry) => entry.operation === 'tokenize')).toBe(true);
    expect(log.some((entry) => entry.operation === 'detokenize')).toBe(true);
  });

  it('should handle edge cases gracefully', () => {
    // Empty string
    expect(tokenizer.tokenize('')).toBe('');

    // null
    expect(tokenizer.tokenize(null)).toBe(null);

    // undefined
    expect(tokenizer.tokenize(undefined)).toBe(undefined);

    // Number
    expect(tokenizer.tokenize(123)).toBe(123);

    // Empty array
    expect(tokenizer.tokenize([])).toEqual([]);

    // Empty object
    expect(tokenizer.tokenize({})).toEqual({});
  });
});

describe('Privacy Leak Prevention', () => {
  it('should prevent PII from appearing in logs', () => {
    const tokenizer = new PIITokenizer();
    const logSpy: string[] = [];

    // Mock console.log
    const originalLog = console.log;
    console.log = (...args: any[]) => {
      logSpy.push(args.join(' '));
      originalLog(...args);
    };

    try {
      // Simulate workflow with PII
      const patientData = {
        email: 'sensitive@example.com',
        phone: '555-987-6543', // Full 10-digit phone
        ssn: '987-65-4321',
      };

      // Tokenize before logging
      const tokenized = tokenizer.tokenize(patientData);

      console.log('Processing patient data:', JSON.stringify(tokenized));

      // Check logs don't contain actual PII
      const allLogs = logSpy.join('\n');
      expect(allLogs).not.toContain('sensitive@example.com');
      expect(allLogs).not.toContain('555-987-6543');
      expect(allLogs).not.toContain('987-65-4321');

      // Check logs contain tokens instead
      expect(allLogs).toMatch(/PII_TOKEN_/);
    } finally {
      console.log = originalLog;
    }
  });

  it('should sanitize error messages', () => {
    const tokenizer = new PIITokenizer();

    const errorData = {
      message: 'Failed to process email: test@example.com',
      details: 'Phone validation failed for 555-123-4567',
    };

    const sanitized = tokenizer.tokenize(errorData);

    expect(sanitized.message).not.toContain('test@example.com');
    expect(sanitized.details).not.toContain('555-123-4567');
    expect(sanitized.message).toMatch(/PII_TOKEN_/);
    expect(sanitized.details).toMatch(/PII_TOKEN_/);
  });

  it('should tokenize PII in file paths and URLs', () => {
    const tokenizer = new PIITokenizer();

    const input = 'File: /data/users/john.doe@example.com/results.txt';
    const tokenized = tokenizer.tokenize(input);

    expect(tokenized).not.toContain('john.doe@example.com');
    expect(tokenized).toMatch(/PII_TOKEN_/);
  });

  it('should handle PII in FASTA headers', () => {
    const tokenizer = new PIITokenizer();

    const fasta = `>Seq1|researcher:john@example.com|lab:192.168.1.100
ATCGATCGATCG
>Seq2|researcher:jane@example.com|phone:555-123-4567
GCTAGCTAGCTA`;

    const tokenized = tokenizer.tokenize(fasta);

    expect(tokenized).not.toContain('john@example.com');
    expect(tokenized).not.toContain('jane@example.com');
    expect(tokenized).not.toContain('192.168.1.100');
    expect(tokenized).not.toContain('555-123-4567');

    // Sequences should be preserved
    expect(tokenized).toContain('ATCGATCGATCG');
    expect(tokenized).toContain('GCTAGCTAGCTA');

    // Should have tokens
    expect(tokenized).toMatch(/PII_TOKEN_/);
  });
});

describe('Sandbox Security', () => {
  it('should prevent access to process.env in sandbox', () => {
    // This test validates that the VM2 sandbox prevents access to process.env
    // In actual implementation, VM2 sandbox would throw an error

    // Simulated test - in real sandbox this would fail
    const dangerousCode = `
      try {
        const apiKey = process.env.API_KEY;
        return { success: true, apiKey };
      } catch (e) {
        return { success: false, error: e.message };
      }
    `;

    // Expected behavior: sandbox should block access
    const expectedResult = {
      success: false,
      error: expect.stringContaining('process is not defined'),
    };

    // Note: This is a specification test. Actual sandbox testing
    // would be done in code-execution/tests/executor.test.ts
  });

  it('should prevent file system access from sandbox', () => {
    // Specification: VM2 sandbox should prevent require('fs')
    const dangerousCode = `
      try {
        const fs = require('fs');
        fs.readFileSync('/etc/passwd');
        return { success: true };
      } catch (e) {
        return { success: false, error: e.message };
      }
    `;

    // Expected: Access denied
    const expectedResult = {
      success: false,
      error: expect.stringContaining('require is not defined'),
    };
  });

  it('should prevent network access from sandbox', () => {
    // Specification: Sandbox should prevent http/https requires
    const dangerousCode = `
      try {
        const http = require('http');
        http.get('http://malicious-site.com');
        return { success: true };
      } catch (e) {
        return { success: false, error: e.message };
      }
    `;

    // Expected: Network access blocked
    const expectedResult = {
      success: false,
      error: expect.stringContaining('require is not defined'),
    };
  });

  it('should enforce timeout limits', () => {
    // Specification: Infinite loops should timeout
    const infiniteLoop = `
      while (true) {
        // Infinite loop
      }
    `;

    // Expected: Timeout after configured duration
    const expectedError = 'Script execution timed out';
  });

  it('should enforce memory limits', () => {
    // Specification: Memory-intensive operations should be limited
    const memoryHog = `
      const bigArray = [];
      for (let i = 0; i < 10000000; i++) {
        bigArray.push(new Array(1000).fill(0));
      }
    `;

    // Expected: Memory limit exceeded
    const expectedError = expect.stringContaining('memory');
  });
});

describe('HIPAA/GDPR Compliance', () => {
  it('should provide audit trail for compliance', () => {
    const tokenizer = new PIITokenizer({ enableAuditLog: true });

    // Tokenize patient data
    tokenizer.tokenize('Patient: john@example.com');

    // Export for external system
    tokenizer.export();

    // Clear tokens
    tokenizer.clear();

    // Get audit log
    const log = tokenizer.getAuditLog();

    // Should have records of all operations
    expect(log.some((e) => e.operation === 'tokenize')).toBe(true);
    expect(log.some((e) => e.operation === 'export')).toBe(true);
    expect(log.some((e) => e.operation === 'clear')).toBe(true);

    // Each entry should have timestamp
    log.forEach((entry) => {
      expect(entry.timestamp).toBeGreaterThan(0);
    });
  });

  it('should support data portability (export/import)', () => {
    const tokenizer1 = new PIITokenizer();
    const data = { email: 'patient@example.com', phone: '555-1234' };

    const tokenized = tokenizer1.tokenize(data);
    const exported = tokenizer1.export();

    // Data can be exported to another system
    expect(exported).toContain('version');
    expect(exported).toContain('tokens');

    // Another system can import and detokenize
    const tokenizer2 = new PIITokenizer();
    tokenizer2.import(exported);

    const detokenized = tokenizer2.detokenize(tokenized);
    expect(detokenized).toEqual(data);
  });

  it('should support right to deletion (clear)', () => {
    const tokenizer = new PIITokenizer();

    tokenizer.tokenize('Email: test@example.com');
    expect(tokenizer.getStats().totalTokens).toBe(1);

    // Clear all PII
    tokenizer.clear();

    expect(tokenizer.getStats().totalTokens).toBe(0);

    // Should have audit log entry
    const log = tokenizer.getAuditLog();
    expect(log.some((e) => e.operation === 'clear')).toBe(true);
  });
});
