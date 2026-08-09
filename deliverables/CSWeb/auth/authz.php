<?php
/**
 * CAPI Console — the single authorization decision point.     Carl, 2026-08-08
 * Plan: capi-console-idp-option-c-plan.md §3.5–3.6
 *
 * Called by openresty as an `auth_request` subrequest for BOTH `/` (the static
 * portal) and `/docs/` (the console tree). One decision point replaces the two
 * that disagree today: nginx auth_request on `/`, Apache FilesMatch on /docs/.
 *
 * Contract with nginx (auth_request only reads the status code and headers —
 * the body is discarded, so never rely on it):
 *
 *   204  allow          + X-Auth-User, X-Auth-Roles
 *   401  no session     -> nginx redirects to the sign-in page
 *   403  signed in but not allowed, with X-Auth-Reason:
 *          forbidden    -> access denied page
 *          pwchange     -> redirect to the change-password page
 *
 * Anything other than 2xx/401/403 makes nginx emit a 500, so every failure
 * path here is explicit and nothing is left to an uncaught exception.
 */
declare(strict_types=1);
ini_set('display_errors', '0');

// In production the library and the ACL live OUTSIDE the docroot, so a future
// gate mistake cannot expose them; the __DIR__ fallback keeps a flat checkout
// (and the test runner) working. Deploy target: /opt/app/lamp/private ->
// /var/www/private, bind-mounted like the docroot so it survives recreation.
$AUTH_LIB = is_dir('/var/www/private/capi-auth') ? '/var/www/private/capi-auth' : __DIR__;
require_once $AUTH_LIB . '/acl.php';
require_once $AUTH_LIB . '/lib.php';

header('Cache-Control: no-store');

/** Terminate with a status and no body. */
function decide(int $code, array $headers = []): never
{
    http_response_code($code);
    foreach ($headers as $k => $v) { header($k . ': ' . $v); }
    exit;
}

// The path being authorized is the ORIGINAL request, not this subrequest.
// nginx must send it; without the header we cannot know what is being asked
// for, and guessing would be a bypass — so refuse.
$orig = $_SERVER['HTTP_X_ORIGINAL_URI'] ?? '';
if ($orig === '') {
    error_log('capi-authz: X-Original-URI missing — check the nginx location block');
    decide(403, ['X-Auth-Reason' => 'forbidden']);
}

$need = acl_required_perm($orig);

// Fast path: public routes never touch the database. This matters because the
// subrequest runs for every asset on every page, and the sign-in page itself
// must load when the database is unreachable.
if ($need === 'PUBLIC') {
    decide(204);
}

try {
    $sess = auth_session_resolve($_COOKIE[AUTH_COOKIE] ?? null);
} catch (Throwable $e) {
    // Database down. Fail CLOSED — but with 503, not 401: a 401 would bounce
    // everyone to a sign-in page that also cannot work, which reads to the user
    // as "my password stopped working" instead of "the service is down".
    error_log('capi-authz: ' . $e->getMessage());
    decide(503);
}

if ($sess === null) {
    decide(401);
}

$user = (string) $sess['username'];

// A user who owes a password change is barred from everything except changing
// it. Same rule as F2's `pwc` claim, and the reason it exists: on this estate
// `password_must_change` was stored but never enforced, which is how a default
// password stayed live on an admin account.
if ((int) $sess['must_change'] === 1 && $need !== 'PWCHANGE') {
    decide(403, ['X-Auth-Reason' => 'pwchange', 'X-Auth-User' => $user]);
}

if ($need === 'DENY') {
    auth_audit($user, 'perm.deny', $orig, ['reason' => 'no rule']);
    decide(403, ['X-Auth-Reason' => 'forbidden', 'X-Auth-User' => $user]);
}

// Roles and permissions arrived with the session in the same query
// (E9-ADMIN-030) — no second round trip on the hot path.
$allowHeaders = [
    'X-Auth-User'  => $user,
    'X-Auth-Roles' => implode(',', $sess['roles']),
];

// AUTH and PWCHANGE need a valid session and nothing more.
if ($need === 'AUTH' || $need === 'PWCHANGE') {
    decide(204, $allowHeaders);
}

if (!in_array($need, $sess['perms'], true)) {
    auth_audit($user, 'perm.deny', $orig, ['need' => $need]);
    decide(403, ['X-Auth-Reason' => 'forbidden', 'X-Auth-User' => $user]);
}

// Allowed. Record reads of respondent data and bulk microdata — the gap that
// matters most now that case viewers were widened to field logins, and the
// question a data-protection query will actually ask.
if (acl_is_auditable_read($orig)) {
    auth_audit($user, 'read', $orig, ['perm' => $need]);
}

decide(204, $allowHeaders);
