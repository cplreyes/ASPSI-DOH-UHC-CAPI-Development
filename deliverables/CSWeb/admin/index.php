<?php
/**
 * CAPI Console — Admin portal shell (E9-ADMIN-020 / -026).
 *
 * Serves the app frame and the two CSRF tokens the two APIs check. Renders no
 * survey data and no account data itself — everything arrives over fetch, so
 * this file has nothing worth leaking.
 *
 * TWO APIS, DELIBERATELY
 *   /docs/admin/api.php   console configuration (activities, alerting, plan).
 *                         Flat envelope, `adm_csrf` cookie. Unchanged.
 *   /docs/idp/admin/...   identity (users, roles, sessions, audit).
 *                         {ok,data,request_id} envelope, `__Host-capi_csrf` cookie.
 *
 * The nav is split the same way, because that split is real: one side edits
 * JSON files on disk, the other decides who may read respondent data.
 */
ini_set('display_errors', '0');

// Identity library. Loaded defensively — this page administered alerts and
// activities long before the provider existed, and a provider outage must
// degrade the access screens, not blank the whole console.
$AUTH_LIB   = is_dir('/var/www/private/capi-auth') ? '/var/www/private/capi-auth' : '';
$AUTH_OK    = false;
if ($AUTH_LIB !== '' && is_file($AUTH_LIB . '/lib.php')) {
    try { require_once $AUTH_LIB . '/lib.php'; $AUTH_OK = true; }
    catch (Throwable $e) { error_log('admin/index.php: identity library unavailable: ' . $e->getMessage()); }
}

// CSRF for the legacy console API. Path-scoped and Strict, as before.
$csrf = bin2hex(random_bytes(16));
setcookie('adm_csrf', $csrf, ['expires' => 0, 'path' => '/docs/admin/',
    'secure' => true, 'httponly' => false, 'samesite' => 'Strict']);

// CSRF for the identity API. Minting it here matters: today an operator
// reaches this page through mod_auth_form, never through the provider's
// sign-in page, so `__Host-capi_csrf` may not exist yet and every write would 403.
if ($AUTH_OK) {
    try { auth_csrf_token(); }
    catch (Throwable $e) { error_log('admin/index.php: csrf mint failed: ' . $e->getMessage()); }
}

/**
 * Who to name in the sidebar.
 *
 * Same precedence as api.php's actor(), and for the same reason: PHP_AUTH_USER
 * and REMOTE_USER both go empty the moment mod_auth_form is retired, so a
 * shell that trusts them renders "Signed in as" followed by nothing on the day
 * of the cutover. Resolved server-side rather than left to the /me fetch so
 * the name is right in the first paint, with no flash of an empty chip.
 */
$user = '';
$hdr  = trim((string) ($_SERVER['HTTP_X_AUTH_USER'] ?? ''));
if ($hdr !== '' && preg_match('/^[A-Za-z0-9._-]{2,64}\z/', $hdr)) {
    $user = $hdr;
} elseif ($AUTH_OK) {
    try {
        $s = auth_session_resolve($_COOKIE[AUTH_COOKIE] ?? null);
        if ($s !== null) { $user = (string) $s['username']; }
    } catch (Throwable $e) { /* fall through to the legacy vars */ }
}
if ($user === '') { $user = (string) ($_SERVER['PHP_AUTH_USER'] ?? $_SERVER['REMOTE_USER'] ?? ''); }

$e = static fn(string $s): string => htmlspecialchars($s, ENT_QUOTES, 'UTF-8');
?><!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>Admin — ASPSI CAPI</title>
<link rel="stylesheet" href="/docs/admin/portal.css">
<link rel="stylesheet" href="/docs/admin/admin.css">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 40 40'%3E%3Crect width='40' height='40' rx='9' fill='%23046a38'/%3E%3Cpath d='M20 9l9 5v12l-9 5-9-5V14z' fill='%23e5b23b'/%3E%3C/svg%3E">
</head>
<body>
<a class="skip" href="#admView">Skip to content</a>
<div class="app">
  <aside class="sidebar">
    <a class="sb-brand" href="https://capi.asiansocial.org/"><span class="sb-mark">A</span>
      <span><b>ASPSI CAPI</b><span>admin console</span></span></a>
    <div class="sb-proj"><div class="sb-proj-card"><div class="k">Signed in as</div>
      <div class="v" id="admWho"><?= $e($user) ?></div></div></div>

    <nav class="sb-nav" aria-label="Admin sections">
      <!-- Access: everything backed by the identity provider. data-perm hides
           an entry the account cannot use; the edge enforces regardless. -->
      <div class="sb-sec">Access</div>
      <a href="#/users"    data-route="users"    data-perm="admin.users"><span>Users &amp; access</span></a>
      <a href="#/roles"    data-route="roles"    data-perm="admin.users"><span>Roles &amp; permissions</span></a>
      <a href="#/sessions" data-route="sessions" data-perm="admin.users"><span>Active sessions</span></a>
      <a href="#/audit"    data-route="audit"    data-perm="audit.view"><span>Audit trail</span></a>

      <!-- Console: file-backed configuration. Nothing here decides access. -->
      <div class="sb-sec">Console</div>
      <a href="#/activities" data-route="activities" data-perm="admin.system"><span>Activities</span></a>
      <a href="#/alerts"     data-route="alerts"     data-perm="admin.system"><span>Alerting</span></a>
      <a href="#/plan"       data-route="plan"       data-perm="admin.system"><span>Assignment plan</span></a>

      <div class="sb-sec">You</div>
      <a href="#/account" data-route="account"><span>My account</span></a>

      <div class="sb-sec">Elsewhere</div>
      <a href="https://capi.asiansocial.org/projects/uhc-y2/"><span>Project overview</span></a>
      <a href="/docs/dashboard.html"><span>Sync dashboard</span></a>
      <a href="/docs/data/"><span>Data room</span></a>
      <a href="/docs/idp/logout"><span>Sign out</span></a>
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
        <p class="lead" id="admLead">Loading&hellip;</p></div>
      <div id="admMsg" aria-live="polite"></div>
      <main id="admView" tabindex="-1"><div class="spin">Loading&hellip;</div></main>
    </div>
  </div>
</div>

<!-- Ordered classic scripts: ui.js defines window.CAPI, each view registers a
     route on it, boot.js starts the router last. No modules, because there is
     no build step on the box and MIME-typed module loading buys nothing here. -->
<script src="/docs/admin/ui.js"></script>
<script src="/docs/admin/view-users.js"></script>
<script src="/docs/admin/view-roles.js"></script>
<script src="/docs/admin/view-sessions.js"></script>
<script src="/docs/admin/view-audit.js"></script>
<script src="/docs/admin/view-account.js"></script>
<script src="/docs/admin/app.js"></script>
<script src="/docs/admin/boot.js"></script>
</body></html>
