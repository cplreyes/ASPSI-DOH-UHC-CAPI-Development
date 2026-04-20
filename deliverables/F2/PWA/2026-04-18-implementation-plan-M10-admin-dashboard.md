# M10 — Admin Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship an Apps Script-served HTML admin dashboard (HtmlService) that gives ASPSI operators read-only views of `F2_Responses`, `F2_Audit`, and `F2_DLQ` — filter by facility/status/event/date, sort newest-first, export CSV per view — gated by a separate `ADMIN_SECRET` (not the HMAC secret used by the PWA).

**Architecture:** Pure-JS admin handlers added to `backend/src/AdminHandlers.js` (filter + CSV functions, fully testable in Node), new `readAll(limit, offset)` methods on the existing `responses/audit/dlq` ctx builders in `apps-script/Code.js`, a `doGet(?action=admin)` branch that returns `HtmlService.createTemplateFromFile('Admin').evaluate()`, and a browser-side UI (`apps-script/Admin.html`) that uses `google.script.run` to call `AdminGlue.js` server functions. Auth pattern: operator types the ADMIN_SECRET into the login view, the client holds it in memory, every RPC passes it back, every server function verifies it with constant-time compare before returning data. No cookies, no sessions — simple token-in-memory.

**Tech Stack:** Google Apps Script (HtmlService, V8 runtime, PropertiesService), vanilla HTML + CSS + JS (no frameworks — Functional, not polished per spec §4.7), Vitest + Node 20 for pure-function TDD.

---

## File Structure

```
deliverables/F2/PWA/backend/
├── src/
│   └── AdminHandlers.js          # NEW — pure functions: verifyAdminToken, filterResponses,
│                                 #        filterAudit, listDlq, rowsToCsv
│
├── apps-script/
│   ├── Code.js                   # MODIFY — extend _buildResponsesCtx/_buildAuditCtx/_buildDlqCtx
│   │                             #           with readAll(limit, offset); add doGet(?action=admin)
│   ├── AdminGlue.js              # NEW — google.script.run-callable wrappers:
│   │                             #        adminAuth, adminListResponses, adminListAudit,
│   │                             #        adminListDlq, adminExportCsv
│   ├── Admin.html                # NEW — login view + tabs (Responses / Audit / DLQ)
│   │                             #        + filter controls + CSV download buttons
│   └── Setup.js                  # MODIFY — generate ADMIN_SECRET on first run
│
├── tests/
│   └── admin-handlers.test.mjs   # NEW — Vitest for every pure function in AdminHandlers.js
│
├── scripts/
│   └── build.mjs                 # MODIFY — include AdminGlue.js in concat order;
│                                 #          copy Admin.html into dist/
│
└── README.md                     # MODIFY — add "Admin dashboard" section with URL + secret
```

**Responsibility boundaries:**

- `src/AdminHandlers.js`: stateless pure functions, no Apps Script globals, no I/O. Filtering accepts arrays of row objects and a filters object; CSV accepts column list + rows.
- `apps-script/AdminGlue.js`: the *only* place that knows about `PropertiesService`, sheet ctx, and HTML template rendering for the admin. Every exported function begins with `_requireAdmin_(token)`.
- `apps-script/Admin.html`: the browser UI. Uses `google.script.run.withSuccessHandler(...).adminXxx(...)` — no `fetch`, no HMAC (HtmlService handles Google auth).
- `tests/admin-handlers.test.mjs`: covers every pure function; verifies filter/CSV edge cases (quotes, commas, newlines, empty result sets, date-range boundaries).

---

## Architectural Decisions (locked in)

1. **Separate admin secret.** `ADMIN_SECRET` is a second ScriptProperty, generated on first `setupBackend()` run. The PWA's `HMAC_SECRET` is never used for admin auth — different threat model (operator in a browser, not a fingerprinted device), different rotation schedule.
2. **Token-in-memory auth.** Operator types the secret into the login view; client JS stores it in a JS variable; every `google.script.run` call forwards it; server verifies on every RPC via constant-time compare. On failure, server throws; client catches via `withFailureHandler`, wipes token, returns to login view. No refresh tokens, no cookies, no session storage — the operator must re-enter the secret each time they reload the tab. Acceptable for ops-only use.
3. **Read-only.** M10 exposes no mutations. Kill-switch / broadcast-message editing is deferred to M11 (explicit spec: §4.7 "Read-only views"). DLQ rows are *surfaced*, not *deleted* or *requeued*.
4. **Pagination via limit/offset.** Default `limit=500`, `offset=0`. No cursor — sheet order is append-only, so offset is stable enough for ops. CSV export ignores pagination and dumps the full filtered result (cap at 10,000 rows; if exceeded, throw `E_EXPORT_TOO_LARGE` with a hint to tighten filters).
5. **Date filtering = ISO-8601 string comparison.** `submitted_at_server` is stored as an ISO string; lexicographic compare matches chronological order for same-format strings. `from`/`to` filters inclusive on both ends; `YYYY-MM-DD` inputs are interpreted as `YYYY-MM-DDT00:00:00.000Z` (from) / `YYYY-MM-DDT23:59:59.999Z` (to).
6. **CSV format = RFC 4180.** Fields wrapped in `"` if they contain `,`, `"`, `\n`, or `\r`. Embedded `"` doubled to `""`. Line terminator `\r\n`. First row is column names. UTF-8, no BOM.
7. **Admin URL = `?action=admin`.** Same Web App deployment as the PWA backend — a new branch inside `doGet`, returning `HtmlService.createTemplateFromFile('Admin').evaluate()` instead of the JSON envelope. No separate deployment.
8. **No admin audit log.** Admin reads are not themselves logged. Spec §4.7 does not require it, and `F2_Audit` is for PWA events only. If later required, a new `F2_AdminAudit` tab is cheap to add in M11+.
9. **Sort order.** Responses and audit: newest first (`submitted_at_server` / `occurred_at_server` descending). DLQ: newest first (`received_at_server` descending).
10. **Column coverage.** Responses view shows all `F2_RESPONSES_COLUMNS` *except* `values_json` (too large for a table row — CSV export still includes it). Audit view shows all `F2_AUDIT_COLUMNS` including `payload_json` (typically small). DLQ view shows all `F2_DLQ_COLUMNS`.
11. **DOM rendering only — no `innerHTML` with data.** The browser UI builds tables using `document.createElement` + `textContent` so that any cell value (however nasty — an attacker who managed to inject a `<script>` tag into `hcw_id` via the PWA) renders as literal text. The login view contains no user-provided data so `innerHTML` is never needed at all.

---

## Task 1: Scaffold AdminHandlers source + test files

**Files:**
- Create: `deliverables/F2/PWA/backend/src/AdminHandlers.js`
- Create: `deliverables/F2/PWA/backend/tests/admin-handlers.test.mjs`

