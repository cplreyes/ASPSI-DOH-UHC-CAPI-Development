<?php
/**
 * CAPI Console — DB-backed tests for sessions, throttling and rehash.
 * E9-ADMIN-040.                                                Carl, 2026-08-09
 *
 *   docker compose exec -T webserver php /var/www/private/capi-auth/test_db.php
 *   docker compose exec -T webserver php /var/www/private/capi-auth/test_db.php --verify-clean
 *
 * WRITES TO THE LIVE DATABASE. Every row it creates carries the literal prefix
 * `zzt_`; no real account starts with it, so `LIKE 'zzt\_%'` is an exact
 * predicate and cleanup cannot catch a live account by accident.
 *
 * Cleanup is registered BEFORE the first insert, via register_shutdown_function,
 * so an assertion failure, an uncaught throw or a fatal all still clean up. A
 * test suite that leaves live identity rows behind on failure is worse than no
 * suite: the residue looks like a real account.
 *
 * NOTE ON console_audit: since E9-ADMIN-012 the application user holds only
 * SELECT and INSERT there, so the audit rows these tests generate CANNOT be
 * deleted by this script. That is the point of the grant. They are tagged with
 * a zzt_ actor and left in place.
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
    printf("FAIL  %-52s got %s  want %s\n", $what, var_export($got, true), var_export($want, true));
}

// ---------------------------------------------------------------------------
// Cleanup, registered first.
// ---------------------------------------------------------------------------
function zzt_cleanup(): void
{
    try {
        $db = auth_db();
        // console_sessions and console_user_roles cascade from console_users.
        $db->prepare('DELETE FROM console_users WHERE username LIKE ?')->execute(['zzt\_%']);
        $db->prepare('DELETE FROM console_roles WHERE name LIKE ?')->execute(['zzt\_%']);
    } catch (Throwable $e) {
        fwrite(STDERR, "CLEANUP FAILED: " . $e->getMessage() . "\n");
    }
}
register_shutdown_function('zzt_cleanup');

function zzt_count_leftovers(): int
{
    $db = auth_db();
    $n  = 0;
    $n += (int) $db->query("SELECT COUNT(*) FROM console_users WHERE username LIKE 'zzt\\_%'")->fetchColumn();
    $n += (int) $db->query("SELECT COUNT(*) FROM console_roles WHERE name LIKE 'zzt\\_%'")->fetchColumn();
    $n += (int) $db->query('SELECT COUNT(*) FROM console_sessions WHERE user_id NOT IN (SELECT id FROM console_users)')->fetchColumn();
    return $n;
}

if (in_array('--verify-clean', $argv, true)) {
    $n = zzt_count_leftovers();
    printf("leftover test rows: %d\n", $n);
    exit($n === 0 ? 0 : 1);
}

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------
$db = auth_db();
zzt_cleanup();                                   // start from a known state

/** Create a zzt_ user; returns its id. */
function zzt_user(string $name, string $pw, string $algo = 'argon2id', array $roles = []): int
{
    $db   = auth_db();
    $hash = $algo === 'apr1' ? auth_apr1_crypt($pw, 'zzt12345') : auth_hash_password($pw);
    $db->prepare(
        'INSERT INTO console_users (username, full_name, pw_hash, pw_algo, must_change, status, created_by)
         VALUES (?, "db test", ?, ?, 0, "active", "test_db")'
    )->execute([$name, $hash, $algo]);
    $id = (int) $db->lastInsertId();

    foreach ($roles as $r) {
        $db->prepare(
            'INSERT INTO console_user_roles (user_id, role_id) SELECT ?, id FROM console_roles WHERE name = ?'
        )->execute([$id, $r]);
    }
    return $id;
}

function zzt_age_session(string $sidHash, string $column, int $secondsAgo): void
{
    // Column name is from a literal in this file only — never from input.
    auth_db()->prepare(
        "UPDATE console_sessions SET $column = DATE_SUB(NOW(), INTERVAL ? SECOND) WHERE sid_hash = ?"
    )->execute([$secondsAgo, $sidHash]);
}

// ---------------------------------------------------------------------------
// Sessions: create and resolve
// ---------------------------------------------------------------------------
$uid = zzt_user('zzt_sess', 'a-long-test-password', 'argon2id', ['field_supervisor']);
$tok = auth_session_create($uid, '203.0.113.5', 'zzt-agent/1.0');
$sid = auth_sid_hash($tok);

