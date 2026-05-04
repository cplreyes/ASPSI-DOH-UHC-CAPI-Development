/**
 * F2 Admin Portal — realistic demo-data seed.
 *
 * Run from the AS Editor when you want the staging dashboards to look like
 * real ASPSI fieldwork-in-progress instead of empty test scaffolding. Used
 * for Monday ASPSI demos and any other "show what this looks like with
 * real data" moment. Idempotent — running twice doesn't duplicate. Use
 * `purgeDemoData()` to clean up.
 *
 * Targets STAGING ONLY. Production seed is meaningless (would pollute live
 * data). The script silently no-ops if it detects the production
 * spreadsheet ID in ScriptProperties — guard rail. To override (for
 * legitimate prod fixture work), set ScriptProperty SEED_DEMO_ALLOW_PROD=1
 * first. Don't.
 *
 * Demo data shape:
 *   - 3 facilities across 3 PH regions (NCR + IV-A + III) — Rural Health
 *     Unit, District Hospital, Lying-In Clinic — covers the operational
 *     variety ASPSI sees in the field.
 *   - 12 HCWs across the 3 facilities, varied roles (Physician, Nurse,
 *     Midwife, Pharmacist, Barangay Health Worker, Laboratory tech,
 *     Nursing asst, Dentist, Health promotion officer).
 *   - 8 submitted self-admin responses (Section A complete + sample of B).
 *   - 1 paper-encoded response (encoder-flow demo).
 *   - 2 enrolled-not-yet-submitted (in-progress demo).
 *   - 1 DLQ entry (operational hiccup — schema_version mismatch).
 *   - 1 token-reissue audit event (operational realism).
 *   - 2 file uploads metadata (Files panel non-empty).
 *
 * Each row tagged with prefix `DEMO-` (for HCW IDs / facility IDs / file
 * IDs) so cleanup is `WHERE id LIKE 'DEMO-%'`. Admin user is whatever
 * carl_admin currently is — the seed doesn't touch F2_Users.
 *
 * Non-goals:
 *   - Filling all 80+ questions in F2 — partial completion is more
 *     realistic anyway and keeps the values_json compact.
 *   - Generating PWA-flow audit events (those land naturally during demo
 *     prep when Carl walks through the actual enrollment flow).
 *   - Touching F2_Users, F2_Roles, F2_Config — already seeded by AP0.
 */

/** ============================================================
 * PUBLIC ENTRY POINTS
 * ============================================================ */

/**
 * Seed staging with the full demo dataset. Idempotent (re-running is a no-op
 * for any row that already exists, by ID lookup). Returns a summary with
 * counts per sheet.
 */
function seedDemoData() {
  _assertStagingOnly();
  var ss = getF2Spreadsheet();
  var summary = {
    facilities: _seedFacilities(ss),
    hcws: _seedHCWs(ss),
    responses: _seedResponses(ss),
    dlq: _seedDLQ(ss),
    files: _seedFiles(ss),
    audit: _seedAuditEvents(ss),
  };
  console.log('seedDemoData complete: ' + JSON.stringify(summary));
  return summary;
}

/**
 * Remove every row tagged DEMO-* across F2_HCWs, F2_Responses, F2_DLQ,
 * F2_FileMeta, F2_Audit, and FacilityMasterList (rows where facility_id
 * starts with DEMO-FAC-). Safe to run anytime; production is also
 * staging-guarded the same way as seedDemoData.
 */
function purgeDemoData() {
  _assertStagingOnly();
  var ss = getF2Spreadsheet();
  var summary = {
    facilities: _purgePrefix(ss, 'FacilityMasterList', 'facility_id', 'DEMO-FAC-'),
    hcws: _purgePrefix(ss, 'F2_HCWs', 'hcw_id', 'DEMO-HCW-'),
    responses: _purgePrefix(ss, 'F2_Responses', 'hcw_id', 'DEMO-HCW-'),
    dlq: _purgePrefix(ss, 'F2_DLQ', 'client_submission_id', 'DEMO-SUB-'),
    files: _purgePrefix(ss, 'F2_FileMeta', 'file_id', 'DEMO-FILE-'),
    auditByHcw: _purgePrefix(ss, 'F2_Audit', 'hcw_id', 'DEMO-HCW-'),
    auditByResource: _purgePrefix(ss, 'F2_Audit', 'event_resource', 'DEMO-HCW-'),
  };
  console.log('purgeDemoData complete: ' + JSON.stringify(summary));
  return summary;
}