- [ ] **Step 1: Create `src/AdminHandlers.js` with empty module scaffold**

```js
// Pure-function admin handlers. No Apps Script globals. All I/O injected via ctx.

if (typeof module !== 'undefined') {
  module.exports = {};
}
```

- [ ] **Step 2: Create `tests/admin-handlers.test.mjs` with bootstrap**

```js
import { describe, it, expect } from 'vitest';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const AdminHandlers = require('../src/AdminHandlers.js');

describe('AdminHandlers module', () => {
  it('exports an object', () => {
    expect(typeof AdminHandlers).toBe('object');
  });
});
```

- [ ] **Step 3: Run to confirm green**

Run: `cd deliverables/F2/PWA/backend && npm test -- admin-handlers`
Expected: `1 passed`.

- [ ] **Step 4: Commit**

```bash
git add deliverables/F2/PWA/backend/src/AdminHandlers.js \
        deliverables/F2/PWA/backend/tests/admin-handlers.test.mjs
git commit -m "feat(M10): scaffold admin handlers module and test"
```

---

## Task 2: `verifyAdminToken` — constant-time compare

**Files:**
- Modify: `deliverables/F2/PWA/backend/src/AdminHandlers.js`
- Modify: `deliverables/F2/PWA/backend/tests/admin-handlers.test.mjs`

- [ ] **Step 1: Add failing tests**

Append to `tests/admin-handlers.test.mjs`:

```js
describe('verifyAdminToken', () => {
  it('returns true when token matches secret exactly', () => {
    expect(AdminHandlers.verifyAdminToken('abc123', 'abc123')).toBe(true);
  });

  it('returns false when token differs', () => {
    expect(AdminHandlers.verifyAdminToken('abc123', 'abc124')).toBe(false);
  });

  it('returns false when token is shorter', () => {
    expect(AdminHandlers.verifyAdminToken('abc', 'abc123')).toBe(false);
  });

  it('returns false when token is longer', () => {
    expect(AdminHandlers.verifyAdminToken('abc123xxx', 'abc123')).toBe(false);
  });

  it('returns false for empty token', () => {
    expect(AdminHandlers.verifyAdminToken('', 'abc123')).toBe(false);
  });

  it('returns false for null/undefined token', () => {
    expect(AdminHandlers.verifyAdminToken(null, 'abc123')).toBe(false);
    expect(AdminHandlers.verifyAdminToken(undefined, 'abc123')).toBe(false);
  });

  it('returns false when secret is empty (disabled auth)', () => {
    expect(AdminHandlers.verifyAdminToken('abc123', '')).toBe(false);
  });
});
```

- [ ] **Step 2: Run to confirm red**

Run: `npm test -- admin-handlers`
Expected: `verifyAdminToken is not a function` — 7 failures.

- [ ] **Step 3: Implement in `src/AdminHandlers.js` (prepend before `module.exports`)**

```js
function verifyAdminToken(token, secret) {
  if (typeof token !== 'string' || typeof secret !== 'string') return false;
  if (token.length === 0 || secret.length === 0) return false;
  if (token.length !== secret.length) return false;
  var diff = 0;
  for (var i = 0; i < token.length; i++) {
    diff |= token.charCodeAt(i) ^ secret.charCodeAt(i);
  }
  return diff === 0;
}
```

Update the `module.exports` block:

```js
if (typeof module !== 'undefined') {
  module.exports = {
    verifyAdminToken: verifyAdminToken,
  };
}
```

- [ ] **Step 4: Run to confirm green**

Run: `npm test -- admin-handlers`
Expected: `8 passed`.

- [ ] **Step 5: Commit**

```bash
git add deliverables/F2/PWA/backend/src/AdminHandlers.js \
        deliverables/F2/PWA/backend/tests/admin-handlers.test.mjs
git commit -m "feat(M10): verifyAdminToken with constant-time compare"
```

---

## Task 3: `filterResponses` — facility / status / date range

**Files:**
- Modify: `deliverables/F2/PWA/backend/src/AdminHandlers.js`
- Modify: `deliverables/F2/PWA/backend/tests/admin-handlers.test.mjs`

- [ ] **Step 1: Add failing tests**

```js
describe('filterResponses', () => {
  const rows = [
    { submission_id: 's1', facility_id: 'fac-1', status: 'stored', submitted_at_server: '2026-04-17T10:00:00.000Z' },
    { submission_id: 's2', facility_id: 'fac-2', status: 'stored', submitted_at_server: '2026-04-18T09:00:00.000Z' },
    { submission_id: 's3', facility_id: 'fac-1', status: 'rejected', submitted_at_server: '2026-04-18T14:00:00.000Z' },
    { submission_id: 's4', facility_id: 'fac-3', status: 'stored', submitted_at_server: '2026-04-19T08:00:00.000Z' },
  ];

  it('returns all rows when filters empty', () => {
    const out = AdminHandlers.filterResponses(rows, {});
    expect(out.map((r) => r.submission_id)).toEqual(['s4', 's3', 's2', 's1']);
  });

  it('filters by facility_id', () => {
    const out = AdminHandlers.filterResponses(rows, { facility_id: 'fac-1' });
    expect(out.map((r) => r.submission_id)).toEqual(['s3', 's1']);
  });

  it('filters by status', () => {
    const out = AdminHandlers.filterResponses(rows, { status: 'rejected' });
    expect(out.map((r) => r.submission_id)).toEqual(['s3']);
  });

  it('filters by date range inclusive (from YYYY-MM-DD)', () => {
    const out = AdminHandlers.filterResponses(rows, { from: '2026-04-18' });
    expect(out.map((r) => r.submission_id)).toEqual(['s4', 's3', 's2']);
  });

  it('filters by date range inclusive (to YYYY-MM-DD)', () => {
    const out = AdminHandlers.filterResponses(rows, { to: '2026-04-18' });
    expect(out.map((r) => r.submission_id)).toEqual(['s3', 's2', 's1']);
  });

  it('combines filters (facility + status + from)', () => {
    const out = AdminHandlers.filterResponses(rows, { facility_id: 'fac-1', status: 'stored', from: '2026-04-01' });
    expect(out.map((r) => r.submission_id)).toEqual(['s1']);
  });

  it('sorts newest first by submitted_at_server', () => {
    const out = AdminHandlers.filterResponses(rows, {});
    expect(out[0].submission_id).toBe('s4');
    expect(out[3].submission_id).toBe('s1');
  });

  it('returns empty array when nothing matches', () => {
    expect(AdminHandlers.filterResponses(rows, { facility_id: 'does-not-exist' })).toEqual([]);
  });
});
```

- [ ] **Step 2: Run to confirm red**

Run: `npm test -- admin-handlers`
Expected: `filterResponses is not a function` — 8 failures.

