<?php
/**
 * CAPI Console — sign out.                                   Carl, 2026-08-08
 *
 * The point of this file: it REVOKES. Today's logout only drops the browser
 * cookie, so a copy of that cookie keeps working for the remainder of the 8 h
 * session — the replay test passes when it should fail. Here the session row
 * is marked revoked, so the very next request carrying that token is rejected.
 *
 * Accepts GET so a plain link works from the static topbar; that is safe
 * because signing someone out is not a damaging action, and the alternative
 * (JS-only POST) would break sign-out on the generated static pages.
 */
declare(strict_types=1);
ini_set('display_errors', '0');

$AUTH_LIB = is_dir('/var/www/private/capi-auth') ? '/var/www/private/capi-auth' : __DIR__;
require_once $AUTH_LIB . '/lib.php';

header('Cache-Control: no-store');

$token = $_COOKIE[AUTH_COOKIE] ?? null;
if (is_string($token) && $token !== '') {
    try {
        $sess = auth_session_resolve($token);
        auth_session_revoke($token);
        if ($sess !== null) {
            auth_audit((string) $sess['username'], 'logout');
        }
    } catch (Throwable $e) {
        // Clearing the cookie still helps the user even if the DB is down.
        error_log('capi-logout: ' . $e->getMessage());
    }
}
auth_clear_cookie();

header('Location: /docs/idp/login?signedout=1', true, 303);
