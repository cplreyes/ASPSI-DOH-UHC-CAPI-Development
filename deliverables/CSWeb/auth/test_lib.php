<?php
/**
 * CAPI Console — unit tests for lib.php's pure functions.      Carl, 2026-08-09
 * E9-ADMIN-040.
 *
 *   docker compose exec -T webserver php /var/www/private/capi-auth/test_lib.php
 *
 * DB-free. The DB-backed behaviour (sessions, throttle, lazy rehash) is
 * test_db.php, which needs disposable rows.
 *
 * THE REASON THIS FILE EXISTS IS auth_apr1_crypt().
 * Fifteen of the eighteen imported accounts still carry `$apr1$` hashes. PHP's
 * crypt() does not implement that variant, so the algorithm is hand-written in
 * lib.php — and a hand-written digest that is subtly wrong locks out fifteen
 * people at once, with a "wrong password" message that gives no hint why.
 * Nothing else in the codebase exercises it.
 *
 * The vectors below were produced by `openssl passwd -apr1 -salt <salt> <pw>`
 * on the production host on 2026-08-09. That matters: they come from a
 * DIFFERENT implementation, so this is a real cross-check rather than the
 * function agreeing with itself.
 */
declare(strict_types=1);

require_once __DIR__ . '/lib.php';

$pass = 0;
$fail = 0;

function check(string $what, $got, $want): void
{
    global $pass, $fail;
    if ($got === $want) { $pass++; return; }
    $fail++;
    printf("FAIL  %-46s\n        got  %s\n        want %s\n", $what, var_export($got, true), var_export($want, true));
}

// ---------------------------------------------------------------------------
// auth_apr1_crypt — cross-checked against OpenSSL
// ---------------------------------------------------------------------------
$vectors = [
    // salt,       password,                        expected (openssl passwd -apr1)
    ['salt1234',  'password',                       '$apr1$salt1234$k3J5yKYW6TlGmTytnkXbQ0'],
    // The setup password this estate actually shipped with — worth pinning.
    ['abcdefgh',  '100%SetupMe!',                   '$apr1$abcdefgh$hQZBO9CiKUQriMAUIOdDg1'],
    // Long, with spaces: exercises the length loop past one MD5 block.
    ['xY9zAb2c',  'correct horse battery staple',   '$apr1$xY9zAb2c$bAd16fP7ECUr1Z2rAEpDI0'],
    // Short salt. Apache pads/uses it as-is; a wrong assumption here breaks a
    // subset of accounts rather than all of them, which is worse to diagnose.
    ['Zz01',      'short',                          '$apr1$Zz01$g20N7fcqIILbd2ze6AU4p.'],
    // Empty password — the degenerate case the length loop can divide by.
    ['12345678',  '',                               '$apr1$12345678$sHuPAw7VA9xjRbJz7zKV7/'],
    // Multi-byte UTF-8. This estate has ñ in real data (Biñan), and a byte vs
    // character mix-up in the loop would only show up on those accounts.
    ['aB3dEf7h',  'ñoño-Biñan-2026',                '$apr1$aB3dEf7h$OJoF0kih3ZLkDaWFXmrXH1'],
];

foreach ($vectors as [$salt, $pw, $want]) {
    check('apr1(' . $salt . ', ' . ($pw === '' ? '<empty>' : substr($pw, 0, 18)) . ')',
          auth_apr1_crypt($pw, $salt), $want);
}

// Salt longer than 8 characters must be truncated to 8, the same way Apache
// does — otherwise every hash we verify against a long-salt file misses.
check('apr1 truncates salt to 8',
      auth_apr1_crypt('password', 'salt1234EXTRA'),
      auth_apr1_crypt('password', 'salt1234'));

// A wrong password must not collide.
check('apr1 rejects a near-miss',
      auth_apr1_crypt('passwore', 'salt1234') === '$apr1$salt1234$k3J5yKYW6TlGmTytnkXbQ0',
      false);

// ---------------------------------------------------------------------------
// auth_verify_password — algorithm dispatch (no DB write path exercised here;
// the lazy-rehash UPDATE is covered in test_db.php)
// ---------------------------------------------------------------------------
$apr1User = ['id' => 0, 'username' => 'zzt', 'pw_algo' => 'apr1',
             'pw_hash' => '$apr1$salt1234$k3J5yKYW6TlGmTytnkXbQ0'];

// Dispatch is asserted through a pure comparison rather than the real function,
// because auth_verify_password() would try to rehash on success and that needs
// a database. What matters here is that the digest matches.
check('apr1 hash matches its own password',
      hash_equals($apr1User['pw_hash'], auth_apr1_crypt('password', 'salt1234')), true);
check('apr1 hash rejects a wrong password',
      hash_equals($apr1User['pw_hash'], auth_apr1_crypt('wrong', 'salt1234')), false);

