/**
 * F2 OnSubmit — implements POST rules from deliverables/F2/F2-Cross-Field.md.
 *
 * Triggered on every Form submission; also re-runnable across the full Sheet
 * via runNightlyCleanSheet() (installed as a daily trigger by buildForm).
 *
 * Writes these columns to the response Sheet:
 *   _qa_flags                — semicolon-separated rule IDs that fired
 *   _qa_disposition          — completed | partial | declined | no_response
 *   _derived_employment_class— full-time | part-time
 *   _dropped_fields          — comma-separated field names whose values were dropped
 *   _qa_last_run_at          — ISO timestamp
 */

var QA_COLS = ['_qa_flags','_qa_disposition','_derived_employment_class','_dropped_fields','_qa_last_run_at'];

function onF2FormSubmit(e) {
  try {
    var sheet = e.range.getSheet();
    ensureQaColumns_(sheet);
    var row = e.range.getRow();
    processRow_(sheet, row);
  } catch (err) {
    Logger.log('onF2FormSubmit error: ' + err);
  }
}

function runNightlyCleanSheet() {
  var props = PropertiesService.getScriptProperties();
  var sheetId = props.getProperty(PROPS_KEY_SHEET_ID);
  if (!sheetId) return;
  var ss = SpreadsheetApp.openById(sheetId);
  var sheet = ss.getSheets()[0];
  ensureQaColumns_(sheet);
  var last = sheet.getLastRow();
  for (var r = 2; r <= last; r++) processRow_(sheet, r);
}

function ensureQaColumns_(sheet) {
  var header = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  QA_COLS.forEach(function (name) {
    if (header.indexOf(name) === -1) {
      sheet.getRange(1, sheet.getLastColumn() + 1).setValue(name);
      header.push(name);
    }
  });
}

function getRowObject_(sheet, row) {
  var header = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  var values = sheet.getRange(row, 1, 1, sheet.getLastColumn()).getValues()[0];
  var obj = {};
  for (var i = 0; i < header.length; i++) obj[header[i]] = values[i];
  obj.__header = header;
  obj.__row = row;
  return obj;
}

function setRowField_(sheet, row, header, name, value) {
  var idx = header.indexOf(name);
  if (idx === -1) return;
  sheet.getRange(row, idx + 1).setValue(value);
}

function findCol_(header, prefix) {
  for (var i = 0; i < header.length; i++) {
    if (header[i] && header[i].indexOf(prefix) === 0) return i;
  }
  return -1;
}

