var _ROUTE_METHODS = {
  'submit':       'POST',
  'batch-submit': 'POST',
  'audit':        'POST',
  'facilities':   'GET',
  'config':       'GET',
  'spec-hash':    'GET',
};

var _ROUTE_HANDLERS = {
  'submit':       'handleSubmit',
  'batch-submit': 'handleBatchSubmit',
  'audit':        'handleAudit',
  'facilities':   'handleFacilities',
  'config':       'handleConfig',
  'spec-hash':    'handleSpecHash',
};

function dispatch(req, ctx, handlers) {
  var expectedMethod = _ROUTE_METHODS[req.action];
  if (!expectedMethod) {
    return { ok: false, error: { code: 'E_ACTION_UNKNOWN', message: 'Unknown action: ' + req.action } };
  }
  if (expectedMethod !== req.method) {
    return { ok: false, error: { code: 'E_METHOD_UNKNOWN', message: 'Action ' + req.action + ' requires ' + expectedMethod } };
  }
  if (ctx.config.get('kill_switch') === 'true') {
    return { ok: false, error: { code: 'E_KILL_SWITCH', message: 'Backend is temporarily unavailable' } };
  }

  var handlerName = _ROUTE_HANDLERS[req.action];
  var handler = handlers[handlerName];

  if (expectedMethod === 'GET') {
    return handler(ctx);
  }

  var parsed;
  try {
    parsed = req.body && req.body.length > 0 ? JSON.parse(req.body) : {};
  } catch (e) {
    return { ok: false, error: { code: 'E_PAYLOAD_INVALID', message: 'Body is not valid JSON: ' + e.message } };
  }
  return handler(parsed, ctx);
}

if (typeof module !== 'undefined') {
  module.exports = { dispatch: dispatch };
}
