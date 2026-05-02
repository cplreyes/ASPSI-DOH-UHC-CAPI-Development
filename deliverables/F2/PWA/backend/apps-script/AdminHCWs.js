/**
 * F2 Admin Portal — F2_HCWs sheet writes.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 2.8)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§5, §7.14)
 *
 * F2_HCWs columns (per Migrations.js):
 *   hcw_id, facility_id, facility_name, enrollment_token_jti,
 *   token_issued_at, token_revoked_at, status, created_at
 *
 * Two RPC entry points:
 *   adminHcwsCreate(payload)  — invoked from the new admin portal token
 *                                reissue flow (Sprint 4 Task 4.5) and from
 *                                future admin_users_create-style operations.
 *   backfillHcws()            — operator-initiated migration helper that
 *                                unions distinct (hcw_id, facility_id) pairs
 *                                from F2_Responses + F2_Audit and creates
 *                                F2_HCWs rows for any HCW not already tracked.
 *                                Idempotent — safe to re-run after staging
 *                                or production cutover.
 */

/**
 * Append a row to F2_HCWs. Locks the document so concurrent enrollments
 * cannot append duplicate rows for the same HCW. Duplicate active hcw_id
 * (any row whose status is not 'revoked') returns E_CONFLICT.
 *
 * Required payload fields: hcw_id, facility_id.
 * Optional fields: facility_name, enrollment_token_jti, token_issued_at,
 *                  status (default 'enrolled').
 */
function adminHcwsCreate(payload) {
  if (!payload || typeof payload !== 'object') {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'payload required' } };
  }
  var hcwId = String(payload.hcw_id || '').trim();
  var facilityId = String(payload.facility_id || '').trim();
  if (!hcwId) return { ok: false, error: { code: 'E_VALIDATION', message: 'hcw_id required' } };
  if (!facilityId) return { ok: false, error: { code: 'E_VALIDATION', message: 'facility_id required' } };

  var ss = getF2Spreadsheet();
  var sh = ss.getSheetByName('F2_HCWs');
  if (!sh) throw new Error('F2_HCWs sheet not found — run runAllMigrations() first');

  var lock = LockService.getScriptLock();
  if (!lock.tryLock(30000)) {
    return { ok: false, error: { code: 'E_LOCK_TIMEOUT', message: 'busy, retry' } };
  }
  try {
    var headers = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0];
    var hcwIdIdx = headers.indexOf('hcw_id');
    var statusIdx = headers.indexOf('status');
    var lastRow = sh.getLastRow();
    if (lastRow > 1) {
      var existing = sh.getRange(2, 1, lastRow - 1, headers.length).getValues();
      for (var i = 0; i < existing.length; i++) {
        if (existing[i][hcwIdIdx] === hcwId && existing[i][statusIdx] !== 'revoked') {
          return {
            ok: false,
            error: { code: 'E_CONFLICT', message: 'hcw_id ' + hcwId + ' already enrolled' },
          };
        }
      }
    }

    var nowIso = new Date().toISOString();
    var row = headers.map(function (h) {
      if (h === 'hcw_id') return hcwId;
      if (h === 'facility_id') return facilityId;
      if (h === 'facility_name') return payload.facility_name || '';
      if (h === 'enrollment_token_jti') return payload.enrollment_token_jti || '';
      if (h === 'token_issued_at') return payload.token_issued_at || nowIso;
      if (h === 'token_revoked_at') return '';
      if (h === 'status') return payload.status || 'enrolled';
      if (h === 'created_at') return nowIso;
      return '';
    });
    sh.appendRow(row);
    return { ok: true, data: { hcw_id: hcwId } };
  } finally {
    lock.releaseLock();
  }
}

/**
 * Read RPC for the Data dashboard's HCWs tab and the encoder queue.
 * Filters: facility_id, status, hcw_id (exact), q (substring across row),
 * limit ≤ 500, offset. Newest-first by created_at.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 2.9)
 */
