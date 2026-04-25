/**
 * Admin UI as a single static HTML+JS string.
 * Vanilla JS, no build step. Served by `GET /admin/`.
 *
 * XSS posture: all dynamic data (tablet_label, facility_id, etc.) is inserted via
 * textContent only. innerHTML is used exclusively for static template strings within
 * this file, never for user-supplied or API-returned data.
 */

export function renderAdminHtml(): string {
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>F2 Auth Admin</title>
<style>
:root { --fg: #111; --muted: #666; --border: #ddd; --bg: #fafafa; --accent: #0d6efd; --danger: #dc3545; }
* { box-sizing: border-box; }
body { font: 14px/1.45 system-ui, sans-serif; color: var(--fg); background: var(--bg); margin: 0; padding: 24px; max-width: 960px; margin: 0 auto; }
h1 { font-size: 1.4rem; margin: 0 0 16px; }
h2 { font-size: 1.1rem; margin: 24px 0 8px; }
input, button, select { font: inherit; padding: 6px 10px; border: 1px solid var(--border); border-radius: 4px; }
button { cursor: pointer; background: var(--accent); color: white; border-color: transparent; }
button:disabled { opacity: 0.5; cursor: not-allowed; }
button.danger { background: var(--danger); }
.row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin: 8px 0; }
.row label { min-width: 120px; color: var(--muted); }
.token { font-family: ui-monospace, monospace; word-break: break-all; background: white; padding: 8px; border: 1px solid var(--border); border-radius: 4px; }
table { width: 100%; border-collapse: collapse; margin-top: 12px; background: white; }
th, td { text-align: left; padding: 8px; border-bottom: 1px solid var(--border); font-size: 13px; }
th { background: #f0f0f0; font-weight: 600; }
.muted { color: var(--muted); font-size: 12px; }
.hidden { display: none; }
.error { color: var(--danger); margin: 8px 0; }
#qr { margin-top: 12px; }
</style>
</head>
<body>
<h1>F2 PWA Auth - Admin</h1>

<section id="login-section">
  <h2>Sign in</h2>
  <div class="row">
    <label for="password">Password</label>
    <input type="password" id="password" autocomplete="current-password">
    <button id="login-btn">Sign in</button>
  </div>
  <div class="error" id="login-error"></div>
</section>

<section id="app" class="hidden">
  <h2>Issue tablet token</h2>
  <div class="row"><label for="facility">Facility</label><input type="text" id="facility" placeholder="F-001"></div>
  <div class="row"><label for="label">Tablet label</label><input type="text" id="label" placeholder="Tablet-3 / Manila General"></div>
  <div class="row"><label for="ttl">TTL (days)</label><input type="number" id="ttl" value="30" min="1" max="365"></div>
  <div class="row"><button id="issue-btn">Issue token</button></div>
  <div id="issue-result" class="hidden">
    <p class="muted">Copy this token and paste into the tablet's enrollment screen, or scan the QR code.</p>
    <div class="token" id="token-display"></div>
    <div id="qr"></div>
  </div>

  <h2>Active tokens</h2>
  <div class="row">
    <label for="filter-facility">Filter by facility</label>
    <input type="text" id="filter-facility" placeholder="(all)">
    <button id="refresh-btn">Refresh</button>
  </div>
  <table id="tokens-table">
    <thead><tr><th>Issued</th><th>Facility</th><th>Label</th><th>Expires</th><th>Status</th><th></th></tr></thead>
    <tbody></tbody>
  </table>
</section>

<script>
async function api(path, opts) {
  opts = opts || {};
  var headers = Object.assign({ 'Content-Type': 'application/json' }, opts.headers || {});
  var resp = await fetch(path, Object.assign({ credentials: 'same-origin' }, opts, { headers: headers }));
  var text = await resp.text();
  var json;
  try { json = JSON.parse(text); } catch (e) { json = { ok: false, error: { code: 'E_PARSE', message: text } }; }
  if (!resp.ok) throw new Error((json.error && json.error.message) || 'Request failed');
  return json;
}

function formatDate(epochS) {
  return new Date(epochS * 1000).toISOString().slice(0, 16).replace('T', ' ');
}

function makeCell(text) {
  var td = document.createElement('td');
  td.textContent = text;
  return td;
}

document.getElementById('login-btn').onclick = async function () {
  var pw = document.getElementById('password').value;
  var errEl = document.getElementById('login-error');
  errEl.textContent = '';
  try {
    await api('/admin/login', { method: 'POST', body: JSON.stringify({ password: pw }) });
    document.getElementById('login-section').classList.add('hidden');
    document.getElementById('app').classList.remove('hidden');
    refreshTokens();
  } catch (err) {
    errEl.textContent = err.message;
  }
};

document.getElementById('issue-btn').onclick = async function () {
  var facility_id = document.getElementById('facility').value.trim();
  var tablet_label = document.getElementById('label').value.trim();
  var ttl_days = parseInt(document.getElementById('ttl').value, 10);
  if (!facility_id || !tablet_label) { alert('Facility and label are required.'); return; }
  try {
    var resp = await api('/admin/issue-token', {
      method: 'POST',
      body: JSON.stringify({ facility_id: facility_id, tablet_label: tablet_label, ttl_days: ttl_days }),
    });
    document.getElementById('token-display').textContent = resp.token;
    document.getElementById('issue-result').classList.remove('hidden');
    // QR via Google Charts (no bundled JS lib). The token is URL-encoded.
    var qrEl = document.getElementById('qr');
    while (qrEl.firstChild) qrEl.removeChild(qrEl.firstChild);
    var img = document.createElement('img');
    img.alt = 'Token QR';
    img.src = 'https://chart.googleapis.com/chart?cht=qr&chs=240x240&chl=' + encodeURIComponent(resp.token);
    qrEl.appendChild(img);
    refreshTokens();
  } catch (err) {
    alert('Issue failed: ' + err.message);
  }
};

document.getElementById('refresh-btn').onclick = refreshTokens;

async function refreshTokens() {
  var filter = document.getElementById('filter-facility').value.trim();
  var url = '/admin/list' + (filter ? '?facility=' + encodeURIComponent(filter) : '');
  try {
    var resp = await api(url);
    var tbody = document.querySelector('#tokens-table tbody');
    while (tbody.firstChild) tbody.removeChild(tbody.firstChild);
    for (var i = 0; i < resp.tokens.length; i++) {
      var t = resp.tokens[i];
      var tr = document.createElement('tr');
      var nowS = Math.floor(Date.now() / 1000);
      var status = t.revoked_at
        ? 'REVOKED ' + formatDate(t.revoked_at)
        : (t.exp < nowS ? 'EXPIRED' : 'active');
      tr.appendChild(makeCell(formatDate(t.issued_at)));
      tr.appendChild(makeCell(t.facility_id));
      tr.appendChild(makeCell(t.tablet_label));
      tr.appendChild(makeCell(formatDate(t.exp)));
      tr.appendChild(makeCell(status));
      var btnCell = document.createElement('td');
      if (!t.revoked_at && t.exp >= nowS) {
        var btn = document.createElement('button');
        btn.className = 'danger';
        btn.textContent = 'Revoke';
        (function (jti, label) {
          btn.onclick = async function () {
            if (!confirm('Revoke ' + label + '?')) return;
            try {
              await api('/admin/revoke', { method: 'POST', body: JSON.stringify({ jti: jti }) });
              refreshTokens();
            } catch (err) { alert('Revoke failed: ' + err.message); }
          };
        })(t.jti, t.tablet_label);
        btnCell.appendChild(btn);
      }
      tr.appendChild(btnCell);
      tbody.appendChild(tr);
    }
  } catch (err) {
    alert('List failed: ' + err.message);
  }
}
</script>
</body>
</html>`;
}
