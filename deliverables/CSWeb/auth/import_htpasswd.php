<?php
/**
 * Migrate the 18 .htpasswd-docs accounts into the identity provider.
 *                                                            Carl, 2026-08-08
 * Plan: capi-console-idp-option-c-plan.md §3.7
 *
 *   php import_htpasswd.php            # dry run — prints the plan, writes nothing
 *   php import_htpasswd.php --apply    # perform the import
 *
 * Design notes that matter:
 *
 *  - NO password reset. $apr1$ hashes are imported as-is with pw_algo='apr1'
 *    and upgraded to argon2id on each owner's next successful sign-in (see
 *    auth_verify_password). A flag-day reset for 18 accounts mid-fieldwork is
 *    how people get locked out of a live survey.
 *
 *  - must_change = 1 on every imported account, and this time it is ENFORCED
 *    (authz.php bars every route but the password page). Storing the flag
 *    without enforcing it is how `100%SetupMe!` stayed live on an admin account.
 *
 *  - Roles come from the tier the account currently holds, read from the live
 *    `Require user` lines — the same source whoami.php uses — so the import
 *    cannot silently grant more than the account has today.
 *
 *  - Username collisions (se_001 vs se-001) are REPORTED, never merged. Two
 *    spellings may be two different people; guessing would hand one person the
 *    other's access.
 */
declare(strict_types=1);

require_once __DIR__ . '/lib.php';

const WWW       = '/var/www/html';
const HTPASSWD  = WWW . '/.htpasswd-docs';
const GATE_DOCS = WWW . '/docs/.htaccess';
const GATE_DATA = WWW . '/docs/data/.htaccess';
const GATE_ADM  = WWW . '/docs/admin/.htaccess';

/** Accounts that should land on `owner` rather than `programme_admin`. */
const OWNERS = ['cplreyes'];

$apply = in_array('--apply', $argv, true);

/**
 * Collisions block --apply by default. This flag says "I looked, they are
 * genuinely separate accounts, import them as separate rows."
 *
 * It never merges anything — each username becomes its own row with its own
 * hash and role, which is exactly what exists in .htpasswd-docs today. The
 * guard exists to stop a silent merge, not to stop an informed import.
 *
 * 2026-08-08: used once. Evidence for the se_00N / se-00N pairs — every
 * hyphen variant has real sync activity (1-10 events); every underscore
 * variant has zero. They are almost certainly dead duplicates from an earlier
 * provisioning batch, but they are ACTIVE on the gate right now, so importing
 * both preserves current access exactly. Disabling the dead ones is a separate,
 * deliberate decision for the admin screen — not something a migration should
 * infer.
 */
$allowDupes = in_array('--allow-duplicates', $argv, true);

function gate_users(string $path): array
{
    $raw = @file_get_contents($path);
    if (!is_string($raw)) { return []; }
    $out = [];
    foreach (preg_split('/\R/', $raw) ?: [] as $line) {
        // Two leading spaces: the admin console writes them that way, so
        // anchoring on ^Require would silently match nothing.
        if (preg_match('/^\s*Require\s+user\s+(.+)$/i', $line, $m)) {
            foreach (preg_split('/\s+/', trim($m[1])) ?: [] as $u) {
                if ($u !== '') { $out[] = $u; }
            }
        }
    }
    return $out;
}

function detect_algo(string $hash): string
{
    if (str_starts_with($hash, '$apr1$'))                       { return 'apr1'; }
    if (str_starts_with($hash, '$2y$') || str_starts_with($hash, '$2b$')) { return 'bcrypt'; }
    if (str_starts_with($hash, '$argon2id$'))                   { return 'argon2id'; }
    return '';
}

