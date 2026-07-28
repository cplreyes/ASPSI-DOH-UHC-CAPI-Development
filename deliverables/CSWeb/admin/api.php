<?php
/**
 * CAPI Console — Admin API (Carl, 2026-07-27).
 *
 * Single JSON endpoint behind the existing /docs/admin/ basic-auth gate.
 * Reusing that gate is deliberate: no second auth system to get wrong, and
 * REMOTE_USER gives every audit entry a real actor for free.
 *
 * Resources:  session · users · tiers · alerts · plan · activities · audit
 * Every mutation: strict allowlist validation -> timestamped backup ->
 * atomic write -> audit entry. Writes that touch Apache config additionally
 * run a loopback canary and self-restore if the server starts 500ing.
 */
declare(strict_types=1);
ini_set('display_errors', '0');
header('Content-Type: application/json');
header('X-Content-Type-Options: nosniff');
header('Cache-Control: no-store');

const WWW      = '/var/www/html';
const HTPASSWD = WWW . '/.htpasswd-docs';
const DOCS_HT  = WWW . '/docs/.htaccess';
const DATA_HT  = WWW . '/docs/data/.htaccess';
const ADMIN_HT = WWW . '/docs/admin/.htaccess';
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

function actor(): string {
    return $_SERVER['PHP_AUTH_USER'] ?? $_SERVER['REMOTE_USER'] ?? 'unknown';
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

function audit(string $action, string $target, array $detail = []): void {
    $line = json_encode([
        'ts' => gmdate('c'), 'actor' => actor(), 'action' => $action,
        'target' => $target, 'detail' => $detail,
        'ip' => $_SERVER['REMOTE_ADDR'] ?? '',
    ]);
    @file_put_contents(AUDIT, $line . "\n", FILE_APPEND | LOCK_EX);
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

/** Loopback canary: a healthy gated URL answers 401 to an anonymous request.
 *  A 500 means we just wrote broken Apache config -- restore and shout. */
function canary_ok(): bool {
    $ch = curl_init('http://127.0.0.1/docs/dashboard.html');
    curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 5,
                            CURLOPT_HEADER => false, CURLOPT_NOBODY => true,
                            CURLOPT_HTTPHEADER => ['Host: csweb.asiansocial.org']]);
    curl_exec($ch);
    $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    return $code === 401 || $code === 200;
}

function restore_latest(string $path): void {
    $g = glob(BAK . '/' . basename($path) . '.*');
    if ($g) { rsort($g); @copy($g[0], $path); }
}

// ---------------------------------------------------------------- users/tiers
function htpasswd_users(): array {
    $out = [];
    foreach (@file(HTPASSWD, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) ?: [] as $l) {
        $p = strpos($l, ':');
        if ($p > 0) { $out[] = substr($l, 0, $p); }
    }
    sort($out);
    return $out;
}

/** Parse the `Require user ...` list out of a gate file. */
function require_list(string $file): array {
    foreach (@file($file, FILE_IGNORE_NEW_LINES) ?: [] as $l) {
        if (preg_match('/^\s*Require\s+user\s+(.+)$/i', $l, $m)) {
            return preg_split('/\s+/', trim($m[1]), -1, PREG_SPLIT_NO_EMPTY);
        }
    }
    return [];
}

function set_require_list(string $file, array $users): bool {
    if (!count($users)) { return false; }          // never write an empty gate
    $src = @file_get_contents($file);
    if ($src === false) { return false; }
    $line = '  Require user ' . implode(' ', $users);
    $new = preg_replace('/^\s*Require\s+user\s+.+$/mi', $line, $src, 1, $n);
    if (!$n) { return false; }
    backup($file);
    return write_atomic($file, $new);
}

