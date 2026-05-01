/**
 * F2 Admin Portal — read RPCs for the Data dashboard.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 2.1)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§7.1, §7.2)
 *
 * Pure logic: takes filters + ctx (sheet readers), filters in-memory,
 * sorts newest-first, paginates. The AS side has no DB so we scan the
 * full sheet on every request — fine for the expected ~30K rows over
 * the project lifetime; if scale grows we revisit with caching.
 *
 * SCAN_CAP = 50,000 is a defensive ceiling; sheets larger than that
 * truncate from the front (oldest dropped) — admin notices via the
 * `total` exceeding what they can paginate to.
 */

var SCAN_CAP = 50000;
var DEFAULT_LIMIT = 50;
var MAX_LIMIT = 500;

function _normalizeFilters(filters) {
  filters = filters || {};
  return {
    from: filters.from || null,                // ISO 8601 string
    to: filters.to || null,                    // ISO 8601 string
    facility_id: filters.facility_id || null,
    status: filters.status || null,
    source_path: filters.source_path || null,
    q: filters.q ? String(filters.q).toLowerCase() : null,
    limit: Math.min(Number(filters.limit) || DEFAULT_LIMIT, MAX_LIMIT),
    offset: Math.max(Number(filters.offset) || 0, 0),
  };
}

function _matchesFilters(row, f) {
  if (f.from && row.submitted_at_server && row.submitted_at_server < f.from) return false;
  if (f.to && row.submitted_at_server && row.submitted_at_server > f.to) return false;
  if (f.facility_id && row.facility_id !== f.facility_id) return false;
  if (f.status && row.status !== f.status) return false;
  if (f.source_path && row.source_path !== f.source_path) return false;
  if (f.q) {
    // Light-weight full-text: stringified row + lowercased compare.
    // Sufficient for hcw_id / submission_id / values_json substring search.
    var hay = JSON.stringify(row).toLowerCase();
    if (hay.indexOf(f.q) === -1) return false;
  }
  return true;
}

function _sortNewestFirst(rows) {
  rows.sort(function (a, b) {
    var ka = a.submitted_at_server || '';
    var kb = b.submitted_at_server || '';
    if (ka < kb) return 1;
    if (ka > kb) return -1;
    return 0;
  });
  return rows;
}

/**
 * Filter + paginate F2_Responses.
 * Returns `{ ok: true, data: { rows, total, has_more } }`.
 */
function adminReadResponses(filters, ctx) {
  var f = _normalizeFilters(filters);
  var all = ctx.responses.readAll(SCAN_CAP, 0);
  var matched = [];
  for (var i = 0; i < all.length; i++) {
    if (_matchesFilters(all[i], f)) matched.push(all[i]);
  }
  _sortNewestFirst(matched);
  var page = matched.slice(f.offset, f.offset + f.limit);
  return {
    ok: true,
    data: {
      rows: page,
      total: matched.length,
      has_more: f.offset + page.length < matched.length,
    },
  };
}

/**
 * Same filters, returns just the count. Used by the dashboard header
 * badge so the UI doesn't have to round-trip a 500-row payload to
 * surface "127 responses today".
 */
function adminCountResponses(filters, ctx) {
  var f = _normalizeFilters(filters);
  var all = ctx.responses.readAll(SCAN_CAP, 0);
  var n = 0;
  for (var i = 0; i < all.length; i++) {
    if (_matchesFilters(all[i], f)) n++;
  }
  return { ok: true, data: { total: n } };
}

/**
 * Lookup a single submission by its server-issued submission_id.
 * Returns E_NOT_FOUND if missing — the worker passes this through
 * as HTTP 404 (other AS errors map to 502).
 */
function adminReadResponseById(payload, ctx) {
  var id = payload && payload.id ? String(payload.id) : '';
  if (!id) {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'id required' } };
  }
  var all = ctx.responses.readAll(SCAN_CAP, 0);
  for (var i = 0; i < all.length; i++) {
    if (all[i].submission_id === id) {
      return { ok: true, data: all[i] };
    }
  }
  return { ok: false, error: { code: 'E_NOT_FOUND', message: 'submission ' + id + ' not found' } };
}

// ----- Audit + DLQ readers (Task 2.3) -------------------------------------

function _matchesAuditFilters(row, f) {
  if (f.from && row.occurred_at_server && row.occurred_at_server < f.from) return false;
  if (f.to && row.occurred_at_server && row.occurred_at_server > f.to) return false;
  if (f.event_type && row.event_type !== f.event_type) return false;
  if (f.hcw_id && row.hcw_id !== f.hcw_id) return false;
  if (f.actor_username && row.actor_username !== f.actor_username) return false;
  if (f.q) {
    var hay = JSON.stringify(row).toLowerCase();
    if (hay.indexOf(f.q) === -1) return false;
  }
  return true;
}

