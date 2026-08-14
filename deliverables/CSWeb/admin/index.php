<?php
/**
 * CAPI Console — Admin portal shell (E9-ADMIN-020 / -026; re-shelled 2026-08-09
 * for the console unification, Slice 5).
 *
 * Serves the app frame and the two CSRF tokens the two APIs check. Renders no
 * survey data and no account data itself — everything arrives over fetch, so
 * this file has nothing worth leaking.
 *
 * THE CHROME IS GENERATED, NOT WRITTEN HERE. capi_shell_open()/close() come
 * from /var/www/private/capi-shell/shell.php, a mechanical transcription of
 * portal_shell.py rewritten on every portal deploy — hand-copying the nav into
 * PHP is exactly how the console once accumulated five different chromes.
 * The admin's own sections live in an in-canvas subnav (.adm-subnav), which is
 * what ui.js scopes its router and permission-hiding to; the left rail is the
 * site's, dimmed per-account by the shell's own script.
 *
 * TWO APIS, DELIBERATELY
 *   /docs/admin/api.php   console configuration (activities, alerting, plan).
 *                         Flat envelope, `adm_csrf` cookie. Unchanged.
 *   /docs/idp/admin/...   identity (users, roles, sessions, audit).
 *                         {ok,data,request_id} envelope, `__Host-capi_csrf`.
 *
 * SERVED FROM TWO PATHS: directly at /docs/admin/ (redirected by nginx) and
 * proxied at /projects/uhc-y2/admin/ (the canonical URL). That is why
 * `adm_csrf` is Path=/ — a cookie scoped to /docs/admin/ is INVISIBLE to
 * document.cookie when the document lives at the portal path, and the
 * double-submit check would fail with no error anywhere. The API targets keep
 * their absolute /docs/ URLs, so the browser attaches cookies to them
 * regardless of where this page was served from.
 */
ini_set('display_errors', '0');

// Identity library. Loaded defensively — a provider outage must degrade the
// access screens, not blank the whole console.
$AUTH_LIB   = is_dir('/var/www/private/capi-auth') ? '/var/www/private/capi-auth' : '';
$AUTH_OK    = false;
if ($AUTH_LIB !== '' && is_file($AUTH_LIB . '/lib.php')) {
    try { require_once $AUTH_LIB . '/lib.php'; $AUTH_OK = true; }
    catch (Throwable $e) { error_log('admin/index.php: identity library unavailable: ' . $e->getMessage()); }
}

// CSRF for the legacy console API. Path=/ so the token is readable from the
// portal path too — see the header comment. Strict, as before.
$csrf = bin2hex(random_bytes(16));
setcookie('adm_csrf', $csrf, ['expires' => 0, 'path' => '/',
    'secure' => true, 'httponly' => false, 'samesite' => 'Strict']);

// CSRF for the identity API — __Host- cookies are Path=/ by definition.
if ($AUTH_OK) {
    try { auth_csrf_token(); }
    catch (Throwable $e) { error_log('admin/index.php: csrf mint failed: ' . $e->getMessage()); }
}

// The generated shell. If it is missing the console must still say something
// useful rather than emit half a page.
$SHELL = '/var/www/private/capi-shell/shell.php';
if (!is_file($SHELL)) {
    http_response_code(503);
    header('Content-Type: text/plain; charset=utf-8');
    exit("admin console: generated shell partial missing at $SHELL — redeploy the portal (build_portal.py --deploy regenerates it).");
}
require_once $SHELL;

echo capi_shell_open('Admin — ASPSI CAPI', 'Admin',
    '<link rel="stylesheet" href="/docs/admin/admin.css">');
?>
<a class="skip" href="#admView">Skip to content</a>
<div class="page-head"><div class="eyebrow">UHC Survey Year 2</div>
  <h1 id="admTitle">Admin</h1>
  <p class="lead" id="admLead">Loading&hellip;</p></div>

<!-- The admin's own sections. ui.js routes on data-route, hides on data-perm,
     and collapses a group label (.sb-sec) whose entries all hid — all scoped
     to .adm-subnav so the site rail is never touched. -->
<nav class="adm-subnav" aria-label="Admin sections">
  <span class="sb-sec">Access</span>
  <a href="#/users"    data-route="users"    data-perm="admin.users">Users &amp; access</a>
  <a href="#/roles"    data-route="roles"    data-perm="admin.users">Roles &amp; permissions</a>
  <a href="#/sessions" data-route="sessions" data-perm="admin.users">Active sessions</a>
  <a href="#/audit"    data-route="audit"    data-perm="audit.view">Audit trail</a>
  <span class="sb-sec">Console</span>
  <a href="#/activities" data-route="activities" data-perm="admin.system">Activities</a>
  <a href="#/alerts"     data-route="alerts"     data-perm="admin.system">Alerting</a>
  <a href="#/plan"       data-route="plan"       data-perm="admin.system">Assignment plan</a>
  <span class="sb-sec">You</span>
  <a href="#/account" data-route="account">My account</a>
  <a class="adm-guide" href="/docs/admin-portal-guide.html">How to use this portal</a>
</nav>

<div id="admMsg" aria-live="polite"></div>
<main id="admView" tabindex="-1"><div class="spin">Loading&hellip;</div></main>

<!-- Ordered classic scripts: ui.js defines window.CAPI, each view registers a
     route on it, boot.js starts the router last. Absolute /docs/ srcs so the
     same markup works served directly or through the portal-path proxy. -->
<script src="/docs/admin/ui.js"></script>
<script src="/docs/admin/view-users.js"></script>
<script src="/docs/admin/view-roles.js"></script>
<script src="/docs/admin/view-sessions.js"></script>
<script src="/docs/admin/view-audit.js"></script>
<script src="/docs/admin/view-account.js"></script>
<script src="/docs/admin/app.js"></script>
<script src="/docs/admin/boot.js"></script>
<?php echo capi_shell_close(); ?>
