<?php
/**
 * CAPI Console — Admin API (Carl, 2026-07-27; repointed 2026-08-08).
 *
 * Single JSON endpoint behind the /docs/admin/ gate.
 * Resources:  session · users · alerts · plan · activities · audit
 *
 * E9-ADMIN-004 — THE CUTOVER BLOCKER, closed here.
 * -----------------------------------------------------------------------
 * Until now this file was the only thing that administered console access,
 * and it did so by editing `.htpasswd` and the `Require user` lines in three
 * `.htaccess` files. After the identity provider takes over the gate, those
 * files stop being consulted — so every write here would have reported
 * success while changing nothing that decides access. "Disable user" would
 * have said Done and the account would have kept working. That is the single
 * worst failure an access-control screen can have, so the writes are gone
 * rather than left to rot:
 *
 *   - users GET   now reads console_users / console_user_roles, the store the
 *                 provider actually consults.
 *   - create | password | tier | delete  return 501 with a pointer to the new
 *                 admin API. They are not silently disabled; a 501 with a
 *                 message is the difference between "this moved" and "this is
 *                 broken".
 *   - actor()     prefers X-Auth-User (set by nginx after cutover) and the
 *                 console session, because PHP_AUTH_USER and REMOTE_USER are
 *                 both empty once mod_auth_form is retired — every audit row
 *                 would otherwise read `unknown`.
 *   - canary_ok() is gone. It probed Apache directly on loopback, bypassing
 *                 the openresty gate entirely, so after cutover it would have
 *                 answered 200 forever regardless of what the real front door
 *                 was doing. A canary that cannot die is worse than none.
 *
 * The htpasswd files are still READ, in one place only: the drift report on
 * the users list, which shows accounts present in one store and not the
 * other. That comparison is exactly what you want to look at before flipping
 * the gate, and it is the reason those helpers survive.
 *
 * Alerts / plan / activities keep their file-backed writes. They are
 * configuration, not access control, and nothing about the cutover changes
 * where they live.
 */
declare(strict_types=1);
ini_set('display_errors', '0');
header('Content-Type: application/json');
header('X-Content-Type-Options: nosniff');
header('Cache-Control: no-store');

// The identity library. Loaded defensively: this screen managed alerts and
// activities long before the provider existed, and a provider outage must
// degrade the users tab, not take the whole admin app down with it.
$CAPI_AUTH_LIB = is_dir('/var/www/private/capi-auth') ? '/var/www/private/capi-auth' : '';
$CAPI_AUTH_OK  = false;
if ($CAPI_AUTH_LIB !== '' && is_file($CAPI_AUTH_LIB . '/lib.php')) {
    try {
        require_once $CAPI_AUTH_LIB . '/lib.php';
        $CAPI_AUTH_OK = true;
    } catch (Throwable $e) {
        error_log('admin/api.php: identity library unavailable: ' . $e->getMessage());
    }
}

const WWW      = '/var/www/html';
// Read-only now, for the drift report. The three .htaccess gate files this
// file used to rewrite (DOCS_HT / DATA_HT / ADMIN_HT) are no longer referenced
// at all — see E9-ADMIN-004 in the header comment.
const HTPASSWD = WWW . '/.htpasswd-docs';
const REG      = __DIR__ . '/activities-registry.json';
const ALERTS   = __DIR__ . '/alerts.json';       // mirrored to /opt by the sync cron
const AUDIT    = __DIR__ . '/audit.log';
const BAK      = __DIR__ . '/backups';
const FEED     = WWW . '/docs/sync-feed.json';
const TARGETS  = WWW . '/docs/admin/targets-control.json';  // provisional flags only

const TIERS  = ['field', 'staff', 'admin'];
const INSTS  = ['f1', 'f3', 'f4', 'f2'];
// Never let the UI lock everyone out: these accounts always keep admin.
const ROOT_ADMINS = ['aspsi', 'marriz_admin'];

/** Read + decode JSON, tolerating a missing file. Needed because
 *  declare(strict_types=1) turns json_decode(false) into a TypeError when
 *  file_get_contents() misses -- a 500 on any absent config file. */
function read_json(string $path) {
    $raw = @file_get_contents($path);
    if (!is_string($raw) || $raw === '') { return null; }
    return json_decode($raw, true);
}