/** ============================================================
 * GUARD RAIL
 * ============================================================ */

function _assertStagingOnly() {
  // Staging spreadsheet IDs differ from production by construction (AP0
  // creates a fresh sheet). The staging sheet has the human-readable name
  // "F2 PWA Backend — Staging" per the AP0 runbook. We can't read the
  // sheet name without opening the spreadsheet, but we CAN check a
  // ScriptProperty marker — staging AS sets PROP_ENV=staging during AP0.
  var props = PropertiesService.getScriptProperties();
  var allow = props.getProperty('SEED_DEMO_ALLOW_PROD');
  if (allow === '1') return;
  var env = props.getProperty('PROP_ENV');
  if (env === 'staging') return;
  // Fallback: check sheet name. If the active sheet's name doesn't include
  // "Staging", refuse to seed.
  try {
    var ss = getF2Spreadsheet();
    var name = ss.getName() || '';
    if (name.toLowerCase().indexOf('staging') === -1) {
      throw new Error(
        'Refusing to seed demo data: this does not look like a staging ' +
        'sheet (name="' + name + '", PROP_ENV unset). To override for ' +
        'legitimate fixture work on a non-staging sheet, set ScriptProperty ' +
        'SEED_DEMO_ALLOW_PROD=1 first. Otherwise set PROP_ENV=staging on ' +
        'the staging AS project.'
      );
    }
  } catch (e) {
    if (e.message && e.message.indexOf('Refusing') === 0) throw e;
    // Spreadsheet not reachable (rare) — don't accidentally seed prod.
    throw new Error('Refusing to seed demo data: cannot verify staging environment.');
  }
}

/** ============================================================
 * FIXTURE DATA — kept inline for readability + version control
 * ============================================================ */

function _demoFacilities() {
  return [
    {
      facility_id: 'DEMO-FAC-RHU-QC-1',
      facility_name: 'Quezon City Health Center 1 (Bagumbayan)',
      facility_type: 'Rural Health Unit',
      region: 'NCR',
      province: 'Metro Manila',
      city_mun: 'Quezon City',
      barangay: 'Bagumbayan',
      lat: 14.6760,
      lng: 121.0437,
    },
    {
      facility_id: 'DEMO-FAC-DH-INFANTA',
      facility_name: 'Infanta District Hospital',
      facility_type: 'District Hospital',
      region: 'Region IV-A (CALABARZON)',
      province: 'Quezon',
      city_mun: 'Infanta',
      barangay: 'Poblacion-1',
      lat: 14.7472,
      lng: 121.6499,
    },
    {
      facility_id: 'DEMO-FAC-LYING-IN-BAL',
      facility_name: 'Sta. Maria Lying-In Clinic',
      facility_type: 'Lying-In Clinic',
      region: 'Region III (Central Luzon)',
      province: 'Bataan',
      city_mun: 'Balanga',
      barangay: 'San Jose',
      lat: 14.6760,
      lng: 120.5384,
    },
  ];
}