- [ ] **Step 3: Implement**

Add to `src/AdminHandlers.js`:

```js
function _dateFromInclusive(ymd) {
  return ymd ? ymd + 'T00:00:00.000Z' : null;
}

function _dateToInclusive(ymd) {
  return ymd ? ymd + 'T23:59:59.999Z' : null;
}

function filterResponses(rows, filters) {
  filters = filters || {};
  var from = _dateFromInclusive(filters.from);
  var to = _dateToInclusive(filters.to);

  var out = [];
  for (var i = 0; i < rows.length; i++) {
    var r = rows[i];
    if (filters.facility_id && r.facility_id !== filters.facility_id) continue;
    if (filters.status && r.status !== filters.status) continue;
    if (from && String(r.submitted_at_server) < from) continue;
    if (to && String(r.submitted_at_server) > to) continue;
    out.push(r);
  }
  out.sort(function (a, b) {
    return String(b.submitted_at_server).localeCompare(String(a.submitted_at_server));
  });
  return out;
}
```

Add `filterResponses: filterResponses,` to `module.exports`.

- [ ] **Step 4: Run to confirm green**

Run: `npm test -- admin-handlers`
Expected: 16 passed.

- [ ] **Step 5: Commit**

```bash
git add deliverables/F2/PWA/backend/src/AdminHandlers.js \
        deliverables/F2/PWA/backend/tests/admin-handlers.test.mjs
git commit -m "feat(M10): filterResponses with facility/status/date filters"
```

---

## Task 4: `filterAudit` — event / hcw / date range

**Files:**
- Modify: `deliverables/F2/PWA/backend/src/AdminHandlers.js`
- Modify: `deliverables/F2/PWA/backend/tests/admin-handlers.test.mjs`

- [ ] **Step 1: Add failing tests**

```js
describe('filterAudit', () => {
  const rows = [
    { audit_id: 'a1', event_type: 'enroll', hcw_id: 'hcw-1', occurred_at_server: '2026-04-17T10:00:00.000Z' },
    { audit_id: 'a2', event_type: 'submit', hcw_id: 'hcw-2', occurred_at_server: '2026-04-18T09:00:00.000Z' },
    { audit_id: 'a3', event_type: 'enroll', hcw_id: 'hcw-1', occurred_at_server: '2026-04-18T14:00:00.000Z' },
  ];

  it('returns all rows when filters empty (newest first)', () => {
    const out = AdminHandlers.filterAudit(rows, {});
    expect(out.map((r) => r.audit_id)).toEqual(['a3', 'a2', 'a1']);
  });

  it('filters by event_type', () => {
    const out = AdminHandlers.filterAudit(rows, { event_type: 'enroll' });
    expect(out.map((r) => r.audit_id)).toEqual(['a3', 'a1']);
  });

  it('filters by hcw_id', () => {
    const out = AdminHandlers.filterAudit(rows, { hcw_id: 'hcw-2' });
    expect(out.map((r) => r.audit_id)).toEqual(['a2']);
  });

  it('filters by date range', () => {
    const out = AdminHandlers.filterAudit(rows, { from: '2026-04-18', to: '2026-04-18' });
    expect(out.map((r) => r.audit_id)).toEqual(['a3', 'a2']);
  });
});
```

- [ ] **Step 2: Run to confirm red**

Run: `npm test -- admin-handlers`
Expected: 4 failures.

- [ ] **Step 3: Implement**

Add to `src/AdminHandlers.js`:

```js
function filterAudit(rows, filters) {
  filters = filters || {};
  var from = _dateFromInclusive(filters.from);
  var to = _dateToInclusive(filters.to);

  var out = [];
  for (var i = 0; i < rows.length; i++) {
    var r = rows[i];
    if (filters.event_type && r.event_type !== filters.event_type) continue;
    if (filters.hcw_id && r.hcw_id !== filters.hcw_id) continue;
    if (from && String(r.occurred_at_server) < from) continue;
    if (to && String(r.occurred_at_server) > to) continue;
    out.push(r);
  }
  out.sort(function (a, b) {
    return String(b.occurred_at_server).localeCompare(String(a.occurred_at_server));
  });
  return out;
}
```

Add `filterAudit: filterAudit,` to `module.exports`.

- [ ] **Step 4: Run to confirm green**

Run: `npm test -- admin-handlers`
Expected: 20 passed.

- [ ] **Step 5: Commit**

```bash
git add deliverables/F2/PWA/backend/src/AdminHandlers.js \
        deliverables/F2/PWA/backend/tests/admin-handlers.test.mjs
git commit -m "feat(M10): filterAudit with event/hcw/date filters"
```

---

## Task 5: `listDlq` — newest first

**Files:**
- Modify: `deliverables/F2/PWA/backend/src/AdminHandlers.js`
- Modify: `deliverables/F2/PWA/backend/tests/admin-handlers.test.mjs`

- [ ] **Step 1: Add failing tests**

```js
describe('listDlq', () => {
  const rows = [
    { dlq_id: 'd1', received_at_server: '2026-04-17T10:00:00.000Z', reason: 'values must be an object' },
    { dlq_id: 'd2', received_at_server: '2026-04-18T09:00:00.000Z', reason: 'missing client_submission_id' },
    { dlq_id: 'd3', received_at_server: '2026-04-18T14:00:00.000Z', reason: 'values must be an object' },
  ];

  it('returns all rows, newest first', () => {
    const out = AdminHandlers.listDlq(rows);
    expect(out.map((r) => r.dlq_id)).toEqual(['d3', 'd2', 'd1']);
  });

  it('returns an empty array for empty input', () => {
    expect(AdminHandlers.listDlq([])).toEqual([]);
  });
});
```

- [ ] **Step 2: Run to confirm red**

Run: `npm test -- admin-handlers`
Expected: 2 failures.

- [ ] **Step 3: Implement**

Add to `src/AdminHandlers.js`:

```js
function listDlq(rows) {
  var copy = rows.slice();
  copy.sort(function (a, b) {
    return String(b.received_at_server).localeCompare(String(a.received_at_server));
  });
  return copy;
}
```

Add `listDlq: listDlq,` to `module.exports`.

- [ ] **Step 4: Run to confirm green**

Run: `npm test -- admin-handlers`
Expected: 22 passed.

- [ ] **Step 5: Commit**

```bash
git add deliverables/F2/PWA/backend/src/AdminHandlers.js \
        deliverables/F2/PWA/backend/tests/admin-handlers.test.mjs
git commit -m "feat(M10): listDlq newest-first"
```

---

## Task 6: `rowsToCsv` — RFC 4180 escaping

**Files:**
- Modify: `deliverables/F2/PWA/backend/src/AdminHandlers.js`
- Modify: `deliverables/F2/PWA/backend/tests/admin-handlers.test.mjs`

