import { describe, it, expect } from 'vitest';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const AdminBreakout = require('../src/AdminBreakout.js');
const AdminSettings = require('../src/AdminSettings.js');

describe('_renderOutputPath', () => {
  // 2026-05-02 in UTC
  const ctx = { nowMs: Date.UTC(2026, 4, 2, 13, 30, 0), setting_id: 's-abc12345' };

  it('substitutes {{date}} as YYYY-MM-DD UTC', () => {
    const path = AdminBreakout._renderOutputPath('exports/{{date}}/responses.csv', ctx);
    expect(path).toBe('exports/2026-05-02/responses.csv');
  });

  it('substitutes {{setting_id}}', () => {
    const path = AdminBreakout._renderOutputPath('s/{{setting_id}}/dump.csv', ctx);
    expect(path).toBe('s/s-abc12345/dump.csv');
  });

  it('substitutes both placeholders, multiple occurrences', () => {
    const path = AdminBreakout._renderOutputPath(
      '{{setting_id}}/{{date}}/{{setting_id}}-{{date}}.csv',
      ctx,
    );
    expect(path).toBe('s-abc12345/2026-05-02/s-abc12345-2026-05-02.csv');
  });

  it('leaves unknown placeholders untouched', () => {
    const path = AdminBreakout._renderOutputPath('{{date}}/{{unknown}}.csv', ctx);
    expect(path).toBe('2026-05-02/{{unknown}}.csv');
  });
});

describe('_csvEscape', () => {
  it('passes through plain strings', () => {
    expect(AdminBreakout._csvEscape('hello')).toBe('hello');
  });

  it('coerces numbers and booleans', () => {
    expect(AdminBreakout._csvEscape(42)).toBe('42');
    expect(AdminBreakout._csvEscape(true)).toBe('true');
  });

  it('returns empty string for null/undefined', () => {
    expect(AdminBreakout._csvEscape(null)).toBe('');
    expect(AdminBreakout._csvEscape(undefined)).toBe('');
  });

  it('quotes values with commas', () => {
    expect(AdminBreakout._csvEscape('a,b')).toBe('"a,b"');
  });

  it('doubles internal quotes and wraps in quotes', () => {
    expect(AdminBreakout._csvEscape('he said "hi"')).toBe('"he said ""hi"""');
  });

  it('quotes values with newlines or carriage returns', () => {
    expect(AdminBreakout._csvEscape('line1\nline2')).toBe('"line1\nline2"');
    expect(AdminBreakout._csvEscape('line1\r\nline2')).toBe('"line1\r\nline2"');
  });
});

describe('_buildCsv', () => {
  it('emits header row and CRLF line endings (RFC 4180)', () => {
    const csv = AdminBreakout._buildCsv(
      ['id', 'name'],
      [{ id: 1, name: 'Ada' }, { id: 2, name: 'Grace' }],
    );
    expect(csv).toBe('id,name\r\n1,Ada\r\n2,Grace\r\n');
  });

  it('includes columns missing from a row as empty cells', () => {
    const csv = AdminBreakout._buildCsv(
      ['id', 'name', 'email'],
      [{ id: 1, name: 'Ada' }],
    );
    expect(csv).toBe('id,name,email\r\n1,Ada,\r\n');
  });

  it('respects column ordering even when row keys differ', () => {
    const csv = AdminBreakout._buildCsv(
      ['name', 'id'],
      [{ id: 1, name: 'Ada' }],
    );
    expect(csv).toBe('name,id\r\nAda,1\r\n');
  });

  it('emits header-only output when rows are empty', () => {
    const csv = AdminBreakout._buildCsv(['a', 'b'], []);
    expect(csv).toBe('a,b\r\n');
  });
});

describe('_parseIncludedColumns', () => {
  const fallback = ['col1', 'col2'];

  it('returns fallback when input is empty', () => {
    expect(AdminBreakout._parseIncludedColumns('', fallback)).toBe(fallback);
    expect(AdminBreakout._parseIncludedColumns(null, fallback)).toBe(fallback);
  });

  it('returns the parsed array on valid JSON', () => {
    expect(AdminBreakout._parseIncludedColumns('["a","b"]', fallback)).toEqual(['a', 'b']);
  });

  it('returns fallback on invalid JSON', () => {
    expect(AdminBreakout._parseIncludedColumns('not json', fallback)).toBe(fallback);
  });

  it('returns fallback when parsed value is not an array', () => {
    expect(AdminBreakout._parseIncludedColumns('{"a":1}', fallback)).toBe(fallback);
  });

  it('drops non-string entries from a parsed array', () => {
    expect(AdminBreakout._parseIncludedColumns('["a", 42, "b"]', fallback)).toEqual(['a', 'b']);
  });

  it('returns fallback when array is empty (no narrowing intended)', () => {
    expect(AdminBreakout._parseIncludedColumns('[]', fallback)).toBe(fallback);
  });
});

describe('_validateInterval', () => {
  it('accepts integers between 5 and 1440', () => {
    expect(AdminSettings._validateInterval(5)).toBe(true);
    expect(AdminSettings._validateInterval(60)).toBe(true);
    expect(AdminSettings._validateInterval(1440)).toBe(true);
  });

  it('rejects values below 5', () => {
    expect(AdminSettings._validateInterval(4)).toBe(false);
    expect(AdminSettings._validateInterval(0)).toBe(false);
  });

  it('rejects values above 1440', () => {
    expect(AdminSettings._validateInterval(1441)).toBe(false);
    expect(AdminSettings._validateInterval(2880)).toBe(false);
  });

  it('rejects non-integers', () => {
    expect(AdminSettings._validateInterval(5.5)).toBe(false);
  });

  it('rejects non-numbers', () => {
    expect(AdminSettings._validateInterval('60')).toBe(false);
    expect(AdminSettings._validateInterval(null)).toBe(false);
  });
});

describe('_validateOutputTemplate', () => {
  it('accepts simple paths', () => {
    expect(AdminSettings._validateOutputTemplate('exports/responses.csv')).toBe(true);
  });

  it('accepts paths with placeholders', () => {
    expect(AdminSettings._validateOutputTemplate('exports/{{date}}/{{setting_id}}.csv')).toBe(true);
  });

  it('rejects empty', () => {
    expect(AdminSettings._validateOutputTemplate('')).toBe(false);
  });

  it('rejects leading slash', () => {
    expect(AdminSettings._validateOutputTemplate('/exports/responses.csv')).toBe(false);
  });

  it('rejects backslash', () => {
    expect(AdminSettings._validateOutputTemplate('exports\\responses.csv')).toBe(false);
  });

  it('rejects path traversal', () => {
    expect(AdminSettings._validateOutputTemplate('exports/../etc.csv')).toBe(false);
  });

  it('rejects non-strings', () => {
    expect(AdminSettings._validateOutputTemplate(42)).toBe(false);
    expect(AdminSettings._validateOutputTemplate(null)).toBe(false);
  });
});