function _demoHCWs() {
  // Filipino-style placeholder names. Clearly fictional + clearly Philippine
  // context. ASPSI will recognize these as demo data, not real PII.
  // Each entry pre-computes facility_name + lat/lng from the facility lookup
  // for response/audit row population without re-querying.
  return [
    // Quezon City RHU 1 — 5 HCWs
    { hcw_id: 'DEMO-HCW-001', facility_id: 'DEMO-FAC-RHU-QC-1', last: 'Cruz',     first: 'Juan',    role: 'Physician/Doctor',           sex: 'Male',   age: 42, status: 'submitted' },
    { hcw_id: 'DEMO-HCW-002', facility_id: 'DEMO-FAC-RHU-QC-1', last: 'Santos',   first: 'Maria',   role: 'Nurse',                      sex: 'Female', age: 35, status: 'submitted' },
    { hcw_id: 'DEMO-HCW-003', facility_id: 'DEMO-FAC-RHU-QC-1', last: 'Reyes',    first: 'Ana',     role: 'Midwife',                    sex: 'Female', age: 38, status: 'submitted' },
    { hcw_id: 'DEMO-HCW-004', facility_id: 'DEMO-FAC-RHU-QC-1', last: 'Garcia',   first: 'Roberto', role: 'Pharmacist/Dispenser',       sex: 'Male',   age: 29, status: 'enrolled' },
    { hcw_id: 'DEMO-HCW-005', facility_id: 'DEMO-FAC-RHU-QC-1', last: 'Bautista', first: 'Lorna',   role: 'Barangay Health Worker',     sex: 'Female', age: 51, status: 'submitted' },
    // Infanta District Hospital — 4 HCWs
    { hcw_id: 'DEMO-HCW-006', facility_id: 'DEMO-FAC-DH-INFANTA', last: 'Mendoza',     first: 'Liza',     role: 'Physician/Doctor',           sex: 'Female', age: 47, status: 'submitted' },
    { hcw_id: 'DEMO-HCW-007', facility_id: 'DEMO-FAC-DH-INFANTA', last: 'Aguilar',     first: 'Marlon',   role: 'Nurse',                      sex: 'Male',   age: 31, status: 'submitted' },
    { hcw_id: 'DEMO-HCW-008', facility_id: 'DEMO-FAC-DH-INFANTA', last: 'del Rosario', first: 'Cristina', role: 'Laboratory technician',      sex: 'Female', age: 44, status: 'paper_encoded' },
    { hcw_id: 'DEMO-HCW-009', facility_id: 'DEMO-FAC-DH-INFANTA', last: 'Santiago',    first: 'Patrick',  role: 'Nursing assistant',          sex: 'Male',   age: 26, status: 'enrolled' },
    // Sta. Maria Lying-In Clinic — 3 HCWs
    { hcw_id: 'DEMO-HCW-010', facility_id: 'DEMO-FAC-LYING-IN-BAL', last: 'Tan',        first: 'Beverly', role: 'Dentist',                       sex: 'Female', age: 39, status: 'submitted' },
    { hcw_id: 'DEMO-HCW-011', facility_id: 'DEMO-FAC-LYING-IN-BAL', last: 'Lim',        first: 'Sofia',   role: 'Midwife',                       sex: 'Female', age: 33, status: 'submitted' },
    { hcw_id: 'DEMO-HCW-012', facility_id: 'DEMO-FAC-LYING-IN-BAL', last: 'Velasquez',  first: 'Ramon',   role: 'Health promotion officer',      sex: 'Male',   age: 45, status: 'dlq' },
  ];
}

/**
 * Build a realistic Section A + sample B values_json payload for a HCW.
 * Not all 80+ questions filled — partial completion is the realistic
 * field shape anyway, and keeps the demo data compact.
 */
function _demoValuesJson(hcw) {
  var values = {
    Q1_1: hcw.last,
    Q1_2: hcw.first,
    Q1_3: '',
    Q2: 'Regular',
    Q3: hcw.sex,
    Q4: hcw.age,
    Q5: hcw.role,
    Q7: 'No',
    Q9_1: Math.max(1, Math.floor(hcw.age / 8)), // years at facility, plausible
    Q9_2: Math.floor(Math.random() * 12),
    Q10: 5,
    Q11: 8,
    Q12: 'Yes', // heard about UHC
    Q13: 'Yes, this was implemented as a direct result of the UHC Act',
    Q14: 'New blood pressure monitors and pulse oximeters distributed by DOH-CHD.',
    Q15: 'Yes, this was pre-existing, but it has significantly improved due to the UHC Act',
    Q16: 'Vaccines and basic medicines (paracetamol, amoxicillin) are more consistently stocked.',
    Q17: 'No, this has not been implemented yet, but we plan to in the next 1-2 years',
    Q18: 'Yes, this has been implemented or improved recently, but not due to the UHC Act',
    Q19: 'Yes, this was implemented as a direct result of the UHC Act',
    Q20: 'Yes, this was pre-existing, but it has significantly improved due to the UHC Act',
    Q25: ['Salary', 'Number of patients', 'Standards to follow'],
    survey_language: 'en',
  };
  // Section A Q6 (specialty) — only Physician/Dentist see this question per
  // role-conditional skip; mirror that here so the response data matches the
  // actual UI logic.
  if (hcw.role === 'Physician/Doctor') {
    values.Q6 = 'Family Medicine';
  } else if (hcw.role === 'Dentist') {
    values.Q6 = 'No specialty';
  }
  // Section A Q8 — only seen if Q7=Yes (private practice). All demo HCWs
  // chose Q7=No to keep the demo simple, so Q8 is correctly absent.
  return values;
}