// --- read the current world --------------------------------------------------
$lines = @file(HTPASSWD, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
if ($lines === false) {
    fwrite(STDERR, "FATAL: cannot read " . HTPASSWD . "\n");
    exit(2);
}

$docs = gate_users(GATE_DOCS);
$data = gate_users(GATE_DATA);
$adm  = gate_users(GATE_ADM);

$accounts = [];
$skipped  = [];
foreach ($lines as $line) {
    $pos = strpos($line, ':');
    if ($pos === false || $pos === 0) { continue; }
    $user = substr($line, 0, $pos);
    $hash = substr($line, $pos + 1);
    $algo = detect_algo($hash);

    if ($algo === '') {
        // Crypt/DES or plaintext. Refuse rather than import something we cannot
        // verify — an un-verifiable hash would lock the person out silently.
        $skipped[] = [$user, 'unrecognised hash format'];
        continue;
    }

    if (in_array($user, $adm, true))       { $tier = 'admin'; }
    elseif (in_array($user, $data, true))  { $tier = 'staff'; }
    elseif (in_array($user, $docs, true))  { $tier = 'field'; }
    else                                   { $tier = 'none'; }

    $role = match ($tier) {
        'admin' => in_array($user, OWNERS, true) ? 'owner' : 'programme_admin',
        'staff' => 'analyst',
        'field' => 'field_supervisor',
        default => '',
    };

    if ($role === '') {
        // In .htpasswd but on no gate — currently cannot reach anything.
        // Import as disabled so the account is visible in the admin UI and can
        // be enabled deliberately, rather than vanishing from the migration.
        $skipped[] = [$user, 'on no gate — imported as disabled'];
    }

    $accounts[] = [
        'user' => $user, 'hash' => $hash, 'algo' => $algo,
        'tier' => $tier, 'role' => $role ?: 'field_supervisor',
        'status' => $role === '' ? 'disabled' : 'active',
    ];
}

// --- collision check ---------------------------------------------------------
$byNorm = [];
foreach ($accounts as $a) {
    $norm = strtolower(str_replace(['_', '-', '.'], '', $a['user']));
    $byNorm[$norm][] = $a['user'];
}
$collisions = array_filter($byNorm, static fn(array $v): bool => count($v) > 1);

// --- report ------------------------------------------------------------------
printf("%-22s %-10s %-18s %s\n", 'USERNAME', 'ALGO', 'ROLE', 'STATUS');
printf("%s\n", str_repeat('-', 66));
foreach ($accounts as $a) {
    printf("%-22s %-10s %-18s %s\n", $a['user'], $a['algo'], $a['role'], $a['status']);
}
printf("\n%d account(s) to import.\n", count($accounts));

if ($skipped) {
    print("\nNOTES:\n");
    foreach ($skipped as [$u, $why]) { printf("  %-22s %s\n", $u, $why); }
}

if ($collisions) {
    print("\n*** COLLISIONS — resolve by hand before applying ***\n");
    foreach ($collisions as $norm => $variants) {
        printf("  %s -> %s\n", $norm, implode(' , ', $variants));
    }
    print("These may be two spellings of one person, or two people. Not merging.\n");
}

if (!$apply) {
    print("\nDry run. Re-run with --apply to write.\n");
    if ($collisions) {
        print("Collisions present: add --allow-duplicates once you have confirmed\n"
            . "they are separate accounts (they will be imported as separate rows,\n"
            . "never merged).\n");
    }
    exit($collisions ? 1 : 0);
}
if ($collisions && !$allowDupes) {
    fwrite(STDERR, "\nRefusing to apply while collisions are unacknowledged.\n"
                 . "Re-run with --allow-duplicates if they are genuinely separate accounts.\n");
    exit(1);
}
if ($collisions) {
    printf("\nProceeding with %d acknowledged collision group(s) as SEPARATE accounts.\n",
           count($collisions));
}

// --- apply -------------------------------------------------------------------
$db = auth_db();
$db->beginTransaction();
try {
    $roleIds = [];
    foreach ($db->query('SELECT id, name FROM console_roles')->fetchAll() as $r) {
        $roleIds[$r['name']] = (int) $r['id'];
    }

    $insUser = $db->prepare(
        'INSERT INTO console_users (username, pw_hash, pw_algo, must_change, status, created_by)
         VALUES (?, ?, ?, 1, ?, "import")
         ON DUPLICATE KEY UPDATE pw_hash = VALUES(pw_hash), pw_algo = VALUES(pw_algo)'
    );
    $insRole = $db->prepare(
        'INSERT IGNORE INTO console_user_roles (user_id, role_id) VALUES (?, ?)'
    );

    $n = 0;
    foreach ($accounts as $a) {
        $insUser->execute([$a['user'], $a['hash'], $a['algo'], $a['status']]);
        $id = (int) $db->query(
            'SELECT id FROM console_users WHERE username = ' . $db->quote($a['user'])
        )->fetchColumn();
        if (!isset($roleIds[$a['role']])) {
            throw new RuntimeException('role missing from console_roles: ' . $a['role']);
        }
        $insRole->execute([$id, $roleIds[$a['role']]]);
        $n++;
    }
    $db->commit();

    auth_audit('import', 'user.import', '', ['count' => $n]);
    printf("\nImported %d account(s). Every one has must_change = 1.\n", $n);
    print("Legacy hashes upgrade to argon2id on each owner's next sign-in.\n");
} catch (Throwable $e) {
    $db->rollBack();
    fwrite(STDERR, "\nFAILED, rolled back: " . $e->getMessage() . "\n");
    exit(2);
}
