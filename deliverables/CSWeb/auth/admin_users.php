<?php
/**
 * CAPI Console — Admin API: users (E9-ADMIN-007).             Carl, 2026-08-08
 * Design: deliverables/CSWeb/admin-portal/DESIGN.md §2, §4
 *
 * The screen this backs is the reason the whole module exists: until account
 * changes land in console_users, the gate cannot be cut over, because the
 * current admin screen would report "disabled" while the account kept working.
 *
 * Two rules run through every handler here:
 *
 *   1. A write that does not persist reports failure (FR-05). No success is
 *      ever returned for a no-op. That is the exact bug being retired.
 *   2. Anything that removes access also revokes sessions, in the same
 *      transaction. A disabled user with a live cookie is not disabled.
 */
declare(strict_types=1);

const ADM_USER_STATUSES = ['active', 'disabled'];

/**
 * @param array<int,string> $seg path segments after `users`
 */
function adm_users_route(string $method, array $seg): never
{
    // Reads and writes are both admin.users. There is no read-only user
    // administrator role in a five-role system for twenty people; inventing
    // one would be a permission nobody is ever granted.
    $actor = adm_require_perm('admin.users');

    if ($seg === []) {
        if ($method === 'GET')  { adm_users_list($actor); }
        if ($method === 'POST') { adm_users_create($actor); }
        throw new AdmError('method', 'Method not allowed.', 405);
    }

    if (!ctype_digit($seg[0])) { throw new AdmError('not_found', 'No such user.', 404); }
    $id  = (int) $seg[0];
    $sub = $seg[1] ?? '';

    switch ($sub) {
        case '':
            if ($method === 'GET')    { adm_users_detail($actor, $id); }
            if ($method === 'PATCH')  { adm_users_patch($actor, $id); }
            if ($method === 'DELETE') { adm_users_disable($actor, $id); }
            break;
        case 'roles':
            if ($method === 'PUT')    { adm_users_set_roles($actor, $id); }
            break;
        case 'password':
            if ($method === 'POST')   { adm_users_reset_password($actor, $id); }
            break;
        case 'logout':
            if ($method === 'POST')   { adm_users_force_logout($actor, $id); }
            break;
        default:
            throw new AdmError('not_found', 'No such endpoint.', 404);
    }
    throw new AdmError('method', 'Method not allowed.', 405);
}

// ---------------------------------------------------------------------------
// Read
// ---------------------------------------------------------------------------

/**
 * Usernames that differ only by `_` vs `-` are the seven se_001/se-001 pairs
 * from the htpasswd import (FR-17). Grouping them in the payload is what lets
 * the UI show them together with their activity, so that disabling the dormant
 * half is a decision made against evidence rather than against a hunch.
 */
function adm_dup_group(string $username): string
{
    return strtolower(str_replace('_', '-', $username));
}

function adm_users_select_sql(string $where): string
{
    return
        'SELECT u.id, u.username, u.full_name, u.email, u.status, u.must_change,
                u.pw_algo, u.row_version, u.failed_count, u.locked_until,
                u.last_login_at, u.pw_changed_at, u.created_at, u.created_by,
                u.updated_at, u.updated_by, u.disabled_at,
                (SELECT GROUP_CONCAT(r.name ORDER BY r.name SEPARATOR ",")
                   FROM console_user_roles ur
                   JOIN console_roles r ON r.id = ur.role_id
                  WHERE ur.user_id = u.id) AS role_csv,
                (SELECT COUNT(*) FROM console_sessions s
                  WHERE s.user_id = u.id
                    AND s.revoked_at IS NULL
                    AND s.expires_at > NOW()
                    AND s.last_seen_at > DATE_SUB(NOW(), INTERVAL ' . (int) AUTH_IDLE_SECS . ' SECOND)
                ) AS live_sessions
           FROM console_users u
          WHERE ' . $where;
}