- [ ] **Step 1: Add failing tests**

```js
describe('rowsToCsv', () => {
  it('emits header row + data rows with CRLF line endings', () => {
    const csv = AdminHandlers.rowsToCsv(['a', 'b'], [{ a: '1', b: '2' }, { a: '3', b: '4' }]);
    expect(csv).toBe('a,b\r\n1,2\r\n3,4\r\n');
  });

  it('emits just the header when rows are empty', () => {
    expect(AdminHandlers.rowsToCsv(['a', 'b'], [])).toBe('a,b\r\n');
  });

  it('quotes fields containing commas', () => {
    const csv = AdminHandlers.rowsToCsv(['a'], [{ a: 'x,y' }]);
    expect(csv).toBe('a\r\n"x,y"\r\n');
  });

  it('quotes and doubles internal quotes', () => {
    const csv = AdminHandlers.rowsToCsv(['a'], [{ a: 'hello "world"' }]);
    expect(csv).toBe('a\r\n"hello ""world"""\r\n');
  });

  it('quotes fields containing newlines', () => {
    const csv = AdminHandlers.rowsToCsv(['a'], [{ a: 'line1\nline2' }]);
    expect(csv).toBe('a\r\n"line1\nline2"\r\n');
  });

  it('coerces null/undefined to empty string', () => {
    const csv = AdminHandlers.rowsToCsv(['a', 'b'], [{ a: null, b: undefined }]);
    expect(csv).toBe('a,b\r\n,\r\n');
  });

  it('coerces numbers and booleans to strings', () => {
    const csv = AdminHandlers.rowsToCsv(['a', 'b'], [{ a: 42, b: true }]);
    expect(csv).toBe('a,b\r\n42,true\r\n');
  });

  it('omits columns not present on a row (empty string)', () => {
    const csv = AdminHandlers.rowsToCsv(['a', 'b'], [{ a: '1' }]);
    expect(csv).toBe('a,b\r\n1,\r\n');
  });
});
```

- [ ] **Step 2: Run to confirm red**

Run: `npm test -- admin-handlers`
Expected: 8 failures.

- [ ] **Step 3: Implement**

Add to `src/AdminHandlers.js`:

```js
function _csvEscape(value) {
  if (value == null) return '';
  var s = String(value);
  if (s.indexOf(',') >= 0 || s.indexOf('"') >= 0 || s.indexOf('\n') >= 0 || s.indexOf('\r') >= 0) {
    return '"' + s.replace(/"/g, '""') + '"';
  }
  return s;
}

function rowsToCsv(columns, rows) {
  var out = columns.map(_csvEscape).join(',') + '\r\n';
  for (var i = 0; i < rows.length; i++) {
    var row = rows[i];
    var cells = [];
    for (var j = 0; j < columns.length; j++) {
      cells.push(_csvEscape(row[columns[j]]));
    }
    out += cells.join(',') + '\r\n';
  }
  return out;
}
```

Add `rowsToCsv: rowsToCsv,` to `module.exports`.

- [ ] **Step 4: Run to confirm green**

Run: `npm test -- admin-handlers`
Expected: 30 passed.

- [ ] **Step 5: Commit**

```bash
git add deliverables/F2/PWA/backend/src/AdminHandlers.js \
        deliverables/F2/PWA/backend/tests/admin-handlers.test.mjs
git commit -m "feat(M10): rowsToCsv with RFC 4180 escaping"
```

---

## Task 7: Extend ctx builders in `Code.js` with `readAll`

**Files:**
- Modify: `deliverables/F2/PWA/backend/apps-script/Code.js`

*Rationale: admin views need to read `F2_Responses`, `F2_Audit`, and `F2_DLQ` in bulk. Current ctx builders only expose write/lookup. We add `readAll(limit, offset)` returning an array of row objects keyed by column name. Tested live via deploy — no Node test coverage (these methods call `SpreadsheetApp`).*

- [ ] **Step 1: Extend `_buildResponsesCtx`**

Inside `_buildResponsesCtx(sheet)`, add before the closing brace of the returned object:

```js
    readAll: function (limit, offset) {
      limit = limit || 500;
      offset = offset || 0;
      var last = sheet.getLastRow();
      if (last < 2) return [];
      var startRow = 2 + offset;
      var availableRows = last - startRow + 1;
      if (availableRows <= 0) return [];
      var take = Math.min(limit, availableRows);
      var data = sheet.getRange(startRow, 1, take, cols.length).getValues();
      return data.map(function (row) {
        var obj = {};
        for (var i = 0; i < cols.length; i++) obj[cols[i]] = row[i];
        return obj;
      });
    },
```

- [ ] **Step 2: Extend `_buildAuditCtx`**

Replace `_buildAuditCtx` body with:

```js
function _buildAuditCtx(sheet) {
  var cols = F2_AUDIT_COLUMNS;
  return {
    appendRow: function (rowObj) {
      var arr = cols.map(function (c) { return rowObj[c] != null ? rowObj[c] : ''; });
      sheet.appendRow(arr);
      return rowObj.audit_id;
    },
    readAll: function (limit, offset) {
      limit = limit || 500;
      offset = offset || 0;
      var last = sheet.getLastRow();
      if (last < 2) return [];
      var startRow = 2 + offset;
      var availableRows = last - startRow + 1;
      if (availableRows <= 0) return [];
      var take = Math.min(limit, availableRows);
      var data = sheet.getRange(startRow, 1, take, cols.length).getValues();
      return data.map(function (row) {
        var obj = {};
        for (var i = 0; i < cols.length; i++) obj[cols[i]] = row[i];
        return obj;
      });
    },
  };
}
```

- [ ] **Step 3: Extend `_buildDlqCtx`**

Replace `_buildDlqCtx` body with:

```js
function _buildDlqCtx(sheet) {
  var cols = F2_DLQ_COLUMNS;
  return {
    appendRow: function (rowObj) {
      var arr = cols.map(function (c) { return rowObj[c] != null ? rowObj[c] : ''; });
      sheet.appendRow(arr);
    },
    readAll: function () {
      var last = sheet.getLastRow();
      if (last < 2) return [];
      var data = sheet.getRange(2, 1, last - 1, cols.length).getValues();
      return data.map(function (row) {
        var obj = {};
        for (var i = 0; i < cols.length; i++) obj[cols[i]] = row[i];
        return obj;
      });
    },
  };
}
```

- [ ] **Step 4: Verify existing tests still pass**

Run: `cd deliverables/F2/PWA/backend && npm test`
Expected: all pre-existing tests green.

- [ ] **Step 5: Commit**

```bash
git add deliverables/F2/PWA/backend/apps-script/Code.js
git commit -m "feat(M10): add readAll(limit, offset) to responses/audit/dlq ctx"
```