/**
 * Who is making this request.
 *
 * Order matters and each step covers a different era:
 *   1. X-Auth-User  — set by nginx from the auth_request subrequest after
 *                     cutover. E9-ADMIN-009 blanks any client-supplied copy at
 *                     the edge, which is what makes it trustworthy here.
 *   2. the console session cookie — works before AND after cutover, and is
 *                     verified against the database rather than taken on
 *                     trust; this is the path that runs today.
 *   3. PHP_AUTH_USER / REMOTE_USER — mod_auth_form's variables. Both go empty
 *                     at cutover, which is why they are last rather than
 *                     first as they were before.
 */
function actor(): string {
    static $who = null;
    if ($who !== null) { return $who; }

    $hdr = trim((string) ($_SERVER['HTTP_X_AUTH_USER'] ?? ''));
    // \z, not $: `$` also matches before a trailing newline, and this value is
    // written verbatim into every audit line this file emits.
    if ($hdr !== '' && preg_match('/^[A-Za-z0-9._-]{2,64}\z/', $hdr)) { return $who = $hdr; }

    if ($GLOBALS['CAPI_AUTH_OK'] ?? false) {
        try {
            $s = auth_session_resolve($_COOKIE[AUTH_COOKIE] ?? null);
            if ($s !== null) { return $who = (string) $s['username']; }
        } catch (Throwable $e) {
            error_log('admin/api.php: session lookup failed: ' . $e->getMessage());
        }
    }

    $legacy = $_SERVER['PHP_AUTH_USER'] ?? $_SERVER['REMOTE_USER'] ?? '';
    return $who = ($legacy !== '' ? (string) $legacy : 'unknown');
}

/** A write path that has moved to the new admin API. Never a silent no-op. */
function moved(string $what): void {
    http_response_code(501);
    echo json_encode(['ok' => false,
        'error' => $what . ' has moved. Account changes are now made in the CAPI Console '
                 . 'admin portal, which writes to the identity provider — this screen '
                 . 'could only edit .htpasswd, which the gate no longer reads.',
        'moved_to' => '/docs/idp/admin/users',
        'code' => 'moved']);
    exit;
}

function fail(string $msg, int $code = 400) {
    http_response_code($code);
    echo json_encode(['ok' => false, 'error' => $msg]);
    exit;
}

function ok(array $data = []) {
    echo json_encode(['ok' => true] + $data);
    exit;
}

/**
 * Record a configuration change.
 *
 * Written to BOTH trails on purpose. The file is the one that still works when
 * MySQL is down, which is exactly when you most want a record of what someone
 * just changed. `console_audit` is the one the Audit screen reads — and a
 * screen that calls itself the audit trail while silently omitting every
 * alerting, activity and plan change is worse than one that admits its scope.
 *
 * Verbs keep their existing spelling (`alerts.update`, `plan.provisional`,
 * `activities.save`) so the file trail and the table agree and the two can be
 * read as one history.
 */
function audit(string $action, string $target, array $detail = []): void {
    $line = json_encode([
        'ts' => gmdate('c'), 'actor' => actor(), 'action' => $action,
        'target' => $target, 'detail' => $detail,
        'ip' => $_SERVER['REMOTE_ADDR'] ?? '',
    ]);
    @file_put_contents(AUDIT, $line . "\n", FILE_APPEND | LOCK_EX);

    if ($GLOBALS['CAPI_AUTH_OK'] ?? false) {
        // auth_audit() already swallows its own failures, so a provider outage
        // costs a table row and never the configuration write itself.
        auth_audit(actor(), $action, $target, $detail === [] ? null : $detail);
    }
}

function backup(string $path): void {
    if (!is_dir(BAK)) { @mkdir(BAK, 0755); }
    if (is_file($path)) {
        @copy($path, BAK . '/' . basename($path) . '.' . gmdate('Ymd-His'));
    }
}

