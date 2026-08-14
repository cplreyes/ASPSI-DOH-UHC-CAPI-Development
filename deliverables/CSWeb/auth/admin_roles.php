<?php
/**
 * CAPI Console — Admin API: roles and permissions (E9-ADMIN-007 / -022).
 * Design: deliverables/CSWeb/admin-portal/DESIGN.md §2, §4       Carl, 2026-08-08
 *
 * The 5 x 7 matrix. Reads are open to anyone who administers users, because
 * you cannot sensibly assign a role you are not allowed to look at. Writes are
 * owner-only: a permission edit changes what every holder of that role can
 * reach, which is a different act from moving one person between roles.
 */
declare(strict_types=1);

/**
 * The console's own permission keys, in display order.
 *
 * This list is the allowlist for writes. It deliberately does NOT include
 * F2's eleven PERM_KEYS: those rows may exist in console_role_perms from
 * Phase 2 onward, and the edit path must leave keys it does not recognise
 * untouched rather than deleting them as "unknown".
 */
const ADM_PERM_KEYS = [
    'monitoring.view'  => 'See the sync dashboard and monitoring pages',
    'case.view'        => 'Open an individual respondent case',
    'data.export'      => 'Download microdata and exports',
    'tabulations.view' => 'View the tabulation tables',
    'admin.users'      => 'Administer console accounts',
    'admin.system'     => 'Change system settings (alerts, activities, plan)',
    'audit.view'       => 'Read the audit trail',
];

/**
 * Permissions the `owner` role can never lose. Without this, one careless
 * un-tick in the matrix removes the only route back into user administration
 * and the fix is a root SSH session and a hand-written INSERT.
 */
const ADM_OWNER_FLOOR = ['admin.users', 'admin.system'];

/** Compact role list used by the users screens. */
function adm_roles_brief(PDO $db): array
{
    $rows = $db->query(
        'SELECT r.id, r.name, r.label, r.version, r.is_protected,
                (SELECT COUNT(*) FROM console_user_roles ur WHERE ur.role_id = r.id) AS user_count
           FROM console_roles r ORDER BY r.id'
    )->fetchAll();

    return array_map(static fn(array $r) => [
        'name'       => (string) $r['name'],
        'label'      => (string) $r['label'],
        'version'    => (int) $r['version'],
        'protected'  => ((int) $r['is_protected'] === 1),
        'user_count' => (int) $r['user_count'],
    ], $rows);
}

/**
 * @param array<int,string> $seg path segments after `roles`
 */
function adm_roles_route(string $method, array $seg): never
{
    if ($seg === [] && $method === 'GET') {
        adm_require_perm('admin.users');
        adm_roles_list();
    }

    if (count($seg) === 2 && $seg[1] === 'perms' && $method === 'PUT') {
        adm_roles_set_perms($seg[0]);
    }

    throw new AdmError('not_found', 'No such endpoint.', 404);
}

function adm_roles_list(): never
{
    $db = auth_db();

    $rows = $db->query(
        'SELECT r.id, r.name, r.label, r.version, r.is_protected,
                (SELECT GROUP_CONCAT(p.perm_key ORDER BY p.perm_key SEPARATOR ",")
                   FROM console_role_perms p WHERE p.role_id = r.id) AS perm_csv,
                (SELECT COUNT(*) FROM console_user_roles ur WHERE ur.role_id = r.id) AS user_count
           FROM console_roles r ORDER BY r.id'
    )->fetchAll();

    $roles = [];
    foreach ($rows as $r) {
        $held = $r['perm_csv'] === null || $r['perm_csv'] === ''
                  ? [] : explode(',', (string) $r['perm_csv']);
        $roles[] = [
            'name'       => (string) $r['name'],
            'label'      => (string) $r['label'],
            'version'    => (int) $r['version'],
            'protected'  => ((int) $r['is_protected'] === 1),
            'user_count' => (int) $r['user_count'],
            'perms'      => array_values(array_intersect($held, array_keys(ADM_PERM_KEYS))),
            // Keys we do not manage (Phase 2 / F2). Surfaced read-only so the
            // matrix does not imply this role has nothing else.
            'other_perms' => array_values(array_diff($held, array_keys(ADM_PERM_KEYS))),
        ];
    }

    $actor = adm_actor();
    adm_ok([
        'roles'    => $roles,
        'keys'     => ADM_PERM_KEYS,
        'editable' => $actor !== null && in_array('owner', $actor['roles'], true),
        'floor'    => ['owner' => ADM_OWNER_FLOOR],
    ]);
}