// bcrypt and argon2id go through password_verify, which is PHP's own.
$bcrypt = password_hash('a-test-password', PASSWORD_BCRYPT);
check('bcrypt verifies',  password_verify('a-test-password', $bcrypt), true);
check('bcrypt rejects',   password_verify('other', $bcrypt), false);
$argon = auth_hash_password('a-test-password');
check('argon2id is argon2id', str_starts_with($argon, '$argon2id$'), true);
check('argon2id verifies', password_verify('a-test-password', $argon), true);
check('argon2id needs no rehash', password_needs_rehash($argon, PASSWORD_ARGON2ID), false);
check('bcrypt DOES need rehash to argon2id', password_needs_rehash($bcrypt, PASSWORD_ARGON2ID), true);

// ---------------------------------------------------------------------------
// auth_password_problem — policy
// ---------------------------------------------------------------------------
$ok = '';
check('12 chars accepted',        auth_password_problem('abcdefghijkl', 'carl') === $ok, true);
check('11 chars rejected',        auth_password_problem('abcdefghijk', 'carl') === $ok, false);
check('empty rejected',           auth_password_problem('', 'carl') === $ok, false);
check('257 chars rejected',       auth_password_problem(str_repeat('a', 257), 'carl') === $ok, false);
check('256 chars accepted',       auth_password_problem(str_repeat('a', 256), 'carl') === $ok, true);
check('contains username',        auth_password_problem('xxcarlxxxxxxxx', 'carl') === $ok, false);
check('username case-insensitive',auth_password_problem('xxCARLxxxxxxxx', 'carl') === $ok, false);
// The two defaults this estate actually shipped and left live.
check('rejects 100%SetupMe!',     auth_password_problem('100%SetupMe!', 'carl') === $ok, false);
check('rejects 100%ChangeMe!',    auth_password_problem('100%ChangeMe!', 'carl') === $ok, false);
check('rejects a capi phrase',    auth_password_problem('capi-console-2026', 'carl') === $ok, false);
check('rejects an aspsi phrase',  auth_password_problem('aspsi-survey-2026', 'carl') === $ok, false);
check('rejects 123456 inside',    auth_password_problem('zzz123456zzzz', 'carl') === $ok, false);
check('empty username not matched', auth_password_problem('abcdefghijkl', '') === $ok, true);

// ---------------------------------------------------------------------------
// auth_sid_hash — the stored value must never be the token
// ---------------------------------------------------------------------------
$tok = auth_session_token();
check('token is url-safe',        (bool) preg_match('/^[A-Za-z0-9_-]+\z/', $tok), true);
check('token is long enough',     strlen($tok) >= 43, true);
check('sid hash is sha256 hex',   (bool) preg_match('/^[0-9a-f]{64}\z/', auth_sid_hash($tok)), true);
check('sid hash != token',        auth_sid_hash($tok) === $tok, false);
check('sid hash is stable',       auth_sid_hash($tok), auth_sid_hash($tok));
check('tokens are distinct',      auth_session_token() === auth_session_token(), false);

// ---------------------------------------------------------------------------
// auth_timing_floor — the login response-time floor (E9-ADMIN-011)
// ---------------------------------------------------------------------------
$t0 = hrtime(true);
auth_timing_floor($t0, 60);
$elapsedMs = (hrtime(true) - $t0) / 1e6;
check('floor waits at least 60ms', $elapsedMs >= 59.0, true);
check('floor does not overshoot wildly', $elapsedMs < 200.0, true);

// Already past the floor: must return promptly rather than adding to it.
$t1 = hrtime(true) - (int) (500 * 1e6);   // pretend 500 ms have passed
$before = hrtime(true);
auth_timing_floor($t1, 60);
check('floor is a floor, not a delay', (hrtime(true) - $before) / 1e6 < 20.0, true);

// ---------------------------------------------------------------------------
// auth_csrf_ok — constant-time compare against the cookie
// ---------------------------------------------------------------------------
$_COOKIE[AUTH_CSRF_COOKIE] = 'a-known-token';
check('csrf matches',            auth_csrf_ok('a-known-token'), true);
check('csrf rejects wrong',      auth_csrf_ok('other-token'), false);
check('csrf rejects null',       auth_csrf_ok(null), false);
check('csrf rejects empty',      auth_csrf_ok(''), false);
check('csrf rejects prefix',     auth_csrf_ok('a-known'), false);
$_COOKIE[AUTH_CSRF_COOKIE] = '';
check('no cookie means no pass', auth_csrf_ok(''), false);
check('no cookie rejects any',   auth_csrf_ok('anything'), false);

// ---------------------------------------------------------------------------
// auth_lock_remaining
// ---------------------------------------------------------------------------
check('no lock',        auth_lock_remaining(['locked_until' => null]), 0);
check('empty lock',     auth_lock_remaining(['locked_until' => '']), 0);
check('past lock',      auth_lock_remaining(['locked_until' => gmdate('Y-m-d H:i:s', time() - 60)]), 0);
$left = auth_lock_remaining(['locked_until' => gmdate('Y-m-d H:i:s', time() + 300)]);
check('future lock is positive', $left > 0 && $left <= 300, true);

printf("\n%d passed, %d failed\n", $pass, $fail);
exit($fail === 0 ? 0 : 1);
