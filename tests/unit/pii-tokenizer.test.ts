/**
 * Unit tests for PII Tokenizer
 *
 * Tests comprehensive PII tokenization including:
 * - Email addresses
 * - Phone numbers
 * - Social Security Numbers
 * - Credit card numbers
 * - IP addresses
 * - API keys
 * - Nested structures
 * - Audit logging
 *
 * @see workspace/lib/mcp-client.ts (PIITokenizer class)
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { PIITokenizer } from '../../workspace/lib/mcp-client.js';

describe('PIITokenizer', () => {
  let tokenizer: PIITokenizer;

  beforeEach(() => {
    tokenizer = new PIITokenizer();
  });

  describe('email tokenization', () => {
    it('should tokenize email addresses', () => {
      const input = 'Contact: john.doe@example.com';
      const tokenized = tokenizer.tokenize(input);

      expect(tokenized).not.toContain('john.doe@example.com');
      expect(tokenized).toMatch(/Contact: \[EMAIL_\d+\]/);
    });

    it('should tokenize multiple email addresses', () => {
      const input = 'Email 1: user1@example.com, Email 2: user2@test.org';
      const tokenized = tokenizer.tokenize(input);

      expect(tokenized).not.toContain('user1@example.com');
      expect(tokenized).not.toContain('user2@test.org');
      expect(tokenized).toContain('[EMAIL_0]');
      expect(tokenized).toContain('[EMAIL_1]');
    });

    it('should maintain consistency for duplicate emails', () => {
      const input = 'Email: test@example.com and again: test@example.com';
      const tokenized = tokenizer.tokenize(input);

      // Same email should get same token
      const matches = tokenized.match(/\[EMAIL_\d+\]/g);
      expect(matches).toHaveLength(2);
      expect(matches![0]).toBe(matches![1]);
    });

    it('should detokenize email addresses', () => {
      const input = 'Contact: user@example.com';
      const tokenized = tokenizer.tokenize(input);
      const detokenized = tokenizer.detokenize(tokenized);

      expect(detokenized).toBe(input);
    });
  });

  describe('phone number tokenization', () => {
    it('should tokenize phone numbers with dashes', () => {
      const input = 'Call: 555-123-4567';
      const tokenized = tokenizer.tokenize(input);

      expect(tokenized).not.toContain('555-123-4567');
      expect(tokenized).toMatch(/Call: \[PHONE_\d+\]/);
    });

    it('should tokenize phone numbers with dots', () => {
      const input = 'Phone: 555.123.4567';
      const tokenized = tokenizer.tokenize(input);

      expect(tokenized).toContain('[PHONE_0]');
      expect(tokenized).not.toContain('555.123.4567');
    });

    it('should tokenize phone numbers without separators', () => {
      const input = 'Mobile: 5551234567';
      const tokenized = tokenizer.tokenize(input);

      expect(tokenized).toContain('[PHONE_0]');
    });

    it('should detokenize phone numbers', () => {
      const input = 'Phone: 555-123-4567';
      const tokenized = tokenizer.tokenize(input);
      const detokenized = tokenizer.detokenize(tokenized);

      expect(detokenized).toBe(input);
    });
  });

  describe('SSN tokenization', () => {
    it('should tokenize Social Security Numbers', () => {
      const input = 'SSN: 123-45-6789';
      const tokenized = tokenizer.tokenize(input);

      expect(tokenized).not.toContain('123-45-6789');
      expect(tokenized).toContain('[SSN_0]');
    });

    it('should detokenize SSN', () => {
      const input = 'SSN: 987-65-4321';
      const tokenized = tokenizer.tokenize(input);
      const detokenized = tokenizer.detokenize(tokenized);

      expect(detokenized).toBe(input);
    });
  });

  describe('credit card tokenization', () => {
    it('should tokenize credit card numbers with spaces', () => {
      const input = 'Card: 4532 1234 5678 9010';
      const tokenized = tokenizer.tokenize(input);

      expect(tokenized).not.toContain('4532 1234 5678 9010');
      expect(tokenized).toContain('[CREDITCARD_0]');
    });

    it('should tokenize credit card numbers with dashes', () => {
      const input = 'Card: 4532-1234-5678-9010';
      const tokenized = tokenizer.tokenize(input);

      expect(tokenized).toContain('[CREDITCARD_0]');
    });

    it('should tokenize credit card numbers without separators', () => {
      const input = 'Card: 4532123456789010';
      const tokenized = tokenizer.tokenize(input);

      expect(tokenized).toContain('[CREDITCARD_0]');
    });

    it('should detokenize credit card numbers', () => {
      const input = 'Card: 4532-1234-5678-9010';
      const tokenized = tokenizer.tokenize(input);
      const detokenized = tokenizer.detokenize(tokenized);

      expect(detokenized).toBe(input);
    });
  });

  describe('IP address tokenization', () => {
    it('should tokenize IPv4 addresses', () => {
      const input = 'Server IP: 192.168.1.1';
      const tokenized = tokenizer.tokenize(input);

      expect(tokenized).not.toContain('192.168.1.1');
      expect(tokenized).toContain('[IPV4_0]');
    });

    it('should detokenize IP addresses', () => {
      const input = 'IP: 10.0.0.1';
      const tokenized = tokenizer.tokenize(input);
      const detokenized = tokenizer.detokenize(tokenized);

      expect(detokenized).toBe(input);
    });
  });

  describe('API key tokenization', () => {
    it('should tokenize API keys with sk_ prefix', () => {
      const input = 'Key: sk_live_EXAMPLE_NOT_REAL_KEY_123456';
      const tokenized = tokenizer.tokenize(input);

      expect(tokenized).not.toContain('sk_live_EXAMPLE_NOT_REAL_KEY_123456');
      expect(tokenized).toContain('[APIKEY_0]');
    });

    it('should tokenize API keys with pk_ prefix', () => {
      const input = 'Public key: pk_test_EXAMPLE_NOT_REAL_KEY_123456';
      const tokenized = tokenizer.tokenize(input);

      expect(tokenized).toContain('[APIKEY_0]');
    });

    it('should tokenize API keys with api_key_ prefix', () => {
      const input = 'API: api_key_1234567890abcdefghijklmnop';
      const tokenized = tokenizer.tokenize(input);

      expect(tokenized).toContain('[APIKEY_0]');
    });

    it('should detokenize API keys', () => {
      const input = 'Key: sk_live_test123456789abcdefgh';
      const tokenized = tokenizer.tokenize(input);
      const detokenized = tokenizer.detokenize(tokenized);

      expect(detokenized).toBe(input);
    });
  });

  describe('nested object tokenization', () => {
    it('should tokenize nested objects', () => {
      const input = {
        user: {
          email: 'user@example.com',
          phone: '555-123-4567',
        },
        admin: {
          email: 'admin@example.com',
        },
      };

      const tokenized = tokenizer.tokenize(input);

      expect(tokenized.user.email).toMatch(/\[EMAIL_\d+\]/);
      expect(tokenized.user.phone).toMatch(/\[PHONE_\d+\]/);
      expect(tokenized.admin.email).toMatch(/\[EMAIL_\d+\]/);
    });

    it('should detokenize nested objects', () => {
      const input = {
        user: {
          email: 'test@example.com',
          phone: '555-999-8888',
        },
      };

      const tokenized = tokenizer.tokenize(input);
      const detokenized = tokenizer.detokenize(tokenized);

      expect(detokenized).toEqual(input);
    });

    it('should handle deeply nested objects', () => {
      const input = {
        level1: {
          level2: {
            level3: {
              email: 'deep@example.com',
            },
          },
        },
      };

      const tokenized = tokenizer.tokenize(input);
      const detokenized = tokenizer.detokenize(tokenized);

      expect(detokenized).toEqual(input);
    });
  });

  describe('array tokenization', () => {
    it('should tokenize arrays of strings', () => {
      const input = ['user1@example.com', 'user2@example.com', 'user3@example.com'];
      const tokenized = tokenizer.tokenize(input);

      expect(tokenized[0]).toMatch(/\[EMAIL_\d+\]/);
      expect(tokenized[1]).toMatch(/\[EMAIL_\d+\]/);
      expect(tokenized[2]).toMatch(/\[EMAIL_\d+\]/);
    });

    it('should tokenize arrays of objects', () => {
      const input = [
        { email: 'user1@example.com' },
        { email: 'user2@example.com' },
      ];

      const tokenized = tokenizer.tokenize(input);

      expect(tokenized[0].email).toMatch(/\[EMAIL_\d+\]/);
      expect(tokenized[1].email).toMatch(/\[EMAIL_\d+\]/);
    });

    it('should detokenize arrays', () => {
      const input = ['test1@example.com', 'test2@example.com'];
      const tokenized = tokenizer.tokenize(input);
      const detokenized = tokenizer.detokenize(tokenized);

      expect(detokenized).toEqual(input);
    });
  });

  describe('mixed data types', () => {
    it('should handle objects with mixed types', () => {
      const input = {
        email: 'user@example.com',
        age: 30,
        active: true,
        score: null,
        metadata: undefined,
      };

      const tokenized = tokenizer.tokenize(input);

      expect(tokenized.email).toMatch(/\[EMAIL_\d+\]/);
      expect(tokenized.age).toBe(30);
      expect(tokenized.active).toBe(true);
      expect(tokenized.score).toBeNull();
      expect(tokenized.metadata).toBeUndefined();
    });

    it('should handle complex nested structures', () => {
      const input = {
        users: [
          { email: 'user1@example.com', phone: '555-111-2222' },
          { email: 'user2@example.com', phone: '555-333-4444' },
        ],
        admin: {
          contact: {
            email: 'admin@example.com',
            phone: '555-999-0000',
          },
        },
        metadata: {
          server: '192.168.1.100',
          apiKey: 'sk_live_test1234567890abcdef',
        },
      };

      const tokenized = tokenizer.tokenize(input);
      const detokenized = tokenizer.detokenize(tokenized);

      expect(detokenized).toEqual(input);
    });
  });

  describe('statistics and audit log', () => {
    it('should track tokenization statistics', () => {
      tokenizer.tokenize('Email: user@example.com, Phone: 555-123-4567');

      const stats = tokenizer.getStats();

      expect(stats.totalTokenized).toBe(2);
      expect(stats.tokenizedByType.email).toBe(1);
      expect(stats.tokenizedByType.phone).toBe(1);
      expect(stats.auditLogSize).toBeGreaterThan(0);
    });

    it('should maintain audit log', () => {
      tokenizer.tokenize('user@example.com');
      tokenizer.tokenize('555-123-4567');

      const log = tokenizer.getAuditLog();

      expect(log.length).toBeGreaterThan(0);
      expect(log[0]).toHaveProperty('timestamp');
      expect(log[0]).toHaveProperty('action');
      expect(log[0]).toHaveProperty('type');
      expect(log[0]).toHaveProperty('count');
    });

    it('should limit audit log entries', () => {
      tokenizer.tokenize('user1@example.com');
      tokenizer.tokenize('user2@example.com');
      tokenizer.tokenize('user3@example.com');

      const log = tokenizer.getAuditLog(2);

      expect(log.length).toBe(2);
    });

    it('should record both tokenize and detokenize actions', () => {
      const input = 'user@example.com';
      const tokenized = tokenizer.tokenize(input);
      tokenizer.detokenize(tokenized);

      const log = tokenizer.getAuditLog();
      const actions = log.map((entry) => entry.action);

      expect(actions).toContain('tokenize');
      expect(actions).toContain('detokenize');
    });
  });

  describe('mapping persistence', () => {
    it('should export tokenization mapping', () => {
      tokenizer.tokenize('user@example.com');
      tokenizer.tokenize('555-123-4567');

      const mapping = tokenizer.exportMapping();

      expect(mapping.tokenMap.length).toBeGreaterThan(0);
      expect(mapping.reverseMap.length).toBeGreaterThan(0);
      expect(mapping.tokenCounter.length).toBeGreaterThan(0);
    });

    it('should import tokenization mapping', () => {
      // Tokenize with first instance
      const original = 'user@example.com';
      const tokenized1 = tokenizer.tokenize(original);

      // Export mapping
      const mapping = tokenizer.exportMapping();

      // Create new tokenizer and import
      const tokenizer2 = new PIITokenizer();
      tokenizer2.importMapping(mapping);

      // Detokenize with second instance
      const detokenized = tokenizer2.detokenize(tokenized1);

      expect(detokenized).toBe(original);
    });

    it('should maintain consistency across export/import', () => {
      const input = {
        email: 'test@example.com',
        phone: '555-999-8888',
        ssn: '123-45-6789',
      };

      const tokenized = tokenizer.tokenize(input);
      const mapping = tokenizer.exportMapping();

      const tokenizer2 = new PIITokenizer();
      tokenizer2.importMapping(mapping);

      const detokenized = tokenizer2.detokenize(tokenized);

      expect(detokenized).toEqual(input);
    });
  });

  describe('clear functionality', () => {
    it('should clear all tokenization data', () => {
      tokenizer.tokenize('user@example.com');
      tokenizer.tokenize('555-123-4567');

      expect(tokenizer.getStats().totalTokenized).toBe(2);

      tokenizer.clear();

      expect(tokenizer.getStats().totalTokenized).toBe(0);
      expect(tokenizer.getStats().auditLogSize).toBe(0);
    });

    it('should not be able to detokenize after clear', () => {
      const input = 'user@example.com';
      const tokenized = tokenizer.tokenize(input);

      tokenizer.clear();

      const detokenized = tokenizer.detokenize(tokenized);

      // Cannot detokenize without mapping
      expect(detokenized).toBe(tokenized);
      expect(detokenized).not.toBe(input);
    });
  });

  describe('edge cases', () => {
    it('should handle empty strings', () => {
      const tokenized = tokenizer.tokenize('');
      expect(tokenized).toBe('');
    });

    it('should handle null values', () => {
      const tokenized = tokenizer.tokenize(null);
      expect(tokenized).toBeNull();
    });

    it('should handle undefined values', () => {
      const tokenized = tokenizer.tokenize(undefined);
      expect(tokenized).toBeUndefined();
    });

    it('should handle numbers', () => {
      const tokenized = tokenizer.tokenize(42);
      expect(tokenized).toBe(42);
    });

    it('should handle booleans', () => {
      expect(tokenizer.tokenize(true)).toBe(true);
      expect(tokenizer.tokenize(false)).toBe(false);
    });

    it('should handle empty objects', () => {
      const tokenized = tokenizer.tokenize({});
      expect(tokenized).toEqual({});
    });

    it('should handle empty arrays', () => {
      const tokenized = tokenizer.tokenize([]);
      expect(tokenized).toEqual([]);
    });

    it('should prevent infinite recursion', () => {
      // Create circular reference (won't actually recurse infinitely due to depth limit)
      const obj: any = { email: 'test@example.com' };
      obj.self = obj;

      // Should not throw
      expect(() => tokenizer.tokenize(obj)).not.toThrow();
    });

    it('should handle strings without PII', () => {
      const input = 'This is just plain text with no sensitive data';
      const tokenized = tokenizer.tokenize(input);

      expect(tokenized).toBe(input);
      expect(tokenizer.getStats().totalTokenized).toBe(0);
    });

    it('should handle mixed PII in single string', () => {
      const input = 'Contact: user@example.com, Phone: 555-123-4567, SSN: 123-45-6789';
      const tokenized = tokenizer.tokenize(input);

      expect(tokenized).toContain('[EMAIL_0]');
      expect(tokenized).toContain('[PHONE_0]');
      expect(tokenized).toContain('[SSN_0]');
      expect(tokenized).not.toContain('user@example.com');
      expect(tokenized).not.toContain('555-123-4567');
      expect(tokenized).not.toContain('123-45-6789');
    });
  });

  describe('security validation', () => {
    it('should not leak PII in tokenized output', () => {
      const sensitiveData = {
        email: 'sensitive@example.com',
        ssn: '987-65-4321',
        creditCard: '4532-1234-5678-9010',
        apiKey: 'sk_live_secret123456789abcdefg',
      };

      const tokenized = tokenizer.tokenize(sensitiveData);
      const tokenizedString = JSON.stringify(tokenized);

      // Verify no PII in tokenized data
      expect(tokenizedString).not.toContain('sensitive@example.com');
      expect(tokenizedString).not.toContain('987-65-4321');
      expect(tokenizedString).not.toContain('4532-1234-5678-9010');
      expect(tokenizedString).not.toContain('sk_live_secret123456789abcdefg');

      // Verify tokens are present
      expect(tokenizedString).toContain('[EMAIL_');
      expect(tokenizedString).toContain('[SSN_');
      expect(tokenizedString).toContain('[CREDITCARD_');
      expect(tokenizedString).toContain('[APIKEY_');
    });

    it('should maintain PII confidentiality in audit log', () => {
      tokenizer.tokenize('user@example.com');

      const log = tokenizer.getAuditLog();
      const logString = JSON.stringify(log);

      // Audit log should not contain actual PII
      expect(logString).not.toContain('user@example.com');
    });

    it('should handle special characters in PII', () => {
      const input = 'Email: test+tag@example.com';
      const tokenized = tokenizer.tokenize(input);

      expect(tokenized).toContain('[EMAIL_0]');
      expect(tokenized).not.toContain('test+tag@example.com');

      const detokenized = tokenizer.detokenize(tokenized);
      expect(detokenized).toBe(input);
    });
  });
});
