var SKEW_MS = 5 * 60 * 1000;

function canonicalString(method, action, ts, body) {
  return method + '|' + action + '|' + ts + '|' + body;
}

function verifyRequest(req, secret, deps) {
  var ts = parseInt(req.ts, 10);
  if (!Number.isFinite(ts) || String(ts) !== String(req.ts).trim()) {
    return { ok: false, error: { code: 'E_TS_INVALID', message: 'Timestamp is not an integer' } };
  }
  var now = deps.nowMs();
  if (Math.abs(now - ts) > SKEW_MS) {
    return { ok: false, error: { code: 'E_TS_SKEW', message: 'Timestamp outside ±5 minute window' } };
  }
  if (typeof req.sig !== 'string' || req.sig.length === 0) {
    return { ok: false, error: { code: 'E_SIG_INVALID', message: 'Missing signature' } };
  }
  var canonical = canonicalString(req.method, req.action, String(ts), req.body || '');
  var expected = deps.hmacSha256Hex(secret, canonical);
  var a = String(expected).toLowerCase();
  var b = String(req.sig).toLowerCase();
  if (a.length !== b.length) {
    return { ok: false, error: { code: 'E_SIG_INVALID', message: 'Signature mismatch' } };
  }
  var diff = 0;
  for (var i = 0; i < a.length; i++) {
    diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  if (diff !== 0) {
    return { ok: false, error: { code: 'E_SIG_INVALID', message: 'Signature mismatch' } };
  }
  return { ok: true };
}

if (typeof module !== 'undefined') {
  module.exports = { verifyRequest: verifyRequest, canonicalString: canonicalString };
}