function adminHcwsList(filters) {
  filters = filters || {};
  var f = {
    facility_id: filters.facility_id || null,
    status: filters.status || null,
    hcw_id: filters.hcw_id || null,
    q: filters.q ? String(filters.q).toLowerCase() : null,
    limit: Math.min(Number(filters.limit) || 50, 500),
    offset: Math.max(Number(filters.offset) || 0, 0),
  };

  var ss = getF2Spreadsheet();
  var sh = ss.getSheetByName('F2_HCWs');
  if (!sh) throw new Error('F2_HCWs sheet not found — run runAllMigrations() first');
  var headers = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0];
  var lastRow = sh.getLastRow();
  if (lastRow < 2) {
    return { ok: true, data: { rows: [], total: 0, has_more: false } };
  }
  var data = sh.getRange(2, 1, lastRow - 1, headers.length).getValues();
  var rows = data.map(function (r) {
    var obj = {};
    for (var i = 0; i < headers.length; i++) obj[headers[i]] = r[i];
    return obj;
  });

  var matched = [];
  for (var k = 0; k < rows.length; k++) {
    var row = rows[k];
    if (f.facility_id && row.facility_id !== f.facility_id) continue;
    if (f.status && row.status !== f.status) continue;
    if (f.hcw_id && row.hcw_id !== f.hcw_id) continue;
    if (f.q) {
      var hay = JSON.stringify(row).toLowerCase();
      if (hay.indexOf(f.q) === -1) continue;
    }
    matched.push(row);
  }
  matched.sort(function (a, b) {
    var ka = a.created_at || '';
    var kb = b.created_at || '';
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

/**
 * Compare-and-swap reissue: rotate the F2_HCWs row's enrollment_token_jti
 * from prev_jti to new_jti, but ONLY if the row currently holds prev_jti.
 * If two admins both click Reissue on the same HCW concurrently, the
 * second one sees prev_jti != current and gets E_CAS_FAILED instead of
 * overwriting the first admin's freshly-issued token.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 4.5)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§7.5)
 *
 * Caller (worker) generates new_jti before calling so the new JWT can
 * be minted with that jti after this returns ok. Sets token_revoked_at
 * on the row to flag the prev token (KV-side revocation lands as a
 * follow-up — for now just records the timestamp for audit).
 */
function adminHcwsReissueToken(payload) {
  if (!payload || !payload.hcw_id) {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'hcw_id required' } };
  }
  if (!payload.new_jti) {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'new_jti required' } };
  }
  var hcwId = String(payload.hcw_id).trim();

  var lock = LockService.getScriptLock();
  if (!lock.tryLock(30000)) {
    return { ok: false, error: { code: 'E_LOCK_TIMEOUT', message: 'busy, retry' } };
  }
  try {
    var ss = getF2Spreadsheet();
    var sh = ss.getSheetByName('F2_HCWs');
    if (!sh) throw new Error('F2_HCWs sheet not found — run runAllMigrations() first');
    var headers = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0];
    var hcwIdIdx = headers.indexOf('hcw_id');
    var jtiIdx = headers.indexOf('enrollment_token_jti');
    var issuedIdx = headers.indexOf('token_issued_at');
    var revokedIdx = headers.indexOf('token_revoked_at');
    var statusIdx = headers.indexOf('status');
    if (hcwIdIdx === -1 || jtiIdx === -1) {
      throw new Error('F2_HCWs schema missing required columns');
    }
    var lastRow = sh.getLastRow();
    if (lastRow < 2) {
      return { ok: false, error: { code: 'E_NOT_FOUND', message: 'hcw_id ' + hcwId + ' not found' } };
    }
    var data = sh.getRange(2, 1, lastRow - 1, headers.length).getValues();
    var rowNumber = -1;
    var rowObj = null;
    for (var i = 0; i < data.length; i++) {
      if (data[i][hcwIdIdx] === hcwId) {
        rowNumber = i + 2;
        rowObj = {};
        for (var j = 0; j < headers.length; j++) rowObj[headers[j]] = data[i][j];
        break;
      }
    }
    if (rowNumber === -1) {
      return { ok: false, error: { code: 'E_NOT_FOUND', message: 'hcw_id ' + hcwId + ' not found' } };
    }
    // CAS: prev_jti must match what's currently on the row.
    // If prev_jti is empty/null in the request AND the row has no jti yet
    // (backfilled row, never had a token), accept the first issuance.
    var currentJti = rowObj.enrollment_token_jti || '';
    var expectedPrev = payload.prev_jti || '';
    if (currentJti !== expectedPrev) {
      return {
        ok: false,
        error: {
          code: 'E_CAS_FAILED',
          message: 'token already reissued by another admin; refresh and retry',
        },
      };
    }
    // Update row.
    var nowIso = new Date().toISOString();
    rowObj.enrollment_token_jti = payload.new_jti;
    if (issuedIdx !== -1) rowObj.token_issued_at = nowIso;
    if (revokedIdx !== -1 && currentJti) rowObj.token_revoked_at = nowIso;
    if (statusIdx !== -1) rowObj.status = 'enrolled';
    var rowArr = headers.map(function (h) { return rowObj[h] != null ? rowObj[h] : ''; });
    sh.getRange(rowNumber, 1, 1, headers.length).setValues([rowArr]);
    return {
      ok: true,
      data: {
        hcw_id: hcwId,
        facility_id: rowObj.facility_id,
        new_jti: payload.new_jti,
        old_jti: currentJti,
        token_issued_at: nowIso,
      },
    };
  } finally {
    lock.releaseLock();
  }
}

