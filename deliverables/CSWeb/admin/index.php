<?php
/**
 * CAPI Console — Admin (SPA shell).
 * Serves the app frame + issues the CSRF token the API checks. All data flows
 * through api.php; this file renders no survey data itself.
 */
ini_set('display_errors', '0');
$csrf = bin2hex(random_bytes(16));
setcookie('adm_csrf', $csrf, ['expires' => 0, 'path' => '/docs/admin/',
    'secure' => true, 'httponly' => false, 'samesite' => 'Strict']);
$user = $_SERVER['PHP_AUTH_USER'] ?? $_SERVER['REMOTE_USER'] ?? '';
?><!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>Admin — ASPSI CAPI</title>
<link rel="stylesheet" href="/docs/admin/portal.css">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 40 40'%3E%3Crect width='40' height='40' rx='9' fill='%23046a38'/%3E%3Cpath d='M20 9l9 5v12l-9 5-9-5V14z' fill='%23e5b23b'/%3E%3C/svg%3E">
<style>
.adm-tabs{display:flex;gap:4px;border-bottom:1px solid var(--line);margin-bottom:20px;flex-wrap:wrap}
.adm-tabs button{background:none;border:0;border-bottom:2px solid transparent;padding:9px 15px;
  font:600 13.5px var(--sans);color:var(--ink-3);cursor:pointer}
.adm-tabs button:hover{color:var(--verde)}
.adm-tabs button.on{color:var(--verde-900);border-bottom-color:var(--verde)}
.adm-card{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);
  padding:18px 20px;box-shadow:var(--shadow-1);margin-bottom:16px}
.adm-card h3{font-size:15.5px;color:var(--verde-900);margin-bottom:4px}
.adm-card .sub{font-size:12.5px;color:var(--ink-3);margin-bottom:12px}
.adm-f{display:flex;gap:10px;flex-wrap:wrap;align-items:flex-end;margin-bottom:10px}
.adm-f label{display:flex;flex-direction:column;gap:4px;font-size:11px;font-weight:700;
  letter-spacing:.09em;text-transform:uppercase;color:var(--ink-3)}
input,select{font:13.5px var(--sans);padding:7px 9px;border:1px solid var(--line-strong);
  border-radius:8px;background:#fff;color:var(--ink)}
input:focus,select:focus{outline:2px solid var(--verde-300);outline-offset:0}
.btn{background:var(--verde);color:#fff;font:700 13px var(--sans);border:0;border-radius:8px;
  padding:9px 16px;cursor:pointer}
.btn:hover{background:var(--verde-700)}
.btn.sec{background:var(--surface);color:var(--ink-2);border:1px solid var(--line-strong)}
.btn.sec:hover{background:var(--surface-2);color:var(--verde)}
.btn.danger{background:#b91c1c}.btn.danger:hover{background:#991b1b}
.btn:disabled{opacity:.5;cursor:not-allowed}
.msg{border-radius:9px;padding:10px 14px;margin-bottom:14px;font-size:13.5px;font-weight:600}
.msg.ok{background:#eefaf3;color:#047857;border:1px solid #b9e2cb}
.msg.err{background:#fdecea;color:#b91c1c;border:1px solid #f5c6c0}
.pillt{font-size:10px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;
  padding:2px 8px;border-radius:6px;white-space:nowrap}
.pillt.field{background:var(--verde-100);color:var(--verde);border:1px solid #cfe6d8}
.pillt.staff{background:#eef2ff;color:#3730a3;border:1px solid #c7d2fe}
.pillt.admin{background:#fdf7e8;color:var(--lock);border:1px solid #f0dcae}
.pillt.none{background:#f1f5f9;color:var(--muted);border:1px solid #dde5ec}
.mono{font-family:var(--mono);font-size:12.5px}
.muted{color:var(--ink-3);font-size:12.5px}
.rowacts{display:flex;gap:6px;flex-wrap:wrap}
.rowacts button{font-size:11.5px;padding:5px 10px}
.audit{font-family:var(--mono);font-size:11.5px;line-height:1.7;max-height:460px;overflow:auto}
.audit b{color:var(--verde-900)}
.spin{color:var(--ink-3);font-size:13px;padding:12px 0}
</style></head>
<body>
<div class="app">
  <aside class="sidebar">
    <a class="sb-brand" href="https://capi.asiansocial.org/"><span class="sb-mark">A</span>
      <span><b>ASPSI CAPI</b><span>admin console</span></span></a>
    <div class="sb-proj"><div class="sb-proj-card"><div class="k">Signed in as</div>
      <div class="v"><?= htmlspecialchars($user, ENT_QUOTES) ?></div></div></div>
    <nav class="sb-nav">
      <div class="sb-sec">Admin</div>
      <a href="#" data-tab="activities"><span>Activities</span></a>
      <a href="#" data-tab="users"><span>Users &amp; access</span></a>
      <a href="#" data-tab="alerts"><span>Alerting</span></a>
      <a href="#" data-tab="plan"><span>Assignment plan</span></a>
      <a href="#" data-tab="audit"><span>Audit trail</span></a>
      <div class="sb-sec">Console</div>
      <a href="https://capi.asiansocial.org/projects/uhc-y2/"><span>Project overview</span></a>
      <a href="/docs/dashboard.html"><span>Sync dashboard</span></a>
      <a href="/docs/data/"><span>Data room</span></a>
    </nav>
    <div class="sb-foot">Asian Social Project Services, Inc.<br>
      <a href="https://asiansocial.org">asiansocial.org</a>
      <div class="sb-powered">Powered by Analytiflow.</div></div>
  </aside>
  <div class="main">
    <div class="topbar"><div class="crumbs"><a href="https://capi.asiansocial.org/">Console</a>
      <span class="sep">/</span><span class="cur">Admin</span></div>
      <div class="tb-right"><span class="pill lock">&#128274; Admin only</span></div></div>
    <div class="canvas">
      <div class="page-head"><div class="eyebrow">UHC Survey Year 2</div>
        <h1 id="admTitle">Admin</h1>
        <p class="lead" id="admLead">Manage what the console runs on. Every change here is
        recorded in the audit trail and reaches the live surfaces within about two minutes.</p></div>
      <div class="adm-tabs" id="admTabs"></div>
      <div id="admMsg"></div>
      <div id="admView"><div class="spin">Loading&hellip;</div></div>
    </div>
  </div>
</div>
<script src="/docs/admin/app.js"></script>
</body></html>