---

## Task 8: Generate ADMIN_SECRET in `Setup.js`

**Files:**
- Modify: `deliverables/F2/PWA/backend/apps-script/Setup.js`

- [ ] **Step 1: Add constant at top of `Setup.js` (above `function setupBackend`)**

```js
var PROP_ADMIN_SECRET = 'ADMIN_SECRET';
```

- [ ] **Step 2: Add secret generation inside `setupBackend`, right after the `HMAC_SECRET` block**

Insert after the existing `Logger.log('HMAC_SECRET already set...')` else-branch:

```js
  var adminSecret = props.getProperty(PROP_ADMIN_SECRET);
  if (!adminSecret) {
    adminSecret = _generateSecret();
    props.setProperty(PROP_ADMIN_SECRET, adminSecret);
    Logger.log('Generated new ADMIN_SECRET (first 6 chars): ' + adminSecret.slice(0, 6) + '…');
  } else {
    Logger.log('ADMIN_SECRET already set (first 6 chars): ' + adminSecret.slice(0, 6) + '…');
  }
```

- [ ] **Step 3: Add `rotateAdminSecret` helper below the existing `rotateSecret` function**

```js
function rotateAdminSecret() {
  var props = PropertiesService.getScriptProperties();
  var newSecret = _generateSecret();
  props.setProperty(PROP_ADMIN_SECRET, newSecret);
  Logger.log('Rotated ADMIN_SECRET. New secret starts: ' + newSecret.slice(0, 6) + '…');
  Logger.log('Distribute to ops team out-of-band. Operators must re-enter on next admin login.');
}
```

- [ ] **Step 4: Commit**

```bash
git add deliverables/F2/PWA/backend/apps-script/Setup.js
git commit -m "feat(M10): generate and rotate ADMIN_SECRET in Setup.js"
```

---

## Task 9: Create `AdminGlue.js` — server-side RPC wrappers

**Files:**
- Create: `deliverables/F2/PWA/backend/apps-script/AdminGlue.js`

- [ ] **Step 1: Write the file**

```js
// Apps Script server functions callable from the Admin.html client via google.script.run.
// Every function begins with _requireAdmin_(token); all return plain JS objects (no JSON string).

var PROP_ADMIN_SECRET_KEY = 'ADMIN_SECRET';
var ADMIN_DEFAULT_LIMIT = 500;
var ADMIN_EXPORT_CAP = 10000;

function _requireAdmin_(token) {
  var secret = PropertiesService.getScriptProperties().getProperty(PROP_ADMIN_SECRET_KEY);
  if (!secret) throw new Error('E_ADMIN_NOT_CONFIGURED');
  if (!verifyAdminToken(token, secret)) throw new Error('E_ADMIN_AUTH');
}

function adminAuth(token) {
  _requireAdmin_(token);
  return { ok: true };
}

function adminListResponses(token, filters, limit, offset) {
  _requireAdmin_(token);
  var ctx = buildCtx();
  var rows = ctx.responses.readAll(limit || ADMIN_DEFAULT_LIMIT, offset || 0);
  var filtered = filterResponses(rows, filters || {});
  return { ok: true, data: { rows: filtered, count: filtered.length } };
}

function adminListAudit(token, filters, limit, offset) {
  _requireAdmin_(token);
  var ctx = buildCtx();
  var rows = ctx.audit.readAll(limit || ADMIN_DEFAULT_LIMIT, offset || 0);
  var filtered = filterAudit(rows, filters || {});
  return { ok: true, data: { rows: filtered, count: filtered.length } };
}

function adminListDlq(token) {
  _requireAdmin_(token);
  var ctx = buildCtx();
  var rows = ctx.dlq.readAll();
  return { ok: true, data: { rows: listDlq(rows), count: rows.length } };
}

function adminExportCsv(token, table, filters) {
  _requireAdmin_(token);
  var ctx = buildCtx();
  var columns;
  var rows;
  if (table === 'responses') {
    rows = filterResponses(ctx.responses.readAll(ADMIN_EXPORT_CAP, 0), filters || {});
    columns = F2_RESPONSES_COLUMNS;
  } else if (table === 'audit') {
    rows = filterAudit(ctx.audit.readAll(ADMIN_EXPORT_CAP, 0), filters || {});
    columns = F2_AUDIT_COLUMNS;
  } else if (table === 'dlq') {
    rows = listDlq(ctx.dlq.readAll());
    columns = F2_DLQ_COLUMNS;
  } else {
    throw new Error('E_UNKNOWN_TABLE');
  }
  if (rows.length >= ADMIN_EXPORT_CAP) {
    throw new Error('E_EXPORT_TOO_LARGE');
  }
  return { ok: true, data: { csv: rowsToCsv(columns, rows), filename: 'f2-' + table + '-' + new Date().toISOString().slice(0, 10) + '.csv' } };
}
```

- [ ] **Step 2: Commit**

```bash
git add deliverables/F2/PWA/backend/apps-script/AdminGlue.js
git commit -m "feat(M10): AdminGlue.js with RPC wrappers"
```

---

## Task 10: Add `?action=admin` branch to `doGet`

**Files:**
- Modify: `deliverables/F2/PWA/backend/apps-script/Code.js`

- [ ] **Step 1: Replace `doGet` with a pre-branch for admin**

Change:

```js
function doGet(e) {
  return _serve('GET', e);
}
```

To:

```js
function doGet(e) {
  var action = (e && e.parameter && e.parameter.action) || '';
  if (action === 'admin') {
    return HtmlService.createTemplateFromFile('Admin').evaluate()
      .setTitle('F2 Admin')
      .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.DEFAULT);
  }
  return _serve('GET', e);
}
```

- [ ] **Step 2: Commit**

```bash
git add deliverables/F2/PWA/backend/apps-script/Code.js
git commit -m "feat(M10): serve Admin HTML at ?action=admin"
```

---

## Task 11: Create `Admin.html` — login + 3 tabs + CSV export

**Files:**
- Create: `deliverables/F2/PWA/backend/apps-script/Admin.html`

*Rationale on the rendering choice: every piece of data that appears in the tables comes from sheet cells that the PWA writes. In theory the PWA only forwards sanitized values, but an attacker who managed to poison a row (e.g. via a leaked HMAC secret) could otherwise XSS the operator. Tables are built with `document.createElement` + `textContent` exclusively — nothing renders HTML from sheet data. `innerHTML` is not used anywhere.*

- [ ] **Step 1: Write the file**