$s = auth_session_resolve($tok);
check('resolve returns the session',   $s !== null, true);
check('resolve carries the username',  $s['username'] ?? null, 'zzt_sess');
check('resolve carries roles',         $s['roles'] ?? null, ['field_supervisor']);
check('resolve carries perms (sorted)',$s['perms'] ?? null, ['case.view', 'monitoring.view', 'tabulations.view']);
check('bad token resolves to null',    auth_session_resolve('not-a-real-token'), null);
check('null token resolves to null',   auth_session_resolve(null), null);
check('empty token resolves to null',  auth_session_resolve(''), null);

// ---------------------------------------------------------------------------
// Sessions: the three expiry tests, at their boundaries
// ---------------------------------------------------------------------------
zzt_age_session($sid, 'last_seen_at', AUTH_IDLE_SECS - 30);
check('inside the idle window survives',  auth_session_resolve($tok) !== null, true);

zzt_age_session($sid, 'last_seen_at', AUTH_IDLE_SECS + 30);
check('past the idle window dies',        auth_session_resolve($tok), null);

zzt_age_session($sid, 'last_seen_at', 5);         // revive
check('revived after touching last_seen', auth_session_resolve($tok) !== null, true);

zzt_age_session($sid, 'expires_at', 60);          // absolute expiry an hour ago
check('past the absolute ceiling dies',   auth_session_resolve($tok), null);

// A fresh session for the remaining cases.
$tok = auth_session_create($uid, '203.0.113.5', 'zzt-agent/1.0');
$sid = auth_sid_hash($tok);
check('fresh session resolves',           auth_session_resolve($tok) !== null, true);

// ---------------------------------------------------------------------------
// Sessions: revocation — the capability the old cookie could not provide
// ---------------------------------------------------------------------------
auth_session_revoke($tok);
check('revoked session dies',             auth_session_resolve($tok), null);

$t1 = auth_session_create($uid, '203.0.113.5', 'a');
$t2 = auth_session_create($uid, '203.0.113.6', 'b');
check('two live sessions resolve',
      auth_session_resolve($t1) !== null && auth_session_resolve($t2) !== null, true);
// Two sessions are LIVE here. An earlier session for this user was left
// expired-but-unrevoked by the ceiling test above, and revoke_user sweeps it
// too — but must not COUNT it, because the count is what an operator was
// promised by the confirmation dialog.
$n = auth_session_revoke_user($uid);
check('revoke_user counts live only',     $n, 2);
check('both sessions now dead',
      auth_session_resolve($t1) === null && auth_session_resolve($t2) === null, true);
check('revoke_user replay reports 0',     auth_session_revoke_user($uid), 0);

// ---------------------------------------------------------------------------
// Sessions: a disabled account cannot resolve, and neither can a role change
// ---------------------------------------------------------------------------
$t3 = auth_session_create($uid, '203.0.113.5', 'c');
check('session before disable',           auth_session_resolve($t3) !== null, true);
$db->prepare('UPDATE console_users SET status = "disabled" WHERE id = ?')->execute([$uid]);
check('disabled account cannot resolve',  auth_session_resolve($t3), null);
$db->prepare('UPDATE console_users SET status = "active" WHERE id = ?')->execute([$uid]);
check('re-enabled account resolves again',auth_session_resolve($t3) !== null, true);

// The role-version check. This is the mechanism that makes a permission edit
// take effect immediately instead of at next sign-in, and it is computed by a
// correlated subquery that is easy to get wrong (E9-ADMIN-030).
$db->exec('UPDATE console_roles SET version = version + 1 WHERE name = "field_supervisor"');
check('role version bump kills the session', auth_session_resolve($t3), null);

// ---------------------------------------------------------------------------
// Lazy rehash: an $apr1$ account upgrades to argon2id on a correct sign-in
// ---------------------------------------------------------------------------
$legacyPw = 'legacy-test-password';
$lid = zzt_user('zzt_legacy', $legacyPw, 'apr1');
$row = auth_find_user('zzt_legacy');
check('legacy user stored as apr1',       $row['pw_algo'] ?? null, 'apr1');
check('legacy hash has the apr1 prefix',  str_starts_with((string) $row['pw_hash'], '$apr1$'), true);