function write_atomic(string $path, string $body): bool {
    // Atomic where we can (admin dir: www-data owns the directory), in-place
    // where we cannot (/var/www/html is not writable by www-data, so the
    // temp-file-then-rename dance fails there). In-place writes are always
    // preceded by backup() and followed by a read-back check, and gate files
    // additionally run the loopback canary -- see apply_tier().
    $tmp = $path . '.tmp-' . getmypid();
    if (@file_put_contents($tmp, $body, LOCK_EX) !== false) {
        @chmod($tmp, 0640);
        if (@rename($tmp, $path)) { return true; }
        @unlink($tmp);
    }
    if (!is_writable($path)) { return false; }
    if (@file_put_contents($path, $body, LOCK_EX) === false) { return false; }
    return @file_get_contents($path) === $body;   // read-back proof
}

// canary_ok() was removed in E9-ADMIN-004. It fetched
// http://127.0.0.1/docs/dashboard.html with a spoofed Host header, i.e. it
// asked Apache directly and never traversed the openresty gate that actually
// decides access. After cutover it would have returned 200 no matter what the
// front door was doing, so every gate write would have "passed" its own
// safety check. There is nothing left for it to guard now that the gate
// writes are gone.

// ------------------------------------------------------ users (console store)
//
// The htpasswd readers below are READ-ONLY and exist for one purpose: the
// drift report. Before the gate is flipped, the question worth asking is
// "which accounts exist in one store and not the other", and answering it
// needs both lists side by side.

function htpasswd_users(): array {
    $out = [];
    foreach (@file(HTPASSWD, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) ?: [] as $l) {
        $p = strpos($l, ':');
        if ($p > 0) { $out[] = substr($l, 0, $p); }
    }
    sort($out);
    return $out;
}

/**
 * The five console roles mapped back onto the three legacy tiers, so the
 * existing app.js keeps rendering while Slice B replaces the screen.
 *
 * This is a display shim, not a model. The tiers were a property of which
 * .htaccess file listed you; roles are a property of the account. Anything
 * that needs the truth should read `roles`, which is also in the payload.
 */
function tier_from_roles(array $roles): string {
    if (array_intersect($roles, ['owner', 'programme_admin'])) { return 'admin'; }
    if (array_intersect($roles, ['analyst']))                  { return 'staff'; }
    if ($roles === [])                                         { return 'none'; }
    return 'field';
}

/**
 * Users as the identity provider sees them — the store that decides access
 * after cutover, and therefore the only honest thing for this screen to show.
 *
 * Returns null when the provider is unreachable, so the caller can say so
 * instead of rendering an empty list that looks like "no users exist".
 */
function console_users(): ?array {
    if (!($GLOBALS['CAPI_AUTH_OK'] ?? false)) { return null; }
    try {
        $rows = auth_db()->query(
            'SELECT u.id, u.username, u.full_name, u.status, u.must_change,
                    u.pw_algo, u.last_login_at, u.locked_until,
                    (SELECT GROUP_CONCAT(r.name ORDER BY r.name SEPARATOR ",")
                       FROM console_user_roles ur
                       JOIN console_roles r ON r.id = ur.role_id
                      WHERE ur.user_id = u.id) AS role_csv,
                    (SELECT COUNT(*) FROM console_sessions s
                      WHERE s.user_id = u.id AND s.revoked_at IS NULL
                        AND s.expires_at > NOW()) AS live_sessions
               FROM console_users u ORDER BY u.username'
        )->fetchAll();
    } catch (Throwable $e) {
        error_log('admin/api.php: console_users failed: ' . $e->getMessage());
        return null;
    }

    $out = [];
    foreach ($rows as $r) {
        $roles = ($r['role_csv'] ?? '') === '' || $r['role_csv'] === null
                   ? [] : explode(',', (string) $r['role_csv']);
        $out[] = [
            'id'            => (int) $r['id'],
            'user'          => (string) $r['username'],
            'full_name'     => (string) $r['full_name'],
            'roles'         => $roles,
            'tier'          => tier_from_roles($roles),
            'status'        => (string) $r['status'],
            'must_change'   => ((int) $r['must_change'] === 1),
            'pw_algo'       => (string) $r['pw_algo'],
            'locked'        => $r['locked_until'] !== null,
            'live_sessions' => (int) $r['live_sessions'],
            'last_login'    => $r['last_login_at'],
            'protected'     => in_array((string) $r['username'], ROOT_ADMINS, true),
        ];
    }
    return $out;
}

function last_seen(): array {
    $out = [];
    $j = read_json(FEED);
    foreach (($j['events'] ?? []) as $e) {
        $u = $e['user'] ?? '';
        if ($u && (!isset($out[$u]) || ($e['time'] ?? '') > $out[$u])) {
            $out[$u] = $e['time'] ?? '';
        }
    }
    return $out;
}