```html
<!DOCTYPE html>
<html>
<head>
  <base target="_top">
  <meta charset="utf-8">
  <title>F2 Admin</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 1rem; color: #111; }
    h1 { font-size: 1.2rem; margin: 0 0 1rem; }
    #login, #app { max-width: 1200px; }
    #app { display: none; }
    .tabs { display: flex; gap: 0.5rem; margin-bottom: 1rem; border-bottom: 1px solid #ccc; }
    .tab { padding: 0.5rem 1rem; cursor: pointer; border: 1px solid transparent; border-bottom: none; }
    .tab.active { background: #f0f0f0; border-color: #ccc; }
    .filters { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.75rem; align-items: end; }
    .filters label { display: flex; flex-direction: column; font-size: 0.75rem; color: #555; }
    .filters input, .filters select { padding: 0.25rem; font-size: 0.9rem; }
    button { padding: 0.4rem 0.8rem; font-size: 0.9rem; cursor: pointer; }
    table { width: 100%; border-collapse: collapse; font-size: 0.8rem; }
    th, td { border: 1px solid #ddd; padding: 0.3rem 0.5rem; text-align: left; vertical-align: top; max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    th { background: #f5f5f5; position: sticky; top: 0; }
    tr:hover { background: #fafafa; }
    .status { margin: 0.5rem 0; color: #555; font-size: 0.85rem; }
    .error { color: #b00; }
    .muted { color: #999; }
  </style>
</head>
<body>
  <h1>F2 Admin Dashboard</h1>

  <div id="login">
    <p>Enter the admin secret provided by the backend operator.</p>
    <label>Admin secret: <input type="password" id="secret-input" autocomplete="off" style="width: 20rem;"></label>
    <button id="login-btn">Sign in</button>
    <div id="login-error" class="error"></div>
  </div>

  <div id="app">
    <div class="tabs">
      <div class="tab active" data-tab="responses">Responses</div>
      <div class="tab" data-tab="audit">Audit</div>
      <div class="tab" data-tab="dlq">DLQ</div>
      <span style="margin-left: auto; font-size: 0.8rem; color: #666;">
        <button id="signout-btn">Sign out</button>
      </span>
    </div>

    <div id="tab-responses" class="tab-panel">
      <div class="filters">
        <label>Facility ID <input type="text" id="resp-facility"></label>
        <label>Status
          <select id="resp-status">
            <option value="">(any)</option>
            <option value="stored">stored</option>
            <option value="rejected">rejected</option>
          </select>
        </label>
        <label>From <input type="date" id="resp-from"></label>
        <label>To <input type="date" id="resp-to"></label>
        <button id="resp-refresh">Refresh</button>
        <button id="resp-export">Export CSV</button>
      </div>
      <div class="status" id="resp-status-text"></div>
      <div id="resp-table"></div>
    </div>

    <div id="tab-audit" class="tab-panel" style="display:none;">
      <div class="filters">
        <label>Event type <input type="text" id="audit-event"></label>
        <label>HCW ID <input type="text" id="audit-hcw"></label>
        <label>From <input type="date" id="audit-from"></label>
        <label>To <input type="date" id="audit-to"></label>
        <button id="audit-refresh">Refresh</button>
        <button id="audit-export">Export CSV</button>
      </div>
      <div class="status" id="audit-status-text"></div>
      <div id="audit-table"></div>
    </div>

    <div id="tab-dlq" class="tab-panel" style="display:none;">
      <div class="filters">
        <button id="dlq-refresh">Refresh</button>
        <button id="dlq-export">Export CSV</button>
      </div>
      <div class="status" id="dlq-status-text"></div>
      <div id="dlq-table"></div>
    </div>
  </div>

<script>
(function () {
  var ADMIN_TOKEN = null;

  function $(id) { return document.getElementById(id); }

  function setText(id, msg) { $(id).textContent = msg || ''; }

  function clearNode(node) {
    while (node.firstChild) node.removeChild(node.firstChild);
  }

  function renderTable(containerId, columns, rows) {
    var container = $(containerId);
    clearNode(container);

    var table = document.createElement('table');
    var thead = document.createElement('thead');
    var headerTr = document.createElement('tr');
    for (var i = 0; i < columns.length; i++) {
      var th = document.createElement('th');
      th.textContent = columns[i];
      headerTr.appendChild(th);
    }
    thead.appendChild(headerTr);
    table.appendChild(thead);

    var tbody = document.createElement('tbody');
    if (rows.length === 0) {
      var emptyTr = document.createElement('tr');
      var emptyTd = document.createElement('td');
      emptyTd.colSpan = columns.length;
      emptyTd.className = 'muted';
      emptyTd.textContent = 'No rows.';
      emptyTr.appendChild(emptyTd);
      tbody.appendChild(emptyTr);
    } else {
      for (var r = 0; r < rows.length; r++) {
        var tr = document.createElement('tr');
        for (var c = 0; c < columns.length; c++) {
          var td = document.createElement('td');
          var v = rows[r][columns[c]];
          td.textContent = v == null ? '' : String(v);
          tr.appendChild(td);
        }
        tbody.appendChild(tr);
      }
    }
    table.appendChild(tbody);
    container.appendChild(table);
  }

  function downloadCsv(csv, filename) {
    var blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  function handleAuthError(err) {
    var msg = err && err.message ? err.message : String(err);
    if (msg.indexOf('E_ADMIN_AUTH') >= 0 || msg.indexOf('E_ADMIN_NOT_CONFIGURED') >= 0) {
      ADMIN_TOKEN = null;
      $('app').style.display = 'none';
      $('login').style.display = '';
      setText('login-error', 'Session invalid. Re-enter secret.');
      return true;
    }
    return false;
  }

  // Login
  $('login-btn').addEventListener('click', function () {
    var token = $('secret-input').value;
    if (!token) { setText('login-error', 'Enter a secret.'); return; }
    setText('login-error', 'Verifying…');
    google.script.run
      .withSuccessHandler(function () {
        ADMIN_TOKEN = token;
        $('login').style.display = 'none';
        $('app').style.display = '';
        $('secret-input').value = '';
        setText('login-error', '');
        loadResponses();
      })
      .withFailureHandler(function (err) {
        if (!handleAuthError(err)) setText('login-error', 'Auth failed: ' + (err.message || err));
      })
      .adminAuth(token);
  });

  $('signout-btn').addEventListener('click', function () {
    ADMIN_TOKEN = null;
    $('app').style.display = 'none';
    $('login').style.display = '';
  });

  // Tabs
  var tabs = document.querySelectorAll('.tab');
  for (var t = 0; t < tabs.length; t++) {
    tabs[t].addEventListener('click', function (ev) {
      var name = ev.target.getAttribute('data-tab');
      for (var i = 0; i < tabs.length; i++) tabs[i].classList.remove('active');
      ev.target.classList.add('active');
      var panels = ['responses', 'audit', 'dlq'];
      for (var j = 0; j < panels.length; j++) {
        $('tab-' + panels[j]).style.display = panels[j] === name ? '' : 'none';
      }
      if (name === 'responses') loadResponses();
      else if (name === 'audit') loadAudit();
      else if (name === 'dlq') loadDlq();
    });
  }

  // Responses
  var RESPONSE_COLUMNS = ['submission_id', 'submitted_at_server', 'hcw_id', 'facility_id', 'status', 'spec_version', 'app_version', 'device_fingerprint', 'client_submission_id'];

  function respFilters() {
    return {
      facility_id: $('resp-facility').value || undefined,
      status: $('resp-status').value || undefined,
      from: $('resp-from').value || undefined,
      to: $('resp-to').value || undefined,
    };
  }

  function loadResponses() {
    setText('resp-status-text', 'Loading…');
    google.script.run
      .withSuccessHandler(function (r) {
        renderTable('resp-table', RESPONSE_COLUMNS, r.data.rows);
        setText('resp-status-text', r.data.count + ' row(s).');
      })
      .withFailureHandler(function (err) {
        if (!handleAuthError(err)) setText('resp-status-text', 'Error: ' + (err.message || err));
      })
      .adminListResponses(ADMIN_TOKEN, respFilters(), 500, 0);
  }

  $('resp-refresh').addEventListener('click', loadResponses);
  $('resp-export').addEventListener('click', function () {
    setText('resp-status-text', 'Exporting…');
    google.script.run
      .withSuccessHandler(function (r) {
        downloadCsv(r.data.csv, r.data.filename);
        setText('resp-status-text', 'Exported.');
      })
      .withFailureHandler(function (err) {
        if (!handleAuthError(err)) setText('resp-status-text', 'Export failed: ' + (err.message || err));
      })
      .adminExportCsv(ADMIN_TOKEN, 'responses', respFilters());
  });

  // Audit
  var AUDIT_COLUMNS = ['audit_id', 'occurred_at_server', 'event_type', 'hcw_id', 'facility_id', 'app_version', 'payload_json'];

  function auditFilters() {
    return {
      event_type: $('audit-event').value || undefined,
      hcw_id: $('audit-hcw').value || undefined,
      from: $('audit-from').value || undefined,
      to: $('audit-to').value || undefined,
    };
  }

  function loadAudit() {
    setText('audit-status-text', 'Loading…');
    google.script.run
      .withSuccessHandler(function (r) {
        renderTable('audit-table', AUDIT_COLUMNS, r.data.rows);
        setText('audit-status-text', r.data.count + ' row(s).');
      })
      .withFailureHandler(function (err) {
        if (!handleAuthError(err)) setText('audit-status-text', 'Error: ' + (err.message || err));
      })
      .adminListAudit(ADMIN_TOKEN, auditFilters(), 500, 0);
  }

  $('audit-refresh').addEventListener('click', loadAudit);
  $('audit-export').addEventListener('click', function () {
    setText('audit-status-text', 'Exporting…');
    google.script.run
      .withSuccessHandler(function (r) {
        downloadCsv(r.data.csv, r.data.filename);
        setText('audit-status-text', 'Exported.');
      })
      .withFailureHandler(function (err) {
        if (!handleAuthError(err)) setText('audit-status-text', 'Export failed: ' + (err.message || err));
      })
      .adminExportCsv(ADMIN_TOKEN, 'audit', auditFilters());
  });

  // DLQ
  var DLQ_COLUMNS = ['dlq_id', 'received_at_server', 'client_submission_id', 'reason', 'payload_json'];

  function loadDlq() {
    setText('dlq-status-text', 'Loading…');
    google.script.run
      .withSuccessHandler(function (r) {
        renderTable('dlq-table', DLQ_COLUMNS, r.data.rows);
        setText('dlq-status-text', r.data.count + ' row(s).');
      })
      .withFailureHandler(function (err) {
        if (!handleAuthError(err)) setText('dlq-status-text', 'Error: ' + (err.message || err));
      })
      .adminListDlq(ADMIN_TOKEN);
  }

  $('dlq-refresh').addEventListener('click', loadDlq);
  $('dlq-export').addEventListener('click', function () {
    setText('dlq-status-text', 'Exporting…');
    google.script.run
      .withSuccessHandler(function (r) {
        downloadCsv(r.data.csv, r.data.filename);
        setText('dlq-status-text', 'Exported.');
      })
      .withFailureHandler(function (err) {
        if (!handleAuthError(err)) setText('dlq-status-text', 'Export failed: ' + (err.message || err));
      })
      .adminExportCsv(ADMIN_TOKEN, 'dlq', {});
  });
})();
</script>
</body>
</html>
```

