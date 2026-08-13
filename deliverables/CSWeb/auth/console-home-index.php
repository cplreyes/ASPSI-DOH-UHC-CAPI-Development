<?php
/**
 * CAPI console — home.
 *
 * /docs/ had no index, so Apache answered 403 to anyone who signed in (the login
 * handler lands here) or simply typed the console address. This is that landing
 * page: it names the signed-in user, their tier, and only the surfaces that tier
 * can actually open.
 *
 * Tier is derived from the live `Require user` lines in the .htaccess gates — the
 * same source Apache enforces from — so this can never advertise a door that will
 * not open.
 */
declare(strict_types=1);
ini_set('display_errors', '0');

header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');
header('Referrer-Policy: strict-origin-when-cross-origin');

$user = $_SERVER['REMOTE_USER'] ?? $_SERVER['PHP_AUTH_USER'] ?? '';

function gate_users(string $path): array {
    $raw = @file_get_contents($path);
    if (!is_string($raw) || $raw === '') { return []; }
    $out = [];
    foreach (preg_split('/\R/', $raw) as $line) {
        // Written with two leading spaces by the admin console — do not anchor on ^Require.
        if (preg_match('/^\s*Require\s+user\s+(.+)$/i', $line, $m)) {
            foreach (preg_split('/\s+/', trim($m[1])) as $u) { if ($u !== '') { $out[] = $u; } }
        }
    }
    return $out;
}

$root = '/var/www/html/docs';
$can = [
    'monitoring' => in_array($user, gate_users($root . '/.htaccess'), true),
    'data_room'  => in_array($user, gate_users($root . '/data/.htaccess'), true),
    'admin'      => in_array($user, gate_users($root . '/admin/.htaccess'), true),
];
$tier = $can['admin'] ? 'admin' : ($can['data_room'] ? 'staff' : ($can['monitoring'] ? 'field' : 'none'));

$cards = [
    ['Sync Dashboard', '/docs/dashboard.html', 'monitoring',
     'Cases synced per instrument, coverage against the assignment plan, enumerator activity, '
     . 'and the filters that drive every figure below them.'],
    ['Map Report', '/docs/map.html', 'monitoring',
     'Where fieldwork has reached: facility coverage by region and municipality, with GPS-verified '
     . 'visits plotted against the plan.'],
    ['Data Room', '/docs/data/', 'data_room',
     'Full response spreadsheets, SPSS/Stata/R exports, CSPro packages, the codebook and the '
     . 'tabulation previews. Staff tier — full microdata.'],
    ['Admin Console', '/docs/admin/', 'admin',
     'Survey activities, users and access tiers, alerting, the assignment plan and the audit '
     . 'trail. Changes reach the live surfaces within about two minutes.'],
];

$e = static fn(string $s): string => htmlspecialchars($s, ENT_QUOTES, 'UTF-8');
?><!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>CAPI Console &mdash; UHC Survey Year 2</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 40 40'%3E%3Crect width='40' height='40' rx='9' fill='%23046a38'/%3E%3Cpath d='M20 9l9 5v12l-9 5-9-5V14z' fill='%23e5b23b'/%3E%3C/svg%3E">
<style>
  :root{--verde:#046a38;--verde-700:#03572e;--verde-900:#04331d;--gold:#e5b23b;
        --ink:#12211a;--ink-2:#3c4b43;--ink-3:#63736a;--line:#e2e9e5;--surface:#fff;--bg:#f6f9f7;
        --sans:system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
  *{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans)}
  .top{background:var(--verde-900);color:#fff;padding:0 22px}
  .top .in{max-width:1000px;margin:0 auto;display:flex;align-items:center;gap:12px;
           min-height:58px;flex-wrap:wrap}
  .mark{width:31px;height:31px;border-radius:8px;background:var(--gold);color:var(--verde-900);
        font-weight:800;display:flex;align-items:center;justify-content:center;font-size:15px}
  .top b{font-size:14.5px;display:block;line-height:1.25}
  .top span.s{color:#bfe3ce;font-size:12px}
  .who{margin-left:auto;display:flex;align-items:center;gap:9px;font-size:12.5px;color:#d6efe1}
  .who .tier{font-size:10px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;
             padding:2px 8px;border-radius:5px;background:rgba(229,178,59,.17);color:var(--gold);
             border:1px solid rgba(229,178,59,.4)}
  .who a{color:#fff;font-weight:650;text-decoration:none;border:1px solid rgba(255,255,255,.32);
         padding:5px 11px;border-radius:7px}
  .who a:hover{background:rgba(255,255,255,.1)}
  .wrap{max-width:1000px;margin:0 auto;padding:30px 22px 44px}
  h1{font-size:22px;margin:0 0 5px;color:var(--verde-900)}
  .lead{color:var(--ink-3);font-size:14px;margin:0 0 26px;line-height:1.55;max-width:64ch}
  .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(272px,1fr));gap:15px}
  .card{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:19px 20px;
        display:flex;flex-direction:column;box-shadow:0 1px 2px rgba(16,40,28,.05)}
  .card h3{margin:0 0 7px;font-size:15.5px;color:var(--verde-900)}
  .card p{margin:0 0 15px;font-size:13px;color:var(--ink-2);line-height:1.55;flex:1}
  .go{align-self:flex-start;background:var(--verde);color:#fff;font-weight:650;font-size:13px;
      text-decoration:none;padding:8px 15px;border-radius:8px}
  .go:hover{background:var(--verde-700)}
  .card.off{opacity:.62;background:#fbfcfb}
  .card.off .go{background:#e6ecea;color:var(--ink-3);pointer-events:none}
  .locked{font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;
          color:var(--ink-3);align-self:flex-start;border:1px solid var(--line);
          padding:5px 10px;border-radius:7px}
  .foot{margin-top:30px;padding-top:17px;border-top:1px solid var(--line);
        font-size:12px;color:var(--ink-3);line-height:1.65}
  .foot a{color:var(--verde)}
</style></head>
<body>
<div class="top"><div class="in">
  <span class="mark">A</span>
  <span><b>ASPSI CAPI Console</b><span class="s">UHC Survey Year 2</span></span>
  <span class="who"><?= $e($user) ?><span class="tier"><?= $e($tier) ?></span>
    <a href="/docs/auth/logout">Sign out</a></span>
</div></div>

<div class="wrap">
  <h1>Console</h1>
  <p class="lead">The working surfaces behind the public portal. You are signed in as
  <b><?= $e($user) ?></b> at <b><?= $e($tier) ?></b> tier &mdash; anything greyed out below is
  outside that tier, not broken.</p>

  <div class="grid">
    <?php foreach ($cards as [$title, $href, $needs, $desc]): $open = $can[$needs]; ?>
      <div class="card<?= $open ? '' : ' off' ?>">
        <h3><?= $e($title) ?></h3>
        <p><?= $e($desc) ?></p>
        <?php if ($open): ?>
          <a class="go" href="<?= $e($href) ?>">Open</a>
        <?php else: ?>
          <span class="locked">&#128274; <?= $e($needs === 'admin' ? 'Admin tier' : ($needs === 'data_room' ? 'Staff tier' : 'Field tier')) ?></span>
        <?php endif; ?>
      </div>
    <?php endforeach; ?>
  </div>

  <div class="foot">
    Public project pages live on the <a href="https://capi.asiansocial.org/projects/uhc-y2/">CAPI
    portal</a>. Tablet syncing is unaffected by this sign-in and continues to use the CSWeb
    endpoint.<br>Asian Social Project Services, Inc. &mdash; authorised users only; activity on
    this console is logged.
  </div>
</div>
</body></html>
