// Pure-function admin handlers. No Apps Script globals. All I/O injected via ctx.

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

function listDlq(rows) {
  var copy = rows.slice();
  copy.sort(function (a, b) {
    return String(b.received_at_server).localeCompare(String(a.received_at_server));
  });
  return copy;
}

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

if (typeof module !== 'undefined') {
  module.exports = {
    verifyAdminToken: verifyAdminToken,
    filterResponses: filterResponses,
    filterAudit: filterAudit,
    listDlq: listDlq,
    rowsToCsv: rowsToCsv,
  };
}