- [ ] **Step 2: Commit**

```bash
git add deliverables/F2/PWA/backend/apps-script/Admin.html
git commit -m "feat(M10): Admin.html with login + 3 tabs + CSV export"
```

---

## Task 12: Update `build.mjs` to include admin files in `dist/`

**Files:**
- Modify: `deliverables/F2/PWA/backend/scripts/build.mjs`

- [ ] **Step 1: Add admin sources to `ORDER`**

Replace the `ORDER` array with:

```js
const ORDER = [
  'src/Schema.js',
  'src/Util.js',
  'src/Auth.js',
  'src/Idempotency.js',
  'src/Handlers.js',
  'src/AdminHandlers.js',
  'src/Router.js',
  'apps-script/Setup.js',
  'apps-script/AdminGlue.js',
  'apps-script/Code.js',
];
```

- [ ] **Step 2: Copy `Admin.html` into `dist/` after writing `Code.gs`**

Insert before the final `console.log(...)` line:

```js
  const adminHtml = await readFile(resolve(root, 'apps-script/Admin.html'), 'utf8');
  await writeFile(resolve(distDir, 'Admin.html'), adminHtml, 'utf8');
```

- [ ] **Step 3: Run the build**

Run: `cd deliverables/F2/PWA/backend && npm run build`
Expected: `dist/Code.gs` plus `dist/Admin.html` both present.

- [ ] **Step 4: Commit**

```bash
git add deliverables/F2/PWA/backend/scripts/build.mjs
git commit -m "feat(M10): bundle AdminHandlers + AdminGlue + Admin.html into dist"
```

---

## Task 13: Update backend `README.md` with admin deploy notes

**Files:**
- Modify: `deliverables/F2/PWA/backend/README.md`

- [ ] **Step 1: Add the section after the existing "Reset the spreadsheet" section, before "Smoke tests"**

