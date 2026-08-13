<?php
/**
 * CAPI Console — Admin API foundation (E9-ADMIN-006).         Carl, 2026-08-08
 * Design: deliverables/CSWeb/admin-portal/DESIGN.md §2, §4
 *
 * Everything shared by every admin endpoint: one response envelope, one CSRF
 * check, one in-process permission gate, one transaction helper, one
 * request_id, one catch-all.
 *
 * "One" is the whole design. A file-per-route admin API ends up with four
 * subtly different permission checks and the weakest one decides.
 *
 * The in-process permission gate is NOT redundant with the nginx auth_request
 * gate. It is load-bearing twice over: before cutover the nginx gate is not
 * enforcing at all, and after cutover it is one config edit away from not
 * enforcing. An admin API that trusts a header it did not verify is an admin
 * API that a single misplaced `proxy_set_header` turns into a public one.
 */
declare(strict_types=1);

$AUTH_LIB = is_dir('/var/www/private/capi-auth') ? '/var/www/private/capi-auth' : __DIR__;
require_once $AUTH_LIB . '/lib.php';

/**
 * Accounts that may never be disabled, demoted or deleted through the API,
 * on top of the last-owner invariant. These are the estate's existing
 * lockout-insurance logins (they were the ROOT_ADMINS of the htpasswd-era
 * admin screen and were imported into console_users with everything else).
 *
 * The real break-glass is the alt-port vhost in E9-ADMIN-010, not a row in
 * this table — a protected row is no help if the provider itself is down.
 * This is the second line, not the first.
 */
if (!defined('ADM_PROTECTED_USERS')) {
    $bg = getenv('CAPI_BREAKGLASS_USERS');
    define('ADM_PROTECTED_USERS', array_values(array_filter(array_map(
        'trim',
        explode(',', is_string($bg) && $bg !== '' ? $bg : 'aspsi,marriz_admin')
    ))));
}

/** Idempotency records older than this are pruned opportunistically. */
const ADM_IDEM_TTL_SECS = 24 * 60 * 60;

/**
 * Is the identity provider the thing that actually decides access yet?
 *
 * Between now and cutover the answer is no: nginx still gates /docs/ with
 * Apache's FilesMatch + .htpasswd, and console_users is a parallel store that
 * enforces nothing. An account created in that window is real, correct and
 * completely unable to sign in — and an admin portal that does not say so is
 * lying by omission, which is the same class of defect as the "disable user"
 * no-op this module was built to remove.
 *
 * Set `CAPI_IDP_GATE=live` on the webserver service as cutover step C6. Until
 * then every create and reset says plainly that the credential is not usable.
 */
function adm_gate_is_live(): bool
{
    return strtolower((string) getenv('CAPI_IDP_GATE')) === 'live';
}

/** The warning to attach to anything that mints a credential pre-cutover. */
function adm_gate_notice(): ?string
{
    return adm_gate_is_live() ? null
        : 'The console gate has not been cut over yet, so this account cannot sign in '
        . 'to /docs/ until it is. Nothing else about the account is provisional.';
}

// ---------------------------------------------------------------------------
// Errors
// ---------------------------------------------------------------------------

/**
 * An error we chose to return. Anything else that escapes is a bug and gets
 * the catch-all's generic 500 — the distinction matters, because only the
 * first kind may put its message in front of a user.
 */
final class AdmError extends RuntimeException
{
    public function __construct(
        public readonly string $errCode,
        string $message,
        public readonly int $status = 400,
        public readonly string $field = ''
    ) {
        parent::__construct($message);
    }
}

function adm_bad(string $msg, string $field = ''): AdmError
{
    return new AdmError('invalid', $msg, 400, $field);
}

// ---------------------------------------------------------------------------
// Request identity and output
// ---------------------------------------------------------------------------

function adm_request_id(): string
{
    return auth_request_id();
}

