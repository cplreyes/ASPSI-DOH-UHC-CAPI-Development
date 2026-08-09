<?php
/**
 * CAPI Console — unit tests for the admin API's pure helpers.  Carl, 2026-08-08
 *
 *   docker compose exec -T webserver php /var/www/private/capi-auth/test_admin.php
 *
 * Deliberately DB-free: everything here is a decision made before any query
 * runs — what counts as a valid username, which permission keys exist, how a
 * date filter is widened. Those are the parts that fail silently. The
 * DB-backed behaviour (transactions, revocation, last-owner) is E9-ADMIN-040's
 * test_db.php, which needs disposable `zzt_` rows.
 */
declare(strict_types=1);

$LIB = __DIR__;
require_once $LIB . '/acl.php';
require_once $LIB . '/admin_bootstrap.php';
require_once $LIB . '/admin_users.php';
require_once $LIB . '/admin_roles.php';
require_once $LIB . '/admin_audit.php';

$pass = 0;
$fail = 0;

function check(string $what, $got, $want): void
{
    global $pass, $fail;
    $g = is_scalar($got) || $got === null ? var_export($got, true) : json_encode($got);
    $w = is_scalar($want) || $want === null ? var_export($want, true) : json_encode($want);
    if ($g === $w) { $pass++; return; }
    $fail++;
    printf("FAIL  %-52s got %s  want %s\n", $what, $g, $w);
}

/** Assert that $fn throws an AdmError with the given code. */
function throws(string $what, callable $fn, string $wantCode): void
{
    global $pass, $fail;
    try {
        $fn();
    } catch (AdmError $e) {
        if ($e->errCode === $wantCode) { $pass++; return; }
        $fail++;
        printf("FAIL  %-52s threw %s  want %s\n", $what, $e->errCode, $wantCode);
        return;
    } catch (Throwable $e) {
        $fail++;
        printf("FAIL  %-52s threw %s  want AdmError(%s)\n", $what, get_class($e), $wantCode);
        return;
    }
    $fail++;
    printf("FAIL  %-52s did not throw  want %s\n", $what, $wantCode);
}

// ---------------------------------------------------------------------------
// The permission list must not drift between the ACL and the role editor.
//
// This is the highest-value assertion in the file. acl.php decides which
// permission a PATH requires; admin_roles.php decides which permissions the
// matrix can GRANT. If a key exists in one and not the other, you get either a
// permission nobody can be granted (a page no role can reach) or a tick box
// that grants something no path ever checks. Both look fine on screen.
// ---------------------------------------------------------------------------
$aclKeys  = CONSOLE_PERMS;
$editKeys = array_keys(ADM_PERM_KEYS);
sort($aclKeys);
sort($editKeys);
check('perm keys: acl.php == admin_roles.php', $editKeys, $aclKeys);

// The owner floor must be a subset of the keys, or the guard can never be met.
check('owner floor within perm keys', array_diff(ADM_OWNER_FLOOR, $editKeys), []);
// ...and must include the two that gate administration itself.
check('owner floor holds admin.users', in_array('admin.users', ADM_OWNER_FLOOR, true), true);
check('owner floor holds admin.system', in_array('admin.system', ADM_OWNER_FLOOR, true), true);

// ---------------------------------------------------------------------------
// Usernames
// ---------------------------------------------------------------------------
$usernames = [
    'carl'          => true,
    'cplreyes'      => true,
    'se-001'        => true,
    'se_001'        => true,
    'a1b'           => true,
    'marriz.admin'  => true,
    'abc'           => true,

    'ab'            => false,   // two characters cannot satisfy start+middle+end
    'a'             => false,
    ''              => false,
    '-carl'         => false,   // leading separator
    'carl-'         => false,   // trailing separator
    '_carl'         => false,
    'carl_'         => false,
    '.carl'         => false,
    'Carl'          => false,   // uppercase: the UNIQUE index is case-insensitive,
    'CARL'          => false,   // so mixed case collides at INSERT with an opaque 23000
    'carl reyes'    => false,   // space
    'carl@aspsi'    => false,
    'carl/../root'  => false,
    "carl\n"        => false,
    str_repeat('a', 33) => false,
    str_repeat('a', 32) => true,
];
foreach ($usernames as $u => $want) {
    check('username(' . var_export($u, true) . ')', adm_valid_username((string) $u), $want);
}

// The predicate rejects uppercase, but the CREATE endpoint lowercases before
// calling it — so mixed case is normalised, not refused. Asserted here because
// reading adm_valid_username() alone gives the opposite impression, and the
// two behaviours are one strtolower() apart. Confirmed against production
// 2026-08-08: POST username "ZZT_Bad" created "zzt_bad".
foreach (['Carl' => 'carl', 'SE-001' => 'se-001', 'Marriz.Admin' => 'marriz.admin'] as $in => $out) {
    check('create normalises ' . $in, adm_valid_username(strtolower($in)) ? strtolower($in) : 'REJECTED', $out);
}