/**
 * Operator helper. Scans F2_Responses + F2_Audit for distinct hcw_ids,
 * appends F2_HCWs rows for any not already tracked. The earliest server
 * timestamp seen for each HCW is used as created_at. enrollment_token_jti
 * is left blank for backfilled rows — the M10-era token store doesn't key
 * jti by HCW, so legacy submissions can't be linked to a specific token.
 *
 * Returns { added, skipped }. Idempotent.
 */
function backfillHcws() {
  var ss = getF2Spreadsheet();
  var hcwsSh = ss.getSheetByName('F2_HCWs');
  if (!hcwsSh) throw new Error('F2_HCWs sheet not found — run runAllMigrations() first');

  var hcwsHeaders = hcwsSh.getRange(1, 1, 1, hcwsSh.getLastColumn()).getValues()[0];
  var hcwIdIdx = hcwsHeaders.indexOf('hcw_id');

  var existing = {};
  var lastHcwsRow = hcwsSh.getLastRow();
  if (lastHcwsRow > 1) {
    var existingRows = hcwsSh.getRange(2, 1, lastHcwsRow - 1, hcwsHeaders.length).getValues();
    for (var i = 0; i < existingRows.length; i++) {
      existing[String(existingRows[i][hcwIdIdx])] = true;
    }
  }

  var seen = {};

  function ingest(sheetName, timestampCol) {
    var sh = ss.getSheetByName(sheetName);
    if (!sh || sh.getLastRow() < 2) return;
    var hdrs = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0];
    var hidIdx = hdrs.indexOf('hcw_id');
    var fidIdx = hdrs.indexOf('facility_id');
    var atIdx = hdrs.indexOf(timestampCol);
    if (hidIdx === -1 || fidIdx === -1) return;
    var data = sh.getRange(2, 1, sh.getLastRow() - 1, hdrs.length).getValues();
    for (var j = 0; j < data.length; j++) {
      var hid = String(data[j][hidIdx] || '').trim();
      var fid = String(data[j][fidIdx] || '').trim();
      if (!hid) continue;
      var at = atIdx !== -1 ? String(data[j][atIdx] || '') : '';
      var prior = seen[hid];
      if (!prior) {
        seen[hid] = { facility_id: fid, earliest: at };
      } else if (at && (!prior.earliest || at < prior.earliest)) {
        prior.earliest = at;
        // Keep the earliest known facility_id; first seen wins on ties.
        if (!prior.facility_id) prior.facility_id = fid;
      }
    }
  }

  ingest('F2_Responses', 'submitted_at_server');
  ingest('F2_Audit', 'occurred_at_server');

  var lock = LockService.getScriptLock();
  if (!lock.tryLock(30000)) throw new Error('E_LOCK_TIMEOUT');
  try {
    var added = 0;
    var skipped = 0;
    var nowIso = new Date().toISOString();
    for (var hid2 in seen) {
      if (!Object.prototype.hasOwnProperty.call(seen, hid2)) continue;
      if (existing[hid2]) { skipped++; continue; }
      var entry = seen[hid2];
      var row = hcwsHeaders.map(function (h) {
        if (h === 'hcw_id') return hid2;
        if (h === 'facility_id') return entry.facility_id;
        if (h === 'created_at') return entry.earliest || nowIso;
        if (h === 'status') return 'enrolled';
        return '';
      });
      hcwsSh.appendRow(row);
      added++;
    }
    console.log('backfillHcws: added=' + added + ' skipped=' + skipped);
    return { added: added, skipped: skipped };
  } finally {
    lock.releaseLock();
  }
}
