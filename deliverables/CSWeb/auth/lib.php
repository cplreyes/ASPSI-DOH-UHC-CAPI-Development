<?php
/**
 * CAPI Console identity provider — core library.              Carl, 2026-08-08
 * Plan: capi-console-idp-option-c-plan.md §3
 *
 * Everything that touches credentials or sessions lives here so there is one
 * place to review. No HTML, no echo — callers own their own output.
 *
 * Credentials come from the environment (set on the `webserver` service in
 * /opt/app/docker-compose.yml, which is host-mounted and therefore survives
 * container recreation). A file fallback is supported for local testing only.
 * The DB user is NOT root: it holds grants on `capi_auth` and nothing else, so
 * a flaw here cannot reach CSWeb's tables or the csweb_f2 mirror.
 */
declare(strict_types=1);

/**
 * Session cookie name (E9-ADMIN-045).
 *
 * The `__Host-` prefix is enforced by the browser, not by us: it refuses to
 * store the cookie at all unless it is Secure, Path=/, and carries NO Domain
 * attribute. The last of those is the one that matters here — without it any
 * host under *.asiansocial.org (uhc-hcw, csweb, a future subdomain, or one
 * that gets compromised) can set a `capi_sid` for the parent domain and have
 * the console accept it. A prefixed cookie cannot be planted from a sibling.
 *
 * Changing the NAME invalidates every existing session, which is why this
 * landed before cutover rather than after: today that logs out a handful of
 * test sessions, afterwards it would log out the whole estate.
 */
const AUTH_COOKIE      = '__Host-capi_sid';
const AUTH_CSRF_COOKIE = '__Host-capi_csrf';
const AUTH_IDLE_SECS   = 60 * 60;        // sliding: 60 min without a request
const AUTH_ABS_SECS    = 12 * 60 * 60;   // hard ceiling regardless of activity
const AUTH_MAX_FAILS   = 8;              // then a cooling-off lockout
const AUTH_LOCK_SECS   = 15 * 60;
const AUTH_MIN_PW_LEN  = 12;             // ASVS 2.1: length over composition

// ---------------------------------------------------------------------------
// Database
// ---------------------------------------------------------------------------

function auth_db(): PDO
{
    static $pdo = null;
    if ($pdo instanceof PDO) { return $pdo; }

    $host = getenv('CAPI_AUTH_DB_HOST') ?: 'database';
    $name = getenv('CAPI_AUTH_DB_NAME') ?: 'capi_auth';
    $user = getenv('CAPI_AUTH_DB_USER') ?: '';
    $pass = getenv('CAPI_AUTH_DB_PASS') ?: '';

    if ($user === '') {
        // Local/dev fallback only. Kept OUTSIDE the docroot on purpose: a
        // credentials file under /var/www/html would be one .htaccess mistake
        // away from being downloadable — the exact class of bug this whole
        // project exists to remove.
        $ini = @parse_ini_file('/var/www/private/capi-auth.ini');
        if (is_array($ini)) {
            $host = $ini['host'] ?? $host;
            $name = $ini['name'] ?? $name;
            $user = $ini['user'] ?? '';
            $pass = $ini['pass'] ?? '';
        }
    }
    if ($user === '') {
        throw new RuntimeException('capi-auth: no database credentials configured');
    }

    $pdo = new PDO(
        sprintf('mysql:host=%s;dbname=%s;charset=utf8mb4', $host, $name),
        $user,
        $pass,
        [
            PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            // Real prepared statements, not client-side interpolation.
            PDO::ATTR_EMULATE_PREPARES   => false,
        ]
    );
    return $pdo;
}

// ---------------------------------------------------------------------------
// Password hashing
// ---------------------------------------------------------------------------

function auth_hash_password(string $pw): string
{
    // argon2id is available on this build (PHP 8.1.34, verified 2026-08-08).
    return password_hash($pw, PASSWORD_ARGON2ID);
}