// ---------------------------------------------------------------------------
// Temporary passwords
// ---------------------------------------------------------------------------
$seen = [];
for ($i = 0; $i < 200; $i++) {
    $p = adm_temp_password();
    $seen[$p] = true;
    if (!preg_match('/^[a-zA-Z2-9]{4}(-[a-zA-Z2-9]{4}){3}$/', $p)) {
        check('temp password shape', $p, 'xxxx-xxxx-xxxx-xxxx');
        break;
    }
    // Ambiguous glyphs cost a support round trip when read aloud or copied
    // out of a chat message; the entropy loss is irrelevant for a credential
    // that must be changed at first use.
    if (preg_match('/[0O1lI]/', $p)) {
        check('temp password excludes ambiguous glyphs', $p, '(none of 0 O 1 l I)');
        break;
    }
}
check('temp password shape/glyphs over 200 draws', true, true);
check('temp passwords are distinct', count($seen), 200);
// 16 characters from a 54-glyph alphabet. Comfortably above the 12-character
// policy floor, which the account holder must satisfy on their own change.
check('temp password length >= policy floor',
      strlen(str_replace('-', '', adm_temp_password())) >= AUTH_MIN_PW_LEN, true);

// ---------------------------------------------------------------------------
// Duplicate grouping — the seven se_00N / se-00N pairs (FR-17)
// ---------------------------------------------------------------------------
check('dup group se_001 == se-001', adm_dup_group('se_001'), adm_dup_group('se-001'));
check('dup group is case-insensitive', adm_dup_group('SE_001'), adm_dup_group('se-001'));
check('dup group se_001 != se_002',
      adm_dup_group('se_001') === adm_dup_group('se_002'), false);
check('dup group leaves dots alone',
      adm_dup_group('marriz.admin') === adm_dup_group('marriz-admin'), false);

// ---------------------------------------------------------------------------
// Input helpers
// ---------------------------------------------------------------------------
check('adm_str trims',            adm_str(['a' => '  x  '], 'a'), 'x');
check('adm_str missing is empty', adm_str([], 'a'), '');
check('adm_str array is empty',   adm_str(['a' => ['x']], 'a'), '');
throws('adm_str required',  static fn() => adm_str([], 'a', 255, true), 'invalid');
throws('adm_str too long',  static fn() => adm_str(['a' => 'xxxxx'], 'a', 4), 'invalid');

check('adm_int default',   adm_int([], 'n', 7), 7);
check('adm_int casts',     adm_int(['n' => '42'], 'n'), 42);
check('adm_int empty',     adm_int(['n' => ''], 'n', 5), 5);
throws('adm_int below min', static fn() => adm_int(['n' => 0], 'n', 0, 1), 'invalid');
throws('adm_int above max', static fn() => adm_int(['n' => 999], 'n', 0, 0, 10), 'invalid');

// ---------------------------------------------------------------------------
// Audit filters
// ---------------------------------------------------------------------------
$cases = [
    // A bare `to` date must cover the whole day. Left as midnight, the last
    // day of every range silently returns nothing — an export that looks
    // complete and is short by a day.
    [['to' => '2026-08-08'],   'a.ts <= ?',  '2026-08-08 23:59:59'],
    [['from' => '2026-08-01'], 'a.ts >= ?',  '2026-08-01 00:00:00'],
    [['from' => '2026-08-01 09:30'], 'a.ts >= ?', '2026-08-01 09:30'],
    [['from' => '2026-08-01T09:30:15'], 'a.ts >= ?', '2026-08-01 09:30:15'],
];
foreach ($cases as $i => [$get, $wantSql, $wantParam]) {
    $_GET = $get;
    [$sql, $params] = adm_audit_filters();
    check("audit filter #$i clause", str_contains($sql, $wantSql), true);
    check("audit filter #$i param",  $params[0], $wantParam);
}

$_GET = ['verb' => 'user.'];
[$sql, $params] = adm_audit_filters();
check('verb family uses LIKE', str_contains($sql, 'a.verb LIKE ?'), true);
check('verb family param',     $params[0], 'user.%');

$_GET = ['verb' => 'login'];
[$sql, $params] = adm_audit_filters();
check('exact verb uses =', str_contains($sql, 'a.verb = ?'), true);

// LIKE metacharacters in user input must not become wildcards: a target
// search for `se_001` must not also match `se-001`, which is the one pair the
// duplicate triage exists to tell apart.
$_GET = ['target' => 'se_001'];
[$sql, $params] = adm_audit_filters();
check('target escapes LIKE underscore', $params[0], '%se\\_001%');

$_GET = ['target' => '100%'];
[$sql, $params] = adm_audit_filters();
check('target escapes LIKE percent', $params[0], '%100\\%%');

$_GET = ['from' => 'yesterday'];
throws('bad date rejected', static fn() => adm_audit_filters(), 'invalid');

$_GET = [];
[$sql, $params] = adm_audit_filters();
check('no filters is a no-op clause', $sql, '1 = 1');
check('no filters binds nothing', $params, []);

// ---------------------------------------------------------------------------
// Protected accounts
// ---------------------------------------------------------------------------
check('protected list is non-empty', count(ADM_PROTECTED_USERS) > 0, true);
foreach (ADM_PROTECTED_USERS as $p) {
    check('protected(' . $p . ')', adm_is_protected($p), true);
}
check('protected(carl)', adm_is_protected('nobody-in-particular'), false);

printf("\n%d passed, %d failed\n", $pass, $fail);
exit($fail === 0 ? 0 : 1);