function adm_json(int $status, array $payload): never
{
    if (!headers_sent()) {
        http_response_code($status);
        header('Content-Type: application/json; charset=utf-8');
        header('X-Content-Type-Options: nosniff');
        header('Cache-Control: no-store, private');
        header('X-Request-Id: ' . adm_request_id());
    }
    echo json_encode($payload + ['request_id' => adm_request_id()],
                     JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
    exit;
}

/**
 * `ok` is spelled the same as the legacy admin/api.php envelope on purpose:
 * the existing frontend fetch wrapper checks `j.ok` and would otherwise have
 * to be forked during the transition.
 */
function adm_ok(array $data = [], int $status = 200): never
{
    adm_json($status, ['ok' => true, 'data' => $data]);
}

function adm_error(AdmError $e): never
{
    adm_json($e->status, ['ok' => false, 'error' => [
        'code'    => $e->errCode,
        'message' => $e->getMessage(),
        'field'   => $e->field,
    ]]);
}

/**
 * Install the catch-all. Called once by the front controller, before routing.
 *
 * This exists because `log_errors` is Off in this image: an uncaught fatal is
 * a completely blank 500 with no line anywhere. Writing the exception to
 * console_audit as verb `error` makes console_audit the error log — which is
 * also why request_id was added to that table in migration 002.
 */
function adm_install_handlers(): void
{
    set_exception_handler(static function (Throwable $e): void {
        if ($e instanceof AdmError) { adm_error($e); }
        adm_log_exception($e);
        adm_json(500, ['ok' => false, 'error' => [
            'code'    => 'internal',
            'message' => 'Something went wrong. Quote the request id when reporting it.',
            'field'   => '',
        ]]);
    });

    // A fatal (out of memory, timeout) never reaches the exception handler.
    register_shutdown_function(static function (): void {
        $err = error_get_last();
        if ($err === null || !in_array($err['type'], [E_ERROR, E_PARSE, E_CORE_ERROR, E_COMPILE_ERROR], true)) {
            return;
        }
        try {
            auth_audit(adm_actor_name(), 'error', 'fatal', [
                'msg'  => $err['message'],
                'file' => basename((string) $err['file']) . ':' . $err['line'],
            ]);
        } catch (Throwable) { /* nothing left to do at this point */ }
        if (!headers_sent()) {
            http_response_code(500);
            header('Content-Type: application/json; charset=utf-8');
            echo json_encode(['ok' => false, 'error' => ['code' => 'internal',
                'message' => 'Something went wrong.', 'field' => ''],
                'request_id' => adm_request_id()]);
        }
    });
}

function adm_log_exception(Throwable $e): void
{
    try {
        auth_audit(adm_actor_name(), 'error', adm_route_label(), [
            'class' => get_class($e),
            // The message can carry SQL fragments; it goes to the audit table,
            // which is admin-readable, never to the HTTP response.
            'msg'   => substr($e->getMessage(), 0, 500),
            'at'    => basename($e->getFile()) . ':' . $e->getLine(),
        ]);
    } catch (Throwable) { /* audit is best-effort; never mask the original */ }
    error_log('capi-admin ' . adm_request_id() . ': ' . $e->getMessage());
}

function adm_route_label(): string
{
    return ($_SERVER['REQUEST_METHOD'] ?? '?') . ' ' .
           substr(strtok((string) ($_SERVER['REQUEST_URI'] ?? ''), '?'), 0, 200);
}

// ---------------------------------------------------------------------------
// Authentication and authorisation
// ---------------------------------------------------------------------------

/**
 * The signed-in actor, resolved from the session cookie — not from a header.
 *
 * X-Auth-User is set by nginx after cutover and is genuinely trustworthy
 * there (E9-ADMIN-009 blanks any client-supplied copy), but this endpoint has
 * to work identically before cutover, and re-resolving costs one query on a
 * page that is not on the hot path.
 *
 * @return array{user_id:int,username:string,sid_hash:string,must_change:bool,
 *               roles:string[],perms:string[]}|null
 */
function adm_actor(): ?array
{
    static $actor = false;
    if ($actor !== false) { return $actor; }

    $sess = auth_session_resolve($_COOKIE[AUTH_COOKIE] ?? null);
    if ($sess === null) { return $actor = null; }

    // Roles and permissions come back with the session (E9-ADMIN-030), so
    // this is one query rather than two.
    return $actor = [
        'user_id'     => (int) $sess['user_id'],
        'username'    => (string) $sess['username'],
        'sid_hash'    => (string) $sess['sid_hash'],
        'must_change' => ((int) $sess['must_change'] === 1),
        'roles'       => $sess['roles'],
        'perms'       => $sess['perms'],
    ];
}

/** Never throws — used by the audit paths, which must work even mid-failure. */
function adm_actor_name(): string
{
    try {
        $a = adm_actor();
        return $a === null ? '' : $a['username'];
    } catch (Throwable) {
        return '';
    }
}

/**
 * Require a signed-in session holding $perm. Returns the actor.
 *
 * must_change is a hard stop rather than a warning: an account still on its
 * setup password is, for our purposes, an account whose password is known to
 * whoever set it up. It may reach exactly one route — its own password change.
 */
function adm_require_perm(string $perm): array
{
    $a = adm_actor();
    if ($a === null) {
        throw new AdmError('unauthenticated', 'Sign in to continue.', 401);
    }
    if ($a['must_change']) {
        throw new AdmError('password_change_required',
            'Set a new password before using the admin tools.', 403);
    }
    if ($perm !== '' && !in_array($perm, $a['perms'], true)) {
        auth_audit($a['username'], 'perm.deny', adm_route_label(), ['need' => $perm]);
        throw new AdmError('forbidden', 'You do not have permission to do that.', 403);
    }
    return $a;
}

function adm_has_perm(array $actor, string $perm): bool
{
    return in_array($perm, $actor['perms'], true);
}

// ---------------------------------------------------------------------------
// Request body, CSRF, origin
// ---------------------------------------------------------------------------

function adm_raw_body(): string
{
    static $raw = null;
    if ($raw === null) { $raw = (string) file_get_contents('php://input'); }
    return $raw;
}

/** @return array<string,mixed> */
function adm_body(): array
{
    static $body = null;
    if ($body !== null) { return $body; }

    $raw = adm_raw_body();
    if ($raw === '') { return $body = []; }
    $j = json_decode($raw, true);
    if (!is_array($j)) { throw adm_bad('Malformed JSON body.'); }
    return $body = $j;
}

/**
 * Double-submit CSRF plus a same-origin check.
 *
 * The token alone is sufficient against classic CSRF. The Origin check is here
 * for the subdomain case: `capi_csrf` is a host cookie today but any
 * *.asiansocial.org host can currently set one (that is E9-ADMIN-045), so a
 * compromised sibling host could plant a token it also knows. Comparing Origin
 * to Host costs nothing and closes that until the `__Host-` prefix lands.
 */
function adm_require_csrf(): void
{
    $sent = $_SERVER['HTTP_X_CSRF_TOKEN'] ?? null;
    if ($sent === null) {
        $b = adm_body();
        $sent = isset($b['_csrf']) && is_string($b['_csrf']) ? $b['_csrf'] : null;
    }
    if (!auth_csrf_ok($sent)) {
        throw new AdmError('csrf', 'Your session token is missing or stale. Reload the page.', 403);
    }

    $origin = (string) ($_SERVER['HTTP_ORIGIN'] ?? '');
    if ($origin !== '') {
        $host = strtolower((string) parse_url($origin, PHP_URL_HOST));
        $self = strtolower((string) ($_SERVER['HTTP_HOST'] ?? ''));
        // Strip any :port before comparing; the proxy terminates TLS on 443
        // but forwards Host verbatim, so these normally match exactly.
        $self = explode(':', $self)[0];
        if ($host !== '' && $host !== $self) {
            throw new AdmError('csrf', 'Cross-origin request refused.', 403);
        }
    }
}

// ---------------------------------------------------------------------------
// Transactions
// ---------------------------------------------------------------------------

/**
 * Run $fn inside one transaction. Every multi-statement invariant in this
 * module depends on this: create writes a user AND its roles AND its audit
 * row, and a half-created user with no role is an account that exists and can
 * sign in to nothing — visible in the list, invisible in the ACL.
 *
 * @template T
 * @param callable(PDO):T $fn
 * @return T
 */
function adm_tx(callable $fn)
{
    $db = auth_db();
    if ($db->inTransaction()) { return $fn($db); }   // nested call: join the caller's

    $db->beginTransaction();
    try {
        $out = $fn($db);
        $db->commit();
        return $out;
    } catch (Throwable $e) {
        if ($db->inTransaction()) { $db->rollBack(); }
        throw $e;
    }
}

// ---------------------------------------------------------------------------
// Idempotency
// ---------------------------------------------------------------------------

/**
 * Replay protection for mutations that are not naturally idempotent.
 *
 * Returns null when this is a fresh request (the caller proceeds, then calls
 * adm_idem_store with the response). Otherwise the endpoint has already run
 * and this replays the stored answer verbatim — it never runs twice.
 *
 * The claim row is inserted with status 0 BEFORE the work, so two concurrent
 * clicks race on the primary key rather than both minting a password.
 */
function adm_idem_begin(string $endpoint, string $actor): ?string
{
    $client = trim((string) ($_SERVER['HTTP_IDEMPOTENCY_KEY'] ?? ''));
    if ($client === '') { return null; }
    if (strlen($client) > 128) { throw adm_bad('Idempotency-Key is too long.'); }

    $key  = hash('sha256', $actor . '|' . $endpoint . '|' . $client);
    $bsha = hash('sha256', adm_raw_body());
    $db   = auth_db();

    try {
        $db->prepare(
            'INSERT INTO console_idem (idem_key, actor, endpoint, status, body_sha256)
             VALUES (?, ?, ?, 0, ?)'
        )->execute([$key, substr($actor, 0, 64), substr($endpoint, 0, 160), $bsha]);
        return $key;                                   // fresh — caller proceeds
    } catch (PDOException $e) {
        if ($e->getCode() !== '23000') { throw $e; }   // not a duplicate key
    }

    $st = $db->prepare('SELECT status, body_sha256, response FROM console_idem WHERE idem_key = ?');
    $st->execute([$key]);
    $row = $st->fetch();
    if (!$row) { return $key; }                        // vanished between calls; treat as fresh

    if (!hash_equals((string) $row['body_sha256'], $bsha)) {
        throw new AdmError('idempotency_mismatch',
            'That Idempotency-Key was already used with a different request body.', 422);
    }
    if ((int) $row['status'] === 0) {
        throw new AdmError('in_progress',
            'The same request is still being processed. Try again in a moment.', 409);
    }

    $payload = json_decode((string) $row['response'], true);
    adm_json((int) $row['status'], is_array($payload) ? $payload : ['ok' => true, 'data' => []]);
}

function adm_idem_store(?string $key, int $status, array $payload): void
{
    if ($key === null) { return; }
    try {
        auth_db()->prepare('UPDATE console_idem SET status = ?, response = ? WHERE idem_key = ?')
                 ->execute([$status, json_encode($payload, JSON_UNESCAPED_SLASHES), $key]);
        // Opportunistic prune; there is no cron for this table yet (E9-ADMIN-043).
        auth_db()->prepare('DELETE FROM console_idem WHERE created_at < DATE_SUB(NOW(), INTERVAL ? SECOND)')
                 ->execute([ADM_IDEM_TTL_SECS]);
    } catch (Throwable $e) {
        error_log('capi-admin idem store failed: ' . $e->getMessage());
    }
}

/** Terminal success helper that records the response for replay first. */
function adm_ok_idem(?string $key, array $data, int $status = 200): never
{
    $payload = ['ok' => true, 'data' => $data];
    adm_idem_store($key, $status, $payload);
    adm_json($status, $payload);
}

// ---------------------------------------------------------------------------
// Input helpers
// ---------------------------------------------------------------------------

function adm_str(array $src, string $key, int $max = 255, bool $required = false): string
{
    $v = isset($src[$key]) && is_scalar($src[$key]) ? trim((string) $src[$key]) : '';
    if ($required && $v === '') { throw adm_bad(ucfirst(str_replace('_', ' ', $key)) . ' is required.', $key); }
    if (strlen($v) > $max) { throw adm_bad('That value is too long (max ' . $max . ').', $key); }
    return $v;
}

function adm_int(array $src, string $key, int $default = 0, int $min = PHP_INT_MIN, int $max = PHP_INT_MAX): int
{
    if (!isset($src[$key]) || $src[$key] === '' || !is_scalar($src[$key])) { return $default; }
    $v = (int) $src[$key];
    if ($v < $min || $v > $max) { throw adm_bad('Value out of range.', $key); }
    return $v;
}

/**
 * Usernames are deliberately narrower than the legacy screen's rule: no
 * leading/trailing separator, and lowercase only. Mixed case in a store whose
 * UNIQUE index is case-insensitive (utf8mb4_unicode_ci) means `Carl` and
 * `carl` collide at insert time with an opaque 23000.
 *
 * NOTE ON CASE, so nobody "fixes" this in the wrong direction: this predicate
 * rejects uppercase, but adm_users_create() lowercases BEFORE calling it, so
 * `Carl` is normalised to `carl` rather than refused. That is intended.
 * auth_find_user() matches under the same case-insensitive collation, so
 * signing in as `Carl` works either way — refusing the input would be friction
 * with no benefit. The response returns the canonical stored name, which is
 * what the admin hands over. Verified end-to-end on 2026-08-08.
 */
function adm_valid_username(string $u): bool
{
    // \z, not $. In PCRE `$` also matches immediately before a trailing
    // newline, so /...$/ accepts "carl\n" — which then becomes a username
    // carrying a line break into log lines, CSV exports and any future
    // htpasswd-shaped file. Caught by test_admin.php.
    return (bool) preg_match('/^[a-z0-9][a-z0-9._-]{1,30}[a-z0-9]\z/', $u);
}

/**
 * A temporary password an admin will read aloud or paste into a chat message.
 * Ambiguous glyphs are excluded (no 0/O, 1/l/I) because the failure mode is a
 * support round-trip, and the entropy loss is irrelevant for a credential that
 * must be changed at first use.
 */
function adm_temp_password(): string
{
    $alphabet = 'abcdefghijkmnpqrstuvwxyzACDEFGHJKLMNPQRSTUVWXYZ23456789';
    $n = strlen($alphabet) - 1;
    $out = '';
    for ($i = 0; $i < 16; $i++) { $out .= $alphabet[random_int(0, $n)]; }
    // Grouped for reading: xxxx-xxxx-xxxx-xxxx.
    return implode('-', str_split($out, 4));
}

function adm_is_protected(string $username): bool
{
    return in_array($username, ADM_PROTECTED_USERS, true);
}

// ---------------------------------------------------------------------------
// Shared invariants
// ---------------------------------------------------------------------------

/**
 * Refuse to leave the system with no active owner.
 *
 * Called INSIDE the transaction, after the change has been applied but before
 * commit, and it locks the candidate rows — checking before the write is a
 * race that two concurrent demotions win together, each seeing the other's
 * owner still in place.
 */
function adm_assert_owner_remains(PDO $db): void
{
    // Select the ids and count in PHP rather than asking MySQL for a COUNT(*).
    // An aggregate collapses the result set, and what this needs is a lock on
    // the actual owner ROWS so a concurrent demotion of a different owner
    // blocks here instead of committing alongside us. Counting in PHP is the
    // cheap way to be sure of that; there are five roles and twenty users.
    $rows = $db->query(
        "SELECT u.id FROM console_users u
           JOIN console_user_roles ur ON ur.user_id = u.id
           JOIN console_roles r       ON r.id = ur.role_id
          WHERE r.name = 'owner' AND u.status = 'active'
          FOR UPDATE"
    )->fetchAll();

    if (count($rows) < 1) {
        throw new AdmError('last_owner',
            'That would leave the console with no active owner.', 409);
    }
}

/** @return array{id:int,name:string}|null */
function adm_role_by_name(PDO $db, string $name): ?array
{
    $st = $db->prepare('SELECT id, name, label, version, is_protected FROM console_roles WHERE name = ?');
    $st->execute([$name]);
    $r = $st->fetch();
    return $r ?: null;
}

function adm_user_row(PDO $db, int $id, bool $lock = false): array
{
    $st = $db->prepare('SELECT * FROM console_users WHERE id = ?' . ($lock ? ' FOR UPDATE' : ''));
    $st->execute([$id]);
    $u = $st->fetch();
    if (!$u) { throw new AdmError('not_found', 'No such user.', 404); }
    return $u;
}

/**
 * Optimistic concurrency. The client sends the row_version it read; if the row
 * has moved on, the edit is refused rather than silently overwriting whatever
 * the other admin just did.
 */
function adm_check_row_version(array $user, array $body): void
{
    if (!array_key_exists('row_version', $body)) {
        throw adm_bad('row_version is required so concurrent edits cannot overwrite each other.', 'row_version');
    }
    if ((int) $body['row_version'] !== (int) $user['row_version']) {
        throw new AdmError('conflict',
            'Someone else changed this user while you were editing. Reload and try again.', 409, 'row_version');
    }
}

function adm_touch_user(PDO $db, int $id, string $actor): void
{
    $db->prepare(
        'UPDATE console_users SET row_version = row_version + 1, updated_at = NOW(), updated_by = ?
          WHERE id = ?'
    )->execute([substr($actor, 0, 64), $id]);
}
