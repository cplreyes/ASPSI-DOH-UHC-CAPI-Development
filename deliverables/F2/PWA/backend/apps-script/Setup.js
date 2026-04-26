// PROP_ADMIN_SECRET removed: admin moved to the Cloudflare Worker (see worker/).
// At cutover (spec §10), clean it from Script Properties:
//   PropertiesService.getScriptProperties().deleteProperty('ADMIN_SECRET');

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