function adm_users_shape(array $r): array
{
    return [
        'id'            => (int) $r['id'],
        'username'      => (string) $r['username'],
        'full_name'     => (string) $r['full_name'],
        'email'         => (string) $r['email'],
        'status'        => (string) $r['status'],
        'must_change'   => ((int) $r['must_change'] === 1),
        'pw_algo'       => (string) $r['pw_algo'],
        'pw_changed_at' => $r['pw_changed_at'],
        'row_version'   => (int) $r['row_version'],
        'locked_until'  => $r['locked_until'],
        'failed_count'  => (int) $r['failed_count'],
        'last_login_at' => $r['last_login_at'],
        'created_at'    => $r['created_at'],
        'created_by'    => (string) $r['created_by'],
        'updated_at'    => $r['updated_at'],
        'updated_by'    => (string) $r['updated_by'],
        'disabled_at'   => $r['disabled_at'],
        'roles'         => $r['role_csv'] === null || $r['role_csv'] === ''
                             ? [] : explode(',', (string) $r['role_csv']),
        'live_sessions' => (int) $r['live_sessions'],
        'protected'     => adm_is_protected((string) $r['username']),
        'dup_group'     => adm_dup_group((string) $r['username']),
    ];
}

function adm_users_list(array $actor): never
{
    $db     = auth_db();
    $where  = ['1 = 1'];
    $params = [];

    $q = adm_str($_GET, 'q', 64);
    if ($q !== '') {
        $where[] = '(u.username LIKE ? OR u.full_name LIKE ? OR u.email LIKE ?)';
        // Escape the LIKE metacharacters; a search for "se_001" must not match
        // "se-001" through the wildcard `_`, which is precisely the pair the
        // duplicate triage is trying to tell apart.
        $like = '%' . str_replace(['\\', '%', '_'], ['\\\\', '\\%', '\\_'], $q) . '%';
        array_push($params, $like, $like, $like);
    }

    $status = adm_str($_GET, 'status', 16);
    if ($status !== '') {
        if (!in_array($status, ADM_USER_STATUSES, true)) { throw adm_bad('Unknown status filter.', 'status'); }
        $where[]  = 'u.status = ?';
        $params[] = $status;
    }

    $role = adm_str($_GET, 'role', 48);
    if ($role !== '') {
        $where[] = 'EXISTS (SELECT 1 FROM console_user_roles ur2
                              JOIN console_roles r2 ON r2.id = ur2.role_id
                             WHERE ur2.user_id = u.id AND r2.name = ?)';
        $params[] = $role;
    }

    $st = $db->prepare(adm_users_select_sql(implode(' AND ', $where)) . ' ORDER BY u.username');
    $st->execute($params);

    $rows = array_map('adm_users_shape', $st->fetchAll());

    // Mark members of a duplicate pair so the list can flag them without a
    // second round trip. Computed here rather than in SQL because the rule is
    // a string normalisation, not a predicate an index could serve.
    $counts = [];
    foreach ($rows as $r) { $counts[$r['dup_group']] = ($counts[$r['dup_group']] ?? 0) + 1; }
    foreach ($rows as &$r) { $r['duplicate'] = $counts[$r['dup_group']] > 1; }
    unset($r);

    adm_ok([
        'users'      => $rows,
        'roles'      => adm_roles_brief($db),
        'me'         => $actor['username'],
        'protected'  => ADM_PROTECTED_USERS,
    ]);
}

function adm_users_detail(array $actor, int $id): never
{
    $db = auth_db();
    $st = $db->prepare(adm_users_select_sql('u.id = ?'));
    $st->execute([$id]);
    $r = $st->fetch();
    if (!$r) { throw new AdmError('not_found', 'No such user.', 404); }

    $user = adm_users_shape($r);

    // The blast radius the destructive dialogs render (FR-19). It is fetched,
    // never guessed: a dialog that says "signs out 0 sessions" because the
    // client defaulted to zero is worse than no number at all.
    $user['impact'] = [
        'live_sessions'  => $user['live_sessions'],
        'is_self'        => ($id === $actor['user_id']),
        'is_last_owner'  => adm_is_last_active_owner($db, $id),
        'is_protected'   => $user['protected'],
    ];

    adm_ok(['user' => $user, 'roles' => adm_roles_brief($db)]);
}