```markdown
## Admin dashboard

The backend also serves an ops-only HTML admin at `?action=admin`. Read-only views of `F2_Responses`, `F2_Audit`, and `F2_DLQ` with facility/status/date filters and per-view CSV export.

### First deploy

After `setupBackend()` runs, a second ScriptProperty `ADMIN_SECRET` is generated. To retrieve it: Editor → Project Settings → Script Properties → copy `ADMIN_SECRET`. Share it with the ops team out-of-band (Signal, 1Password, etc. — never Slack/email).

When pasting source into `script.google.com`, add `Admin.html` as a second file (File → New → HTML) and paste the contents of `dist/Admin.html`.

### Access

Admin URL = the same Web App `/exec` URL with `?action=admin` appended. Example:

```
https://script.google.com/macros/s/AKfycb.../exec?action=admin
```

Operator enters the admin secret on the login screen. Token is held in browser memory only — closing the tab ends the session.

### Rotate the admin secret

Run `rotateAdminSecret()` from the editor. Redistribute out-of-band. Existing operator sessions will fail on next request and drop back to the login screen.
```

- [ ] **Step 2: Commit**

```bash
git add deliverables/F2/PWA/backend/README.md
git commit -m "docs(M10): admin dashboard deploy + rotation notes"
```

---

## Task 14: Rewrite `app/NEXT.md` — point at M11

**Files:**
- Modify: `deliverables/F2/PWA/app/NEXT.md`

- [ ] **Step 1: Replace contents**

```markdown
# Next step (future-Carl)

**Last milestone shipped:** M10 — Admin dashboard. Apps-Script-served HTML at `?action=admin`, separate `ADMIN_SECRET` ScriptProperty, three tabs (Responses / Audit / DLQ), per-view filters (facility / status / event / hcw / date range), per-view CSV export capped at 10 000 rows. Read-only — no mutations in M10. `backend/src/AdminHandlers.js` is pure-JS + Vitest-covered (verifyAdminToken with constant-time compare, filterResponses, filterAudit, listDlq, rowsToCsv with RFC 4180 escaping). `apps-script/AdminGlue.js` wraps each pure function with `_requireAdmin_(token)`. `apps-script/Admin.html` is the browser UI (vanilla HTML/JS + `google.script.run`, tables built via `createElement`/`textContent` — no innerHTML). Operators retrieve the admin secret from `Project Settings → Script Properties → ADMIN_SECRET` and rotate via `rotateAdminSecret()`.

**Next milestone:** M11 — Hardening / release prep. 6–10h per spec §11.1 row M11.

**Before starting M11:**

1. Re-invoke `superpowers:writing-plans` against `../2026-04-17-design-spec.md` §11.1 row M11 and any spec §12 notes about production readiness.
2. Candidate scope (confirm with spec §11.1):
   - PWA calls `/config` on app open and honors `kill_switch` + surfaces `broadcast_message`.
   - Auto-refresh facilities on app open (not just explicit Refresh button).
   - Sync-page "change enrollment" affordance (the `unenroll()` helper already exists — wire a button).
   - Spec-version drift UI (when `current_spec_version` > locally shipped `spec_version`, block submits until user upgrades the PWA).
   - Admin mutations deferred from M10: kill-switch toggle, broadcast_message editor, requeue-from-DLQ action.
3. Expected deliverable: `../YYYY-MM-DD-implementation-plan-M11-hardening.md`.

**M10 follow-ups (slot in when needed):**

- **Admin role separation.** M10 has one secret = full admin. If ASPSI wants read-only vs. operator vs. auditor, add a tiny role map keyed by a per-person secret.
- **Admin audit log.** Currently admin reads are not logged. If compliance later requires it, add an `F2_AdminAudit` tab and log every RPC call.
- **Pagination UI.** M10 caps each view at 500 rows with no paging controls. Large deployments may need "next page" affordance.

**M9 follow-ups (still outstanding):**

- **Filipino instrument translations.** Add `spec/F2-Spec.fil.md` overlay; extend `app/scripts/lib/parse-spec.ts` to populate `fil` from it. 3–5h.
- **Filipino chrome translations.** Replace placeholders in `app/src/i18n/locales/fil.ts`. 1–2h.
- **Browser language auto-detection on first load.** Optional `i18next-browser-languagedetector`. 30m.

**M8 technical debt still outstanding:**

- **`facility_has_bucas` / `facility_has_gamot` flags** — backend schema additions; needed before FAC-01..07 cross-field rules can wire up.
- **`response_source` per-respondent capture** — currently hardcoded `source: 'pwa'`. SRC-01..03 rules want this.

**When picking this back up after a gap:**

- `cd deliverables/F2/PWA/app && npm install && npm run test && npm run typecheck && npm run build` — confirm M9 still green.
- `cd deliverables/F2/PWA/backend && npm install && npm test && npm run build` — confirm M4+M10 still green.
- Deploy the fresh `dist/Code.gs` + `dist/Admin.html` to the Apps Script project if any backend source changed.
- Copy `.env.example` → `.env.local` and fill both vars from the live Apps Script deployment.
- `npm run dev`, walk through: enrollment → form → review → submit → sync.
- Open the Admin URL (`<backend-url>?action=admin`) and confirm login + all three tabs + CSV export.
- Open `../2026-04-17-design-spec.md` §11.1 row M11 to re-orient.
```

- [ ] **Step 2: Commit**

```bash
git add deliverables/F2/PWA/app/NEXT.md
git commit -m "docs(M10): rewrite NEXT.md to point at M11"
```

---

## Self-Review Checklist

**Spec coverage (§4.7 + §11.1 row M10):**
- ✅ HtmlService-served HTML → Task 10 + 11
- ✅ Read-only views of `F2_Responses` and `F2_Audit` → Tasks 3, 4, 7, 9, 11
- ✅ Filter by facility → Task 3 + 11 (resp-facility input)
- ✅ Filter by date → Tasks 3, 4 + 11 (from/to date inputs)
- ✅ Filter by status → Task 3 + 11 (resp-status select)
- ✅ Flag `F2_DLQ` rows → Task 5 + 11 (dedicated DLQ tab)
- ✅ CSV export → Tasks 6, 9, 11, 12
- ✅ 10–15h budget → 14 tasks, each 30–60 min, fits

**Placeholders:** None — every code block is complete.

**Type consistency:** `filterResponses`/`filterAudit`/`listDlq` all return arrays of row objects with the same shape as the Schema.js column lists. `adminListX` return envelopes all use `{ ok, data: { rows, count } }`. `adminExportCsv` returns `{ ok, data: { csv, filename } }`. `_requireAdmin_` throws on failure (matches Apps Script `google.script.run` error convention — `withFailureHandler` catches thrown errors).

**Architectural consistency:** Admin is a parallel stack to the existing HMAC-signed JSON API. No coupling: if M10 is backed out, the PWA still works. `AdminHandlers.js` follows the same pure-function + ctx-injection + CJS `module.exports` pattern as every other file in `backend/src/`.

**XSS safety:** Table rendering uses `document.createElement` + `textContent` exclusively. No `innerHTML` with data. The only HTML assigned via the static markup is the login view (no user data) and the filter labels (static strings).