/** ============================================================
 * SHEET WRITERS
 * ============================================================ */

function _seedFacilities(ss) {
  var sh = ss.getSheetByName(TABS.FACILITIES);
  if (!sh) throw new Error('FacilityMasterList sheet not found');
  var headers = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0];
  var idIdx = headers.indexOf('facility_id');
  var existing = _existingIds(sh, idIdx);
  var added = 0, skipped = 0;
  var facilities = _demoFacilities();
  for (var i = 0; i < facilities.length; i++) {
    var f = facilities[i];
    if (existing[f.facility_id]) { skipped++; continue; }
    var row = headers.map(function (h) {
      if (h === 'facility_id') return f.facility_id;
      if (h === 'facility_name') return f.facility_name;
      if (h === 'facility_type') return f.facility_type;
      if (h === 'region') return f.region;
      if (h === 'province') return f.province;
      if (h === 'city_mun') return f.city_mun;
      if (h === 'barangay') return f.barangay;
      return '';
    });
    sh.appendRow(row);
    added++;
  }
  return { added: added, skipped: skipped };
}

function _seedHCWs(ss) {
  var sh = ss.getSheetByName('F2_HCWs');
  if (!sh) throw new Error('F2_HCWs sheet not found — run runAllMigrations() first');
  var headers = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0];
  var idIdx = headers.indexOf('hcw_id');
  var existing = _existingIds(sh, idIdx);
  var added = 0, skipped = 0;
  var hcws = _demoHCWs();
  var facilities = _facilityLookup();
  for (var i = 0; i < hcws.length; i++) {
    var h = hcws[i];
    if (existing[h.hcw_id]) { skipped++; continue; }
    var fac = facilities[h.facility_id];
    var nowIso = new Date().toISOString();
    // Stagger created_at so the HCWs list isn't all the same timestamp.
    var createdAt = _stagger(nowIso, -i * 3 * 60 * 60 * 1000); // i hours back, more for older ones
    var rowStatus = h.status === 'enrolled' ? 'enrolled' : 'enrolled';
    var row = headers.map(function (col) {
      if (col === 'hcw_id') return h.hcw_id;
      if (col === 'facility_id') return h.facility_id;
      if (col === 'facility_name') return fac ? fac.facility_name : '';
      if (col === 'enrollment_token_jti') return _demoJti(h.hcw_id, 0);
      if (col === 'token_issued_at') return createdAt;
      if (col === 'token_revoked_at') return '';
      if (col === 'status') return rowStatus;
      if (col === 'created_at') return createdAt;
      return '';
    });
    sh.appendRow(row);
    added++;
  }
  return { added: added, skipped: skipped };
}

function _seedResponses(ss) {
  var sh = ss.getSheetByName(TABS.RESPONSES);
  if (!sh) throw new Error('F2_Responses sheet not found');
  var headers = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0];
  var hcwIdx = headers.indexOf('hcw_id');
  var existing = {};
  // Skip HCWs that already have a response row.
  var lastRow = sh.getLastRow();
  if (lastRow > 1) {
    var data = sh.getRange(2, 1, lastRow - 1, headers.length).getValues();
    for (var k = 0; k < data.length; k++) existing[String(data[k][hcwIdx])] = true;
  }
  var added = 0, skipped = 0;
  var hcws = _demoHCWs();
  var facilities = _facilityLookup();
  for (var i = 0; i < hcws.length; i++) {
    var h = hcws[i];
    if (h.status === 'enrolled' || h.status === 'dlq') continue; // no response row
    if (existing[h.hcw_id]) { skipped++; continue; }
    var fac = facilities[h.facility_id];
    var values = _demoValuesJson(h);
    var nowIso = new Date().toISOString();
    var submittedAt = _stagger(nowIso, -i * 4 * 60 * 60 * 1000); // staggered over the past day or so
    var row = headers.map(function (col) {
      if (col === 'submission_id') return 'DEMO-SUB-' + h.hcw_id.replace('DEMO-HCW-', '');
      if (col === 'client_submission_id') return 'DEMO-CSID-' + h.hcw_id.replace('DEMO-HCW-', '') + '-1';
      if (col === 'submitted_at_server') return submittedAt;
      if (col === 'submitted_at_client') return submittedAt;
      if (col === 'source') return 'pwa';
      if (col === 'spec_version') return '2026-04-17-m1';
      if (col === 'app_version') return '1.3.0';
      if (col === 'hcw_id') return h.hcw_id;
      if (col === 'facility_id') return h.facility_id;
      if (col === 'device_fingerprint') return 'DEMO-DEV-' + (i % 3 + 1);
      if (col === 'sync_attempt_count') return 1;
      if (col === 'status') return 'synced';
      if (col === 'values_json') return JSON.stringify(values);
      if (col === 'submission_lat') return fac ? fac.lat + (Math.random() - 0.5) * 0.005 : '';
      if (col === 'submission_lng') return fac ? fac.lng + (Math.random() - 0.5) * 0.005 : '';
      if (col === 'source_path') return h.status === 'paper_encoded' ? 'paper_encoded' : 'self_admin';
      if (col === 'encoded_by') return h.status === 'paper_encoded' ? 'carl_admin' : '';
      if (col === 'encoded_at') return h.status === 'paper_encoded' ? submittedAt : '';
      return '';
    });
    sh.appendRow(row);
    added++;
  }
  return { added: added, skipped: skipped };
}

