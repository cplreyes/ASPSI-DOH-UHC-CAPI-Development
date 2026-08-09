<?php
/**
 * CAPI Console — "who am I, and what may I reach".           Carl, 2026-08-08
 *
 * Successor to /docs/whoami.php. Same job for the topbar chip on the generated
 * static pages, but the answer now comes from roles in the database instead of
 * being reverse-engineered from `Require user` lines in .htaccess.
 *
 * IMPORTANT: this is for RENDERING ONLY. Hiding a nav link is cosmetic — the
 * edge still enforces via authz.php, so a user who types the URL is refused
 * regardless of what this returns. Never treat it as a security boundary.
 */
declare(strict_types=1);
ini_set('display_errors', '0');

$AUTH_LIB = is_dir('/var/www/private/capi-auth') ? '/var/www/private/capi-auth' : __DIR__;
require_once $AUTH_LIB . '/lib.php';

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');

try {
    $sess = auth_session_resolve($_COOKIE[AUTH_COOKIE] ?? null);
} catch (Throwable $e) {
    error_log('capi-me: ' . $e->getMessage());
    http_response_code(503);
    echo json_encode(['signed_in' => false, 'error' => 'unavailable']);
    exit;
}

if ($sess === null) {
    http_response_code(401);
    echo json_encode(['signed_in' => false, 'user' => null]);
    exit;
}

// Carried on the session by auth_session_resolve (E9-ADMIN-030); this endpoint
// is fetched by the topbar of every generated page, so the saved round trip is
// not academic.
$grants = ['roles' => $sess['roles'], 'perms' => $sess['perms']];
$perms  = $grants['perms'];

// Legacy `tier`, kept for backward compatibility. Every generated page's topbar
// chip does `fetch('/docs/whoami.php').then(d => … d.tier)` — see
// portal_shell.py:140 (two copies) and csweb-responses-gen.py:427 — and each of
// those fetches ends in an EMPTY .catch(), so an absent field does not error, it
// just silently blanks the chip on every page. Emitting `tier` here lets those
// pages be repointed at /docs/idp/me one at a time instead of in a flag day.
// Same precedence the old whoami.php used: admin > staff > field.
$tier = 'none';
if (in_array('monitoring.view', $perms, true))                { $tier = 'field'; }
if (in_array('data.export', $perms, true))                    { $tier = 'staff'; }
if (in_array('admin.system', $perms, true)
 || in_array('admin.users', $perms, true))                    { $tier = 'admin'; }

echo json_encode([
    'signed_in'   => true,
    'user'        => $sess['username'],
    'roles'       => $grants['roles'],
    'perms'       => $perms,
    'must_change' => (int) $sess['must_change'] === 1,
    // Convenience booleans so the static pages don't each reimplement the
    // mapping from permission to menu item.
    'can'         => [
        'monitoring'  => in_array('monitoring.view', $perms, true),
        'cases'       => in_array('case.view', $perms, true),
        'data_room'   => in_array('data.export', $perms, true),
        'tabulations' => in_array('tabulations.view', $perms, true),
        'admin'       => in_array('admin.system', $perms, true)
                      || in_array('admin.users', $perms, true),
        'audit'       => in_array('audit.view', $perms, true),
    ],
    'logout'      => '/docs/idp/logout',
], JSON_UNESCAPED_SLASHES);