/** True when disabling or demoting this user would leave no active owner. */
function adm_is_last_active_owner(PDO $db, int $id): bool
{
    $st = $db->prepare(
        "SELECT COUNT(*) FROM console_users u
           JOIN console_user_roles ur ON ur.user_id = u.id
           JOIN console_roles r       ON r.id = ur.role_id
          WHERE r.name = 'owner' AND u.status = 'active' AND u.id <> ?"
    );
    $st->execute([$id]);
    if ((int) $st->fetchColumn() > 0) { return false; }

    // Nobody else is an active owner — so this user is the last one only if
    // they are an active owner themselves.
    $st = $db->prepare(
        "SELECT COUNT(*) FROM console_users u
           JOIN console_user_roles ur ON ur.user_id = u.id
           JOIN console_roles r       ON r.id = ur.role_id
          WHERE r.name = 'owner' AND u.status = 'active' AND u.id = ?"
    );
    $st->execute([$id]);
    return (int) $st->fetchColumn() > 0;
}

// ---------------------------------------------------------------------------
// Role assignment guards
// ---------------------------------------------------------------------------

/**
 * Resolve role names to ids, rejecting unknown ones by name so the message is
 * useful. An empty set is refused: a user with no role can sign in and reach
 * nothing, which looks like a broken account rather than a denied one.
 *
 * @param string[] $names
 * @return array<string,int> name => id
 */
function adm_resolve_roles(PDO $db, array $names): array
{
    $names = array_values(array_unique(array_map(
        static fn($n) => strtolower(trim((string) $n)),
        $names
    )));
    if ($names === []) { throw adm_bad('Choose at least one role.', 'roles'); }
    if (count($names) > 5) { throw adm_bad('Too many roles.', 'roles'); }

    $in = implode(',', array_fill(0, count($names), '?'));
    $st = $db->prepare("SELECT id, name FROM console_roles WHERE name IN ($in)");
    $st->execute($names);

    $map = [];
    foreach ($st->fetchAll() as $r) { $map[(string) $r['name']] = (int) $r['id']; }

    $missing = array_diff($names, array_keys($map));
    if ($missing !== []) {
        throw adm_bad('Unknown role: ' . implode(', ', $missing) . '.', 'roles');
    }
    return $map;
}

/**
 * Privilege-escalation guard on the owner role.
 *
 * programme_admin holds admin.users, which is what lets ASPSI onboard field
 * staff without waiting for Carl. Without this check that same permission
 * lets them grant themselves `owner` — i.e. admin.users would silently be the
 * top of the hierarchy rather than a delegated slice of it.
 *
 * @param string[] $newRoles
 * @param string[] $currentRoles
 */
function adm_assert_may_set_roles(array $actor, array $newRoles, array $currentRoles): void
{
    if (in_array('owner', $actor['roles'], true)) { return; }

    if (in_array('owner', $newRoles, true)) {
        throw new AdmError('forbidden', 'Only an owner can grant the owner role.', 403, 'roles');
    }
    if (in_array('owner', $currentRoles, true)) {
        throw new AdmError('forbidden', 'Only an owner can change another owner\'s roles.', 403, 'roles');
    }
}

/** @return string[] */
function adm_current_role_names(PDO $db, int $userId): array
{
    $st = $db->prepare(
        'SELECT r.name FROM console_user_roles ur
           JOIN console_roles r ON r.id = ur.role_id
          WHERE ur.user_id = ? ORDER BY r.name'
    );
    $st->execute([$userId]);
    return array_map(static fn($r) => (string) $r['name'], $st->fetchAll());
}

// ---------------------------------------------------------------------------
// Create
// ---------------------------------------------------------------------------