function processRow_(sheet, row) {
  var r = getRowObject_(sheet, row);
  var flags = [];
  var dropped = [];
  var header = r.__header;

  // ---- helpers -------------------------------------------------
  function get(prefix) { var i = findCol_(header, prefix); return i === -1 ? '' : r[header[i]]; }
  function dropField(prefix) {
    var i = findCol_(header, prefix); if (i === -1) return;
    if (r[header[i]] !== '' && r[header[i]] != null) {
      sheet.getRange(row, i + 1).setValue('');
      dropped.push(header[i]);
    }
  }
  function inRole(roles) { var q5 = String(get('Q5.')); return roles.some(function (x) { return q5.indexOf(x) !== -1; }); }
  var DOCTOR_DENTIST = ['Physician/Doctor','Dentist'];
  var BUCKET_CD_ROLES = ['Administrator','Physician/Doctor','Nurse','Midwife','Dentist','Nutrition'];
  var BUCKET_PHARM_ROLES = ['Pharmacist','assistant pharmacist'];

  // ---- SRC rules ----------------------------------------------
  var respondentEmail = get('Email Address') || get('email') || '';
  var responseSource = String(get('response_source') || 'self');
  if (responseSource === 'self' && !respondentEmail) flags.push('SRC-01');

  // ---- CONS rules ---------------------------------------------
  var consent = String(get('I have read the information above'));
  if (consent.indexOf('No') === 0) {
    // Drop all Q* body answers
    header.forEach(function (h, i) {
      if (/^Q\d/.test(h) && r[h] !== '' && r[h] != null) {
        sheet.getRange(row, i + 1).setValue('');
        dropped.push(h);
      }
    });
    flags.push('CONS-02-dropped');
  }

  // ---- GATE rules ---------------------------------------------
  // GATE-01: Q55 non-doctor/dentist drop
  if (!inRole(DOCTOR_DENTIST) && get('Q55.') !== '') {
    dropField('Q55.'); flags.push('GATE-01-dropped');
  }
  // GATE-02: Q56..Q80 non-doctor/dentist drop
  if (!inRole(DOCTOR_DENTIST)) {
    for (var q = 56; q <= 80; q++) {
      dropField('Q' + q + '.'); dropField('Q' + q + '.1');
    }
  }
  // GATE-03: BUCAS gate
  var hasBucas = String(get('Does your facility have a BUCAS')).indexOf('Yes') === 0;
  if (!(hasBucas && inRole(BUCKET_CD_ROLES))) {
    ['Q43.','Q44.','Q45.'].forEach(dropField);
    if (dropped.length) flags.push('GATE-03-dropped');
  }
  // GATE-04: GAMOT gate
  var hasGamot = String(get('Does your facility have a GAMOT')).indexOf('Yes') === 0;
  var gamotRoles = inRole(BUCKET_CD_ROLES) || inRole(BUCKET_PHARM_ROLES);
  if (!(hasGamot && gamotRoles)) {
    ['Q46.','Q47.','Q48.'].forEach(dropField);
  }
  // GATE-05: C/D role gate — Q27..Q42
  if (!inRole(BUCKET_CD_ROLES)) {
    for (var q2 = 27; q2 <= 42; q2++) dropField('Q' + q2 + '.');
  }

  // ---- FAC rules (ZBB/NBB split) ------------------------------
  var facType = String(get('Please confirm your facility type'));
  var isDohRetained = facType.indexOf('DOH-retained') === 0;
  var isPublic = isDohRetained || facType.indexOf('Public') === 0;
  if (!isDohRetained) { dropField('Q62.'); dropField('Q67.'); dropField('Q78.'); }
  if (!isPublic)      { dropField('Q62.1'); dropField('Q67.1'); dropField('Q78.1'); }
  if (isDohRetained) {
    // FAC-07: warn if missing either dual
    ['Q62.','Q62.1','Q67.','Q67.1','Q78.','Q78.1'].forEach(function (p) {
      if (get(p) === '') flags.push('FAC-07-missing-' + p);
    });
  }

  // ---- PROF rules (warn) --------------------------------------
  var age = parseInt(get('Q4.'), 10);
  var tenureYears = parseInt(get('Q9a.'), 10);
  if (!isNaN(age) && !isNaN(tenureYears) && tenureYears > age - 15) flags.push('PROF-01');
  if (!inRole(DOCTOR_DENTIST)) {
    var spec = String(get('Q6.'));
    if (spec && spec !== 'No specialty') flags.push('PROF-02');
  }
  var hoursPerDay = parseInt(get('Q11.'), 10);
  var employmentClass = (!isNaN(hoursPerDay) && hoursPerDay >= 8) ? 'full-time' : 'part-time';
  var daysPerWeek = parseInt(get('Q10.'), 10);
  if (!isNaN(hoursPerDay) && !isNaN(daysPerWeek) && (hoursPerDay * daysPerWeek) > 80) flags.push('PROF-04');
  var q7 = String(get('Q7.'));
  if (get('Q8.') !== '' && (q7.indexOf('No') === 0 || facType.indexOf('Private') === 0)) flags.push('PROF-05');

  // ---- DISP rules ---------------------------------------------
  var ts = r['Timestamp'] || r[header[0]];
  var disposition;
  if (consent.indexOf('No') === 0) disposition = 'declined';
  else if (ts) disposition = 'completed';
  else disposition = 'partial';

  // ---- write QA columns ---------------------------------------
  setRowField_(sheet, row, header, '_qa_flags', flags.join(';'));
  setRowField_(sheet, row, header, '_qa_disposition', disposition);
  setRowField_(sheet, row, header, '_derived_employment_class', employmentClass);
  setRowField_(sheet, row, header, '_dropped_fields', dropped.join(','));
  setRowField_(sheet, row, header, '_qa_last_run_at', new Date().toISOString());
}
