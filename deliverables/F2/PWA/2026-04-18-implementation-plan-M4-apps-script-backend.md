# M4 — Apps Script Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a deployable Google Apps Script Web App that implements the six F2 PWA backend routes (`submit`, `batch-submit`, `facilities`, `config`, `spec-hash`, `audit`), backed by a Google Sheet with five tabs, secured by HMAC-SHA256 request signing, and end-to-end curl-testable.

**Architecture:** Pure-JS source modules under `deliverables/F2/PWA/backend/src/` written so they execute unchanged inside Apps Script (no ESM `import`, no `require`) but also expose `module.exports` when run in Node for Vitest TDD. A thin Apps Script glue layer under `backend/apps-script/` wires `SpreadsheetApp` + `PropertiesService` + `Utilities` into a dependency-injected context and dispatches `doGet` / `doPost`. A build script concatenates `src/*.js` + the glue into a single `dist/Code.gs` paste-ready for `script.google.com`. Idempotency uses client-generated UUIDs; HMAC inputs are `${method}|${action}|${timestamp}|${body}`; values are stored as a single `values_json` column in `F2_Responses` for M4 (flat columns deferred to M10 admin dashboard work).

**Tech Stack:** Google Apps Script (V8 runtime), Node 20 + Vitest (TDD), crypto (Node built-in for test-side HMAC), plain JavaScript (no TypeScript — keeps Apps Script-compat trivial). No clasp; deploy via paste-into-editor matches the existing `deliverables/F2/apps-script/` recipe.

---

## File Structure

```
deliverables/F2/PWA/backend/
├── package.json              # Vitest only; no runtime deps
├── vitest.config.mjs
├── README.md                 # Deployment recipe + curl examples
├── .gitignore                # node_modules, dist, .secrets
│
├── src/                      # Apps-Script-compatible pure JS modules
│   ├── Util.js               # jsonResponse, timingSafeEq, generateUuid
│   ├── Auth.js               # verifyRequest (HMAC + timestamp skew)
│   ├── Router.js             # dispatch(action, method, parsed)
│   ├── Idempotency.js        # findExistingSubmission
│   ├── Handlers.js           # submit, batchSubmit, audit, facilities, config, specHash
│   └── Schema.js             # F2_RESPONSES_COLUMNS, F2_AUDIT_COLUMNS, etc.
│
├── apps-script/              # Hand-written GAS glue (not bundled — small)
│   ├── appsscript.json       # Web App manifest + scopes
│   ├── Code.js               # doGet, doPost, buildCtx
│   └── Setup.js              # setupBackend, rotateSecret, getSpreadsheetId
│
├── tests/                    # Vitest
│   ├── util.test.mjs
│   ├── auth.test.mjs
│   ├── router.test.mjs
│   ├── idempotency.test.mjs
│   └── handlers.test.mjs
│
└── scripts/
    ├── build.mjs             # Concatenate src/*.js + apps-script/*.js → dist/
    └── smoke.sh              # curl end-to-end tests against deployed URL
```

**Responsibility boundaries:**

- `src/` files: stateless pure functions. No Apps Script globals. Dependencies (sheet readers, HMAC, clock, uuid) are injected via a `ctx` object so Vitest can mock them trivially.
- `apps-script/` files: the only place that touches `SpreadsheetApp`, `PropertiesService`, `Utilities`, `LockService`. Constructs the `ctx`, calls `Router.dispatch`, serializes the response with `ContentService`.
- `scripts/build.mjs`: concatenation only, no transform. Ordering: `Schema.js` → `Util.js` → `Auth.js` → `Idempotency.js` → `Router.js` → `Handlers.js` → `Setup.js` → `Code.js`. Each source file is suffixed with an Apps-Script-ignored `if (typeof module !== 'undefined') module.exports = {...}` block so Node require works for tests.

---

## Architectural Decisions (locked in)

1. **HMAC input canonicalization:** `${method}|${action}|${ts}|${body}` — method is uppercase (`GET`/`POST`), action is the `e.parameter.action` string, ts is integer milliseconds since epoch as a string, body is raw request body string (empty `""` for GET). Signature is lowercase hex sha256.
2. **Timestamp skew window:** ±5 minutes. Outside the window → `E_TS_SKEW`.
3. **Request params:** `?action=X&ts=<ms>&sig=<hex>`. POST body is `application/json` (raw text, Apps Script `e.postData.contents`).
4. **Response envelope:** `{ok: true, data: ...}` on success, `{ok: false, error: {code, message}}` on failure. HTTP status is always 200 (Apps Script limitation — use envelope).
5. **Idempotency key:** `client_submission_id` (UUID from device). Duplicate detection scans the `client_submission_id` column of `F2_Responses`.
6. **Values storage (M4-only):** `F2_Responses` has flat metadata columns + **one `values_json` column** holding the entire form-values object as a JSON string. Flat per-item columns are deferred to M10 when the admin dashboard needs them.
7. **Secret management:** `PropertiesService.getScriptProperties()` holds `HMAC_SECRET`. `setupBackend()` generates a 32-byte random secret on first run if missing. `rotateSecret()` overwrites with a new one (operator runs manually when needed).
8. **Lock strategy:** Every write path wraps its Sheet mutation in `LockService.getScriptLock().waitLock(10000)`. Reads do not lock.
9. **Kill-switch honor:** Before any handler runs, router checks `F2_Config[kill_switch]`. If `true`, return `E_KILL_SWITCH`.
10. **Spec-version gate:** submit/batch-submit payload must carry `spec_version`. If `spec_version < F2_Config[min_accepted_spec_version]` (string compare; versions are ISO-date-ish), return `E_SPEC_TOO_OLD`.

---

## Task 1: Scaffold backend workspace

**Files:**
- Create: `deliverables/F2/PWA/backend/package.json`
- Create: `deliverables/F2/PWA/backend/vitest.config.mjs`
- Create: `deliverables/F2/PWA/backend/.gitignore`
- Create: `deliverables/F2/PWA/backend/README.md` (stub — filled in Task 11)
- Create: `deliverables/F2/PWA/backend/tests/smoke.test.mjs`

- [ ] **Step 1: Create `package.json`**

```json
{
  "name": "f2-pwa-backend",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest",
    "build": "node scripts/build.mjs"
  },
  "devDependencies": {
    "vitest": "^4.1.4"
  }
}
```

- [ ] **Step 2: Create `vitest.config.mjs`**

```js
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'node',
    include: ['tests/**/*.test.mjs'],
    clearMocks: true,
  },
});
```

- [ ] **Step 3: Create `.gitignore`**

```
node_modules
dist
.secrets
```

- [ ] **Step 4: Create README stub**

```markdown
# F2 PWA Backend — Apps Script

Placeholder. Populated by Task 11.
```

- [ ] **Step 5: Write a smoke test to prove Vitest runs**

Write `tests/smoke.test.mjs`:

```js
import { describe, it, expect } from 'vitest';

describe('smoke', () => {
  it('runs Vitest in the backend workspace', () => {
    expect(1 + 1).toBe(2);
  });
});
```

- [ ] **Step 6: Install and verify**

Run:
```bash
cd deliverables/F2/PWA/backend && npm install && npm test
```
Expected: `Test Files 1 passed (1) | Tests 1 passed (1)`.

- [ ] **Step 7: Commit**

*(Per user preference — do not suggest git commands. Pause, let the human commit manually, then proceed.)*

---

## Task 2: `Util.js` — response envelope, UUID, timing-safe equal

**Files:**
- Create: `deliverables/F2/PWA/backend/src/Util.js`
- Create: `deliverables/F2/PWA/backend/tests/util.test.mjs`

- [ ] **Step 1: Write failing tests**

Write `tests/util.test.mjs`:

```js
import { describe, it, expect } from 'vitest';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const { ok, fail, timingSafeEq, generateUuid, nowMs } = require('../src/Util.js');

describe('Util.ok / Util.fail', () => {
  it('ok returns {ok: true, data}', () => {
    expect(ok({ a: 1 })).toEqual({ ok: true, data: { a: 1 } });
  });

  it('fail returns {ok: false, error: {code, message}}', () => {
    expect(fail('E_X', 'nope')).toEqual({
      ok: false,
      error: { code: 'E_X', message: 'nope' },
    });
  });
});

describe('Util.timingSafeEq', () => {
  it('returns true for equal strings', () => {
    expect(timingSafeEq('abc', 'abc')).toBe(true);
  });
  it('returns false for different strings', () => {
    expect(timingSafeEq('abc', 'abd')).toBe(false);
  });
  it('returns false for different-length strings', () => {
    expect(timingSafeEq('abc', 'abcd')).toBe(false);
  });
  it('returns false when either input is not a string', () => {
    expect(timingSafeEq('abc', null)).toBe(false);
    expect(timingSafeEq(undefined, 'abc')).toBe(false);
  });
});

describe('Util.generateUuid', () => {
  it('returns a v4-looking UUID string', () => {
    const id = generateUuid();
    expect(id).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/);
  });
  it('returns unique ids on repeated calls', () => {
    const a = generateUuid();
    const b = generateUuid();
    expect(a).not.toBe(b);
  });
});

describe('Util.nowMs', () => {
  it('returns a positive integer close to Date.now()', () => {
    const n = nowMs();
    expect(Number.isInteger(n)).toBe(true);
    expect(Math.abs(n - Date.now())).toBeLessThan(1000);
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd deliverables/F2/PWA/backend && npm test`
Expected: FAIL — `Cannot find module '../src/Util.js'`.