function adm_users_create(array $actor): never
{
    adm_require_csrf();
    $idem = adm_idem_begin('POST /admin/users', $actor['username']);
    $b    = adm_body();

    $username = strtolower(adm_str($b, 'username', 32, true));
    if (!adm_valid_username($username)) {
        throw adm_bad('Username: 3–32 characters, lowercase letters, digits, dot, underscore or hyphen, '
                    . 'starting and ending with a letter or digit.', 'username');
    }
    $fullName = adm_str($b, 'full_name', 128);
    $email    = adm_str($b, 'email', 190);
    if ($email !== '' && !filter_var($email, FILTER_VALIDATE_EMAIL)) {
        throw adm_bad('That does not look like an email address.', 'email');
    }
    $roleNames = isset($b['roles']) && is_array($b['roles']) ? $b['roles'] : [];

    $temp = adm_temp_password();

    $created = adm_tx(static function (PDO $db) use ($actor, $username, $fullName, $email, $roleNames, $temp) {
        $roles = adm_resolve_roles($db, $roleNames);
        adm_assert_may_set_roles($actor, array_keys($roles), []);

        try {
            $db->prepare(
                'INSERT INTO console_users
                   (username, full_name, email, pw_hash, pw_algo, must_change,
                    status, created_by, pw_changed_at, updated_at, updated_by)
                 VALUES (?, ?, ?, ?, "argon2id", 1, "active", ?, NOW(), NOW(), ?)'
            )->execute([$username, $fullName, $email, auth_hash_password($temp),
                        $actor['username'], $actor['username']]);
        } catch (PDOException $e) {
            if ($e->getCode() === '23000') {
                throw new AdmError('duplicate', 'That username already exists.', 409, 'username');
            }
            throw $e;
        }

        $id = (int) $db->lastInsertId();
        $ins = $db->prepare('INSERT INTO console_user_roles (user_id, role_id) VALUES (?, ?)');
        foreach ($roles as $rid) { $ins->execute([$id, $rid]); }

        auth_audit($actor['username'], 'user.create', $username,
                   ['id' => $id, 'roles' => array_keys($roles)]);

        return ['id' => $id, 'roles' => array_keys($roles)];
    });

    // The temporary password is returned exactly once and is not recoverable:
    // only its argon2id hash was stored. If the admin loses it, the fix is a
    // second reset, not a lookup.
    adm_ok_idem($idem, [
        'id'            => $created['id'],
        'username'      => $username,
        'roles'         => $created['roles'],
        'temp_password' => $temp,
        'must_change'   => true,
        // Null once the gate is cut over. Before that, this account exists and
        // is correct but cannot reach /docs/ — say so at the moment the
        // credential is handed over, not in a runbook nobody re-reads.
        'gate_notice'   => adm_gate_notice(),
    ], 201);
}

// ---------------------------------------------------------------------------
// Update
// ---------------------------------------------------------------------------

function adm_users_patch(array $actor, int $id): never
{
    adm_require_csrf();
    $b = adm_body();

    $result = adm_tx(static function (PDO $db) use ($actor, $id, $b) {
        $user = adm_user_row($db, $id, true);
        adm_check_row_version($user, $b);

        $sets    = [];
        $params  = [];
        $changed = [];
        $revoked = 0;

        if (array_key_exists('full_name', $b)) {
            $sets[]  = 'full_name = ?';
            $params[] = adm_str($b, 'full_name', 128);
            $changed['full_name'] = $params[count($params) - 1];
        }
        if (array_key_exists('email', $b)) {
            $email = adm_str($b, 'email', 190);
            if ($email !== '' && !filter_var($email, FILTER_VALIDATE_EMAIL)) {
                throw adm_bad('That does not look like an email address.', 'email');
            }
            $sets[]   = 'email = ?';
            $params[] = $email;
            $changed['email'] = $email;
        }

        // Clearing a lockout (NFR-07). Setting one is not offered: lockouts
        // are earned by failed attempts, not administered.
        if (array_key_exists('locked', $b) && $b['locked'] === false) {
            $sets[] = 'locked_until = NULL, failed_count = 0';
            $changed['locked'] = false;
        }

        if (array_key_exists('status', $b)) {
            $status = adm_str($b, 'status', 16, true);
            if (!in_array($status, ADM_USER_STATUSES, true)) {
                throw adm_bad('Unknown status.', 'status');
            }
            if ($status !== $user['status']) {
                if ($status === 'disabled') {
                    adm_assert_may_disable($actor, $user, $id);
                    $sets[] = 'status = "disabled", disabled_at = NOW()';
                } else {
                    // Re-enabling clears the lockout too: an account disabled
                    // during an incident is usually also locked, and leaving
                    // that behind means "enabled" that still cannot sign in.
                    $sets[] = 'status = "active", disabled_at = NULL, locked_until = NULL, failed_count = 0';
                }
                $changed['status'] = $status;
            }
        }

        if ($sets === []) { throw adm_bad('Nothing to change.'); }

        $params[] = $id;
        $st = $db->prepare('UPDATE console_users SET ' . implode(', ', $sets) . ' WHERE id = ?');
        $st->execute($params);

        // FR-05: a write that did not persist must not report success.
        if ($st->rowCount() < 1) {
            throw new AdmError('not_applied',
                'The change was not saved. Reload and try again.', 500);
        }

        // Removing access revokes sessions in the SAME transaction. Split
        // these and there is a window where the row says disabled and the
        // cookie still works — the exact defect this module exists to remove.
        if (($changed['status'] ?? null) === 'disabled') {
            $revoked = auth_session_revoke_user($id);
            adm_assert_owner_remains($db);
        }

        adm_touch_user($db, $id, $actor['username']);
        auth_audit($actor['username'],
                   ($changed['status'] ?? null) === 'disabled' ? 'user.disable' : 'user.update',
                   (string) $user['username'],
                   ['id' => $id, 'changed' => array_keys($changed)] + ['revoked' => $revoked]);

        return ['changed' => array_keys($changed), 'revoked_sessions' => $revoked];
    });

    adm_ok($result);
}

