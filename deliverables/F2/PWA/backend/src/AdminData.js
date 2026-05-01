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

if (typeof module !== 'undefined') {
  module.exports = {
    adminReadResponses: adminReadResponses,
    adminCountResponses: adminCountResponses,
    adminReadResponseById: adminReadResponseById,
  };
}
