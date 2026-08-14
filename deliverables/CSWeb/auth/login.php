<?php
/**
 * CAPI Console — sign in.                                    Carl, 2026-08-08
 * Plan: capi-console-idp-option-c-plan.md §3.5
 *
 * Replaces mod_auth_form. The gain that matters is not the form, it is what
 * sits behind it: a server-side session row that logout can actually revoke.
 * The current stateless cookie cannot be revoked at all — sign out, replay the
 * cookie, and you are still in for the rest of the 8 h.
 *
 * Handles: sign-in, forced password change on first use, and sign-out landing.
 */
declare(strict_types=1);
ini_set('display_errors', '0');

$AUTH_LIB = is_dir('/var/www/private/capi-auth') ? '/var/www/private/capi-auth' : __DIR__;
require_once $AUTH_LIB . '/lib.php';

header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');
header('X-Frame-Options: DENY');
header('Referrer-Policy: strict-origin-when-cross-origin');

// Content-Security-Policy on the sign-in page (E9-ADMIN-045).
//
// This page is entirely self-contained — no scripts, no images, no external
// fonts — so it can afford the strictest useful policy: default-src 'none'
// permits nothing at all, and the one inline <style> is allowed by nonce
// rather than by 'unsafe-inline'. If a future edit adds an asset here, the
// page will visibly break rather than quietly widening the policy, which is
// the behaviour worth having on the page that handles passwords.
//
// form-action 'self' is the load-bearing one: it stops an injected <form>
// posting a username and password to another origin.
$cspNonce = base64_encode(random_bytes(16));
header("Content-Security-Policy: default-src 'none'; style-src 'nonce-{$cspNonce}'; "
     . "form-action 'self'; frame-ancestors 'none'; base-uri 'none'");

// Where to send the user after signing in. Sanitised in lib.php (auth_safe_next)
// rather than here, so the open-redirect guard is unit-tested — the backslash
// case is easy to get wrong and impossible to spot by reading.
$next   = auth_safe_next((string) ($_GET['next'] ?? $_POST['next'] ?? '/'));
$mode   = str_contains($_SERVER['REQUEST_URI'] ?? '', 'change-password')
          ? 'change' : 'login';
$notice = '';
$error  = '';

if (isset($_GET['signedout'])) { $notice = 'You have been signed out.'; }
if (isset($_GET['expired']))   { $notice = 'Your session expired. Please sign in again.'; }

$csrf = auth_csrf_token();