function _seedDLQ(ss) {
  var sh = ss.getSheetByName(TABS.DLQ);
  if (!sh) throw new Error('F2_DLQ sheet not found');
  var headers = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0];
  var csidIdx = headers.indexOf('client_submission_id');
  var existing = _existingIds(sh, csidIdx);
  var added = 0, skipped = 0;
  // One DLQ entry: HCW-012 (Ramon Velasquez) hit a schema_version mismatch.
  // Realistic operational hiccup: tablet had stale spec_version after an
  // offline period, server rejected with E_SPEC_DRIFT.
  var entry = {
    dlq_id: 'DEMO-DLQ-001',
    received_at_server: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    client_submission_id: 'DEMO-SUB-012',
    reason: 'E_SPEC_DRIFT: client submitted spec_version=2026-04-08 below min_accepted=2026-04-17-m1; tablet needs to fetch latest config and resubmit.',
    payload_json: JSON.stringify({
      hcw_id: 'DEMO-HCW-012',
      facility_id: 'DEMO-FAC-LYING-IN-BAL',
      spec_version: '2026-04-08',
      app_version: '1.2.3',
      values_summary: 'Section A complete; submission rejected at gate before sheet write.',
    }),
  };
  if (existing[entry.client_submission_id]) {
    skipped = 1;
  } else {
    var row = headers.map(function (col) { return entry[col] != null ? entry[col] : ''; });
    sh.appendRow(row);
    added = 1;
  }
  return { added: added, skipped: skipped };
}

function _seedFiles(ss) {
  var sh = ss.getSheetByName('F2_FileMeta');
  if (!sh) throw new Error('F2_FileMeta sheet not found — run runAllMigrations() first');
  var headers = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0];
  var idIdx = headers.indexOf('file_id');
  var existing = _existingIds(sh, idIdx);
  var added = 0, skipped = 0;
  var files = [
    {
      file_id: 'DEMO-FILE-001',
      filename: 'Demo - Field Plan 2026-Q1.pdf',
      content_type: 'application/pdf',
      size_bytes: 248576,
      uploaded_by: 'carl_admin',
      uploaded_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
      description: 'Q1 fieldwork plan — facility coverage + enumerator assignments.',
      deleted_at: '',
    },
    {
      file_id: 'DEMO-FILE-002',
      filename: 'Demo - Facility Roster.csv',
      content_type: 'text/csv',
      size_bytes: 12480,
      uploaded_by: 'carl_admin',
      uploaded_at: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
      description: 'Sample facility list with PSGC region/province/city/barangay cols.',
      deleted_at: '',
    },
  ];
  for (var i = 0; i < files.length; i++) {
    var f = files[i];
    if (existing[f.file_id]) { skipped++; continue; }
    var row = headers.map(function (col) { return f[col] != null ? f[col] : ''; });
    sh.appendRow(row);
    added++;
  }
  return { added: added, skipped: skipped };
}

