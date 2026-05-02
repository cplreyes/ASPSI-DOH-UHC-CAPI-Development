var PROP_HMAC_SECRET = 'HMAC_SECRET';
var PROP_SPREADSHEET_ID = 'SPREADSHEET_ID';

function doGet(e) {
  // Admin UI moved to the Cloudflare Worker. See worker/src/admin-html.ts.
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

    // Admin Portal envelope path: when no URL-param action is set and the
    // body parses as `{action: 'admin_*', ts, request_id, payload, hmac}`,
    // route through the AdminDispatch HMAC verifier + handler table.
    // Falls through to legacy verifyRequest + dispatch for tablet traffic.
    if (method === 'POST' && !action && body) {
      var parsedBody = null;
      try { parsedBody = JSON.parse(body); } catch (e1) { parsedBody = null; }
      var envelope = parsedBody ? _isAdminEnvelope(parsedBody) : null;
      if (envelope) {
        var adminCtx = buildCtx();
        // Admin RPCs that mutate sheets manage their own LockService scope
        // (LockService.getDocumentLock at the handler level), so doPost
        // doesn't need to wrap the whole call in a script lock - that
        // would serialize unrelated reads and burn AS quota.
        var adminResult = dispatchAdminAction(
          envelope,
          secret,
          adminCtx,
          { hmacSha256Hex: _gasHmacHex, nowMs: Date.now },
        );
        return _jsonOut(adminResult);
      }
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
    readAll: function (limit, offset) {
      limit = limit || 500;
      offset = offset || 0;
      var last = sheet.getLastRow();
      if (last < 2) return [];
      var startRow = 2 + offset;
      var availableRows = last - startRow + 1;
      if (availableRows <= 0) return [];
      var take = Math.min(limit, availableRows);
      var data = sheet.getRange(startRow, 1, take, cols.length).getValues();
      return data.map(function (row) {
        var obj = {};
        for (var i = 0; i < cols.length; i++) obj[cols[i]] = row[i];
        return obj;
      });
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

function _buildAuditCtx(sheet) {
  var cols = F2_AUDIT_COLUMNS;
  return {
    appendRow: function (rowObj) {
      var arr = cols.map(function (c) { return rowObj[c] != null ? rowObj[c] : ''; });
      sheet.appendRow(arr);
      return rowObj.audit_id;
    },
    readAll: function (limit, offset) {
      limit = limit || 500;
      offset = offset || 0;
      var last = sheet.getLastRow();
      if (last < 2) return [];
      var startRow = 2 + offset;
      var availableRows = last - startRow + 1;
      if (availableRows <= 0) return [];
      var take = Math.min(limit, availableRows);
      var data = sheet.getRange(startRow, 1, take, cols.length).getValues();
      return data.map(function (row) {
        var obj = {};
        for (var i = 0; i < cols.length; i++) obj[cols[i]] = row[i];
        return obj;
      });
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
