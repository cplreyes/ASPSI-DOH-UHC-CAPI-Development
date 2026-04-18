function ok(data) {
  return { ok: true, data: data };
}

function fail(code, message) {
  return { ok: false, error: { code: code, message: message } };
}

function timingSafeEq(a, b) {
  if (typeof a !== 'string' || typeof b !== 'string') return false;
  if (a.length !== b.length) return false;
  var diff = 0;
  for (var i = 0; i < a.length; i++) {
    diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return diff === 0;
}

function generateUuid() {
  var hex = '0123456789abcdef';
  var s = '';
  for (var i = 0; i < 36; i++) {
    if (i === 8 || i === 13 || i === 18 || i === 23) {
      s += '-';
    } else if (i === 14) {
      s += '4';
    } else if (i === 19) {
      s += hex[(Math.random() * 4) | 8];
    } else {
      s += hex[(Math.random() * 16) | 0];
    }
  }
  return s;
}

function nowMs() {
  return Date.now();
}

if (typeof module !== 'undefined') {
  module.exports = { ok: ok, fail: fail, timingSafeEq: timingSafeEq, generateUuid: generateUuid, nowMs: nowMs };
}