function _seedAuditEvents(ss) {
  // Add one operational realism event: token reissue for HCW-006 by carl_admin
  // ~3 hours ago. The recent admin_login / admin_revoke_sessions entries are
  // already populated organically by real Carl login traffic — we don't need
  // to seed those.
  var sh = ss.getSheetByName(TABS.AUDIT);
  if (!sh) throw new Error('F2_Audit sheet not found');
  var headers = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0];
  var idIdx = headers.indexOf('audit_id');
  var existing = _existingIds(sh, idIdx);
  var added = 0, skipped = 0;
  var events = [
    {
      audit_id: 'DEMO-AUD-001',
      occurred_at_server: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
      occurred_at_client: '',
      event_type: 'admin_hcws_reissue_token',
      hcw_id: 'DEMO-HCW-006',
      facility_id: 'DEMO-FAC-DH-INFANTA',
      app_version: '',
      payload_json: '',
      actor_username: 'carl_admin',
      actor_jti: '',
      actor_role: 'Administrator',
      event_resource: 'DEMO-HCW-006',
      event_payload_json: JSON.stringify({ reason: 'HCW lost device; reissue requested via Viber' }),
      client_ip_hash: '',
      request_id: 'demo-rid-001',
    },
    {
      audit_id: 'DEMO-AUD-002',
      occurred_at_server: new Date(Date.now() - 90 * 60 * 1000).toISOString(),
      occurred_at_client: '',
      event_type: 'admin_login_failed',
      hcw_id: '',
      facility_id: '',
      app_version: '',
      payload_json: '',
      actor_username: 'unknown_user',
      actor_jti: '',
      actor_role: '',
      event_resource: '',
      event_payload_json: JSON.stringify({ reason: 'invalid_credentials', username_attempted: 'admin' }),
      client_ip_hash: 'demo-iphash-xyz',
      request_id: 'demo-rid-002',
    },
  ];
  for (var i = 0; i < events.length; i++) {
    var e = events[i];
    if (existing[e.audit_id]) { skipped++; continue; }
    var row = headers.map(function (col) { return e[col] != null ? e[col] : ''; });
    sh.appendRow(row);
    added++;
  }
  return { added: added, skipped: skipped };
}

/** ============================================================
 * INTERNAL HELPERS
 * ============================================================ */

function _existingIds(sh, idColumnIndex) {
  var existing = {};
  var lastRow = sh.getLastRow();
  if (lastRow < 2 || idColumnIndex < 0) return existing;
  var data = sh.getRange(2, 1, lastRow - 1, sh.getLastColumn()).getValues();
  for (var i = 0; i < data.length; i++) {
    var v = String(data[i][idColumnIndex] || '').trim();
    if (v) existing[v] = true;
  }
  return existing;
}

function _facilityLookup() {
  var lookup = {};
  var facilities = _demoFacilities();
  for (var i = 0; i < facilities.length; i++) {
    lookup[facilities[i].facility_id] = facilities[i];
  }
  return lookup;
}

function _stagger(nowIso, deltaMs) {
  return new Date(new Date(nowIso).getTime() + deltaMs).toISOString();
}

function _demoJti(hcwId, sequence) {
  // Deterministic-looking placeholder JTI for demo rows. Real JTIs are UUIDs
  // minted by the Worker; these don't need to verify, just look plausible.
  return 'demo-jti-' + hcwId.replace('DEMO-HCW-', '').toLowerCase() + '-' + sequence;
}

function _purgePrefix(ss, sheetName, columnName, prefix) {
  var sh = ss.getSheetByName(sheetName);
  if (!sh) return { purged: 0, note: 'sheet not found' };
  var headers = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0];
  var colIdx = headers.indexOf(columnName);
  if (colIdx < 0) return { purged: 0, note: 'column not found' };
  var lastRow = sh.getLastRow();
  if (lastRow < 2) return { purged: 0 };
  var data = sh.getRange(2, 1, lastRow - 1, headers.length).getValues();
  // Walk bottom-up so deleteRow indices stay correct.
  var purged = 0;
  for (var i = data.length - 1; i >= 0; i--) {
    var v = String(data[i][colIdx] || '');
    if (v.indexOf(prefix) === 0) {
      sh.deleteRow(i + 2);
      purged++;
    }
  }
  return { purged: purged };
}

if (typeof module !== 'undefined') {
  module.exports = {
    seedDemoData: seedDemoData,
    purgeDemoData: purgeDemoData,
  };
}
