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