function adm_roles_set_perms(string $roleName): never
{
    $actor = adm_require_perm('admin.system');
    if (!in_array('owner', $actor['roles'], true)) {
        throw new AdmError('forbidden',
            'Only an owner can change what a role is allowed to do.', 403);
    }
    adm_require_csrf();

    $b = adm_body();
    if (!isset($b['perms']) || !is_array($b['perms'])) {
        throw adm_bad('Send the complete list of permissions for this role.', 'perms');
    }

    $want = array_values(array_unique(array_map(
        static fn($p) => strtolower(trim((string) $p)), $b['perms']
    )));
    $unknown = array_diff($want, array_keys(ADM_PERM_KEYS));
    if ($unknown !== []) {
        throw adm_bad('Unknown permission: ' . implode(', ', $unknown) . '.', 'perms');
    }

    $result = adm_tx(static function (PDO $db) use ($actor, $roleName, $want) {
        $st = $db->prepare('SELECT * FROM console_roles WHERE name = ? FOR UPDATE');
        $st->execute([strtolower($roleName)]);
        $role = $st->fetch();
        if (!$role) { throw new AdmError('not_found', 'No such role.', 404); }

        if ($role['name'] === 'owner') {
            $missing = array_diff(ADM_OWNER_FLOOR, $want);
            if ($missing !== []) {
                throw new AdmError('owner_floor',
                    'The owner role must keep ' . implode(' and ', $missing)
                    . ' — removing it would lock everyone out of administration.', 409, 'perms');
            }
        }

        $rid = (int) $role['id'];

        // Read the current set so the audit row records the actual delta, and
        // so a replay of the same set can be reported as a no-op instead of
        // bumping the version and signing everyone out for nothing.
        $cur = $db->prepare(
            'SELECT perm_key FROM console_role_perms WHERE role_id = ? AND perm_key IN ('
            . implode(',', array_fill(0, count(ADM_PERM_KEYS), '?')) . ')'
        );
        $cur->execute(array_merge([$rid], array_keys(ADM_PERM_KEYS)));
        $have = array_map(static fn($r) => (string) $r['perm_key'], $cur->fetchAll());

        sort($have); $sortedWant = $want; sort($sortedWant);
        if ($have === $sortedWant) {
            return ['role' => $role['name'], 'perms' => $sortedWant,
                    'changed' => false, 'version' => (int) $role['version']];
        }

        // Delete only the keys this endpoint manages. `NOT IN (managed)` rows
        // are F2's and must survive an edit made from the console matrix.
        $del = $db->prepare(
            'DELETE FROM console_role_perms WHERE role_id = ? AND perm_key IN ('
            . implode(',', array_fill(0, count(ADM_PERM_KEYS), '?')) . ')'
        );
        $del->execute(array_merge([$rid], array_keys(ADM_PERM_KEYS)));

        $ins = $db->prepare('INSERT INTO console_role_perms (role_id, perm_key) VALUES (?, ?)');
        foreach ($sortedWant as $p) { $ins->execute([$rid, $p]); }

        // The version bump MUST be in this transaction. Split it out and every
        // live session holding this role runs on the old grant set until the
        // second statement lands — which is a window in which a permission you
        // just removed is still in force.
        $db->prepare('UPDATE console_roles SET version = version + 1 WHERE id = ?')->execute([$rid]);

        auth_audit($actor['username'], 'role.perms', (string) $role['name'], [
            'added'   => array_values(array_diff($sortedWant, $have)),
            'removed' => array_values(array_diff($have, $sortedWant)),
        ]);

        return ['role' => $role['name'], 'perms' => $sortedWant,
                'changed' => true, 'version' => ((int) $role['version']) + 1];
    });

    adm_ok($result);
}