// apply_tier() / set_require_list() were removed in E9-ADMIN-004 along with
// the canary. They rewrote `Require user` lines in three .htaccess files —
// the mechanism the identity provider replaces. Keeping them would mean this
// screen could still edit a file nothing reads, which is exactly the silent
// no-op the cutover has to be free of.

// ------------------------------------------------------------------- dispatch
$r = $_GET['r'] ?? '';
$isPost = $_SERVER['REQUEST_METHOD'] === 'POST';
$body = [];
if ($isPost) {
    $raw = file_get_contents('php://input');
    $body = json_decode(is_string($raw) && $raw !== '' ? $raw : '[]', true);
    if (!is_array($body)) { fail('malformed JSON body'); }
    // CSRF: the SPA echoes the token the shell issued in the session
    if (!hash_equals($_COOKIE['adm_csrf'] ?? '', (string)($body['_csrf'] ?? ''))) {
        fail('bad or missing CSRF token', 403);
    }
}

switch ($r) {

case 'session': {
    $roles = [];
    $perms = [];
    if ($CAPI_AUTH_OK) {
        try {
            $s = auth_session_resolve($_COOKIE[AUTH_COOKIE] ?? null);
            if ($s !== null) {
                // Carried on the session since E9-ADMIN-030.
                $roles = $s['roles'];
                $perms = $s['perms'];
            }
        } catch (Throwable $e) { /* leave both empty; the screen still loads */ }
    }
    ok(['user' => actor(), 'tiers' => TIERS, 'insts' => INSTS,
        'roles' => $roles, 'perms' => $perms,
        'user_writes_moved' => true]);
}

case 'users': {
    if (!$isPost) {
        $rows = console_users();
        if ($rows === null) {
            // Say so. An empty array here would render as "no accounts",
            // which is indistinguishable from a wiped user table.
            fail('The identity provider is unreachable, so the account list cannot be '
               . 'shown. Alerts, plan and activities are unaffected.', 503);
        }

        // Drift between the two stores, while both still exist. Which side
        // matters depends on which store the gate is reading:
        //   before cutover  htpasswd decides, so `console_only` accounts
        //                   exist but cannot sign in;
        //   after cutover   console_users decides, so `htpasswd_only`
        //                   accounts have just silently lost access.
        // This is the list to look at immediately before flipping.
        $gateLive = strtolower((string) getenv('CAPI_IDP_GATE')) === 'live';
        $ht       = htpasswd_users();
        $console  = array_map(static fn($r) => $r['user'], $rows);
        $seen     = last_seen();
        foreach ($rows as &$r) { $r['last_seen'] = $seen[$r['user']] ?? null; }
        unset($r);

        ok([
            'users'  => $rows,
            'source' => 'console_users',
            'writes' => 'moved',           // app.js may use this to hide buttons
            'drift'  => [
                'htpasswd_only' => array_values(array_diff($ht, $console)),
                'console_only'  => array_values(array_diff($console, $ht)),
                'gate'          => $gateLive ? 'idp' : 'htpasswd',
                'blocking'      => $gateLive ? 'htpasswd_only' : 'console_only',
            ],
        ]);
    }

    // Every write path is gone. See the header comment: these edited
    // .htpasswd and .htaccess, and after cutover that is a store nothing
    // reads — so the honest answer is 501 and a pointer, not a success.
    $act = (string)($body['action'] ?? '');
    switch ($act) {
        case 'create':   moved('Creating an account');
        case 'password': moved('Setting a password');
        case 'tier':     moved('Changing a role');
        case 'delete':   moved('Removing an account');
    }
    fail('unknown users action');
}

case 'alerts': {
    $def = ['webhook' => '', 'silence_hours' => 24, 'high_hours' => 72,
            'expire_hours' => 96, 'max_push' => 6, 'quiet_start' => '', 'quiet_end' => '',
            'types' => ['silence' => true, 'offplan' => true, 'dup' => true]];
    $cur = read_json(ALERTS);
    if (!is_array($cur)) { $cur = $def; }
    $cur += $def;
    if (!$isPost) {
        $shown = $cur;
        $shown['webhook_set'] = $cur['webhook'] !== '';
        $shown['webhook'] = $cur['webhook'] === '' ? '' : '••••••' . substr($cur['webhook'], -6);
        ok(['alerts' => $shown]);
    }
    if (($body['action'] ?? '') === 'test') {
        if ($cur['webhook'] === '') { fail('no webhook configured yet — save one first'); }
        $ch = curl_init($cur['webhook']);
        curl_setopt_array($ch, [CURLOPT_POST => true, CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT => 10, CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
            CURLOPT_POSTFIELDS => json_encode(['text' =>
                ':white_check_mark: CAPI console test alert — sent by ' . actor()])]);
        curl_exec($ch);
        $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        audit('alerts.test', 'webhook', ['http' => $code]);
        if ($code >= 200 && $code < 300) { ok(['sent' => true, 'http' => $code]); }
        fail("webhook responded HTTP $code");
    }
    $new = $cur;
    if (array_key_exists('webhook', $body)) {
        $w = trim((string)$body['webhook']);
        if ($w !== '' && !preg_match('#^https://hooks\.slack\.com/services/[A-Za-z0-9/_-]+$#', $w)) {
            fail('webhook must be a https://hooks.slack.com/services/... URL');
        }
        $new['webhook'] = $w;
    }
    foreach (['silence_hours' => [1, 240], 'high_hours' => [1, 480],
              'expire_hours' => [2, 720], 'max_push' => [1, 50]] as $k => [$lo, $hi]) {
        if (array_key_exists($k, $body)) {
            $v = (int)$body[$k];
            if ($v < $lo || $v > $hi) { fail("$k must be between $lo and $hi"); }
            $new[$k] = $v;
        }
    }
    if ($new['expire_hours'] <= $new['silence_hours']) { fail('expire_hours must exceed silence_hours'); }
    foreach (['quiet_start', 'quiet_end'] as $k) {
        if (array_key_exists($k, $body)) {
            $v = trim((string)$body[$k]);
            if ($v !== '' && !preg_match('/^([01]\d|2[0-3]):[0-5]\d$/', $v)) { fail("$k must be HH:MM or empty"); }
            $new[$k] = $v;
        }
    }
    if (isset($body['types']) && is_array($body['types'])) {
        foreach (['silence', 'offplan', 'dup'] as $t) {
            $new['types'][$t] = !empty($body['types'][$t]);
        }
    }
    backup(ALERTS);
    if (!write_atomic(ALERTS, json_encode($new, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES))) {
        fail('could not write alert config', 500);
    }
    $log = $new; $log['webhook'] = $new['webhook'] === '' ? '(cleared)' : '(set)';
    audit('alerts.update', 'config', $log);
    ok();
}

case 'plan': {
    $ctl = read_json(TARGETS);
    if (!is_array($ctl)) { $ctl = ['provisional' => ['f1' => false, 'f3' => true, 'f4' => true]]; }
    if (!$isPost) {
        $sum = ['label' => null, 'counts' => [], 'targets' => []];
        $t = read_json(WWW . '/docs/admin/targets-summary.json');
        if (is_array($t)) { $sum = $t + $sum; }
        ok(['provisional' => $ctl['provisional'], 'summary' => $sum]);
    }
    if (($body['action'] ?? '') !== 'provisional') { fail('unknown plan action'); }
    $inst = (string)($body['inst'] ?? '');
    if (!in_array($inst, INSTS, true)) { fail('unknown instrument'); }
    $ctl['provisional'][$inst] = !empty($body['value']);
    backup(TARGETS);
    if (!write_atomic(TARGETS, json_encode($ctl, JSON_PRETTY_PRINT))) { fail('could not write', 500); }
    audit('plan.provisional', $inst, ['value' => $ctl['provisional'][$inst]]);
    ok(['provisional' => $ctl['provisional']]);
}

case 'activities': {
    $acts = read_json(REG);
    if (!$isPost) { ok(['activities' => $acts['activities'] ?? []]); }
    $rows = $body['activities'] ?? null;
    if (!is_array($rows) || !count($rows)) { fail('refusing to save an empty registry'); }
    $out = []; $seen = [];
    foreach ($rows as $a) {
        if (!is_array($a)) { continue; }
        $id = trim((string)($a['id'] ?? ''));
        if (!preg_match('/^[A-Za-z0-9_-]{1,12}$/', $id)) { fail("bad activity id '$id'"); }
        if (isset($seen[$id])) { fail("duplicate activity id '$id'"); }
        $seen[$id] = 1;
        $name = trim((string)($a['name'] ?? ''));
        if ($name === '' || mb_strlen($name) > 60) { fail("activity $id needs a label (max 60)"); }
        $phase = (string)($a['phase'] ?? '');
        if (!in_array($phase, ['pretest', 'training', 'survey'], true)) { fail("activity $id: bad phase"); }
        $kind = (string)($a['kind'] ?? 'other');
        if (!in_array($kind, ['pretest','training','collection','listing','mopup','other'], true)) { fail("activity $id: bad kind"); }
        foreach (['start', 'end'] as $f) {
            $v = trim((string)($a[$f] ?? ''));
            if ($v !== '' && !preg_match('/^\d{4}-\d{2}-\d{2}$/', $v)) { fail("activity $id: $f must be YYYY-MM-DD"); }
            $a[$f] = $v === '' ? null : $v;
        }
        if ($a['start'] && $a['end'] && $a['end'] < $a['start']) { fail("activity $id: end before start"); }
        $logins = [];
        foreach ((array)($a['logins'] ?? []) as $lg) {
            $lg = trim((string)$lg);
            if ($lg === '') { continue; }
            if (!preg_match('/^[A-Za-z0-9._-]{2,32}$/', $lg)) { fail("activity $id: bad login '$lg'"); }
            $logins[] = $lg;
        }
        $quotas = [];
        foreach ((array)($a['quotas'] ?? []) as $k => $v) {
            if (!in_array($k, INSTS, true)) { fail("activity $id: unknown instrument '$k'"); }
            $n = (int)$v;
            if ($n < 0 || $n > 999999) { fail("activity $id: quota out of range"); }
            if ($n > 0) { $quotas[$k] = $n; }
        }
        $out[] = ['id' => $id, 'name' => $name, 'phase' => $phase, 'kind' => $kind,
                  'start' => $a['start'], 'end' => $a['end'],
                  'planned' => !empty($a['planned']), 'logins' => $logins,
                  'quotas' => (object)$quotas];
    }
    backup(REG);
    if (!write_atomic(REG, json_encode(['activities' => $out], JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES))) {
        fail('could not write registry', 500);
    }
    audit('activities.save', 'registry', ['count' => count($out),
        'ids' => array_map(fn($a) => $a['id'], $out)]);
    ok(['count' => count($out)]);
}

case 'audit': {
    // Two trails exist during the transition: this file, written by the
    // config screens below, and console_audit, written by the identity
    // provider. Merge them rather than showing one and calling it "the audit
    // trail" — the whole point of an audit trail is that it is not partial.
    $out = [];

    $lines = @file(AUDIT, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) ?: [];
    foreach (array_slice($lines, -200) as $l) {
        $j = json_decode($l, true);
        if (is_array($j)) { $j['source'] = 'config'; $out[] = $j; }
    }

    if ($CAPI_AUTH_OK) {
        try {
            foreach (auth_db()->query(
                'SELECT ts, actor, verb, target, detail, ip FROM console_audit
                  ORDER BY id DESC LIMIT 200'
            )->fetchAll() as $r) {
                $out[] = [
                    // gmdate('c') to match the file trail's format, so the
                    // merged list sorts as strings without a parse step.
                    'ts'     => gmdate('c', strtotime((string) $r['ts'] . ' UTC')),
                    'actor'  => (string) $r['actor'],
                    'action' => (string) $r['verb'],
                    'target' => (string) $r['target'],
                    'detail' => $r['detail'] === null ? [] : json_decode((string) $r['detail'], true),
                    'ip'     => (string) $r['ip'],
                    'source' => 'identity',
                ];
            }
        } catch (Throwable $e) {
            error_log('admin/api.php: console_audit read failed: ' . $e->getMessage());
        }
    }

    usort($out, static fn($a, $b) => strcmp((string) ($b['ts'] ?? ''), (string) ($a['ts'] ?? '')));
    ok(['entries' => array_slice($out, 0, 200)]);
}

default:
    fail('unknown resource', 404);
}