// ---------------------------------------------------------------------------
// POST — sign in, or set a new password
// ---------------------------------------------------------------------------
if (($_SERVER['REQUEST_METHOD'] ?? 'GET') === 'POST') {
    if (!auth_csrf_ok($_POST['csrf'] ?? null)) {
        $error = 'Your sign-in form expired. Please try again.';
    } elseif (($_POST['action'] ?? '') === 'change') {
        // --- forced / self-service password change --------------------------
        $sess = null;
        try { $sess = auth_session_resolve($_COOKIE[AUTH_COOKIE] ?? null); }
        catch (Throwable $e) { $error = 'Service temporarily unavailable.'; }

        if ($sess === null && $error === '') {
            $error = 'Your session expired. Please sign in again.';
            $mode  = 'login';
        } elseif ($error === '') {
            $new = (string) ($_POST['new_password'] ?? '');
            $rpt = (string) ($_POST['repeat_password'] ?? '');
            $cur = (string) ($_POST['current_password'] ?? '');
            $problem = auth_password_problem($new, (string) $sess['username']);

            // Re-authenticate before changing a password. Without this, a stolen
            // cookie is enough to set a new password — and because the change
            // then revokes every other session, the legitimate owner is locked
            // out of their own account. Cookie theft would become permanent
            // takeover. (Found in security review 2026-08-08.)
            //
            // Waived only while must_change = 1: those users are mid-migration
            // and their "current" password is the setup one we are forcing them
            // off. They still had to authenticate with it moments ago to get a
            // session at all, so the step adds friction without adding proof.
            $needsCurrent = ((int) $sess['must_change'] !== 1);
            $curOk = true;
            if ($needsCurrent) {
                $u = auth_find_user((string) $sess['username']);
                $curOk = $u !== null && $cur !== '' && auth_verify_password($u, $cur);
            }

            if (!$curOk) {
                auth_audit((string) $sess['username'], 'password.change.fail', '',
                           ['reason' => 'bad current password']);
                $error = 'Your current password is not correct.';
                $mode  = 'change';
            } elseif ($new !== $rpt) {
                $error = 'The two passwords do not match.';
                $mode  = 'change';
            } elseif ($problem !== '') {
                $error = $problem;
                $mode  = 'change';
            } elseif ($needsCurrent && hash_equals($cur, $new)) {
                $error = 'The new password must be different from the current one.';
                $mode  = 'change';
            } else {
                auth_db()->prepare(
                    'UPDATE console_users
                        SET pw_hash = ?, pw_algo = ?, must_change = 0
                      WHERE id = ?'
                )->execute([auth_hash_password($new), 'argon2id', $sess['user_id']]);

                // Metadata added by migration 002, written separately and
                // best-effort so that a box where the code landed before the
                // migration still changes passwords. Never merge this into the
                // statement above: an unknown column there is a blank 500 on
                // the one page a locked-out user has to be able to use.
                try {
                    auth_db()->prepare(
                        'UPDATE console_users
                            SET pw_changed_at = NOW(), row_version = row_version + 1
                          WHERE id = ?'
                    )->execute([$sess['user_id']]);
                } catch (Throwable $e) {
                    error_log('capi-login: pw metadata skipped: ' . $e->getMessage());
                }

                // Every OTHER session for this user dies: if the forced change
                // was triggered by a suspected compromise, leaving the
                // attacker's session alive would defeat the whole exercise.
                auth_session_revoke_user((int) $sess['user_id']);
                auth_audit((string) $sess['username'], 'password.change');

                $token = auth_session_create(
                    (int) $sess['user_id'],
                    auth_client_ip(),
                    (string) ($_SERVER['HTTP_USER_AGENT'] ?? '')
                );
                auth_set_cookie($token);
                header('Location: ' . $next, true, 303);
                exit;
            }
        }
    } else {
        // --- sign in ---------------------------------------------------------
        // Every response from this branch is held to AUTH_LOGIN_FLOOR_MS (see
        // auth_timing_floor). Start the clock before any work, including the
        // database lookup, or the floor measures the wrong interval.
        $t0 = hrtime(true);

        $username = trim((string) ($_POST['username'] ?? ''));
        $password = (string) ($_POST['password'] ?? '');
        $user     = null;
        $clientIp = auth_client_ip();

        // Per-IP ceiling, checked BEFORE the user lookup so that a spray of
        // fictional usernames costs the attacker the same as a real one and
        // never reaches a password hash.
        if (auth_ip_blocked($clientIp)) {
            auth_audit($username, 'login.throttled', '', ['ip_fails' => auth_ip_fail_count($clientIp)]);
            $error = 'Too many failed attempts from this network. Try again in 15 minutes.';
            auth_timing_floor($t0);
        }

        if ($error === '') {
            try { $user = auth_find_user($username); }
            catch (Throwable $e) {
                error_log('capi-login: ' . $e->getMessage());
                $error = 'Service temporarily unavailable. Please try again shortly.';
            }
        }

        if ($error === '') {
            // One message for every failure mode, on purpose: distinguishing
            // "no such user" from "wrong password" hands an attacker a free
            // account-enumeration oracle.
            $generic = 'Incorrect username or password.';

            if ($user === null) {
                // No dummy hash here any more. It was meant to equalise timing
                // but did the opposite (most real accounts are fast $apr1$),
                // and it handed anyone an unauthenticated argon2id CPU burn.
                // The floor below equalises timing without doing the work.
                auth_audit($username, 'login.fail', '', ['reason' => 'no such user']);
                $error = $generic;
            } elseif (($left = auth_lock_remaining($user)) > 0) {
                auth_audit($username, 'login.fail', '', ['reason' => 'locked']);
                $error = 'Too many attempts. Try again in ' . ceil($left / 60) . ' minute(s).';
            } elseif ($user['status'] !== 'active') {
                auth_audit($username, 'login.fail', '', ['reason' => 'disabled']);
                $error = $generic;
            } elseif (!auth_verify_password($user, $password)) {
                auth_note_failure($user);
                auth_audit($username, 'login.fail', '', ['reason' => 'bad password']);
                $error = $generic;
            } else {
                auth_note_success((int) $user['id']);
                $token = auth_session_create(
                    (int) $user['id'],
                    $clientIp,
                    (string) ($_SERVER['HTTP_USER_AGENT'] ?? '')
                );
                auth_set_cookie($token);
                auth_audit($username, 'login');

                // The floor applies to SUCCESS too. Exempting it would make a
                // correct password the one fast answer, which is the whole
                // oracle back again in a more useful form.
                auth_timing_floor($t0);

                if ((int) $user['must_change'] === 1) {
                    header('Location: /docs/idp/change-password?next=' . rawurlencode($next), true, 303);
                    exit;
                }
                header('Location: ' . $next, true, 303);
                exit;
            }

            // Every failing branch above lands here.
            auth_timing_floor($t0);
        }
    }
}