/**
 * Apache's $apr1$ MD5-crypt. PHP's crypt() does NOT implement this variant —
 * it only knows $1$ — so verifying the 18 imported legacy hashes requires the
 * algorithm here. Used for verification only; never for new hashes.
 */
function auth_apr1_crypt(string $pw, string $salt): string
{
    $salt = substr($salt, 0, 8);
    $len  = strlen($pw);
    $text = $pw . '$apr1$' . $salt;
    $bin  = md5($pw . $salt . $pw, true);

    for ($i = $len; $i > 0; $i -= 16) {
        $text .= substr($bin, 0, min(16, $i));
    }
    for ($i = $len; $i > 0; $i >>= 1) {
        $text .= ($i & 1) ? chr(0) : $pw[0];
    }
    $bin = md5($text, true);

    for ($i = 0; $i < 1000; $i++) {
        $new  = ($i & 1) ? $pw : $bin;
        if ($i % 3) { $new .= $salt; }
        if ($i % 7) { $new .= $pw; }
        $new .= ($i & 1) ? $bin : $pw;
        $bin  = md5($new, true);
    }

    $tmp = '';
    for ($i = 0; $i < 5; $i++) {
        $k = $i + 6;
        $j = $i + 12;
        if ($j === 16) { $j = 5; }
        $tmp = $bin[$i] . $bin[$k] . $bin[$j] . $tmp;
    }
    $tmp = chr(0) . chr(0) . $bin[11] . $tmp;
    $tmp = strtr(
        strrev(substr(base64_encode($tmp), 2)),
        'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/',
        './0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    );
    return '$apr1$' . $salt . '$' . $tmp;
}

/**
 * Verify a password against a stored hash of any supported algorithm, and
 * transparently upgrade legacy hashes on success ("lazy rehash").
 *
 * This is what avoids a flag-day password reset for all 18 accounts. $apr1$
 * hashes cannot be converted without the plaintext — but at the moment someone
 * signs in, we HAVE the plaintext, so that is when the upgrade happens.
 */
function auth_verify_password(array $user, string $pw): bool
{
    $hash = (string) $user['pw_hash'];
    $algo = (string) $user['pw_algo'];
    $ok   = false;

    if ($algo === 'apr1' || str_starts_with($hash, '$apr1$')) {
        $parts = explode('$', $hash);              // ['', 'apr1', salt, digest]
        $salt  = $parts[2] ?? '';
        $ok    = $salt !== '' && hash_equals($hash, auth_apr1_crypt($pw, $salt));
    } else {
        $ok = password_verify($pw, $hash);
    }

    if ($ok && ($algo !== 'argon2id' || password_needs_rehash($hash, PASSWORD_ARGON2ID))) {
        try {
            auth_db()->prepare(
                'UPDATE console_users SET pw_hash = ?, pw_algo = ? WHERE id = ?'
            )->execute([auth_hash_password($pw), 'argon2id', $user['id']]);
        } catch (Throwable $e) {
            // An upgrade failure must never block a valid sign-in; the next
            // login retries. Recorded so a persistent failure is visible.
            auth_audit('', 'rehash.fail', (string) $user['username'], ['err' => $e->getMessage()]);
        }
    }
    return $ok;
}

/** Policy check for a NEW password. Returns '' when acceptable. */
function auth_password_problem(string $pw, string $username): string
{
    if (strlen($pw) < AUTH_MIN_PW_LEN) {
        return 'Password must be at least ' . AUTH_MIN_PW_LEN . ' characters.';
    }
    if (strlen($pw) > 256) {
        return 'Password must be 256 characters or fewer.';
    }
    if ($username !== '' && stripos($pw, $username) !== false) {
        return 'Password must not contain your username.';
    }
    // Cheap, high-yield screen. These are the patterns actually seen on this
    // estate (100%SetupMe! / 100%ChangeMe! shipped as defaults and stayed live).
    foreach (['SetupMe', 'ChangeMe', 'password', 'capi', 'aspsi', '123456'] as $bad) {
        if (stripos($pw, $bad) !== false) {
            return 'Password contains a well-known pattern. Choose something unrelated.';
        }
    }
    return '';
}

// ---------------------------------------------------------------------------
// Users, roles, permissions
// ---------------------------------------------------------------------------

function auth_find_user(string $username): ?array
{
    $st = auth_db()->prepare('SELECT * FROM console_users WHERE username = ? LIMIT 1');
    $st->execute([$username]);
    $r = $st->fetch();
    return $r ?: null;
}

/**
 * Sum of the versions of every role the user holds.
 *
 * Stored on the session and re-checked on every request: change any role's
 * PERMISSION SET, bump its version, and the sum changes — so every live session
 * held by anyone with that role dies on its next request instead of lingering
 * until logout. Versions only ever increase, so for permission edits the sum is
 * monotonic and two changes cannot cancel out.
 *
 * KNOWN GAP (found in review 2026-08-08, do not mistake this for full coverage):
 * the sum does NOT detect a change of WHICH roles a user holds. Swapping role A
 * (version 3) for role B (version 3) leaves the sum at 3 and the session lives.
 *
 * That is not a privilege escalation — the permission set is re-read from the
 * database on every request (it comes back with the session in the same query,
 * see auth_session_resolve), so the demoted user's permissions are already
 * correct; they simply keep their seat rather than being forced to sign in
 * again. Even so, any
 * code path that reassigns roles MUST call auth_session_revoke_user() inside the
 * same transaction. Do not rely on version arithmetic to cover reassignment.
 */
function auth_role_version_sum(int $userId): int
{
    $st = auth_db()->prepare(
        'SELECT COALESCE(SUM(r.version), 0) AS v
           FROM console_user_roles ur
           JOIN console_roles r ON r.id = ur.role_id
          WHERE ur.user_id = ?'
    );
    $st->execute([$userId]);
    return (int) ($st->fetchColumn() ?: 0);
}

/** @return array{roles:string[], perms:string[]} */
function auth_user_grants(int $userId): array
{
    $st = auth_db()->prepare(
        'SELECT r.name AS role, p.perm_key AS perm
           FROM console_user_roles ur
           JOIN console_roles r        ON r.id = ur.role_id
           LEFT JOIN console_role_perms p ON p.role_id = r.id
          WHERE ur.user_id = ?'
    );
    $st->execute([$userId]);
    $roles = $perms = [];
    foreach ($st->fetchAll() as $row) {
        $roles[$row['role']] = true;
        if ($row['perm'] !== null) { $perms[$row['perm']] = true; }
    }
    return ['roles' => array_keys($roles), 'perms' => array_keys($perms)];
}

// ---------------------------------------------------------------------------
// Sessions
// ---------------------------------------------------------------------------

function auth_session_token(): string
{
    return rtrim(strtr(base64_encode(random_bytes(32)), '+/', '-_'), '=');
}

function auth_sid_hash(string $token): string
{
    return hash('sha256', $token);
}

/** Mint a session and return the raw token (the only time it exists in clear). */
function auth_session_create(int $userId, string $ip, string $ua): string
{
    $token = auth_session_token();
    auth_db()->prepare(
        'INSERT INTO console_sessions
           (sid_hash, user_id, role_version, issued_at, last_seen_at, expires_at, ip, user_agent)
         VALUES (?, ?, ?, NOW(), NOW(), DATE_ADD(NOW(), INTERVAL ? SECOND), ?, ?)'
    )->execute([
        auth_sid_hash($token), $userId, auth_role_version_sum($userId),
        AUTH_ABS_SECS, substr($ip, 0, 45), substr($ua, 0, 255),
    ]);
    return $token;
}

/**
 * Resolve a cookie token to a live session + user, or null.
 *
 * Enforces, in order: existence, revocation, absolute expiry, idle timeout,
 * account status, and role-version currency. Touches last_seen_at so the idle
 * window slides.
 */
function auth_session_resolve(?string $token): ?array
{
    if ($token === null || $token === '') { return null; }

    // ONE query for session + user + roles + permissions + role-version sum
    // (E9-ADMIN-030). This runs on EVERY request once the gate is live —
    // including every stylesheet and image — so the previous shape (three
    // SELECTs and an UPDATE, i.e. ~100 queries and ~25 writes for one
    // dashboard load with its assets) was the wrong shape by two orders of
    // magnitude, not by a constant.
    //
    // Two details that are easy to get wrong:
    //  - GROUP_CONCAT needs DISTINCT. Joining user_roles to role_perms
    //    multiplies rows, so without it a user with two roles lists every
    //    role once per permission.
    //  - The version total MUST be a correlated subquery, not SUM() over this
    //    join, for the same reason: SUM over the multiplied rows counts each
    //    role's version once per permission and never matches the session.
    $st = auth_db()->prepare(
        'SELECT s.sid_hash, s.user_id, s.role_version, s.revoked_at,
                s.expires_at, s.last_seen_at,
                u.username, u.status, u.must_change,
                (SELECT COALESCE(SUM(r2.version), 0)
                   FROM console_user_roles ur2
                   JOIN console_roles r2 ON r2.id = ur2.role_id
                  WHERE ur2.user_id = s.user_id) AS ver_sum,
                GROUP_CONCAT(DISTINCT r.name  ORDER BY r.name  SEPARATOR ",") AS role_csv,
                GROUP_CONCAT(DISTINCT p.perm_key ORDER BY p.perm_key SEPARATOR ",") AS perm_csv
           FROM console_sessions s
           JOIN console_users u             ON u.id = s.user_id
           LEFT JOIN console_user_roles ur  ON ur.user_id = s.user_id
           LEFT JOIN console_roles r        ON r.id = ur.role_id
           LEFT JOIN console_role_perms p   ON p.role_id = r.id
          WHERE s.sid_hash = ?
          GROUP BY s.sid_hash'
    );
    $st->execute([auth_sid_hash($token)]);
    $s = $st->fetch();
    if (!$s)                                   { return null; }
    if ($s['revoked_at'] !== null)             { return null; }
    if (strtotime((string) $s['expires_at']) <= time())                    { return null; }
    if (time() - strtotime((string) $s['last_seen_at']) > AUTH_IDLE_SECS)  { return null; }
    if ($s['status'] !== 'active')             { return null; }

    // A permission change anywhere in the user's roles invalidates the session.
    if ((int) $s['role_version'] !== (int) $s['ver_sum']) { return null; }

    // Roles and permissions come back with the session, so callers on the hot
    // path do not need a second round trip. auth_user_grants() still exists
    // for the places that have a user id but no session.
    $s['roles'] = ($s['role_csv'] ?? '') === '' || $s['role_csv'] === null
                    ? [] : explode(',', (string) $s['role_csv']);
    $s['perms'] = ($s['perm_csv'] ?? '') === '' || $s['perm_csv'] === null
                    ? [] : explode(',', (string) $s['perm_csv']);

    // Conditional touch: the idle window is an hour, so writing last_seen_at
    // on every request bought a resolution nothing uses and cost a write per
    // static asset. Once a minute keeps the sliding window accurate to 60s.
    if (time() - strtotime((string) $s['last_seen_at']) >= 60) {
        auth_db()->prepare(
            'UPDATE console_sessions SET last_seen_at = NOW()
              WHERE sid_hash = ? AND last_seen_at < DATE_SUB(NOW(), INTERVAL 60 SECOND)'
        )->execute([$s['sid_hash']]);
    }

    return $s;
}

function auth_session_revoke(string $token): void
{
    auth_db()->prepare(
        'UPDATE console_sessions SET revoked_at = NOW() WHERE sid_hash = ? AND revoked_at IS NULL'
    )->execute([auth_sid_hash($token)]);
}

/**
 * Admin-initiated force-logout: kills every session the user holds.
 *
 * Revokes every row that is not already revoked — including ones that have
 * expired or gone idle. That is deliberate hygiene: leaving a dead row
 * unrevoked means "revoked_at IS NULL" stops meaning anything.
 *
 * But it RETURNS the number that were actually LIVE, using the same three
 * tests the gate applies. The count is shown to an operator as "signs out N
 * active sessions", and the destructive dialog promised that figure from a
 * preflight read — so if this returned the wider number, the confirmation and
 * the result would disagree and the operator would be right to distrust both.
 * (Caught by test_db.php, which expected 2 and got 3.)
 */
function auth_session_revoke_user(int $userId): int
{
    $db = auth_db();

    $st = $db->prepare(
        'SELECT COUNT(*) FROM console_sessions
          WHERE user_id = ? AND revoked_at IS NULL
            AND expires_at > NOW()
            AND last_seen_at > DATE_SUB(NOW(), INTERVAL ? SECOND)'
    );
    $st->execute([$userId, AUTH_IDLE_SECS]);
    $live = (int) $st->fetchColumn();

    $db->prepare(
        'UPDATE console_sessions SET revoked_at = NOW() WHERE user_id = ? AND revoked_at IS NULL'
    )->execute([$userId]);

    return $live;
}

function auth_set_cookie(string $token): void
{
    setcookie(AUTH_COOKIE, $token, [
        'expires'  => 0,          // session cookie; the server holds the real clock
        'path'     => '/',
        'secure'   => true,
        'httponly' => true,
        'samesite' => 'Lax',
    ]);
}

function auth_clear_cookie(): void
{
    setcookie(AUTH_COOKIE, '', [
        'expires'  => time() - 3600,
        'path'     => '/',
        'secure'   => true,
        'httponly' => true,
        'samesite' => 'Lax',
    ]);
}

// ---------------------------------------------------------------------------
// Throttling
// ---------------------------------------------------------------------------

/** @return int seconds remaining on a lockout, or 0 when not locked. */
function auth_lock_remaining(array $user): int
{
    if (empty($user['locked_until'])) { return 0; }
    $left = strtotime((string) $user['locked_until']) - time();
    return $left > 0 ? $left : 0;
}

function auth_note_failure(array $user): void
{
    $n = ((int) $user['failed_count']) + 1;
    if ($n >= AUTH_MAX_FAILS) {
        auth_db()->prepare(
            'UPDATE console_users
                SET failed_count = 0, locked_until = DATE_ADD(NOW(), INTERVAL ? SECOND)
              WHERE id = ?'
        )->execute([AUTH_LOCK_SECS, $user['id']]);
    } else {
        auth_db()->prepare('UPDATE console_users SET failed_count = ? WHERE id = ?')
                 ->execute([$n, $user['id']]);
    }
}

function auth_note_success(int $userId): void
{
    auth_db()->prepare(
        'UPDATE console_users
            SET failed_count = 0, locked_until = NULL, last_login_at = NOW()
          WHERE id = ?'
    )->execute([$userId]);
}

// ---------------------------------------------------------------------------
// Per-IP throttling and the response-time floor (E9-ADMIN-011)
// ---------------------------------------------------------------------------

/**
 * Per-IP failure ceiling.
 *
 * The per-ACCOUNT lockout above cannot see the attack that matters here:
 * it needs a console_users row, so an attacker who guesses USERNAMES rather
 * than passwords is never counted at all. That gives unlimited username
 * spraying, and — before the floor below — a free way to make the server
 * compute an argon2id hash per request while unauthenticated.
 *
 * Counted from console_audit rather than a dedicated table: at this volume the
 * COUNT is cheap (ix_aud_ip covers it, migration 003), the rows already exist,
 * and there is no second thing to garbage-collect.
 */
const AUTH_IP_MAX_FAILS   = 20;
const AUTH_IP_WINDOW_SECS = 15 * 60;

function auth_ip_fail_count(string $ip): int
{
    if ($ip === '') { return 0; }
    try {
        $st = auth_db()->prepare(
            "SELECT COUNT(*) FROM console_audit
              WHERE ip = ?
                AND verb IN ('login.fail','login.throttled')
                AND ts > DATE_SUB(NOW(), INTERVAL ? SECOND)"
        );
        $st->execute([$ip, AUTH_IP_WINDOW_SECS]);
        return (int) $st->fetchColumn();
    } catch (Throwable $e) {
        // Never let a counting failure become a sign-in failure.
        error_log('capi-auth ip throttle count failed: ' . $e->getMessage());
        return 0;
    }
}

function auth_ip_blocked(string $ip): bool
{
    return auth_ip_fail_count($ip) >= AUTH_IP_MAX_FAILS;
}

/**
 * Hold every sign-in response to the same minimum duration.
 *
 * This closes a timing oracle that is INVERTED on this estate and therefore
 * especially misleading: 15 of the 18 imported accounts still verify against
 * `$apr1$` (1000 rounds of MD5 — microseconds), while the not-a-real-user path
 * used to spend a full argon2id hash. Real accounts answered FASTER than
 * fictional ones, so timing did not merely leak existence, it advertised it.
 *
 * A floor is the right shape rather than a random jitter: jitter is averaged
 * away over enough samples, a floor is not. 250 ms is above the slowest real
 * path (argon2id on this box) and below anything a person notices.
 *
 * @param int $startNs hrtime(true) captured at the top of the request
 */
const AUTH_LOGIN_FLOOR_MS = 250;

function auth_timing_floor(int $startNs, int $minMs = AUTH_LOGIN_FLOOR_MS): void
{
    $elapsedUs = (int) ((hrtime(true) - $startNs) / 1000);
    $targetUs  = $minMs * 1000;
    if ($elapsedUs < $targetUs) { usleep($targetUs - $elapsedUs); }
}

// ---------------------------------------------------------------------------
// Audit
// ---------------------------------------------------------------------------

/**
 * One id for the whole request, stamped on every audit row it produces.
 *
 * Turns "an error happened" into "these six rows are the same failed request",
 * which matters more here than in most systems: log_errors is Off on this
 * image, so console_audit is the error log.
 */
function auth_request_id(): string
{
    static $rid = null;
    if ($rid === null) { $rid = bin2hex(random_bytes(16)); }
    return $rid;
}

function auth_audit(string $actor, string $verb, string $target = '', ?array $detail = null): void
{
    // console_audit.request_id arrives with migration 002. lib.php and the
    // migration are deployed by separate commands, so assume neither ordering:
    // try the current shape, and fall back permanently for this process if the
    // column is not there yet. A missed column must not cost us a login.
    static $hasRequestId = true;

    $args = [
        substr($actor, 0, 64),
        substr($verb, 0, 32),
        substr($target, 0, 255),
        $detail === null ? null : json_encode($detail, JSON_UNESCAPED_SLASHES),
        substr(auth_client_ip(), 0, 45),
    ];

    try {
        if ($hasRequestId) {
            try {
                auth_db()->prepare(
                    'INSERT INTO console_audit (actor, verb, target, detail, ip, request_id)
                     VALUES (?, ?, ?, ?, ?, ?)'
                )->execute([...$args, auth_request_id()]);
                return;
            } catch (PDOException $e) {
                // 42S22 = unknown column. Anything else is a real failure.
                if ($e->getCode() !== '42S22') { throw $e; }
                $hasRequestId = false;
            }
        }
        auth_db()->prepare(
            'INSERT INTO console_audit (actor, verb, target, detail, ip) VALUES (?, ?, ?, ?, ?)'
        )->execute($args);
    } catch (Throwable $e) {
        // Auditing must never take the site down. Losing one line is bad;
        // 500ing every request because the audit table is full is worse.
        error_log('capi-auth audit failed: ' . $e->getMessage());
    }
}

function auth_client_ip(): string
{
    // Behind Elestio's openresty, so the socket peer is always the proxy.
    // X-Forwarded-For is only trustworthy because nothing but that proxy can
    // reach this container; take the FIRST hop and ignore the rest.
    $xff = $_SERVER['HTTP_X_FORWARDED_FOR'] ?? '';
    if ($xff !== '') {
        $first = trim(explode(',', $xff)[0]);
        if (filter_var($first, FILTER_VALIDATE_IP)) { return $first; }
    }
    return (string) ($_SERVER['REMOTE_ADDR'] ?? '');
}

// ---------------------------------------------------------------------------
// Post-sign-in redirect target
// ---------------------------------------------------------------------------

/**
 * Sanitise a `?next=` value into a site-relative path, or fall back to '/'.
 *
 * This guards an open redirect: a phishing link of the form
 * `…/docs/auth/login?next=<attacker>` would bounce the user off-site at the
 * exact moment they have just proven who they are — the most convincing
 * possible time to be handed a fake sign-in page.
 *
 * The subtle case, and the reason this lives here with tests rather than
 * inline: browsers fold '\' to '/' while parsing the authority, so `/\evil.com`
 * resolves as the protocol-relative `//evil.com`. Every check written in terms
 * of '/' misses it. Reject backslashes outright.
 */
function auth_safe_next(string $raw): string
{
    $fallback = '/';

    if ($raw === '' || $raw[0] !== '/') { return $fallback; }

    // Control characters — CR/LF header injection, and NUL/TAB which some
    // parsers strip before resolving, changing what the string means.
    if (preg_match('/[\x00-\x1F\x7F]/', $raw)) { return $fallback; }

    // Any backslash: see the note above.
    if (str_contains($raw, '\\')) { return $fallback; }

    // '//host' — protocol-relative.
    if (isset($raw[1]) && $raw[1] === '/') { return $fallback; }

    // Belt and braces: if it still parses as carrying a scheme, host or
    // credentials, discard it rather than trying to repair it.
    $parts = parse_url($raw);
    if ($parts === false) { return $fallback; }
    if (isset($parts['scheme']) || isset($parts['host']) || isset($parts['user'])) {
        return $fallback;
    }

    $path = $parts['path'] ?? '';
    if ($path === '' || $path[0] !== '/') { return $fallback; }

    // Keep path + query; the fragment is never sent to the server anyway.
    $next = $path . (isset($parts['query']) ? '?' . $parts['query'] : '');

    // Never bounce back into the auth endpoints themselves.
    if (str_starts_with($next, '/docs/idp/')) { return $fallback; }

    return $next;
}

// ---------------------------------------------------------------------------
// CSRF (for the login form and any state-changing POST)
// ---------------------------------------------------------------------------

function auth_csrf_token(): string
{
    if (empty($_COOKIE[AUTH_CSRF_COOKIE])) {
        $t = rtrim(strtr(base64_encode(random_bytes(24)), '+/', '-_'), '=');
        // httponly is false on purpose — the SPA has to read this to echo it
        // back as a header. That is what a double-submit token IS; its value
        // is that an attacker on another origin cannot read it, not that
        // script here cannot. Path '/' and no Domain are required by __Host-.
        setcookie(AUTH_CSRF_COOKIE, $t, [
            'expires' => 0, 'path' => '/', 'secure' => true,
            'httponly' => false, 'samesite' => 'Lax',
        ]);
        return $t;
    }
    return (string) $_COOKIE[AUTH_CSRF_COOKIE];
}

function auth_csrf_ok(?string $sent): bool
{
    $have = (string) ($_COOKIE[AUTH_CSRF_COOKIE] ?? '');
    return $have !== '' && is_string($sent) && hash_equals($have, $sent);
}
