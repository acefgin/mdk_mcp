/**
 * Tests for PII Tokenization System
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { PIITokenizer, PIIType } from '../pii-tokenizer';
import { promises as fs } from 'fs';

describe('PIITokenizer', () => {
  let tokenizer: PIITokenizer;

  beforeEach(() => {
    tokenizer = new PIITokenizer({ enableAuditLog: true });
  });

  afterEach(() => {
    tokenizer.clear();
  });

  describe('Email Detection', () => {
    it('should tokenize email addresses', () => {
      const input = 'Contact us at support@example.com for help';
      const result = tokenizer.tokenize(input);

      expect(result).not.toContain('support@example.com');
      expect(result).toContain('PII_TOKEN_');
    });

    it('should tokenize multiple emails', () => {
      const input = 'Email john@example.com or jane@example.org';
      const result = tokenizer.tokenize(input);

      expect(result).not.toContain('john@example.com');
      expect(result).not.toContain('jane@example.org');

      const tokens = result.match(/PII_TOKEN_[a-f0-9]{32}/g);
      expect(tokens).toHaveLength(2);
    });

    it('should detokenize emails correctly', () => {
      const input = 'Email: user@example.com';
      const tokenized = tokenizer.tokenize(input);
      const detokenized = tokenizer.detokenize(tokenized);

      expect(detokenized).toBe(input);
    });
  });

  describe('Phone Number Detection', () => {
    it('should tokenize US phone numbers', () => {
      const input = 'Call us at 555-123-4567';
      const result = tokenizer.tokenize(input);

      expect(result).not.toContain('555-123-4567');
      expect(result).toContain('PII_TOKEN_');
    });

    it('should tokenize phone numbers with parentheses', () => {
      const input = 'Phone: (555) 123-4567';
      const result = tokenizer.tokenize(input);

      expect(result).not.toContain('(555) 123-4567');
      expect(result).toContain('PII_TOKEN_');
    });

    it('should tokenize phone numbers with +1 prefix', () => {
      const input = 'International: +1-555-123-4567';
      const result = tokenizer.tokenize(input);

      expect(result).not.toContain('+1-555-123-4567');
      expect(result).toContain('PII_TOKEN_');
    });
  });

  describe('SSN Detection', () => {
    it('should tokenize Social Security Numbers', () => {
      const input = 'SSN: 123-45-6789';
      const result = tokenizer.tokenize(input);

      expect(result).not.toContain('123-45-6789');
      expect(result).toContain('PII_TOKEN_');
    });

    it('should detokenize SSN correctly', () => {
      const input = 'Patient SSN: 987-65-4321';
      const tokenized = tokenizer.tokenize(input);
      const detokenized = tokenizer.detokenize(tokenized);

      expect(detokenized).toBe(input);
    });
  });

  describe('Credit Card Detection', () => {
    it('should tokenize credit card numbers', () => {
      const input = 'Card: 4532-1234-5678-9010';
      const result = tokenizer.tokenize(input);

      expect(result).not.toContain('4532-1234-5678-9010');
      expect(result).toContain('PII_TOKEN_');
    });

    it('should tokenize credit cards without dashes', () => {
      const input = 'Card: 4532123456789010';
      const result = tokenizer.tokenize(input);

      expect(result).not.toContain('4532123456789010');
      expect(result).toContain('PII_TOKEN_');
    });

    it('should tokenize credit cards with spaces', () => {
      const input = 'Card: 4532 1234 5678 9010';
      const result = tokenizer.tokenize(input);

      expect(result).not.toContain('4532 1234 5678 9010');
      expect(result).toContain('PII_TOKEN_');
    });
  });

  describe('IP Address Detection', () => {
    it('should tokenize IPv4 addresses', () => {
      const input = 'Server: 192.168.1.100';
      const result = tokenizer.tokenize(input);

      expect(result).not.toContain('192.168.1.100');
      expect(result).toContain('PII_TOKEN_');
    });

    it('should tokenize multiple IP addresses', () => {
      const input = 'From 10.0.0.1 to 10.0.0.255';
      const result = tokenizer.tokenize(input);

      expect(result).not.toContain('10.0.0.1');
      expect(result).not.toContain('10.0.0.255');

      const tokens = result.match(/PII_TOKEN_[a-f0-9]{32}/g);
      expect(tokens).toHaveLength(2);
    });
  });

  describe('API Key Detection', () => {
    it('should tokenize API keys', () => {
      const input = 'api_key: abc123def456ghi789jkl012mno345pqr678';
      const result = tokenizer.tokenize(input);

      expect(result).not.toContain('abc123def456ghi789jkl012mno345pqr678');
      expect(result).toContain('PII_TOKEN_');
    });

    it('should tokenize access tokens', () => {
      const input = 'access_token=xyz123abc456def789ghi012jkl345mno678';
      const result = tokenizer.tokenize(input);

      expect(result).not.toContain('xyz123abc456def789ghi012jkl345mno678');
      expect(result).toContain('PII_TOKEN_');
    });
  });

  describe('Object Tokenization', () => {
    it('should tokenize PII in objects', () => {
      const input = {
        name: 'John Doe',
        email: 'john@example.com',
        phone: '555-123-4567',
      };

      const result = tokenizer.tokenize(input);

      expect(result.name).toBe('John Doe'); // No PII
      expect(result.email).not.toBe('john@example.com');
      expect(result.email).toContain('PII_TOKEN_');
      expect(result.phone).not.toBe('555-123-4567');
      expect(result.phone).toContain('PII_TOKEN_');
    });

    it('should tokenize PII in nested objects', () => {
      const input = {
        user: {
          contact: {
            email: 'user@example.com',
            phone: '555-987-6543',
          },
        },
      };

      const result = tokenizer.tokenize(input);

      expect(result.user.contact.email).toContain('PII_TOKEN_');
      expect(result.user.contact.phone).toContain('PII_TOKEN_');
    });

    it('should detokenize objects correctly', () => {
      const input = {
        email: 'test@example.com',
        data: 'Some data',
      };

      const tokenized = tokenizer.tokenize(input);
      const detokenized = tokenizer.detokenize(tokenized);

      expect(detokenized).toEqual(input);
    });
  });

  describe('Array Tokenization', () => {
    it('should tokenize PII in arrays', () => {
      const input = ['user1@example.com', 'user2@example.com', 'user3@example.com'];

      const result = tokenizer.tokenize(input);

      expect(result[0]).toContain('PII_TOKEN_');
      expect(result[1]).toContain('PII_TOKEN_');
      expect(result[2]).toContain('PII_TOKEN_');
      expect(result).toHaveLength(3);
    });

    it('should detokenize arrays correctly', () => {
      const input = ['email1@test.com', 'email2@test.com'];
      const tokenized = tokenizer.tokenize(input);
      const detokenized = tokenizer.detokenize(tokenized);

      expect(detokenized).toEqual(input);
    });
  });

  describe('Statistics', () => {
    it('should track tokenization statistics', () => {
      tokenizer.tokenize('Email: user@example.com, Phone: 555-123-4567');

      const stats = tokenizer.getStats();

      expect(stats.totalTokens).toBe(2);
      expect(stats.tokensByType[PIIType.EMAIL]).toBe(1);
      expect(stats.tokensByType[PIIType.PHONE]).toBe(1);
      expect(stats.oldestToken).toBeDefined();
      expect(stats.newestToken).toBeDefined();
    });

    it('should show zero stats for empty tokenizer', () => {
      const stats = tokenizer.getStats();

      expect(stats.totalTokens).toBe(0);
      expect(stats.oldestToken).toBeNull();
      expect(stats.newestToken).toBeNull();
    });
  });

  describe('Export/Import', () => {
    it('should export token mappings', () => {
      tokenizer.tokenize('Email: test@example.com');

      const exported = tokenizer.export();
      const data = JSON.parse(exported);

      expect(data).toHaveProperty('version');
      expect(data).toHaveProperty('timestamp');
      expect(data).toHaveProperty('tokens');
      expect(data.tokens).toHaveLength(1);
      expect(data.tokens[0]).toHaveProperty('token');
      expect(data.tokens[0]).toHaveProperty('originalValue');
      expect(data.tokens[0]).toHaveProperty('type');
    });

    it('should import token mappings', () => {
      const input = 'Contact: admin@example.com';
      const tokenized = tokenizer.tokenize(input);

      const exported = tokenizer.export();

      const newTokenizer = new PIITokenizer();
      newTokenizer.import(exported);

      const detokenized = newTokenizer.detokenize(tokenized);
      expect(detokenized).toBe(input);
    });

    it('should clear existing mappings on import', () => {
      tokenizer.tokenize('user1@example.com');
      expect(tokenizer.getStats().totalTokens).toBe(1);

      const otherTokenizer = new PIITokenizer();
      otherTokenizer.tokenize('user2@example.com');
      const exported = otherTokenizer.export();

      tokenizer.import(exported);
      expect(tokenizer.getStats().totalTokens).toBe(1);
    });

    it('should handle invalid import data', () => {
      expect(() => {
        tokenizer.import('invalid json');
      }).toThrow();

      expect(() => {
        tokenizer.import('{"invalid": "format"}');
      }).toThrow('Invalid export format');
    });
  });

  describe('Clear', () => {
    it('should clear all token mappings', () => {
      tokenizer.tokenize('Email: test@example.com, Phone: 555-123-4567');

      expect(tokenizer.getStats().totalTokens).toBe(2);

      tokenizer.clear();

      expect(tokenizer.getStats().totalTokens).toBe(0);
    });
  });

  describe('Pattern Enable/Disable', () => {
    it('should allow disabling specific patterns', () => {
      tokenizer.setPatternEnabled(PIIType.EMAIL, false);

      const input = 'Email: test@example.com, Phone: 555-123-4567';
      const result = tokenizer.tokenize(input);

      expect(result).toContain('test@example.com'); // Email not tokenized
      expect(result).not.toContain('555-123-4567'); // Phone still tokenized
    });

    it('should allow re-enabling patterns', () => {
      tokenizer.setPatternEnabled(PIIType.EMAIL, false);
      tokenizer.setPatternEnabled(PIIType.EMAIL, true);

      const input = 'Email: test@example.com';
      const result = tokenizer.tokenize(input);

      expect(result).not.toContain('test@example.com');
      expect(result).toContain('PII_TOKEN_');
    });
  });

  describe('Audit Logging', () => {
    it('should log tokenization operations', () => {
      tokenizer.tokenize('Email: test@example.com');

      const log = tokenizer.getAuditLog();

      expect(log).toHaveLength(1);
      expect(log[0].operation).toBe('tokenize');
      expect(log[0].count).toBe(1);
      expect(log[0].timestamp).toBeDefined();
    });

    it('should log detokenization operations', () => {
      const tokenized = tokenizer.tokenize('Email: test@example.com');
      tokenizer.detokenize(tokenized);

      const log = tokenizer.getAuditLog();

      expect(log).toHaveLength(2);
      expect(log[0].operation).toBe('tokenize');
      expect(log[1].operation).toBe('detokenize');
    });

    it('should log export operations', () => {
      tokenizer.tokenize('Email: test@example.com');
      tokenizer.export();

      const log = tokenizer.getAuditLog();

      expect(log.some(entry => entry.operation === 'export')).toBe(true);
    });

    it('should log import operations', () => {
      const otherTokenizer = new PIITokenizer();
      otherTokenizer.tokenize('test@example.com');
      const exported = otherTokenizer.export();

      tokenizer.import(exported);

      const log = tokenizer.getAuditLog();
      expect(log.some(entry => entry.operation === 'import')).toBe(true);
    });

    it('should log clear operations', () => {
      tokenizer.tokenize('test@example.com');
      tokenizer.clear();

      const log = tokenizer.getAuditLog();
      expect(log.some(entry => entry.operation === 'clear')).toBe(true);
    });

    it('should limit audit log to 1000 entries', () => {
      // Create 1100 entries
      for (let i = 0; i < 1100; i++) {
        tokenizer.tokenize(`email${i}@example.com`);
      }

      const log = tokenizer.getAuditLog();
      expect(log.length).toBeLessThanOrEqual(1000);
    });

    it('should not log when audit logging is disabled', () => {
      const noLogTokenizer = new PIITokenizer({ enableAuditLog: false });
      noLogTokenizer.tokenize('test@example.com');

      const log = noLogTokenizer.getAuditLog();
      expect(log).toHaveLength(0);
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty strings', () => {
      const result = tokenizer.tokenize('');
      expect(result).toBe('');
    });

    it('should handle null values', () => {
      const result = tokenizer.tokenize(null);
      expect(result).toBeNull();
    });

    it('should handle undefined values', () => {
      const result = tokenizer.tokenize(undefined);
      expect(result).toBeUndefined();
    });

    it('should handle numbers', () => {
      const result = tokenizer.tokenize(12345);
      expect(result).toBe(12345);
    });

    it('should handle booleans', () => {
      const result = tokenizer.tokenize(true);
      expect(result).toBe(true);
    });

    it('should handle text without PII', () => {
      const input = 'This text contains no PII data';
      const result = tokenizer.tokenize(input);
      expect(result).toBe(input);
    });

    it('should not double-tokenize already tokenized data', () => {
      const input = 'Email: test@example.com';
      const tokenized1 = tokenizer.tokenize(input);
      const tokenized2 = tokenizer.tokenize(tokenized1);

      expect(tokenized1).toBe(tokenized2);
    });
  });

  describe('Complex Scenarios', () => {
    it('should handle mixed PII types', () => {
      const input = `
        Contact Information:
        Email: john.doe@example.com
        Phone: (555) 123-4567
        SSN: 123-45-6789
        Card: 4532-1234-5678-9010
        IP: 192.168.1.1
        API Key: api_key=abc123def456ghi789jkl012mno345pqr678
      `;

      const tokenized = tokenizer.tokenize(input);

      expect(tokenized).not.toContain('john.doe@example.com');
      expect(tokenized).not.toContain('(555) 123-4567');
      expect(tokenized).not.toContain('123-45-6789');
      expect(tokenized).not.toContain('4532-1234-5678-9010');
      expect(tokenized).not.toContain('192.168.1.1');
      expect(tokenized).not.toContain('abc123def456ghi789jkl012mno345pqr678');

      const stats = tokenizer.getStats();
      expect(stats.totalTokens).toBeGreaterThanOrEqual(5); // At least 5 PII types detected
    });

    it('should maintain data structure integrity', () => {
      const input = {
        users: [
          { name: 'Alice', email: 'alice@example.com' },
          { name: 'Bob', email: 'bob@example.com' },
        ],
        metadata: {
          server: '192.168.1.100',
          apiKey: 'api_key: secret123abc456def789ghi012jkl345mno678',
        },
      };

      const tokenized = tokenizer.tokenize(input);
      const detokenized = tokenizer.detokenize(tokenized);

      expect(detokenized).toEqual(input);
      expect(detokenized.users).toHaveLength(2);
      expect(detokenized.users[0].name).toBe('Alice');
      expect(detokenized.users[1].name).toBe('Bob');
    });
  });
});