check('wrong password does not verify',   auth_verify_password($row, 'not-it'), false);
$after = auth_find_user('zzt_legacy');
check('a failed attempt does NOT rehash', $after['pw_algo'], 'apr1');

check('correct password verifies',        auth_verify_password($row, $legacyPw), true);
$after = auth_find_user('zzt_legacy');
check('success upgraded the algorithm',   $after['pw_algo'], 'argon2id');
check('success upgraded the hash',        str_starts_with((string) $after['pw_hash'], '$argon2id$'), true);
check('the upgraded hash still verifies', auth_verify_password($after, $legacyPw), true);
check('the upgraded hash rejects wrong',  auth_verify_password($after, 'not-it'), false);

// ---------------------------------------------------------------------------
// Per-account throttle and lockout
// ---------------------------------------------------------------------------
$tid = zzt_user('zzt_lock', 'a-long-test-password');
$u   = auth_find_user('zzt_lock');
check('starts unlocked',                  auth_lock_remaining($u), 0);

for ($i = 1; $i < AUTH_MAX_FAILS; $i++) { auth_note_failure(auth_find_user('zzt_lock')); }
$u = auth_find_user('zzt_lock');
check('below the ceiling, not locked',    auth_lock_remaining($u), 0);
check('failures were counted',            (int) $u['failed_count'], AUTH_MAX_FAILS - 1);

auth_note_failure($u);                                   // the one that trips it
$u = auth_find_user('zzt_lock');
check('at the ceiling, locked',           auth_lock_remaining($u) > 0, true);
check('counter reset on lockout',         (int) $u['failed_count'], 0);

auth_note_success($tid);
$u = auth_find_user('zzt_lock');
check('success clears the lockout',       auth_lock_remaining($u), 0);
check('success records last_login_at',    $u['last_login_at'] !== null, true);

// ---------------------------------------------------------------------------
// Per-IP throttle (E9-ADMIN-011)
// ---------------------------------------------------------------------------
// 198.51.100.0/24 is TEST-NET-2 and can never be a real client.
$probeIp = '198.51.100.' . random_int(2, 250);
check('unseen IP starts at zero',         auth_ip_fail_count($probeIp), 0);
check('unseen IP is not blocked',         auth_ip_blocked($probeIp), false);

$ins = $db->prepare('INSERT INTO console_audit (actor, verb, target, ip) VALUES ("zzt_spray","login.fail","",?)');
for ($i = 0; $i < AUTH_IP_MAX_FAILS - 1; $i++) { $ins->execute([$probeIp]); }
check('one below the ceiling',            auth_ip_blocked($probeIp), false);
$ins->execute([$probeIp]);
check('at the ceiling, blocked',          auth_ip_blocked($probeIp), true);
check('count is exact',                   auth_ip_fail_count($probeIp), AUTH_IP_MAX_FAILS);
check('a different IP is unaffected',     auth_ip_blocked('198.51.100.251'), false);
// Those audit rows cannot be deleted by this user by design (E9-ADMIN-012).
// They are tagged zzt_spray on a TEST-NET address.

// ---------------------------------------------------------------------------
// auth_user_grants still agrees with what the session carries
// ---------------------------------------------------------------------------
$gid = zzt_user('zzt_grants', 'a-long-test-password', 'argon2id', ['analyst']);
$g   = auth_user_grants($gid);
check('grants roles',  $g['roles'], ['analyst']);
sort($g['perms']);
check('grants perms',  $g['perms'], ['case.view', 'data.export', 'monitoring.view', 'tabulations.view']);
$gt = auth_session_create($gid, '203.0.113.9', 'g');
$gs = auth_session_resolve($gt);
check('session perms == grants perms', $gs['perms'], $g['perms']);
check('session roles == grants roles', $gs['roles'], $g['roles']);

// A user with no roles at all: must resolve, but reach nothing.
$nid = zzt_user('zzt_noroles', 'a-long-test-password');
$nt  = auth_session_create($nid, '203.0.113.10', 'n');
$ns  = auth_session_resolve($nt);
check('roleless session still resolves', $ns !== null, true);
check('roleless session has no roles',   $ns['roles'], []);
check('roleless session has no perms',   $ns['perms'], []);

// ---------------------------------------------------------------------------
zzt_cleanup();
$left = zzt_count_leftovers();
check('cleanup left nothing behind', $left, 0);

printf("\n%d passed, %d failed\n", $pass, $fail);
exit($fail === 0 ? 0 : 1);
