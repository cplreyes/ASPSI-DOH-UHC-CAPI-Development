/**
 * F2 Admin Portal — aggregation reports for the Report dashboard.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Tasks 2.10, 2.12)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§7.7, §7.8)
 *
 * Pure logic: pivots F2_Responses by geography level (region / province /
 * facility) for the Sync Report; emits lat/lng marker list for the Map
 * Report. PSGC code extraction relies on the convention that facility_id
 * embeds region (2 chars), province (4 chars), city/mun (6 chars) at the
 * head — same scheme used by the Facility Master List.
 *
 * `_expectedFor` is a stub returning null until F2_SampleFrame ships
 * (Sprint 4-ish followup); the % complete column then becomes meaningful.
 */

var REPORT_SCAN_CAP = 50000;

function _extractGeoKey(facilityId, level) {
  if (!facilityId) return '';
  var s = String(facilityId);
  if (level === 'region') return s.slice(0, 2);
  if (level === 'province') return s.slice(0, 4);
  if (level === 'facility') return s;
  // Default region.
  return s.slice(0, 2);
}

function _expectedFor(_key, _level) {
  // Stub. F2_SampleFrame lookup lands with the sample-frame ingest later.
  return null;
}

function _normalizeReportFilters(filters) {
  filters = filters || {};
  return {
    level: filters.level || 'region',
    from: filters.from || null,
    to: filters.to || null,
  };
}

function adminSyncReport(filters, ctx) {
  var f = _normalizeReportFilters(filters);
  var all = ctx.responses.readAll(REPORT_SCAN_CAP, 0);
  var byKey = {};
  for (var i = 0; i < all.length; i++) {
    var row = all[i];
    if (f.from && row.submitted_at_server && row.submitted_at_server < f.from) continue;
    if (f.to && row.submitted_at_server && row.submitted_at_server > f.to) continue;
    var key = _extractGeoKey(row.facility_id, f.level);
    if (!key) continue;
    if (!byKey[key]) {
      byKey[key] = {
        key: key,
        submitted: 0,
        last_submitted_at: '',
        expected: _expectedFor(key, f.level),
      };
    }
    byKey[key].submitted++;
    var ts = row.submitted_at_server || '';
    if (ts > byKey[key].last_submitted_at) byKey[key].last_submitted_at = ts;
  }

  var pivot = [];
  for (var k in byKey) {
    if (Object.prototype.hasOwnProperty.call(byKey, k)) {
      var entry = byKey[k];
      entry.percent_complete = entry.expected != null && entry.expected > 0
        ? Math.round((entry.submitted / entry.expected) * 100)
        : null;
      pivot.push(entry);
    }
  }
  // Sort key ascending (stable region order).
  pivot.sort(function (a, b) {
    if (a.key < b.key) return -1;
    if (a.key > b.key) return 1;
    return 0;
  });

  var totals = {
    submitted: pivot.reduce(function (n, e) { return n + e.submitted; }, 0),
    expected: null,
    keys: pivot.length,
  };

  return { ok: true, data: { level: f.level, pivot: pivot, totals: totals } };
}

function adminMapReport(filters, ctx) {
  filters = filters || {};
  var f = {
    from: filters.from || null,
    to: filters.to || null,
    region_id: filters.region_id || null,
    province_id: filters.province_id || null,
  };
  var all = ctx.responses.readAll(REPORT_SCAN_CAP, 0);
  var markers = [];
  var noGps = 0;
  for (var i = 0; i < all.length; i++) {
    var row = all[i];
    if (f.from && row.submitted_at_server && row.submitted_at_server < f.from) continue;
    if (f.to && row.submitted_at_server && row.submitted_at_server > f.to) continue;
    if (f.region_id && row.facility_id && String(row.facility_id).slice(0, 2) !== f.region_id) continue;
    if (f.province_id && row.facility_id && String(row.facility_id).slice(0, 4) !== f.province_id) continue;

    var lat = row.submission_lat;
    var lng = row.submission_lng;
    var hasGps = typeof lat === 'number' && typeof lng === 'number' && isFinite(lat) && isFinite(lng);
    if (!hasGps) {
      noGps++;
      continue;
    }
    markers.push({
      submission_id: row.submission_id,
      hcw_id: row.hcw_id,
      facility_id: row.facility_id,
      lat: lat,
      lng: lng,
      submitted_at: row.submitted_at_server,
    });
  }
  return { ok: true, data: { markers: markers, no_gps_count: noGps } };
}

if (typeof module !== 'undefined') {
  module.exports = {
    adminSyncReport: adminSyncReport,
    adminMapReport: adminMapReport,
    _extractGeoKey: _extractGeoKey,
  };
}
