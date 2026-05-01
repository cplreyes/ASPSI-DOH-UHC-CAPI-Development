function _requireString(obj, key) {
  return typeof obj[key] === 'string' && obj[key].length > 0;
}

function _coordOrEmpty(v) {
  if (typeof v === 'number' && isFinite(v)) return v;
  return '';
}

function _buildResponseRow(payload, serverSubmissionId, ctx) {
  var values = payload.values || {};
  return {
    submission_id: serverSubmissionId,
    client_submission_id: payload.client_submission_id,
    submitted_at_server: new Date(ctx.nowMs()).toISOString(),
    submitted_at_client: payload.submitted_at_client != null
      ? new Date(payload.submitted_at_client).toISOString()
      : '',
    source: 'PWA',
    spec_version: payload.spec_version || '',
    app_version: payload.app_version || '',
    hcw_id: payload.hcw_id || '',
    facility_id: payload.facility_id || '',
    device_fingerprint: payload.device_fingerprint || '',
    sync_attempt_count: payload.sync_attempt_count != null ? String(payload.sync_attempt_count) : '1',
    status: 'stored',
    values_json: JSON.stringify(values),
    // Admin Portal columns (Task 2.7). PWA submits insert lat/lng into the
    // values dict (Task 2.6); the encoder write path (Task 4.2) sends them
    // as top-level fields plus encoded_by/encoded_at and source_path='paper_encoded'.
    // Top-level wins over values to keep the encoder path explicit.
    submission_lat: _coordOrEmpty(payload.submission_lat != null ? payload.submission_lat : values.submission_lat),
    submission_lng: _coordOrEmpty(payload.submission_lng != null ? payload.submission_lng : values.submission_lng),
    source_path: payload.source_path || values.source_path || 'self_admin',
    encoded_by: payload.encoded_by || '',
    encoded_at: payload.encoded_at
      ? new Date(payload.encoded_at).toISOString()
      : '',
  };
}

function handleSubmit(payload, ctx) {
  if (!payload || typeof payload !== 'object') {
    return { ok: false, error: { code: 'E_PAYLOAD_INVALID', message: 'Body must be a JSON object' } };
  }
  if (!_requireString(payload, 'client_submission_id')) {
    return { ok: false, error: { code: 'E_PAYLOAD_INVALID', message: 'Missing client_submission_id' } };
  }
  if (!_requireString(payload, 'spec_version')) {
    return { ok: false, error: { code: 'E_PAYLOAD_INVALID', message: 'Missing spec_version' } };
  }
  if (payload.values == null) {
    return { ok: false, error: { code: 'E_PAYLOAD_INVALID', message: 'Missing values' } };
  }
  var minSpec = ctx.config.get('min_accepted_spec_version') || '';
  if (minSpec && payload.spec_version < minSpec) {
    return { ok: false, error: { code: 'E_SPEC_TOO_OLD', message: 'spec_version ' + payload.spec_version + ' < ' + minSpec } };
  }
  if (typeof payload.values !== 'object' || Array.isArray(payload.values)) {
    ctx.dlq.appendRow({
      dlq_id: ctx.generateUuid(),
      received_at_server: new Date(ctx.nowMs()).toISOString(),
      client_submission_id: payload.client_submission_id,
      reason: 'values must be an object',
      payload_json: JSON.stringify(payload),
    });
    return { ok: false, error: { code: 'E_VALIDATION', message: 'values must be an object' } };
  }

  var existing = ctx.responses.findExisting(payload.client_submission_id);
  if (existing) {
    return { ok: true, data: { submission_id: existing.submission_id, status: 'duplicate', server_timestamp: new Date(ctx.nowMs()).toISOString() } };
  }

  var serverId = 'srv-' + ctx.generateUuid();
  var row = _buildResponseRow(payload, serverId, ctx);
  var appendedId = ctx.responses.appendRow(row);
  return {
    ok: true,
    data: {
      submission_id: appendedId || serverId,
      status: 'accepted',
      server_timestamp: row.submitted_at_server,
    },
  };
}

function handleBatchSubmit(payload, ctx) {
  if (!payload || !Array.isArray(payload.responses)) {
    return { ok: false, error: { code: 'E_PAYLOAD_INVALID', message: 'Body must be { responses: [] }' } };
  }
  if (payload.responses.length > 50) {
    return { ok: false, error: { code: 'E_BATCH_TOO_LARGE', message: 'Max 50 responses per batch' } };
  }
  var results = [];
  for (var i = 0; i < payload.responses.length; i++) {
    var item = payload.responses[i];
    var clientId = item && item.client_submission_id ? item.client_submission_id : null;
    var r = handleSubmit(item, ctx);
    if (r.ok) {
      results.push({
        client_submission_id: clientId,
        submission_id: r.data.submission_id,
        status: r.data.status,
      });
    } else {
      results.push({
        client_submission_id: clientId,
        status: 'rejected',
        error: r.error,
      });
    }
  }
  return { ok: true, data: { results: results } };
}

function handleFacilities(ctx) {
  var rows = ctx.facilities.readAll();
  return { ok: true, data: { facilities: rows } };
}

function _coerceConfigValue(value) {
  if (value === 'true') return true;
  if (value === 'false') return false;
  return value;
}

function handleConfig(ctx) {
  var pairs = ctx.config.readAll();
  var out = {};
  for (var i = 0; i < pairs.length; i++) {
    var key = pairs[i][0];
    var val = pairs[i][1];
    out[key] = _coerceConfigValue(val);
  }
  return { ok: true, data: out };
}

function handleSpecHash(ctx) {
  return {
    ok: true,
    data: {
      spec_hash: ctx.config.get('spec_hash') || '',
      current_spec_version: ctx.config.get('current_spec_version') || '',
    },
  };
}

function handleAudit(payload, ctx) {
  if (!payload || typeof payload !== 'object' || typeof payload.event_type !== 'string' || !payload.event_type) {
    return { ok: false, error: { code: 'E_PAYLOAD_INVALID', message: 'Missing event_type' } };
  }
  var auditId = ctx.generateUuid();
  ctx.audit.appendRow({
    audit_id: auditId,
    occurred_at_server: new Date(ctx.nowMs()).toISOString(),
    occurred_at_client: payload.occurred_at_client != null ? new Date(payload.occurred_at_client).toISOString() : '',
    event_type: payload.event_type,
    hcw_id: payload.hcw_id || '',
    facility_id: payload.facility_id || '',
    app_version: payload.app_version || '',
    payload_json: JSON.stringify(payload.payload || {}),
  });
  return { ok: true, data: { audit_id: auditId } };
}

if (typeof module !== 'undefined') {
  module.exports = {
    handleSubmit: handleSubmit,
    handleBatchSubmit: handleBatchSubmit,
    handleFacilities: handleFacilities,
    handleConfig: handleConfig,
    handleSpecHash: handleSpecHash,
    handleAudit: handleAudit,
  };
}
