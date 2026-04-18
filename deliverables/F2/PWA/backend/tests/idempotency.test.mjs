import { describe, it, expect } from 'vitest';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const { findExistingSubmission } = require('../src/Idempotency.js');

function makeReader(rows) {
  return {
    readClientIdsColumn: function () {
      return rows.map(function (r) { return [r.client_submission_id]; });
    },
    readRowByNumber: function (n) {
      var row = rows.filter(function (r) { return r.rowNumber === n; })[0];
      return row ? row : null;
    },
    headerRowOffset: function () { return 1; },
  };
}

describe('findExistingSubmission', () => {
  it('returns null when the sheet has no matching client_submission_id', () => {
    const reader = makeReader([
      { client_submission_id: 'A', submission_id: 'srv-1', rowNumber: 2 },
      { client_submission_id: 'B', submission_id: 'srv-2', rowNumber: 3 },
    ]);
    expect(findExistingSubmission(reader, 'Z')).toBeNull();
  });

  it('returns the existing submission_id for a match', () => {
    const reader = makeReader([
      { client_submission_id: 'A', submission_id: 'srv-1', rowNumber: 2 },
      { client_submission_id: 'B', submission_id: 'srv-2', rowNumber: 3 },
    ]);
    const result = findExistingSubmission(reader, 'B');
    expect(result).toEqual({ submission_id: 'srv-2', row_number: 3 });
  });

  it('returns null for empty sheet', () => {
    const reader = makeReader([]);
    expect(findExistingSubmission(reader, 'anything')).toBeNull();
  });

  it('skips blank client_submission_id cells', () => {
    const reader = makeReader([
      { client_submission_id: '', submission_id: '', rowNumber: 2 },
      { client_submission_id: 'X', submission_id: 'srv-x', rowNumber: 3 },
    ]);
    expect(findExistingSubmission(reader, 'X')).toEqual({ submission_id: 'srv-x', row_number: 3 });
  });
});