function _normalizeAuditFilters(filters) {
  filters = filters || {};
  return {
    from: filters.from || null,
    to: filters.to || null,
    event_type: filters.event_type || null,
    hcw_id: filters.hcw_id || null,
    actor_username: filters.actor_username || null,
    q: filters.q ? String(filters.q).toLowerCase() : null,
    limit: Math.min(Number(filters.limit) || DEFAULT_LIMIT, MAX_LIMIT),
    offset: Math.max(Number(filters.offset) || 0, 0),
  };
}

function _sortAuditNewestFirst(rows) {
  rows.sort(function (a, b) {
    var ka = a.occurred_at_server || '';
    var kb = b.occurred_at_server || '';
    if (ka < kb) return 1;
    if (ka > kb) return -1;
    return 0;
  });
  return rows;
}

function adminReadAudit(filters, ctx) {
  var f = _normalizeAuditFilters(filters);
  var all = ctx.audit.readAll(SCAN_CAP, 0);
  var matched = [];
  for (var i = 0; i < all.length; i++) {
    if (_matchesAuditFilters(all[i], f)) matched.push(all[i]);
  }
  _sortAuditNewestFirst(matched);
  var page = matched.slice(f.offset, f.offset + f.limit);
  return {
    ok: true,
    data: { rows: page, total: matched.length, has_more: f.offset + page.length < matched.length },
  };
}

function _matchesDlqFilters(row, f) {
  if (f.from && row.received_at_server && row.received_at_server < f.from) return false;
  if (f.to && row.received_at_server && row.received_at_server > f.to) return false;
  if (f.q) {
    var hay = JSON.stringify(row).toLowerCase();
    if (hay.indexOf(f.q) === -1) return false;
  }
  return true;
}

function _normalizeDlqFilters(filters) {
  filters = filters || {};
  return {
    from: filters.from || null,
    to: filters.to || null,
    q: filters.q ? String(filters.q).toLowerCase() : null,
    limit: Math.min(Number(filters.limit) || DEFAULT_LIMIT, MAX_LIMIT),
    offset: Math.max(Number(filters.offset) || 0, 0),
  };
}

function adminReadDlq(filters, ctx) {
  var f = _normalizeDlqFilters(filters);
  var all = ctx.dlq.readAll
    ? ctx.dlq.readAll(SCAN_CAP, 0)
    // Code.js's _buildDlqCtx exposed readAll() with no args; tolerate either shape.
    : ctx.dlq.readAll();
  var matched = [];
  for (var i = 0; i < all.length; i++) {
    if (_matchesDlqFilters(all[i], f)) matched.push(all[i]);
  }
  // DLQ sorted newest-first by received_at_server.
  matched.sort(function (a, b) {
    var ka = a.received_at_server || '';
    var kb = b.received_at_server || '';
    if (ka < kb) return 1;
    if (ka > kb) return -1;
    return 0;
  });
  var page = matched.slice(f.offset, f.offset + f.limit);
  return {
    ok: true,
    data: { rows: page, total: matched.length, has_more: f.offset + page.length < matched.length },
  };
}

// ----- Versioning aggregation (Task 3.6) ----------------------------------

/**
 * Aggregate F2_Responses by spec_version for the Apps dashboard's
 * Versioning panel. The bundle SHA + PWA version come from the worker
 * (build-time env), not from AS — AS knows about spec_version (the
 * questionnaire revision) and submission counts at each.
 *
 * Returns `{ revisions: [{ spec_version, count, last_seen_at }], total }`
 * sorted with the most recent spec_version first (string compare on
 * ISO-prefixed spec versions like 2026-04-17-m1 sorts correctly).
 */
function adminFormRevisions(_filters, ctx) {
  var all = ctx.responses.readAll(SCAN_CAP, 0);
  var byVersion = {};
  for (var i = 0; i < all.length; i++) {
    var row = all[i];
    var v = row.spec_version || '(unknown)';
    if (!byVersion[v]) {
      byVersion[v] = { spec_version: v, count: 0, last_seen_at: '' };
    }
    byVersion[v].count++;
    var ts = row.submitted_at_server || '';
    if (ts > byVersion[v].last_seen_at) byVersion[v].last_seen_at = ts;
  }
  var revisions = [];
  for (var k in byVersion) {
    if (Object.prototype.hasOwnProperty.call(byVersion, k)) revisions.push(byVersion[k]);
  }
  revisions.sort(function (a, b) {
    if (a.spec_version < b.spec_version) return 1;
    if (a.spec_version > b.spec_version) return -1;
    return 0;
  });
  return {
    ok: true,
    data: {
      revisions: revisions,
      total: revisions.reduce(function (n, r) { return n + r.count; }, 0),
    },
  };
}

if (typeof module !== 'undefined') {
  module.exports = {
    adminReadResponses: adminReadResponses,
    adminCountResponses: adminCountResponses,
    adminReadResponseById: adminReadResponseById,
    adminReadAudit: adminReadAudit,
    adminReadDlq: adminReadDlq,
    adminFormRevisions: adminFormRevisions,
  };
}