- [ ] **Step 3: Create `src/Util.js`**

```js
function ok(data) {
  return { ok: true, data: data };
}

function fail(code, message) {
  return { ok: false, error: { code: code, message: message } };
}

function timingSafeEq(a, b) {
  if (typeof a !== 'string' || typeof b !== 'string') return false;
  if (a.length !== b.length) return false;
  var diff = 0;
  for (var i = 0; i < a.length; i++) {
    diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return diff === 0;
}

function generateUuid() {
  // RFC 4122 v4 — uses Math.random which is fine (not a secret, just an id).
  // Apps Script V8 has crypto.getRandomValues available on Utilities.getUuid(),
  // but Math.random is good enough for identifier collision resistance.
  var hex = '0123456789abcdef';
  var s = '';
  for (var i = 0; i < 36; i++) {
    if (i === 8 || i === 13 || i === 18 || i === 23) {
      s += '-';
    } else if (i === 14) {
      s += '4';
    } else if (i === 19) {
      s += hex[(Math.random() * 4) | 8];
    } else {
      s += hex[(Math.random() * 16) | 0];
    }
  }
  return s;
}

function nowMs() {
  return Date.now();
}

if (typeof module !== 'undefined') {
  module.exports = { ok: ok, fail: fail, timingSafeEq: timingSafeEq, generateUuid: generateUuid, nowMs: nowMs };
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `npm test`
Expected: PASS — 10 util assertions.

- [ ] **Step 5: Commit**

*(Pause for manual commit.)*

---

## Task 3: `Auth.js` — HMAC verification

**Files:**
- Create: `deliverables/F2/PWA/backend/src/Auth.js`
- Create: `deliverables/F2/PWA/backend/tests/auth.test.mjs`

- [ ] **Step 1: Write failing tests**

Write `tests/auth.test.mjs`:

```js
import { describe, it, expect } from 'vitest';
import crypto from 'node:crypto';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const { verifyRequest, canonicalString } = require('../src/Auth.js');

const SECRET = 'test-secret-0123456789';
const nodeHmacHex = (key, data) =>
  crypto.createHmac('sha256', key).update(data).digest('hex');

function signed({ method = 'POST', action = 'submit', ts, body = '' }) {
  const canonical = `${method}|${action}|${ts}|${body}`;
  return {
    method,
    action,
    ts: String(ts),
    body,
    sig: nodeHmacHex(SECRET, canonical),
  };
}

describe('Auth.canonicalString', () => {
  it('joins method|action|ts|body with pipes', () => {
    expect(canonicalString('POST', 'submit', '1700000000000', '{"a":1}'))
      .toBe('POST|submit|1700000000000|{"a":1}');
  });
});

