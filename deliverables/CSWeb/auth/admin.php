<?php
/**
 * CAPI Console — Admin API front controller (E9-ADMIN-006).   Carl, 2026-08-08
 * Deploy to /opt/app/lamp/www/docs/idp/admin.php
 *
 * Routing only. Every handler lives outside the docroot in
 * /var/www/private/capi-auth so that a webserver misconfiguration exposes this
 * file — twelve lines of dispatch — rather than the logic and the SQL.
 *
 * One controller, not one file per route: there is then exactly one place that
 * decides "is this person allowed", and it cannot be bypassed by adding a file.
 */
declare(strict_types=1);
ini_set('display_errors', '0');

$AUTH_LIB = is_dir('/var/www/private/capi-auth') ? '/var/www/private/capi-auth' : __DIR__;
require_once $AUTH_LIB . '/admin_bootstrap.php';
require_once $AUTH_LIB . '/admin_users.php';
require_once $AUTH_LIB . '/admin_roles.php';
require_once $AUTH_LIB . '/admin_sessions.php';
require_once $AUTH_LIB . '/admin_audit.php';

adm_install_handlers();

/**
 * Segments after /docs/idp/admin.
 *
 * Read from REQUEST_URI rather than PATH_INFO so the same code works whether
 * the rewrite is `^admin(/.*)?$` or the file is hit directly as admin.php —
 * PATH_INFO is empty in the first case, which would silently route everything
 * to the collection endpoint.
 */
$uri  = (string) strtok((string) ($_SERVER['REQUEST_URI'] ?? ''), '?');
$path = preg_replace('#^.*/docs/idp/admin(?:\.php)?#', '', $uri) ?? '';
$seg  = array_values(array_filter(explode('/', trim($path, '/')), static fn($s) => $s !== ''));

// Decode once, here, and never again downstream. Every segment is either
// matched against a literal or cast to int, so nothing that survives this is
// interpolated anywhere.
$seg = array_map('rawurldecode', $seg);

$method   = strtoupper((string) ($_SERVER['REQUEST_METHOD'] ?? 'GET'));
$resource = array_shift($seg) ?? '';

// `/admin/audit.csv` is the documented spelling and the one a browser will
// hand a sensible filename to. Treat it as `/admin/audit/csv`.
if ($resource === 'audit.csv') { $resource = 'audit'; array_unshift($seg, 'csv'); }

switch ($resource) {
    case 'users':    adm_users_route($method, $seg);
    case 'roles':    adm_roles_route($method, $seg);
    case 'sessions': adm_sessions_route($method, $seg);
    case 'audit':    adm_audit_route($method, $seg);

    // A cheap liveness probe for the cutover script: authenticated, no
    // permission, no writes. Answers "is the admin API reachable and is my
    // session good" without touching a single row of user data.
    case 'ping':
        $a = adm_require_perm('');
        adm_ok(['pong' => true, 'user' => $a['username'], 'perms' => $a['perms']]);

    default:
        throw new AdmError('not_found', 'No such endpoint.', 404);
}