// If we are rendering the change form, confirm there is a session behind it,
// and learn whether this is a forced first-use change (no current password
// asked) or a voluntary one (current password required — see the re-auth block
// above; the form must match what the handler enforces or the flow deadlocks).
$mustChange = false;
if ($mode === 'change') {
    try {
        $s = auth_session_resolve($_COOKIE[AUTH_COOKIE] ?? null);
        if ($s === null) {
            if ($error === '') {
                $mode  = 'login';
                $error = 'Your session expired. Please sign in again.';
            }
        } else {
            $mustChange = ((int) $s['must_change'] === 1);
        }
    } catch (Throwable $e) { /* fall through to the form */ }
}

$e = static fn(string $s): string => htmlspecialchars($s, ENT_QUOTES, 'UTF-8');
?>
<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title><?= $mode === 'change' ? 'Choose a new password' : 'Sign in' ?> — CAPI Console</title>
<style nonce="<?= $e($cspNonce) ?>">
:root{--g:#046a38;--ink:#12171a;--muted:#5a6a7a;--line:#d8dee7;--paper:#eef1f5;--red:#d32f2f}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
  font:15px/1.55 system-ui,Segoe UI,Roboto,sans-serif;
  display:flex;align-items:center;justify-content:center;min-height:100vh;padding:24px}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;
  box-shadow:0 2px 10px rgba(16,32,64,.08);padding:28px 30px;width:100%;max-width:420px}
h1{font-size:20px;margin:0 0 4px}
.sub{color:var(--muted);font-size:13px;margin:0 0 20px}
label{display:block;font-size:12px;font-weight:700;letter-spacing:.06em;
  text-transform:uppercase;color:var(--muted);margin:14px 0 5px}
input[type=text],input[type=password]{width:100%;padding:10px 12px;border:1px solid var(--line);
  border-radius:6px;font:inherit;background:#fff}
input:focus{outline:2px solid var(--g);outline-offset:1px}
button{margin-top:20px;width:100%;padding:11px 14px;border:0;border-radius:6px;
  background:var(--g);color:#fff;font:inherit;font-weight:700;cursor:pointer}
button:hover{filter:brightness(1.08)}
.msg{padding:10px 12px;border-radius:6px;font-size:13.5px;margin-bottom:16px}
.msg.err{background:#fdecea;border-left:4px solid var(--red)}
.msg.ok{background:#e8f5e9;border-left:4px solid var(--g)}
.hint{color:var(--muted);font-size:12.5px;margin-top:14px}
</style>
</head>
<body>
<div class="card">
<?php if ($mode === 'change'): ?>
  <h1>Choose a new password</h1>
  <p class="sub"><?= $mustChange
      ? 'This account still uses its setup password. Pick a new one to continue.'
      : 'Confirm your current password, then choose a new one.' ?></p>
  <?php if ($error !== ''): ?><div class="msg err"><?= $e($error) ?></div><?php endif; ?>
  <form method="post" action="/docs/idp/change-password" autocomplete="off">
    <input type="hidden" name="action" value="change">
    <input type="hidden" name="csrf" value="<?= $e($csrf) ?>">
    <input type="hidden" name="next" value="<?= $e($next) ?>">
<?php if (!$mustChange): ?>
    <label for="cp">Current password</label>
    <input id="cp" name="current_password" type="password" required autofocus>
<?php endif; ?>
    <label for="np">New password</label>
    <input id="np" name="new_password" type="password" required minlength="<?= AUTH_MIN_PW_LEN ?>"
           <?= $mustChange ? 'autofocus' : '' ?>>
    <label for="rp">Repeat new password</label>
    <input id="rp" name="repeat_password" type="password" required minlength="<?= AUTH_MIN_PW_LEN ?>">
    <button type="submit">Set password and continue</button>
  </form>
  <p class="hint">At least <?= AUTH_MIN_PW_LEN ?> characters. Length matters more than
     punctuation — a short phrase you can remember beats a mangled word.</p>
<?php else: ?>
  <h1>CAPI Console</h1>
  <p class="sub">UHC Survey Year 2 — sign in to continue.</p>
  <?php if ($error !== ''): ?><div class="msg err"><?= $e($error) ?></div><?php endif; ?>
  <?php if ($notice !== ''): ?><div class="msg ok"><?= $e($notice) ?></div><?php endif; ?>
  <form method="post" action="/docs/idp/login" autocomplete="off">
    <input type="hidden" name="csrf" value="<?= $e($csrf) ?>">
    <input type="hidden" name="next" value="<?= $e($next) ?>">
    <label for="u">Username</label>
    <input id="u" name="username" type="text" required autofocus autocapitalize="none" spellcheck="false">
    <label for="p">Password</label>
    <input id="p" name="password" type="password" required>
    <button type="submit">Sign in</button>
  </form>
  <p class="hint">Access is per person. If you need an account, ask the survey manager.</p>
<?php endif; ?>
</div>
</body></html>