function tier_of(string $u, array $docs, array $data, array $admin): string {
    if (in_array($u, $admin, true)) { return 'admin'; }
    if (in_array($u, $data, true))  { return 'staff'; }
    if (in_array($u, $docs, true))  { return 'field'; }
    return 'none';
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

function apply_tier(string $user, string $tier): bool {
    $docs = require_list(DOCS_HT); $data = require_list(DATA_HT); $adm = require_list(ADMIN_HT);
    $rm = function (array $a) use ($user) { return array_values(array_diff($a, [$user])); };
    $add = function (array $a) use ($user) { return in_array($user, $a, true) ? $a : array_merge($a, [$user]); };
    $docs = $rm($docs); $data = $rm($data); $adm = $rm($adm);
    if ($tier === 'field') { $docs = $add($docs); }
    if ($tier === 'staff') { $docs = $add($docs); $data = $add($data); }
    if ($tier === 'admin') { $docs = $add($docs); $data = $add($data); $adm = $add($adm); }
    foreach (ROOT_ADMINS as $ra) {                       // lockout insurance
        if (!in_array($ra, $adm, true)) { $adm[] = $ra; }
        if (!in_array($ra, $data, true)) { $data[] = $ra; }
        if (!in_array($ra, $docs, true)) { $docs[] = $ra; }
    }
    $wrote = set_require_list(DOCS_HT, $docs) && set_require_list(DATA_HT, $data)
             && set_require_list(ADMIN_HT, $adm);
    if (!$wrote || !canary_ok()) {
        restore_latest(DOCS_HT); restore_latest(DATA_HT); restore_latest(ADMIN_HT);
        return false;
    }
    return true;
}

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

case 'session':
    ok(['user' => actor(), 'tiers' => TIERS, 'insts' => INSTS]);

case 'users': {
    if (!$isPost) {
        $docs = require_list(DOCS_HT); $data = require_list(DATA_HT); $adm = require_list(ADMIN_HT);
        $seen = last_seen();
        $rows = [];
        foreach (htpasswd_users() as $u) {
            $rows[] = ['user' => $u, 'tier' => tier_of($u, $docs, $data, $adm),
                       'last_seen' => $seen[$u] ?? null,
                       'protected' => in_array($u, ROOT_ADMINS, true)];
        }
        ok(['users' => $rows]);
    }
    $act = $body['action'] ?? '';
    $u = trim((string)($body['user'] ?? ''));
    if (!preg_match('/^[A-Za-z0-9._-]{2,32}$/', $u)) { fail('username must be 2-32 chars: letters, digits, . _ -'); }

    if ($act === 'create' || $act === 'password') {
        $pw = (string)($body['password'] ?? '');
        if (strlen($pw) < 10) { fail('password must be at least 10 characters'); }
        $exists = in_array($u, htpasswd_users(), true);
        if ($act === 'create' && $exists) { fail("user '$u' already exists"); }
        if ($act === 'password' && !$exists) { fail("user '$u' not found"); }
        $hash = password_hash($pw, PASSWORD_BCRYPT);
        $lines = [];
        foreach (@file(HTPASSWD, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) ?: [] as $l) {
            if (strpos($l, $u . ':') !== 0) { $lines[] = $l; }
        }
        $lines[] = $u . ':' . $hash;
        backup(HTPASSWD);
        if (!write_atomic(HTPASSWD, implode("\n", $lines) . "\n")) { fail('could not write htpasswd', 500); }
        @chmod(HTPASSWD, 0640);
        if ($act === 'create') {
            $tier = (string)($body['tier'] ?? 'field');
            if (!in_array($tier, TIERS, true)) { fail('unknown tier'); }
            if (!apply_tier($u, $tier)) { fail('tier write failed; gates restored from backup', 500); }
            audit('user.create', $u, ['tier' => $tier]);
            ok(['user' => $u, 'tier' => $tier]);
        }
        audit('user.password', $u);
        ok(['user' => $u]);
    }

    if ($act === 'tier') {
        $tier = (string)($body['tier'] ?? '');
        if (!in_array($tier, TIERS, true)) { fail('unknown tier'); }
        if (in_array($u, ROOT_ADMINS, true) && $tier !== 'admin') {
            fail("$u is a protected admin and cannot be demoted here");
        }
        if (!in_array($u, htpasswd_users(), true)) { fail("user '$u' not found"); }
        if (!apply_tier($u, $tier)) { fail('tier write failed; gates restored from backup', 500); }
        audit('user.tier', $u, ['tier' => $tier]);
        ok(['user' => $u, 'tier' => $tier]);
    }

    if ($act === 'delete') {
        if (in_array($u, ROOT_ADMINS, true)) { fail("$u is protected and cannot be removed"); }
        $lines = [];
        foreach (@file(HTPASSWD, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) ?: [] as $l) {
            if (strpos($l, $u . ':') !== 0) { $lines[] = $l; }
        }
        backup(HTPASSWD);
        if (!write_atomic(HTPASSWD, implode("\n", $lines) . "\n")) { fail('could not write htpasswd', 500); }
        @chmod(HTPASSWD, 0640);
        $docs = array_values(array_diff(require_list(DOCS_HT), [$u]));
        $data = array_values(array_diff(require_list(DATA_HT), [$u]));
        $adm  = array_values(array_diff(require_list(ADMIN_HT), [$u]));
        set_require_list(DOCS_HT, $docs); set_require_list(DATA_HT, $data); set_require_list(ADMIN_HT, $adm);
        if (!canary_ok()) {
            restore_latest(DOCS_HT); restore_latest(DATA_HT); restore_latest(ADMIN_HT);
            fail('gate write failed; restored from backup', 500);
        }
        audit('user.delete', $u);
        ok(['user' => $u]);
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
    $lines = @file(AUDIT, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) ?: [];
    $lines = array_slice($lines, -200);
    $out = [];
    foreach (array_reverse($lines) as $l) {
        $j = json_decode($l, true);
        if (is_array($j)) { $out[] = $j; }
    }
    ok(['entries' => $out]);
}

default:
    fail('unknown resource', 404);
}
