<?php
/**
 * CAPI Console — Admin API: live sessions (E9-ADMIN-007 / -023).
 * Design: deliverables/CSWeb/admin-portal/DESIGN.md §2         Carl, 2026-08-08
 *
 * "Who is signed in right now, and can I end it" is the single capability the
 * mod_session_cookie setup could not provide at all. This is the screen that
 * answers SC-2 — and the reason the session table stores a hash rather than
 * the token is that this screen exists: an admin list of live sessions must
 * not be an admin list of usable credentials.
 */
declare(strict_types=1);

/**
 * @param array<int,string> $seg path segments after `sessions`
 */
function adm_sessions_route(string $method, array $seg): never
{
    $actor = adm_require_perm('admin.users');

    if ($seg === []) {
        if ($method === 'GET')    { adm_sessions_list($actor); }
        if ($method === 'DELETE') { adm_sessions_kill_user($actor); }
        throw new AdmError('method', 'Method not allowed.', 405);
    }

    if ($method === 'DELETE') { adm_sessions_kill($actor, $seg[0]); }
    throw new AdmError('method', 'Method not allowed.', 405);
}

function adm_sessions_list(array $actor): never
{
    $db = auth_db();

    // "Live" is the same three-part test authz.php applies on every request:
    // not revoked, inside the absolute expiry, and inside the idle window.
    // Anything looser lists sessions that would already be refused, which
    // makes the kill button look broken when it reports 0 revoked.
    $where  = ['s.revoked_at IS NULL', 's.expires_at > NOW()',
               's.last_seen_at > DATE_SUB(NOW(), INTERVAL ' . (int) AUTH_IDLE_SECS . ' SECOND)'];
    $params = [];

    $userId = adm_int($_GET, 'user_id', 0, 0);
    if ($userId > 0) { $where[] = 's.user_id = ?'; $params[] = $userId; }

    $st = $db->prepare(
        'SELECT s.sid_hash, s.user_id, s.issued_at, s.last_seen_at, s.expires_at,
                s.ip, s.user_agent, u.username, u.full_name, u.status
           FROM console_sessions s
           JOIN console_users u ON u.id = s.user_id
          WHERE ' . implode(' AND ', $where) . '
          ORDER BY s.last_seen_at DESC
          LIMIT 500'
    );
    $st->execute($params);

    $rows = [];
    foreach ($st->fetchAll() as $r) {
        $rows[] = [
            // The stored hash, which is also the handle the kill endpoint
            // takes. It is not a credential: knowing it does not let you
            // present it as a cookie.
            'sid'          => (string) $r['sid_hash'],
            'user_id'      => (int) $r['user_id'],
            'username'     => (string) $r['username'],
            'full_name'    => (string) $r['full_name'],
            'issued_at'    => $r['issued_at'],
            'last_seen_at' => $r['last_seen_at'],
            'expires_at'   => $r['expires_at'],
            'ip'           => (string) $r['ip'],
            'user_agent'   => (string) $r['user_agent'],
            'is_self'      => hash_equals($actor['sid_hash'], (string) $r['sid_hash']),
        ];
    }

    adm_ok(['sessions' => $rows, 'count' => count($rows), 'idle_secs' => AUTH_IDLE_SECS]);
}

function adm_sessions_kill(array $actor, string $sid): never
{
    adm_require_csrf();

    // \z rather than $ — see adm_valid_username; `$` would accept a trailing
    // newline and turn a malformed handle into a confusing 404.
    if (!preg_match('/^[0-9a-f]{64}\z/', $sid)) {
        throw adm_bad('That is not a session handle.', 'sid');
    }

    // Refusing to kill your own current session here is a usability guard, not
    // a security one: an admin clearing a list of sessions should not sign
    // themselves out halfway through and lose the rest of the work. Sign out
    // is a separate, deliberate act with its own button.
    if (hash_equals($actor['sid_hash'], $sid)) {
        throw new AdmError('self_session',
            'That is your own session. Use Sign out instead.', 409);
    }

    $out = adm_tx(static function (PDO $db) use ($actor, $sid) {
        $st = $db->prepare(
            'SELECT s.sid_hash, u.username FROM console_sessions s
               JOIN console_users u ON u.id = s.user_id
              WHERE s.sid_hash = ? FOR UPDATE'
        );
        $st->execute([$sid]);
        $row = $st->fetch();
        if (!$row) { throw new AdmError('not_found', 'No such session.', 404); }

        $up = $db->prepare(
            'UPDATE console_sessions SET revoked_at = NOW()
              WHERE sid_hash = ? AND revoked_at IS NULL'
        );
        $up->execute([$sid]);
        $n = $up->rowCount();

        auth_audit($actor['username'], 'session.kill', (string) $row['username'],
                   ['sid_prefix' => substr($sid, 0, 12), 'revoked' => $n]);

        // 0 means it was already revoked — a replay, not a failure.
        return ['revoked' => $n, 'username' => (string) $row['username']];
    });

    adm_ok($out);
}

/** Kill every session for one user. Same effect as the user-level endpoint,
 *  reachable from the sessions screen so the operator does not have to leave
 *  the list they are looking at. */
function adm_sessions_kill_user(array $actor): never
{
    adm_require_csrf();
    $b  = adm_body();
    $id = adm_int($b, 'user_id', 0, 1);
    if ($id === 0) { throw adm_bad('user_id is required.', 'user_id'); }

    $out = adm_tx(static function (PDO $db) use ($actor, $id) {
        $user    = adm_user_row($db, $id);
        $revoked = auth_session_revoke_user($id);
        auth_audit($actor['username'], 'user.forcelogout', (string) $user['username'],
                   ['id' => $id, 'revoked' => $revoked, 'via' => 'sessions']);
        return ['username' => (string) $user['username'], 'revoked_sessions' => $revoked];
    });

    adm_ok($out);
}