/**
 * The three ways an admin can lock everyone out, refused in one place.
 * `adm_assert_owner_remains` runs after the write as well; this one produces
 * the message a human can act on.
 */
function adm_assert_may_disable(array $actor, array $user, int $id): void
{
    if ($id === $actor['user_id']) {
        throw new AdmError('self_disable',
            'You cannot disable your own account. Ask another owner.', 409);
    }
    if (adm_is_protected((string) $user['username'])) {
        throw new AdmError('protected',
            (string) $user['username'] . ' is a break-glass account and cannot be disabled here.', 409);
    }
}

// ---------------------------------------------------------------------------
// Roles — full-set replace
// ---------------------------------------------------------------------------

function adm_users_set_roles(array $actor, int $id): never
{
    adm_require_csrf();
    $b = adm_body();
    if (!isset($b['roles']) || !is_array($b['roles'])) {
        throw adm_bad('Send the complete list of roles this user should have.', 'roles');
    }

    $result = adm_tx(static function (PDO $db) use ($actor, $id, $b) {
        $user = adm_user_row($db, $id, true);
        adm_check_row_version($user, $b);

        if ($id === $actor['user_id']) {
            // Self-demotion is how an admin removes their own last route back
            // in. Refusing it outright is cheaper to reason about than trying
            // to work out which subsets are survivable.
            throw new AdmError('self_demote',
                'You cannot change your own roles. Ask another owner.', 409);
        }

        $current = adm_current_role_names($db, $id);
        $roles   = adm_resolve_roles($db, $b['roles']);
        $target  = array_keys($roles);

        adm_assert_may_set_roles($actor, $target, $current);

        sort($current); sort($target);
        if ($current === $target) {
            // A replay of the same full set. Report it honestly as a no-op
            // rather than inventing a change — the whole point of taking the
            // full set rather than a delta is that replay is safe.
            return ['roles' => $target, 'changed' => false, 'revoked_sessions' => 0];
        }

        $db->prepare('DELETE FROM console_user_roles WHERE user_id = ?')->execute([$id]);
        $ins = $db->prepare('INSERT INTO console_user_roles (user_id, role_id) VALUES (?, ?)');
        foreach ($roles as $rid) { $ins->execute([$id, $rid]); }

        // Explicit, and NOT covered by role_version arithmetic: swapping role A
        // (v3) for role B (v3) leaves the version sum unchanged, so the session
        // would survive a demotion. See lib.php auth_role_version_sum.
        $revoked = auth_session_revoke_user($id);

        adm_assert_owner_remains($db);
        adm_touch_user($db, $id, $actor['username']);
        auth_audit($actor['username'], 'user.roles', (string) $user['username'],
                   ['id' => $id, 'from' => $current, 'to' => $target, 'revoked' => $revoked]);

        return ['roles' => $target, 'changed' => true, 'revoked_sessions' => $revoked];
    });

    adm_ok($result);
}

