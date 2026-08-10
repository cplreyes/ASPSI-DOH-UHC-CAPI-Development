<?php
/**
 * CAPI console — sign in.
 *
 * Serves two roles:
 *   1. the ErrorDocument for 401 on every gated path under /docs/, so an
 *      unauthenticated visitor gets this page instead of a browser popup;
 *   2. a directly reachable /docs/login.php.
 *
 * It posts to /docs/auth/login, which is Apache's form-login-handler
 * (mod_auth_form). No credentials are handled by PHP at any point — this file
 * only renders the form and works out where to send the user afterwards.
 */
declare(strict_types=1);
ini_set('display_errors', '0');

/* Where the user was heading before the gate stopped them. Apache exposes the
 * original path as REDIRECT_URL when this file is rendered as ErrorDocument. */
function intended_path(): string {
    $cands = [];
    if (isset($_GET['next']))              { $cands[] = (string) $_GET['next']; }
    if (isset($_SERVER['REDIRECT_URL']))   { $cands[] = (string) $_SERVER['REDIRECT_URL']; }
    foreach ($cands as $c) {
        /* Same-origin paths under /docs/ only — never bounce to another host. */
        if (preg_match('#^/docs/[A-Za-z0-9._~!$&\'()*+,;=:@%/-]*$#', $c)
            && strpos($c, '//') === false
            && strpos($c, '/docs/login.php') !== 0
            && strpos($c, '/docs/auth/') !== 0) {
            $q = $_SERVER['REDIRECT_QUERY_STRING'] ?? '';
            if ($c === ($_SERVER['REDIRECT_URL'] ?? null) && $q !== '' && !isset($_GET['next'])) {
                $c .= '?' . $q;
            }
            return $c;
        }
    }
    return '/docs/';
}

$next    = intended_path();
$isError = isset($_GET['e']);
$isBye   = isset($_GET['bye']);

/* Preserve the 401 when this is the error document: it keeps scripted health
 * checks meaningful and stops caches storing the login page as the resource. */
if (!$isError && !$isBye && isset($_SERVER['REDIRECT_STATUS'])
    && $_SERVER['REDIRECT_STATUS'] === '401') {
    http_response_code(401);
}
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');
header('X-Frame-Options: DENY');
header('Referrer-Policy: strict-origin-when-cross-origin');

$e = static fn(string $s): string => htmlspecialchars($s, ENT_QUOTES, 'UTF-8');
?><!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>Sign in &mdash; ASPSI CAPI Console</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 40 40'%3E%3Crect width='40' height='40' rx='9' fill='%23046a38'/%3E%3Cpath d='M20 9l9 5v12l-9 5-9-5V14z' fill='%23e5b23b'/%3E%3C/svg%3E">
<style>
  :root{ --verde:#046a38; --verde-700:#03572e; --verde-900:#04331d; --gold:#e5b23b;
         --ink:#12211a; --ink-2:#3c4b43; --ink-3:#63736a; --line:#e2e9e5; --surface:#fff;
         --sans:system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; }
  *{box-sizing:border-box}
  body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;
       padding:28px 18px;font-family:var(--sans);color:var(--ink);
       background:linear-gradient(160deg,#04331d 0%,#046a38 46%,#0a7d45 100%)}
  .wrap{width:100%;max-width:404px}
  .brand{display:flex;align-items:center;gap:11px;justify-content:center;margin-bottom:20px}
  .mark{width:40px;height:40px;border-radius:10px;background:var(--gold);color:var(--verde-900);
        font-weight:800;font-size:19px;display:flex;align-items:center;justify-content:center}
  .brand b{color:#fff;font-size:16.5px;letter-spacing:.01em;display:block;line-height:1.25}
  .brand span{color:#bfe3ce;font-size:12.5px}
  .card{background:var(--surface);border-radius:14px;padding:26px 26px 22px;
        box-shadow:0 18px 44px rgba(0,0,0,.24)}
  h1{margin:0 0 4px;font-size:19px;color:var(--verde-900)}
  .sub{margin:0 0 18px;font-size:13.5px;color:var(--ink-3);line-height:1.5}
  label{display:block;font-size:11px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;
        color:var(--ink-3);margin-bottom:5px}
  input[type=text],input[type=password]{width:100%;font:15px var(--sans);padding:10px 12px;
        border:1px solid #cfdad4;border-radius:9px;background:#fff;color:var(--ink);margin-bottom:14px}
  input:focus{outline:2px solid #9ed4b6;outline-offset:0;border-color:var(--verde)}
  button{width:100%;background:var(--verde);color:#fff;font:700 14.5px var(--sans);border:0;
         border-radius:9px;padding:12px 16px;cursor:pointer}
  button:hover{background:var(--verde-700)}
  .msg{border-radius:9px;padding:10px 13px;margin-bottom:16px;font-size:13px;font-weight:600;line-height:1.45}
  .msg.err{background:#fdecea;color:#b3261e;border:1px solid #f3c6c1}
  .msg.ok{background:#eefaf3;color:#12693f;border:1px solid #b9e2cb}
  .foot{margin-top:16px;padding-top:14px;border-top:1px solid var(--line);
        font-size:12px;color:var(--ink-3);line-height:1.6}
  .foot a{color:var(--verde);text-decoration:none}
  .foot a:hover{text-decoration:underline}
  .legal{text-align:center;margin-top:15px;font-size:11.5px;color:#a9d3bd;line-height:1.6}
</style></head>
<body>
<div class="wrap">
  <div class="brand"><span class="mark">A</span>
    <span><b>ASPSI CAPI Console</b><span>UHC Survey Year 2</span></span></div>

  <div class="card">
    <?php if ($isBye): ?>
      <div class="msg ok">You have been signed out. Close the browser to clear the session
      completely on a shared device.</div>
    <?php elseif ($isError): ?>
      <div class="msg err">That username and password did not match. Check your caps lock and
      try again, or ask your supervisor to reset it.</div>
    <?php endif; ?>

    <h1>Sign in</h1>
    <p class="sub">Use the console account issued to you. This is <b>not</b> your CSEntry tablet
    sync login &mdash; tablet syncing is unaffected and needs no sign-in here.</p>

    <form method="post" action="/docs/auth/login" autocomplete="on">
      <input type="hidden" name="httpd_location" value="<?= $e($next) ?>">
      <label for="u">Username</label>
      <input id="u" name="httpd_username" type="text" required autofocus
             autocapitalize="none" autocorrect="off" spellcheck="false" autocomplete="username">
      <label for="p">Password</label>
      <input id="p" name="httpd_password" type="password" required autocomplete="current-password">
      <button type="submit">Sign in</button>
    </form>

    <div class="foot">
      Access depends on your tier: <b>field</b> reaches the sync dashboard and map,
      <b>staff</b> adds the data room, <b>admin</b> adds the admin console.
      <br><a href="https://capi.asiansocial.org/">&larr; Back to the public portal</a>
    </div>
  </div>

  <div class="legal">Asian Social Project Services, Inc.<br>
    Authorised users only. Activity on this console is logged.</div>
</div>
</body></html>