describe('Auth.verifyRequest', () => {
  const deps = { hmacSha256Hex: nodeHmacHex, nowMs: () => 1700000000000 };

  it('returns {ok: true} for a valid signature within skew', () => {
    const r = signed({ ts: 1700000000000, body: '{"x":1}' });
    expect(verifyRequest(r, SECRET, deps)).toEqual({ ok: true });
  });

  it('returns E_TS_SKEW when timestamp is >5 minutes old', () => {
    const r = signed({ ts: 1700000000000 - 6 * 60 * 1000 });
    expect(verifyRequest(r, SECRET, deps)).toEqual({
      ok: false,
      error: { code: 'E_TS_SKEW', message: 'Timestamp outside ±5 minute window' },
    });
  });

  it('returns E_TS_SKEW when timestamp is >5 minutes in the future', () => {
    const r = signed({ ts: 1700000000000 + 6 * 60 * 1000 });
    expect(verifyRequest(r, SECRET, deps).error.code).toBe('E_TS_SKEW');
  });

  it('returns E_TS_INVALID when ts is not an integer', () => {
    const r = signed({ ts: 1700000000000 });
    r.ts = 'nope';
    expect(verifyRequest(r, SECRET, deps).error.code).toBe('E_TS_INVALID');
  });

  it('returns E_SIG_INVALID when body is tampered', () => {
    const r = signed({ ts: 1700000000000, body: '{"x":1}' });
    r.body = '{"x":2}';
    expect(verifyRequest(r, SECRET, deps).error.code).toBe('E_SIG_INVALID');
  });

  it('returns E_SIG_INVALID when signature is missing', () => {
    const r = signed({ ts: 1700000000000 });
    r.sig = '';
    expect(verifyRequest(r, SECRET, deps).error.code).toBe('E_SIG_INVALID');
  });

  it('returns E_SIG_INVALID when secret does not match', () => {
    const r = signed({ ts: 1700000000000 });
    expect(verifyRequest(r, 'wrong-secret', deps).error.code).toBe('E_SIG_INVALID');
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm test tests/auth.test.mjs`
Expected: FAIL — `Cannot find module '../src/Auth.js'`.

- [ ] **Step 3: Create `src/Auth.js`**

```js
var SKEW_MS = 5 * 60 * 1000;

function canonicalString(method, action, ts, body) {
  return method + '|' + action + '|' + ts + '|' + body;
}

function verifyRequest(req, secret, deps) {
  var ts = parseInt(req.ts, 10);
  if (!Number.isFinite(ts) || String(ts) !== String(req.ts).trim()) {
    return { ok: false, error: { code: 'E_TS_INVALID', message: 'Timestamp is not an integer' } };
  }
  var now = deps.nowMs();
  if (Math.abs(now - ts) > SKEW_MS) {
    return { ok: false, error: { code: 'E_TS_SKEW', message: 'Timestamp outside ±5 minute window' } };
  }
  if (typeof req.sig !== 'string' || req.sig.length === 0) {
    return { ok: false, error: { code: 'E_SIG_INVALID', message: 'Missing signature' } };
  }
  var canonical = canonicalString(req.method, req.action, String(ts), req.body || '');
  var expected = deps.hmacSha256Hex(secret, canonical);
  var a = String(expected).toLowerCase();
  var b = String(req.sig).toLowerCase();
  if (a.length !== b.length) {
    return { ok: false, error: { code: 'E_SIG_INVALID', message: 'Signature mismatch' } };
  }
  var diff = 0;
  for (var i = 0; i < a.length; i++) {
    diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  if (diff !== 0) {
    return { ok: false, error: { code: 'E_SIG_INVALID', message: 'Signature mismatch' } };
  }
  return { ok: true };
}

if (typeof module !== 'undefined') {
  module.exports = { verifyRequest: verifyRequest, canonicalString: canonicalString };
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `npm test tests/auth.test.mjs`
Expected: PASS — 8 assertions.

- [ ] **Step 5: Commit**

---

## Task 4: `Idempotency.js` — duplicate detection on `client_submission_id`

**Files:**
- Create: `deliverables/F2/PWA/backend/src/Idempotency.js`
- Create: `deliverables/F2/PWA/backend/tests/idempotency.test.mjs`

- [ ] **Step 1: Write failing tests**

Write `tests/idempotency.test.mjs`:

```js
import { describe, it, expect } from 'vitest';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const { findExistingSubmission } = require('../src/Idempotency.js');

function makeReader(rows) {
  // rows: [{client_submission_id, submission_id, rowNumber}]
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm test tests/idempotency.test.mjs`
Expected: FAIL — module not found.

- [ ] **Step 3: Create `src/Idempotency.js`**

```js
function findExistingSubmission(reader, clientSubmissionId) {
  if (!clientSubmissionId) return null;
  var cells = reader.readClientIdsColumn();
  if (!cells || cells.length === 0) return null;
  var offset = reader.headerRowOffset();
  for (var i = 0; i < cells.length; i++) {
    var value = cells[i][0];
    if (value && value === clientSubmissionId) {
      var rowNumber = i + 1 + offset;
      var row = reader.readRowByNumber(rowNumber);
      if (row) {
        return { submission_id: row.submission_id, row_number: rowNumber };
      }
    }
  }
  return null;
}

if (typeof module !== 'undefined') {
  module.exports = { findExistingSubmission: findExistingSubmission };
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `npm test tests/idempotency.test.mjs`
Expected: PASS — 4 assertions.

- [ ] **Step 5: Commit**

---

## Task 5: `Schema.js` — column definitions for all five tabs

**Files:**
- Create: `deliverables/F2/PWA/backend/src/Schema.js`

No unit tests for this file — it is data declarations. Downstream tests cover correctness indirectly.

- [ ] **Step 1: Create `src/Schema.js`**

```js
var F2_RESPONSES_COLUMNS = [
  'submission_id',
  'client_submission_id',
  'submitted_at_server',
  'submitted_at_client',
  'source',
  'spec_version',
  'app_version',
  'hcw_id',
  'facility_id',
  'device_fingerprint',
  'sync_attempt_count',
  'status',
  'values_json',
];

var F2_AUDIT_COLUMNS = [
  'audit_id',
  'occurred_at_server',
  'occurred_at_client',
  'event_type',
  'hcw_id',
  'facility_id',
  'app_version',
  'payload_json',
];

var F2_CONFIG_COLUMNS = ['key', 'value'];

var F2_CONFIG_DEFAULTS = [
  ['current_spec_version', '2026-04-17-m1'],
  ['min_accepted_spec_version', '2026-04-17-m1'],
  ['kill_switch', 'false'],
  ['broadcast_message', ''],
  ['spec_hash', ''],
];

var FACILITY_MASTER_LIST_COLUMNS = [
  'facility_id',
  'facility_name',
  'facility_type',
  'region',
  'province',
  'city_mun',
  'barangay',
];

var F2_DLQ_COLUMNS = [
  'dlq_id',
  'received_at_server',
  'client_submission_id',
  'reason',
  'payload_json',
];

var TABS = {
  RESPONSES: 'F2_Responses',
  AUDIT: 'F2_Audit',
  CONFIG: 'F2_Config',
  FACILITIES: 'FacilityMasterList',
  DLQ: 'F2_DLQ',
};

if (typeof module !== 'undefined') {
  module.exports = {
    F2_RESPONSES_COLUMNS: F2_RESPONSES_COLUMNS,
    F2_AUDIT_COLUMNS: F2_AUDIT_COLUMNS,
    F2_CONFIG_COLUMNS: F2_CONFIG_COLUMNS,
    F2_CONFIG_DEFAULTS: F2_CONFIG_DEFAULTS,
    FACILITY_MASTER_LIST_COLUMNS: FACILITY_MASTER_LIST_COLUMNS,
    F2_DLQ_COLUMNS: F2_DLQ_COLUMNS,
    TABS: TABS,
  };
}
```

- [ ] **Step 2: Commit**

---

## Task 6: `Handlers.js` — `submit` handler (single response)

**Files:**
- Create: `deliverables/F2/PWA/backend/src/Handlers.js`
- Create: `deliverables/F2/PWA/backend/tests/handlers.test.mjs`

- [ ] **Step 1: Write failing tests for `handleSubmit`**

Write `tests/handlers.test.mjs`:

```js
import { describe, it, expect, vi } from 'vitest';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const { handleSubmit } = require('../src/Handlers.js');

function makeCtx(overrides) {
  const appended = [];
  const base = {
    nowMs: () => 1700000000000,
    generateUuid: () => 'gen-uuid-fixed',
    responses: {
      findExisting: () => null,
      appendRow: (row) => { appended.push(row); return 'srv-new-1'; },
    },
    dlq: { appendRow: (row) => {} },
    config: {
      get: (key) => {
        if (key === 'kill_switch') return 'false';
        if (key === 'min_accepted_spec_version') return '2026-04-17-m1';
        return '';
      },
    },
    _appended: appended,
  };
  return Object.assign(base, overrides || {});
}

describe('handleSubmit', () => {
  it('appends a row and returns a new submission_id for a fresh client_submission_id', () => {
    const ctx = makeCtx();
    const result = handleSubmit(
      {
        client_submission_id: 'cli-1',
        hcw_id: 'hcw-1',
        facility_id: 'fac-1',
        spec_version: '2026-04-17-m1',
        app_version: '0.1.0',
        submitted_at_client: 1700000000000,
        device_fingerprint: 'android-chrome-138',
        values: { Q2: 'Regular', Q3: 'Female' },
      },
      ctx,
    );
    expect(result.ok).toBe(true);
    expect(result.data.status).toBe('accepted');
    expect(result.data.submission_id).toBe('srv-new-1');
    expect(ctx._appended).toHaveLength(1);
    expect(ctx._appended[0].client_submission_id).toBe('cli-1');
    expect(ctx._appended[0].submission_id).toBe('srv-new-1');
    expect(ctx._appended[0].source).toBe('PWA');
    expect(ctx._appended[0].status).toBe('stored');
    expect(JSON.parse(ctx._appended[0].values_json)).toEqual({ Q2: 'Regular', Q3: 'Female' });
  });

  it('returns duplicate status for a repeated client_submission_id', () => {
    const ctx = makeCtx({
      responses: {
        findExisting: () => ({ submission_id: 'srv-existing', row_number: 5 }),
        appendRow: vi.fn(() => 'unused'),
      },
    });
    const result = handleSubmit(
      {
        client_submission_id: 'cli-dup',
        hcw_id: 'hcw-1',
        facility_id: 'fac-1',
        spec_version: '2026-04-17-m1',
        submitted_at_client: 1700000000000,
        values: {},
      },
      ctx,
    );
    expect(result.ok).toBe(true);
    expect(result.data.status).toBe('duplicate');
    expect(result.data.submission_id).toBe('srv-existing');
    expect(ctx.responses.appendRow).not.toHaveBeenCalled();
  });

  it('rejects payload missing client_submission_id with E_PAYLOAD_INVALID', () => {
    const result = handleSubmit({ hcw_id: 'hcw-1', values: {} }, makeCtx());
    expect(result).toEqual({
      ok: false,
      error: { code: 'E_PAYLOAD_INVALID', message: 'Missing client_submission_id' },
    });
  });

  it('rejects payload missing values with E_PAYLOAD_INVALID', () => {
    const result = handleSubmit(
      { client_submission_id: 'cli-1', hcw_id: 'hcw-1', spec_version: '2026-04-17-m1' },
      makeCtx(),
    );
    expect(result.error.code).toBe('E_PAYLOAD_INVALID');
  });

  it('rejects payload missing spec_version with E_PAYLOAD_INVALID', () => {
    const result = handleSubmit(
      { client_submission_id: 'cli-1', hcw_id: 'hcw-1', values: {} },
      makeCtx(),
    );
    expect(result.error.code).toBe('E_PAYLOAD_INVALID');
  });

  it('rejects spec_version older than min_accepted_spec_version with E_SPEC_TOO_OLD', () => {
    const result = handleSubmit(
      {
        client_submission_id: 'cli-old',
        hcw_id: 'hcw-1',
        facility_id: 'fac-1',
        spec_version: '2026-01-01-m1',
        submitted_at_client: 1700000000000,
        values: {},
      },
      makeCtx(),
    );
    expect(result.error.code).toBe('E_SPEC_TOO_OLD');
  });

  it('writes to DLQ and returns E_VALIDATION when values is not an object', () => {
    const dlq = [];
    const ctx = makeCtx({ dlq: { appendRow: (row) => { dlq.push(row); } } });
    const result = handleSubmit(
      {
        client_submission_id: 'cli-bad',
        hcw_id: 'hcw-1',
        facility_id: 'fac-1',
        spec_version: '2026-04-17-m1',
        submitted_at_client: 1700000000000,
        values: 'not-an-object',
      },
      ctx,
    );
    expect(result.error.code).toBe('E_VALIDATION');
    expect(dlq).toHaveLength(1);
    expect(dlq[0].reason).toContain('values must be an object');
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm test tests/handlers.test.mjs`
Expected: FAIL — module not found.

- [ ] **Step 3: Create `src/Handlers.js` with `handleSubmit` only (other handlers added in later tasks)**

```js
function _requireString(obj, key) {
  return typeof obj[key] === 'string' && obj[key].length > 0;
}

function _buildResponseRow(payload, serverSubmissionId, ctx) {
  return {
    submission_id: serverSubmissionId,
    client_submission_id: payload.client_submission_id,
    submitted_at_server: new Date(ctx.nowMs()).toISOString(),
    submitted_at_client: payload.submitted_at_client != null
      ? new Date(payload.submitted_at_client).toISOString()
      : '',
    source: 'PWA',
    spec_version: payload.spec_version || '',
    app_version: payload.app_version || '',
    hcw_id: payload.hcw_id || '',
    facility_id: payload.facility_id || '',
    device_fingerprint: payload.device_fingerprint || '',
    sync_attempt_count: payload.sync_attempt_count != null ? String(payload.sync_attempt_count) : '1',
    status: 'stored',
    values_json: JSON.stringify(payload.values || {}),
  };
}

function handleSubmit(payload, ctx) {
  if (!payload || typeof payload !== 'object') {
    return { ok: false, error: { code: 'E_PAYLOAD_INVALID', message: 'Body must be a JSON object' } };
  }
  if (!_requireString(payload, 'client_submission_id')) {
    return { ok: false, error: { code: 'E_PAYLOAD_INVALID', message: 'Missing client_submission_id' } };
  }
  if (!_requireString(payload, 'spec_version')) {
    return { ok: false, error: { code: 'E_PAYLOAD_INVALID', message: 'Missing spec_version' } };
  }
  if (payload.values == null) {
    return { ok: false, error: { code: 'E_PAYLOAD_INVALID', message: 'Missing values' } };
  }
  var minSpec = ctx.config.get('min_accepted_spec_version') || '';
  if (minSpec && payload.spec_version < minSpec) {
    return { ok: false, error: { code: 'E_SPEC_TOO_OLD', message: 'spec_version ' + payload.spec_version + ' < ' + minSpec } };
  }
  if (typeof payload.values !== 'object' || Array.isArray(payload.values)) {
    ctx.dlq.appendRow({
      dlq_id: ctx.generateUuid(),
      received_at_server: new Date(ctx.nowMs()).toISOString(),
      client_submission_id: payload.client_submission_id,
      reason: 'values must be an object',
      payload_json: JSON.stringify(payload),
    });
    return { ok: false, error: { code: 'E_VALIDATION', message: 'values must be an object' } };
  }

  var existing = ctx.responses.findExisting(payload.client_submission_id);
  if (existing) {
    return { ok: true, data: { submission_id: existing.submission_id, status: 'duplicate', server_timestamp: new Date(ctx.nowMs()).toISOString() } };
  }

  var serverId = 'srv-' + ctx.generateUuid();
  var row = _buildResponseRow(payload, serverId, ctx);
  var appendedId = ctx.responses.appendRow(row);
  return {
    ok: true,
    data: {
      submission_id: appendedId || serverId,
      status: 'accepted',
      server_timestamp: row.submitted_at_server,
    },
  };
}

if (typeof module !== 'undefined') {
  module.exports = { handleSubmit: handleSubmit };
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `npm test tests/handlers.test.mjs`
Expected: PASS — 7 assertions.

- [ ] **Step 5: Commit**

---

## Task 7: `Handlers.js` — `handleBatchSubmit`

**Files:**
- Modify: `deliverables/F2/PWA/backend/src/Handlers.js`
- Modify: `deliverables/F2/PWA/backend/tests/handlers.test.mjs`

- [ ] **Step 1: Append failing tests**

Append to `tests/handlers.test.mjs`:

```js
const { handleBatchSubmit } = require('../src/Handlers.js');

describe('handleBatchSubmit', () => {
  it('processes an array of responses and returns per-item results', () => {
    let nextId = 0;
    const ctx = {
      nowMs: () => 1700000000000,
      generateUuid: () => 'u' + (++nextId),
      responses: {
        findExisting: () => null,
        appendRow: (row) => row.submission_id,
      },
      dlq: { appendRow: () => {} },
      config: { get: (k) => (k === 'min_accepted_spec_version' ? '2026-04-17-m1' : '') },
    };
    const payload = {
      responses: [
        { client_submission_id: 'c1', hcw_id: 'h1', spec_version: '2026-04-17-m1', values: {} },
        { client_submission_id: 'c2', hcw_id: 'h1', spec_version: '2026-04-17-m1', values: {} },
      ],
    };
    const result = handleBatchSubmit(payload, ctx);
    expect(result.ok).toBe(true);
    expect(result.data.results).toHaveLength(2);
    expect(result.data.results[0].client_submission_id).toBe('c1');
    expect(result.data.results[0].status).toBe('accepted');
    expect(result.data.results[1].status).toBe('accepted');
  });

  it('rejects non-array payload with E_PAYLOAD_INVALID', () => {
    const result = handleBatchSubmit({ responses: 'not-an-array' }, {});
    expect(result.error.code).toBe('E_PAYLOAD_INVALID');
  });

  it('rejects batches over 50 items with E_BATCH_TOO_LARGE', () => {
    const responses = Array.from({ length: 51 }, (_, i) => ({
      client_submission_id: 'c' + i,
      spec_version: '2026-04-17-m1',
      values: {},
    }));
    const result = handleBatchSubmit({ responses }, {});
    expect(result.error.code).toBe('E_BATCH_TOO_LARGE');
  });

  it('returns per-item errors without aborting the batch', () => {
    let nextId = 0;
    const ctx = {
      nowMs: () => 1700000000000,
      generateUuid: () => 'u' + (++nextId),
      responses: {
        findExisting: () => null,
        appendRow: (row) => row.submission_id,
      },
      dlq: { appendRow: () => {} },
      config: { get: () => '' },
    };
    const result = handleBatchSubmit({
      responses: [
        { client_submission_id: 'c1', spec_version: '2026-04-17-m1', values: {} },
        { hcw_id: 'no-client-id', spec_version: '2026-04-17-m1', values: {} },
        { client_submission_id: 'c3', spec_version: '2026-04-17-m1', values: {} },
      ],
    }, ctx);
    expect(result.data.results).toHaveLength(3);
    expect(result.data.results[0].status).toBe('accepted');
    expect(result.data.results[1].status).toBe('rejected');
    expect(result.data.results[1].error.code).toBe('E_PAYLOAD_INVALID');
    expect(result.data.results[2].status).toBe('accepted');
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm test tests/handlers.test.mjs`
Expected: FAIL — `handleBatchSubmit is not a function`.

- [ ] **Step 3: Append `handleBatchSubmit` to `src/Handlers.js`**

Add before the `if (typeof module !== 'undefined')` block:

```js
function handleBatchSubmit(payload, ctx) {
  if (!payload || !Array.isArray(payload.responses)) {
    return { ok: false, error: { code: 'E_PAYLOAD_INVALID', message: 'Body must be { responses: [] }' } };
  }
  if (payload.responses.length > 50) {
    return { ok: false, error: { code: 'E_BATCH_TOO_LARGE', message: 'Max 50 responses per batch' } };
  }
  var results = [];
  for (var i = 0; i < payload.responses.length; i++) {
    var item = payload.responses[i];
    var clientId = item && item.client_submission_id ? item.client_submission_id : null;
    var r = handleSubmit(item, ctx);
    if (r.ok) {
      results.push({
        client_submission_id: clientId,
        submission_id: r.data.submission_id,
        status: r.data.status,
      });
    } else {
      results.push({
        client_submission_id: clientId,
        status: 'rejected',
        error: r.error,
      });
    }
  }
  return { ok: true, data: { results: results } };
}
```

And update the export line to include `handleBatchSubmit`:

```js
if (typeof module !== 'undefined') {
  module.exports = { handleSubmit: handleSubmit, handleBatchSubmit: handleBatchSubmit };
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `npm test tests/handlers.test.mjs`
Expected: PASS — all assertions (11 total: 7 submit + 4 batch).

- [ ] **Step 5: Commit**

---

## Task 8: `Handlers.js` — `handleFacilities`, `handleConfig`, `handleSpecHash`, `handleAudit`

**Files:**
- Modify: `deliverables/F2/PWA/backend/src/Handlers.js`
- Modify: `deliverables/F2/PWA/backend/tests/handlers.test.mjs`

- [ ] **Step 1: Append failing tests**

Append to `tests/handlers.test.mjs`:

```js
const { handleFacilities, handleConfig, handleSpecHash, handleAudit } = require('../src/Handlers.js');

describe('handleFacilities', () => {
  it('returns the facility master list as an array of objects', () => {
    const ctx = {
      facilities: {
        readAll: () => [
          { facility_id: 'F001', facility_name: 'RHU Laguna', region: 'IV-A', province: 'Laguna', city_mun: 'Los Baños', barangay: 'Batong Malake', facility_type: 'RHU' },
          { facility_id: 'F002', facility_name: 'Provincial Hospital', region: 'IV-A', province: 'Laguna', city_mun: 'Sta Cruz', barangay: 'Poblacion', facility_type: 'Hospital' },
        ],
      },
    };
    const r = handleFacilities(ctx);
    expect(r.ok).toBe(true);
    expect(r.data.facilities).toHaveLength(2);
    expect(r.data.facilities[0].facility_id).toBe('F001');
  });

  it('returns empty array when sheet is empty', () => {
    const r = handleFacilities({ facilities: { readAll: () => [] } });
    expect(r.data.facilities).toEqual([]);
  });
});

describe('handleConfig', () => {
  it('returns all config key/value pairs as an object, coercing bool/number strings', () => {
    const ctx = {
      config: {
        readAll: () => [
          ['current_spec_version', '2026-04-17-m1'],
          ['min_accepted_spec_version', '2026-04-17-m1'],
          ['kill_switch', 'false'],
          ['broadcast_message', 'Hello'],
          ['spec_hash', 'abc123'],
        ],
      },
    };
    const r = handleConfig(ctx);
    expect(r.ok).toBe(true);
    expect(r.data).toEqual({
      current_spec_version: '2026-04-17-m1',
      min_accepted_spec_version: '2026-04-17-m1',
      kill_switch: false,
      broadcast_message: 'Hello',
      spec_hash: 'abc123',
    });
  });

  it('coerces kill_switch=true correctly', () => {
    const r = handleConfig({
      config: { readAll: () => [['kill_switch', 'true']] },
    });
    expect(r.data.kill_switch).toBe(true);
  });
});

describe('handleSpecHash', () => {
  it('returns spec_hash and current_spec_version from config', () => {
    const ctx = {
      config: {
        get: (k) => {
          if (k === 'spec_hash') return 'abc123';
          if (k === 'current_spec_version') return '2026-04-17-m1';
          return '';
        },
      },
    };
    const r = handleSpecHash(ctx);
    expect(r).toEqual({
      ok: true,
      data: { spec_hash: 'abc123', current_spec_version: '2026-04-17-m1' },
    });
  });
});

describe('handleAudit', () => {
  it('appends an audit row and returns the audit_id', () => {
    const appended = [];
    const ctx = {
      nowMs: () => 1700000000000,
      generateUuid: () => 'aud-fixed',
      audit: { appendRow: (row) => { appended.push(row); return row.audit_id; } },
    };
    const r = handleAudit(
      {
        event_type: 'app_install',
        occurred_at_client: 1699999999000,
        hcw_id: 'hcw-1',
        facility_id: 'fac-1',
        app_version: '0.1.0',
        payload: { source: 'beforeinstallprompt' },
      },
      ctx,
    );
    expect(r.ok).toBe(true);
    expect(r.data.audit_id).toBe('aud-fixed');
    expect(appended).toHaveLength(1);
    expect(appended[0].event_type).toBe('app_install');
    expect(JSON.parse(appended[0].payload_json)).toEqual({ source: 'beforeinstallprompt' });
  });

  it('rejects payload missing event_type with E_PAYLOAD_INVALID', () => {
    const r = handleAudit({}, {
      nowMs: () => 1,
      generateUuid: () => 'x',
      audit: { appendRow: () => {} },
    });
    expect(r.error.code).toBe('E_PAYLOAD_INVALID');
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm test tests/handlers.test.mjs`
Expected: FAIL — 4 handlers not exported.

- [ ] **Step 3: Append handlers to `src/Handlers.js`**

Append before the export block:

```js
function handleFacilities(ctx) {
  var rows = ctx.facilities.readAll();
  return { ok: true, data: { facilities: rows } };
}

function _coerceConfigValue(value) {
  if (value === 'true') return true;
  if (value === 'false') return false;
  return value;
}

function handleConfig(ctx) {
  var pairs = ctx.config.readAll();
  var out = {};
  for (var i = 0; i < pairs.length; i++) {
    var key = pairs[i][0];
    var val = pairs[i][1];
    out[key] = _coerceConfigValue(val);
  }
  return { ok: true, data: out };
}

function handleSpecHash(ctx) {
  return {
    ok: true,
    data: {
      spec_hash: ctx.config.get('spec_hash') || '',
      current_spec_version: ctx.config.get('current_spec_version') || '',
    },
  };
}

function handleAudit(payload, ctx) {
  if (!payload || typeof payload !== 'object' || typeof payload.event_type !== 'string' || !payload.event_type) {
    return { ok: false, error: { code: 'E_PAYLOAD_INVALID', message: 'Missing event_type' } };
  }
  var auditId = ctx.generateUuid();
  ctx.audit.appendRow({
    audit_id: auditId,
    occurred_at_server: new Date(ctx.nowMs()).toISOString(),
    occurred_at_client: payload.occurred_at_client != null ? new Date(payload.occurred_at_client).toISOString() : '',
    event_type: payload.event_type,
    hcw_id: payload.hcw_id || '',
    facility_id: payload.facility_id || '',
    app_version: payload.app_version || '',
    payload_json: JSON.stringify(payload.payload || {}),
  });
  return { ok: true, data: { audit_id: auditId } };
}
```

Update the export line:

```js
if (typeof module !== 'undefined') {
  module.exports = {
    handleSubmit: handleSubmit,
    handleBatchSubmit: handleBatchSubmit,
    handleFacilities: handleFacilities,
    handleConfig: handleConfig,
    handleSpecHash: handleSpecHash,
    handleAudit: handleAudit,
  };
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `npm test tests/handlers.test.mjs`
Expected: PASS — all 17 assertions across 6 handlers.

- [ ] **Step 5: Commit**

---

## Task 9: `Router.js` — action dispatch with kill-switch

**Files:**
- Create: `deliverables/F2/PWA/backend/src/Router.js`
- Create: `deliverables/F2/PWA/backend/tests/router.test.mjs`

- [ ] **Step 1: Write failing tests**

Write `tests/router.test.mjs`:

```js
import { describe, it, expect, vi } from 'vitest';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const { dispatch } = require('../src/Router.js');

function makeCtx(configOverrides) {
  return {
    config: {
      get: (k) => (configOverrides && configOverrides[k] != null ? configOverrides[k] : ''),
      readAll: () => [],
    },
    responses: {},
    dlq: {},
    audit: {},
    facilities: { readAll: () => [] },
    nowMs: () => 1,
    generateUuid: () => 'fixed',
  };
}

describe('dispatch', () => {
  it('returns E_ACTION_UNKNOWN for unknown actions', () => {
    const r = dispatch({ action: 'wtf', method: 'GET', body: '' }, makeCtx(), {});
    expect(r.error.code).toBe('E_ACTION_UNKNOWN');
  });

  it('returns E_METHOD_UNKNOWN when POST-only action is called with GET', () => {
    const r = dispatch({ action: 'submit', method: 'GET', body: '' }, makeCtx(), {});
    expect(r.error.code).toBe('E_METHOD_UNKNOWN');
  });

  it('returns E_METHOD_UNKNOWN when GET-only action is called with POST', () => {
    const r = dispatch({ action: 'facilities', method: 'POST', body: '{}' }, makeCtx(), {});
    expect(r.error.code).toBe('E_METHOD_UNKNOWN');
  });

  it('returns E_KILL_SWITCH when config.kill_switch is true', () => {
    const r = dispatch(
      { action: 'facilities', method: 'GET', body: '' },
      makeCtx({ kill_switch: 'true' }),
      {},
    );
    expect(r.error.code).toBe('E_KILL_SWITCH');
  });

  it('calls the correct handler for each known action', () => {
    const handlers = {
      handleSubmit: vi.fn(() => ({ ok: true, data: 'submit-ok' })),
      handleBatchSubmit: vi.fn(() => ({ ok: true, data: 'batch-ok' })),
      handleAudit: vi.fn(() => ({ ok: true, data: 'audit-ok' })),
      handleFacilities: vi.fn(() => ({ ok: true, data: 'fac-ok' })),
      handleConfig: vi.fn(() => ({ ok: true, data: 'cfg-ok' })),
      handleSpecHash: vi.fn(() => ({ ok: true, data: 'hash-ok' })),
    };
    expect(dispatch({ action: 'submit', method: 'POST', body: '{"a":1}' }, makeCtx(), handlers).data).toBe('submit-ok');
    expect(handlers.handleSubmit).toHaveBeenCalledWith({ a: 1 }, expect.any(Object));
    expect(dispatch({ action: 'batch-submit', method: 'POST', body: '{"responses":[]}' }, makeCtx(), handlers).data).toBe('batch-ok');
    expect(dispatch({ action: 'audit', method: 'POST', body: '{"event_type":"x"}' }, makeCtx(), handlers).data).toBe('audit-ok');
    expect(dispatch({ action: 'facilities', method: 'GET', body: '' }, makeCtx(), handlers).data).toBe('fac-ok');
    expect(dispatch({ action: 'config', method: 'GET', body: '' }, makeCtx(), handlers).data).toBe('cfg-ok');
    expect(dispatch({ action: 'spec-hash', method: 'GET', body: '' }, makeCtx(), handlers).data).toBe('hash-ok');
  });

  it('returns E_PAYLOAD_INVALID when POST body is not valid JSON', () => {
    const handlers = { handleSubmit: vi.fn() };
    const r = dispatch({ action: 'submit', method: 'POST', body: 'not-json' }, makeCtx(), handlers);
    expect(r.error.code).toBe('E_PAYLOAD_INVALID');
    expect(handlers.handleSubmit).not.toHaveBeenCalled();
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm test tests/router.test.mjs`
Expected: FAIL — module not found.

- [ ] **Step 3: Create `src/Router.js`**

```js
var _ROUTE_METHODS = {
  'submit':       'POST',
  'batch-submit': 'POST',
  'audit':        'POST',
  'facilities':   'GET',
  'config':       'GET',
  'spec-hash':    'GET',
};

var _ROUTE_HANDLERS = {
  'submit':       'handleSubmit',
  'batch-submit': 'handleBatchSubmit',
  'audit':        'handleAudit',
  'facilities':   'handleFacilities',
  'config':       'handleConfig',
  'spec-hash':    'handleSpecHash',
};

function dispatch(req, ctx, handlers) {
  var expectedMethod = _ROUTE_METHODS[req.action];
  if (!expectedMethod) {
    return { ok: false, error: { code: 'E_ACTION_UNKNOWN', message: 'Unknown action: ' + req.action } };
  }
  if (expectedMethod !== req.method) {
    return { ok: false, error: { code: 'E_METHOD_UNKNOWN', message: 'Action ' + req.action + ' requires ' + expectedMethod } };
  }
  if (ctx.config.get('kill_switch') === 'true') {
    return { ok: false, error: { code: 'E_KILL_SWITCH', message: 'Backend is temporarily unavailable' } };
  }

  var handlerName = _ROUTE_HANDLERS[req.action];
  var handler = handlers[handlerName];

  if (expectedMethod === 'GET') {
    return handler(ctx);
  }

  var parsed;
  try {
    parsed = req.body && req.body.length > 0 ? JSON.parse(req.body) : {};
  } catch (e) {
    return { ok: false, error: { code: 'E_PAYLOAD_INVALID', message: 'Body is not valid JSON: ' + e.message } };
  }
  return handler(parsed, ctx);
}

if (typeof module !== 'undefined') {
  module.exports = { dispatch: dispatch };
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `npm test tests/router.test.mjs`
Expected: PASS — 6 router scenarios.

- [ ] **Step 5: Commit**

---

## Task 10: Apps Script glue — `appsscript.json`, `Code.js`, `Setup.js`

**Files:**
- Create: `deliverables/F2/PWA/backend/apps-script/appsscript.json`
- Create: `deliverables/F2/PWA/backend/apps-script/Code.js`
- Create: `deliverables/F2/PWA/backend/apps-script/Setup.js`

This task has no Vitest tests — these files only run inside Apps Script. Verification is via Task 12's curl smoke tests against a deployed Web App.

- [ ] **Step 1: Create `apps-script/appsscript.json`**

```json
{
  "timeZone": "Asia/Manila",
  "runtimeVersion": "V8",
  "exceptionLogging": "STACKDRIVER",
  "webapp": {
    "executeAs": "USER_DEPLOYING",
    "access": "ANYONE_ANONYMOUS"
  },
  "oauthScopes": [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/script.external_request",
    "https://www.googleapis.com/auth/script.scriptapp",
    "https://www.googleapis.com/auth/script.storage"
  ]
}
```

- [ ] **Step 2: Create `apps-script/Code.js` — `doGet`, `doPost`, and `buildCtx`**

```js
var PROP_HMAC_SECRET = 'HMAC_SECRET';
var PROP_SPREADSHEET_ID = 'SPREADSHEET_ID';

function doGet(e) {
  return _serve('GET', e);
}

function doPost(e) {
  return _serve('POST', e);
}

function _serve(method, e) {
  try {
    var action = (e && e.parameter && e.parameter.action) || '';
    var ts = (e && e.parameter && e.parameter.ts) || '';
    var sig = (e && e.parameter && e.parameter.sig) || '';
    var body = method === 'POST' && e.postData && e.postData.contents ? e.postData.contents : '';

    var secret = PropertiesService.getScriptProperties().getProperty(PROP_HMAC_SECRET);
    if (!secret) {
      return _jsonOut({ ok: false, error: { code: 'E_INTERNAL', message: 'HMAC secret not configured. Run setupBackend().' } });
    }

    var verifyResult = verifyRequest(
      { method: method, action: action, ts: ts, sig: sig, body: body },
      secret,
      { hmacSha256Hex: _gasHmacHex, nowMs: Date.now },
    );
    if (!verifyResult.ok) return _jsonOut(verifyResult);

    var ctx = buildCtx();
    var handlers = {
      handleSubmit: handleSubmit,
      handleBatchSubmit: handleBatchSubmit,
      handleAudit: handleAudit,
      handleFacilities: handleFacilities,
      handleConfig: handleConfig,
      handleSpecHash: handleSpecHash,
    };

    // Writes take a script-level lock; reads do not.
    var needsLock = method === 'POST';
    if (needsLock) {
      var lock = LockService.getScriptLock();
      lock.waitLock(10000);
      try {
        var r = dispatch({ action: action, method: method, body: body }, ctx, handlers);
        return _jsonOut(r);
      } finally {
        lock.releaseLock();
      }
    } else {
      var r2 = dispatch({ action: action, method: method, body: body }, ctx, handlers);
      return _jsonOut(r2);
    }
  } catch (err) {
    return _jsonOut({ ok: false, error: { code: 'E_INTERNAL', message: String(err && err.message ? err.message : err) } });
  }
}

function buildCtx() {
  var ssId = PropertiesService.getScriptProperties().getProperty(PROP_SPREADSHEET_ID);
  if (!ssId) throw new Error('SPREADSHEET_ID not configured. Run setupBackend().');
  var ss = SpreadsheetApp.openById(ssId);
  var tabs = {
    responses: ss.getSheetByName('F2_Responses'),
    audit: ss.getSheetByName('F2_Audit'),
    config: ss.getSheetByName('F2_Config'),
    facilities: ss.getSheetByName('FacilityMasterList'),
    dlq: ss.getSheetByName('F2_DLQ'),
  };

  return {
    nowMs: Date.now,
    generateUuid: function () { return Utilities.getUuid(); },
    responses: _buildResponsesCtx(tabs.responses),
    dlq: _buildDlqCtx(tabs.dlq),
    audit: _buildAuditCtx(tabs.audit),
    config: _buildConfigCtx(tabs.config),
    facilities: _buildFacilitiesCtx(tabs.facilities),
  };
}

function _buildResponsesCtx(sheet) {
  var cols = F2_RESPONSES_COLUMNS;
  var clientIdCol = cols.indexOf('client_submission_id') + 1;

  return {
    findExisting: function (clientSubmissionId) {
      var reader = {
        readClientIdsColumn: function () {
          var last = sheet.getLastRow();
          if (last < 2) return [];
          return sheet.getRange(2, clientIdCol, last - 1, 1).getValues();
        },
        readRowByNumber: function (rowNumber) {
          var values = sheet.getRange(rowNumber, 1, 1, cols.length).getValues()[0];
          var out = {};
          for (var i = 0; i < cols.length; i++) out[cols[i]] = values[i];
          return out;
        },
        headerRowOffset: function () { return 1; },
      };
      return findExistingSubmission(reader, clientSubmissionId);
    },
    appendRow: function (rowObj) {
      var arr = cols.map(function (c) { return rowObj[c] != null ? rowObj[c] : ''; });
      sheet.appendRow(arr);
      return rowObj.submission_id;
    },
  };
}

function _buildDlqCtx(sheet) {
  var cols = F2_DLQ_COLUMNS;
  return {
    appendRow: function (rowObj) {
      var arr = cols.map(function (c) { return rowObj[c] != null ? rowObj[c] : ''; });
      sheet.appendRow(arr);
    },
  };
}

function _buildAuditCtx(sheet) {
  var cols = F2_AUDIT_COLUMNS;
  return {
    appendRow: function (rowObj) {
      var arr = cols.map(function (c) { return rowObj[c] != null ? rowObj[c] : ''; });
      sheet.appendRow(arr);
      return rowObj.audit_id;
    },
  };
}

function _buildConfigCtx(sheet) {
  return {
    readAll: function () {
      var last = sheet.getLastRow();
      if (last < 2) return [];
      return sheet.getRange(2, 1, last - 1, 2).getValues();
    },
    get: function (key) {
      var rows = this.readAll();
      for (var i = 0; i < rows.length; i++) {
        if (rows[i][0] === key) return String(rows[i][1]);
      }
      return '';
    },
  };
}

function _buildFacilitiesCtx(sheet) {
  var cols = FACILITY_MASTER_LIST_COLUMNS;
  return {
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

function _gasHmacHex(secret, message) {
  var bytes = Utilities.computeHmacSha256Signature(message, secret);
  var hex = '';
  for (var i = 0; i < bytes.length; i++) {
    var b = bytes[i];
    if (b < 0) b += 256;
    var h = b.toString(16);
    hex += h.length === 1 ? '0' + h : h;
  }
  return hex;
}

function _jsonOut(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
```

- [ ] **Step 3: Create `apps-script/Setup.js` — one-time and rotation helpers**

```js
function setupBackend() {
  var props = PropertiesService.getScriptProperties();

  var ssId = props.getProperty(PROP_SPREADSHEET_ID);
  var ss;
  if (ssId) {
    ss = SpreadsheetApp.openById(ssId);
    Logger.log('Reusing existing spreadsheet: ' + ss.getUrl());
  } else {
    ss = SpreadsheetApp.create('F2 PWA Backend — ' + new Date().toISOString().slice(0, 10));
    props.setProperty(PROP_SPREADSHEET_ID, ss.getId());
    Logger.log('Created spreadsheet: ' + ss.getUrl());
  }

  _ensureSheetWithHeader(ss, TABS.RESPONSES, F2_RESPONSES_COLUMNS);
  _ensureSheetWithHeader(ss, TABS.AUDIT, F2_AUDIT_COLUMNS);
  _ensureSheetWithHeader(ss, TABS.CONFIG, F2_CONFIG_COLUMNS);
  _ensureSheetWithHeader(ss, TABS.FACILITIES, FACILITY_MASTER_LIST_COLUMNS);
  _ensureSheetWithHeader(ss, TABS.DLQ, F2_DLQ_COLUMNS);

  var defaultSheet = ss.getSheetByName('Sheet1');
  if (defaultSheet) ss.deleteSheet(defaultSheet);

  _seedConfigDefaults(ss.getSheetByName(TABS.CONFIG));

  var secret = props.getProperty(PROP_HMAC_SECRET);
  if (!secret) {
    secret = _generateSecret();
    props.setProperty(PROP_HMAC_SECRET, secret);
    Logger.log('Generated new HMAC_SECRET (first 6 chars): ' + secret.slice(0, 6) + '…');
  } else {
    Logger.log('HMAC_SECRET already set (first 6 chars): ' + secret.slice(0, 6) + '…');
  }

  Logger.log('Setup complete.');
  Logger.log('Spreadsheet URL: ' + ss.getUrl());
  Logger.log('Next: Deploy → New deployment → Web app. Save the deployment URL.');
}

function rotateSecret() {
  var props = PropertiesService.getScriptProperties();
  var newSecret = _generateSecret();
  props.setProperty(PROP_HMAC_SECRET, newSecret);
  Logger.log('Rotated HMAC_SECRET. New secret starts: ' + newSecret.slice(0, 6) + '…');
  Logger.log('Update the PWA build-time env var VITE_F2_HMAC_SECRET and redeploy.');
}

function getSpreadsheetUrl() {
  var ssId = PropertiesService.getScriptProperties().getProperty(PROP_SPREADSHEET_ID);
  if (!ssId) { Logger.log('No spreadsheet — run setupBackend() first.'); return; }
  Logger.log(SpreadsheetApp.openById(ssId).getUrl());
}

function _ensureSheetWithHeader(ss, name, columns) {
  var sheet = ss.getSheetByName(name);
  if (!sheet) sheet = ss.insertSheet(name);
  var header = sheet.getRange(1, 1, 1, columns.length).getValues()[0];
  var needsHeader = false;
  for (var i = 0; i < columns.length; i++) {
    if (header[i] !== columns[i]) { needsHeader = true; break; }
  }
  if (needsHeader) {
    sheet.getRange(1, 1, 1, columns.length).setValues([columns]).setFontWeight('bold');
    sheet.setFrozenRows(1);
  }
}

function _seedConfigDefaults(sheet) {
  var last = sheet.getLastRow();
  var existing = {};
  if (last >= 2) {
    var rows = sheet.getRange(2, 1, last - 1, 2).getValues();
    for (var i = 0; i < rows.length; i++) existing[rows[i][0]] = true;
  }
  for (var j = 0; j < F2_CONFIG_DEFAULTS.length; j++) {
    var key = F2_CONFIG_DEFAULTS[j][0];
    if (!existing[key]) {
      sheet.appendRow(F2_CONFIG_DEFAULTS[j]);
    }
  }
}

function _generateSecret() {
  var hex = '0123456789abcdef';
  var s = '';
  for (var i = 0; i < 64; i++) {
    s += hex[(Math.random() * 16) | 0];
  }
  return s;
}
```

- [ ] **Step 4: Commit**

*(This task adds no tests; verification is via the live curl smoke test in Task 12.)*

---

## Task 11: `scripts/build.mjs` — concatenate sources into `dist/Code.gs`

**Files:**
- Create: `deliverables/F2/PWA/backend/scripts/build.mjs`

- [ ] **Step 1: Create `scripts/build.mjs`**

```js
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, '..');

// Concatenation order matters: types and helpers before callers.
const ORDER = [
  'src/Schema.js',
  'src/Util.js',
  'src/Auth.js',
  'src/Idempotency.js',
  'src/Handlers.js',
  'src/Router.js',
  'apps-script/Setup.js',
  'apps-script/Code.js',
];

function stripCjsExport(source) {
  // Remove the `if (typeof module !== 'undefined') module.exports = {...};` tail block so the
  // concatenated file is clean Apps Script. The block always lives at end-of-file by convention.
  return source.replace(/\n?if \(typeof module !== ['"]undefined['"]\)[\s\S]*?\};?\s*$/m, '\n');
}

async function main() {
  const parts = [];
  parts.push('// AUTOGENERATED by scripts/build.mjs — do not edit by hand.');
  parts.push('// Regenerate with `npm run build` inside deliverables/F2/PWA/backend/.');
  parts.push(`// Built: ${new Date().toISOString()}`);
  parts.push('');

  for (const rel of ORDER) {
    const abs = resolve(root, rel);
    if (!existsSync(abs)) throw new Error(`Missing source file: ${rel}`);
    const source = await readFile(abs, 'utf8');
    parts.push(`// ===== ${rel} =====`);
    parts.push(stripCjsExport(source).trim());
    parts.push('');
  }

  const distDir = resolve(root, 'dist');
  await mkdir(distDir, { recursive: true });
  const outPath = resolve(distDir, 'Code.gs');
  await writeFile(outPath, parts.join('\n'), 'utf8');

  // Also copy appsscript.json so a clasp push would work if the user chooses that path.
  const manifest = await readFile(resolve(root, 'apps-script/appsscript.json'), 'utf8');
  await writeFile(resolve(distDir, 'appsscript.json'), manifest, 'utf8');

  console.log(`Wrote ${outPath} (${parts.join('\n').length} chars)`);
}

main().catch((err) => { console.error(err); process.exit(1); });
```

- [ ] **Step 2: Run the build**

Run: `cd deliverables/F2/PWA/backend && npm run build`
Expected: `Wrote .../dist/Code.gs (N chars)` with N > 5000.

- [ ] **Step 3: Sanity-check the output**

Run: `head -30 dist/Code.gs`
Expected: top shows the autogenerated banner, followed by `// ===== src/Schema.js =====` then `var F2_RESPONSES_COLUMNS = [...]`. Scroll to confirm `function doGet(e)` and `function doPost(e)` appear near the bottom, and no `module.exports` lines survived.

Run: `grep -c "module.exports" dist/Code.gs`
Expected: `0`.

- [ ] **Step 4: Commit**

---

## Task 12: Curl smoke tests + README + NEXT.md for M5

**Files:**
- Create: `deliverables/F2/PWA/backend/scripts/smoke.sh`
- Create: `deliverables/F2/PWA/backend/scripts/sign.mjs`
- Modify: `deliverables/F2/PWA/backend/README.md`
- Modify: `deliverables/F2/PWA/app/NEXT.md`

- [ ] **Step 1: Create `scripts/sign.mjs` — helper that builds a signed URL**

```js
#!/usr/bin/env node
// Usage: node scripts/sign.mjs <method> <action> <body-or-empty>
// Reads BACKEND_URL and HMAC_SECRET from env.
// Prints a curl-ready command to stdout.

import crypto from 'node:crypto';

const [method, action, body = ''] = process.argv.slice(2);
if (!method || !action) {
  console.error('Usage: node scripts/sign.mjs <METHOD> <ACTION> [BODY]');
  process.exit(2);
}

const url = process.env.BACKEND_URL;
const secret = process.env.HMAC_SECRET;
if (!url || !secret) {
  console.error('Set BACKEND_URL and HMAC_SECRET env vars.');
  process.exit(2);
}

const ts = Date.now();
const canonical = `${method.toUpperCase()}|${action}|${ts}|${body}`;
const sig = crypto.createHmac('sha256', secret).update(canonical).digest('hex');
const q = new URLSearchParams({ action, ts: String(ts), sig }).toString();
const fullUrl = `${url}?${q}`;

if (method.toUpperCase() === 'GET') {
  console.log(`curl -sSL "${fullUrl}"`);
} else {
  console.log(`curl -sSL -X POST -H "Content-Type: application/json" --data '${body.replace(/'/g, "'\\''")}' "${fullUrl}"`);
}
```

- [ ] **Step 2: Create `scripts/smoke.sh`**

```bash
#!/usr/bin/env bash
# Smoke-test every M4 route against a deployed Apps Script Web App.
# Requires: BACKEND_URL, HMAC_SECRET in env.
# Run: bash scripts/smoke.sh

set -euo pipefail

: "${BACKEND_URL:?set BACKEND_URL to your Web App /exec URL}"
: "${HMAC_SECRET:?set HMAC_SECRET to the value from ScriptProperties}"

sign() {
  node scripts/sign.mjs "$@"
}

section() { printf '\n===== %s =====\n' "$1"; }

section "GET ?action=config"
eval "$(sign GET config)" | tee /tmp/f2-config.json
echo

section "GET ?action=spec-hash"
eval "$(sign GET spec-hash)"
echo

section "GET ?action=facilities"
eval "$(sign GET facilities)" | head -c 300
echo

section "POST ?action=audit"
BODY='{"event_type":"smoke_test","occurred_at_client":'"$(node -e 'console.log(Date.now())')"',"app_version":"smoke","payload":{"script":"smoke.sh"}}'
eval "$(sign POST audit "$BODY")"
echo

section "POST ?action=submit (idempotent — run twice)"
CID="smoke-$(node -e 'console.log(Date.now())')"
BODY='{"client_submission_id":"'"$CID"'","hcw_id":"smoke-hcw","facility_id":"smoke-fac","spec_version":"2026-04-17-m1","app_version":"smoke","submitted_at_client":'"$(node -e 'console.log(Date.now())')"',"device_fingerprint":"smoke-node","values":{"Q2":"Regular","Q3":"Female","Q4":30,"Q5":"Nurse","Q7":"No","Q10":5,"Q11":8}}'
eval "$(sign POST submit "$BODY")"
echo
echo "-- replay same submission (expect duplicate) --"
eval "$(sign POST submit "$BODY")"
echo

section "POST ?action=batch-submit"
BCID1="smoke-b1-$(node -e 'console.log(Date.now())')"
BCID2="smoke-b2-$(node -e 'console.log(Date.now())')"
BATCH='{"responses":[{"client_submission_id":"'"$BCID1"'","hcw_id":"smoke-hcw","facility_id":"smoke-fac","spec_version":"2026-04-17-m1","submitted_at_client":'"$(node -e 'console.log(Date.now())')"',"values":{"Q2":"Casual"}},{"client_submission_id":"'"$BCID2"'","hcw_id":"smoke-hcw","facility_id":"smoke-fac","spec_version":"2026-04-17-m1","submitted_at_client":'"$(node -e 'console.log(Date.now())')"',"values":{"Q2":"Regular"}}]}'
eval "$(sign POST batch-submit "$BATCH")"
echo

echo
echo "Smoke tests complete. Open the spreadsheet in Sheets to verify rows landed."
```

- [ ] **Step 3: Replace `README.md`**

```markdown
# F2 PWA Backend — Apps Script

Apps Script Web App that serves the PWA frontend (see `../app/`). Six routes, HMAC-signed, idempotent.

## One-time deploy

1. `npm install && npm run build` — emits `dist/Code.gs` and `dist/appsscript.json`.
2. Go to https://script.google.com while signed in as `aspsi.doh.uhc.survey2.data@gmail.com`.
3. New project → name it `F2-PWA-Backend`.
4. Paste `dist/Code.gs` into `Code.gs` (replace default contents).
5. Editor → Project Settings → "Show appsscript.json" → paste `dist/appsscript.json`.
6. Run `setupBackend()` from the editor. First run authorizes scopes. Output log shows:
   - Created spreadsheet URL (save it).
   - Generated HMAC_SECRET (first 6 chars — retrieve the full value from Project Settings → Script Properties).
7. Deploy → New deployment → Type: Web app → Execute as: Me → Who has access: Anyone → Deploy. Save the `/exec` URL.

## Rotate the HMAC secret

Run `rotateSecret()` from the editor. Update the PWA's build-time `VITE_F2_HMAC_SECRET` and redeploy the frontend.

## Reset the spreadsheet

Delete the ScriptProperty `SPREADSHEET_ID` and re-run `setupBackend()`. The old spreadsheet remains in Drive for audit.

## Smoke tests

```bash
export BACKEND_URL='https://script.google.com/macros/s/.../exec'
export HMAC_SECRET='…full secret from ScriptProperties…'
bash scripts/smoke.sh
```

Verifies every route, including idempotency (submit replay returns `duplicate`) and batching.

## Request format

- Query params: `?action=<route>&ts=<ms-since-epoch>&sig=<hex-sha256>`.
- HMAC input: `${METHOD}|${action}|${ts}|${body}` with lowercase hex output.
- Body: `application/json` for POSTs, empty string for GETs.
- Response envelope: `{ok: true, data: …}` on success, `{ok: false, error: {code, message}}` on failure.

## Routes

| Action | Method | Body | Response |
|---|---|---|---|
| `submit` | POST | `{client_submission_id, hcw_id, facility_id, spec_version, app_version, submitted_at_client, device_fingerprint, values}` | `{submission_id, status: 'accepted' \| 'duplicate', server_timestamp}` |
| `batch-submit` | POST | `{responses: [<submit payload>, …]}` (max 50) | `{results: [{client_submission_id, submission_id, status, error?}, …]}` |
| `facilities` | GET | — | `{facilities: [<row>, …]}` |
| `config` | GET | — | `{current_spec_version, min_accepted_spec_version, kill_switch, broadcast_message, spec_hash}` |
| `spec-hash` | GET | — | `{spec_hash, current_spec_version}` |
| `audit` | POST | `{event_type, occurred_at_client, hcw_id, facility_id, app_version, payload}` | `{audit_id}` |

## Error codes

| Code | Meaning |
|---|---|
| `E_ACTION_UNKNOWN` | `action` parameter missing or unknown |
| `E_METHOD_UNKNOWN` | Route called with wrong HTTP verb |
| `E_TS_INVALID` | `ts` is not an integer |
| `E_TS_SKEW` | `ts` outside ±5 min window |
| `E_SIG_INVALID` | HMAC mismatch |
| `E_KILL_SWITCH` | Config `kill_switch = true` |
| `E_PAYLOAD_INVALID` | Request body fails shape check |
| `E_SPEC_TOO_OLD` | `spec_version` < `min_accepted_spec_version` |
| `E_VALIDATION` | Payload shape OK but content invalid — also written to F2_DLQ |
| `E_BATCH_TOO_LARGE` | `responses.length > 50` |
| `E_INTERNAL` | Unexpected server error (check Stackdriver) |

## Deferred to later milestones

- **Flat per-item columns in `F2_Responses`.** M4 stores all form values as `values_json` (single column). Flattening happens in M10 when the admin dashboard needs per-column filters.
- **Rate limiting.** Spec §4.3 mentions IP + per-hcw_id limits. Deferred until observed abuse, because HMAC + static API key already block random spam.
- **Sync orchestrator.** PWA-side integration of these routes is M5.
- **Admin dashboard.** HtmlService UI to browse responses + DLQ is M10.
```

- [ ] **Step 4: Run the final full verification pass**

Run: `cd deliverables/F2/PWA/backend && npm test && npm run build`
Expected: all Vitest suites green (util + auth + router + idempotency + handlers + smoke), build writes `dist/Code.gs`.

- [ ] **Step 5: Live deploy + smoke (human-executed, optional)**

Instruct the operator to follow README §"One-time deploy". Once the `/exec` URL is live, export `BACKEND_URL` + `HMAC_SECRET` and run `bash scripts/smoke.sh`. Expected: every section prints `{"ok":true, …}` (or `E_SPEC_TOO_OLD` / `duplicate` as designed).

- [ ] **Step 6: Replace `../app/NEXT.md`**

```markdown
# Next step (future-Carl)

**Last milestone shipped:** M4 — Apps Script backend (6 HMAC-signed routes — submit, batch-submit, facilities, config, spec-hash, audit — backed by a 5-tab Google Sheet, curl-testable via `scripts/smoke.sh`).

**Next milestone:** M5 — Sync orchestrator end-to-end ⭐. 15–20h per spec §11.1. **This is the first demo-able vertical slice.**

**Before starting M5:**

1. Re-invoke `superpowers:writing-plans` against `../2026-04-17-design-spec.md` §7 (Offline / Sync Strategy) — specifically 7.1 SW caching, 7.2 IndexedDB schema, 7.3 sync orchestrator state machine, 7.7 spec-version handling.
2. Target: PWA drains `pending_sync` submissions to the M4 `batch-submit` endpoint, honors the status state machine (`pending_sync → syncing → synced | rejected | retry_scheduled`), respects `E_SPEC_TOO_OLD` by forcing an update, and surfaces a "Sync now" button + pending-count UI.
3. Expected deliverable: `../YYYY-MM-DD-implementation-plan-M5-sync-orchestrator.md`.
4. Ships per spec §11.1: **First vertical slice. Demo-able.** Promotion checkpoint to Dr Myra.

**M4 technical debt to address in later milestones:**

- Form values stored as `values_json` in a single column. Flatten to per-item columns in M10 (admin dashboard) once column list stabilizes post-M6.
- No rate limiting — HMAC + static key already block random spam; revisit if abuse observed.
- No live key rotation orchestration — operator runs `rotateSecret()` then redeploys frontend. Tolerable at MVP scale.

**When picking this back up after a gap:**

- `cd deliverables/F2/PWA/app && npm install && npm run test && npm run typecheck && npm run build` — confirm M3 still green.
- `cd deliverables/F2/PWA/backend && npm install && npm test && npm run build` — confirm M4 still green.
- Export `BACKEND_URL` + `HMAC_SECRET`, run `bash scripts/smoke.sh` — confirm deployed backend still answers.
- Open `../2026-04-17-design-spec.md` §7 to re-orient.
```

- [ ] **Step 7: Commit**

*(All M4 work is complete. Pause for manual commit of the final task, then M4 is shipped.)*

---

## Self-Review Notes

- **Spec §4.1 (5 Sheet tabs):** `F2_Responses` ✓ (Task 5 schema, Task 10 setup), `F2_Audit` ✓, `F2_Config` ✓, `FacilityMasterList` ✓, `F2_DLQ` ✓ (populated by `handleSubmit` on validation failure). Metadata columns present in `F2_RESPONSES_COLUMNS`.
- **Spec §4.2 (6 endpoints):** `submit` (Task 6), `batch-submit` (Task 7), `facilities` + `config` + `spec-hash` + `audit` (Task 8). All dispatched by `Router.dispatch` (Task 9). Wrong-method requests return `E_METHOD_UNKNOWN`.
- **Spec §4.3 (HMAC):** Task 3 verifies signature + timestamp skew. Apps Script side uses `Utilities.computeHmacSha256Signature`. Static key intentionally out of scope for M4 — HMAC alone suffices since the PWA embeds the same shared secret at build time. (Static key in spec §4.3 is the public API key, which is effectively the URL obscurity at MVP.)
- **Spec §4.4 (data flow):** round-trip covered — verify HMAC → idempotency check → validate → append or DLQ → return result. Idempotency via `findExistingSubmission` (Task 4).
- **Spec §4.5 (idempotency/dedup/versioning):** client UUIDs (Task 6 uses `client_submission_id`), spec-version gating (`E_SPEC_TOO_OLD` in `handleSubmit`), last-submit-wins explicitly deferred (still an open item flagged in README). "Superseded" marking is a future concern.
- **Spec §4.6 (performance):** `LockService` mutex wraps POST routes (Code.js). Batch cap of 50 enforced. No URL fetches.
- **Spec §4.7 (admin dashboard):** explicitly deferred to M10 (noted in README "Deferred" section).
- **Spec §4.8 (failure modes):** kill-switch honored (Task 9), DLQ on validation failure (Task 6), spec-version mismatch returns 409-equivalent envelope.
- **Spec §11.1 M4 row coverage:** "Apps Script Web App, request signing" ✓, "Backend live, curl-testable" ✓ (Task 12 smoke).
- **Placeholder scan:** No TBD/TODO/Similar-to-Task-N. All code blocks complete. Commands specified with expected output.
- **Type consistency:** Handler method names match everywhere — `handleSubmit`, `handleBatchSubmit`, `handleFacilities`, `handleConfig`, `handleSpecHash`, `handleAudit`. Dispatch lookup in `Router.js` uses the same keys. Sheet column constants `F2_RESPONSES_COLUMNS` / `F2_AUDIT_COLUMNS` / `F2_CONFIG_COLUMNS` / `FACILITY_MASTER_LIST_COLUMNS` / `F2_DLQ_COLUMNS` defined in `Schema.js` (Task 5) and referenced verbatim in `Code.js` + `Setup.js` (Task 10).
- **Tab constants:** `TABS.RESPONSES` etc. used in Setup.js only; Code.js uses string literals (`'F2_Responses'`) to keep glue readable. Consistent at read time.

---

## Execution Handoff

Plan complete and saved to `deliverables/F2/PWA/2026-04-18-implementation-plan-M4-apps-script-backend.md`. Two execution options:

**1. Subagent-Driven (recommended by default)** — dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — execute tasks in this session using `superpowers:executing-plans`, batch execution with checkpoints.

Which approach?