// ---------------------------------------------------------------------------
// Password reset
// ---------------------------------------------------------------------------

function adm_users_reset_password(array $actor, int $id): never
{
    adm_require_csrf();
    $idem = adm_idem_begin('POST /admin/users/' . $id . '/password', $actor['username']);

    $temp = adm_temp_password();

    $out = adm_tx(static function (PDO $db) use ($actor, $id, $temp) {
        $user = adm_user_row($db, $id, true);

        if (adm_is_protected((string) $user['username']) && !in_array('owner', $actor['roles'], true)) {
            throw new AdmError('protected',
                'Only an owner can reset a break-glass account.', 403);
        }

        $st = $db->prepare(
            'UPDATE console_users
                SET pw_hash = ?, pw_algo = "argon2id", must_change = 1,
                    pw_changed_at = NOW(), failed_count = 0, locked_until = NULL
              WHERE id = ?'
        );
        $st->execute([auth_hash_password($temp), $id]);
        if ($st->rowCount() < 1) {
            throw new AdmError('not_applied', 'The reset was not saved. Try again.', 500);
        }

        // FR-11. Without the revoke, a compromised session survives the very
        // reset that was performed to end it.
        $revoked = auth_session_revoke_user($id);

        adm_touch_user($db, $id, $actor['username']);
        auth_audit($actor['username'], 'user.password.reset', (string) $user['username'],
                   ['id' => $id, 'revoked' => $revoked]);

        return ['username' => (string) $user['username'], 'revoked_sessions' => $revoked];
    });

    adm_ok_idem($idem, [
        'username'         => $out['username'],
        'temp_password'    => $temp,
        'must_change'      => true,
        'revoked_sessions' => $out['revoked_sessions'],
        'gate_notice'      => adm_gate_notice(),
    ]);
}

// ---------------------------------------------------------------------------
// Force logout / soft delete
// ---------------------------------------------------------------------------

function adm_users_force_logout(array $actor, int $id): never
{
    adm_require_csrf();
    $idem = adm_idem_begin('POST /admin/users/' . $id . '/logout', $actor['username']);

    $out = adm_tx(static function (PDO $db) use ($actor, $id) {
        $user    = adm_user_row($db, $id);
        $revoked = auth_session_revoke_user($id);
        auth_audit($actor['username'], 'user.forcelogout', (string) $user['username'],
                   ['id' => $id, 'revoked' => $revoked]);
        return ['username' => (string) $user['username'], 'revoked_sessions' => $revoked];
    });

    // A replay legitimately reports 0 — there is nothing left to revoke, and
    // saying so is more useful than pretending the second click did work.
    adm_ok_idem($idem, $out);
}

/**
 * DELETE is a disable, deliberately. A hard delete orphans every console_audit
 * row that names the account, which is the opposite of what an audit trail is
 * for: the people most worth investigating are the ones most likely to be
 * removed afterwards.
 */
function adm_users_disable(array $actor, int $id): never
{
    adm_require_csrf();

    $out = adm_tx(static function (PDO $db) use ($actor, $id) {
        $user = adm_user_row($db, $id, true);
        adm_assert_may_disable($actor, $user, $id);

        if ($user['status'] === 'disabled') {
            return ['username' => (string) $user['username'], 'revoked_sessions' => 0, 'changed' => false];
        }

        $st = $db->prepare('UPDATE console_users SET status = "disabled", disabled_at = NOW() WHERE id = ?');
        $st->execute([$id]);
        if ($st->rowCount() < 1) {
            throw new AdmError('not_applied', 'The account was not disabled. Try again.', 500);
        }

        $revoked = auth_session_revoke_user($id);
        adm_assert_owner_remains($db);
        adm_touch_user($db, $id, $actor['username']);
        auth_audit($actor['username'], 'user.disable', (string) $user['username'],
                   ['id' => $id, 'revoked' => $revoked, 'via' => 'delete']);

        return ['username' => (string) $user['username'], 'revoked_sessions' => $revoked, 'changed' => true];
    });

    adm_ok($out);
}
