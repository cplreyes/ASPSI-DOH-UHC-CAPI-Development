<?php
/**
 * CAPI Console — the authoritative path -> permission map.        Carl, 2026-08-08
 * Plan: capi-console-idp-option-c-plan.md §3.4
 *
 * WHY THIS IS A FILE AND NOT A TABLE
 * A database problem must never be able to silently WIDEN access. Rules live in
 * version control, get reviewed like code, and fail closed; only the *grants*
 * (which role holds which permission) live in MySQL.
 *
 * WHY THE DEFAULT IS DENY
 * The gate this replaces was Apache `FilesMatch`, which matches by FILENAME —
 * so every new file or directory under /docs/ was public until somebody
 * remembered to list it. That nearly shipped plan.json, /docs/f2/ and
 * /docs/cases/ to anonymous readers. Here an unmatched path is DENIED, so
 * forgetting fails safe. The cost is that genuinely new pages must be added
 * here; that is the trade we are deliberately making.
 *
 * WHY EVERYTHING LIVES UNDER /docs/, AND WHY THE DIRECTORY IS /docs/idp/
 * On this box `/` is served by `capi-www` (plain nginx:alpine, no PHP) while
 * `/docs/` proxies to Apache, so PHP endpoints must sit under /docs/.
 *
 * NOT /docs/auth/ — that path is already claimed. `00-uhc-auth.conf` declares
 * `<Location /docs/auth/login> SetHandler form-login-handler` for mod_auth_form,
 * so anything placed there is intercepted by Apache and never executes (it
 * returns a bare 500). Discovered the hard way, 2026-08-08.
 *
 * The generated pages link to /docs/auth/logout. That stays a valid PUBLIC path
 * below: at cutover the mod_auth_form Location blocks are removed and it becomes
 * a redirect to /docs/idp/logout, so no page has to be regenerated.
 */
declare(strict_types=1);

/** Permissions that exist. Used to validate role grants and admin edits. */
const CONSOLE_PERMS = [
    'monitoring.view',   // Sync Dashboard, Map, sync feed, plan.json
    'case.view',         // respondent-level case detail (F1/F3/F4/F2)
    'data.export',       // data room, CSV/SPSS/Stata/R, codebook
    'tabulations.view',  // tabulation catalogue + generated tables
    'admin.users',       // create/disable users, assign roles, reset passwords
    'admin.system',      // alerts, targets, activities, deploys
    'audit.view',        // access + change audit trail
];

/**
 * Pseudo-permissions:
 *   PUBLIC    no session required. Deliberately tiny — without it nobody could
 *             ever sign in. Nothing is added here without a specific reason.
 *   AUTH      any authenticated, non-expired session; no permission needed.
 *   PWCHANGE  reachable while must_change = 1. ONLY the password endpoints.
 */

/** Exact-match rules, checked first. O(1) and immune to ordering mistakes. */
const ACL_EXACT = [
    // --- the sign-in surface itself -----------------------------------------
    '/docs/idp/login'            => 'PUBLIC',
    '/docs/idp/logout'           => 'PUBLIC',   // idempotent; fine when already out
    // Legacy path baked into every generated page's topbar. Today mod_auth_form
    // owns it; after cutover it redirects to /docs/idp/logout. PUBLIC either way,
    // so the link never breaks and nothing has to be regenerated.
    '/docs/auth/logout'          => 'PUBLIC',
    // The old mod_auth_form POST target. Nothing should reach it any more —
    // /docs/login.php now redirects away from the form that posted here — but
    // a bookmark or a cached page still can, and the Apache redirect that
    // would rescue them only runs if the gate lets the request through.
    // PUBLIC costs nothing: the path no longer does anything but redirect.
    '/docs/auth/login'           => 'PUBLIC',
    '/favicon.ico'               => 'PUBLIC',
    '/robots.txt'                => 'PUBLIC',
    // capi-www's error page. PUBLIC because a 404 must render for anyone —
    // otherwise a wrong URL becomes a redirect to sign-in, which reads as
    // "you are logged out" rather than "that page does not exist".
    '/404.html'                  => 'PUBLIC',
    // The pre-migration Apache sign-in page. PUBLIC only so the cutover cannot
    // strand anyone mid-flight; DELETE this file and this line after step 6.
    '/docs/login.php'            => 'PUBLIC',

    // --- reachable while the user still owes a password change --------------
    '/docs/idp/change-password' => 'PWCHANGE',

    // --- signed in, no specific permission ----------------------------------
    '/docs/idp/me'              => 'AUTH',
    '/docs/whoami.php'           => 'AUTH',     // legacy chip; retire after step 7
    '/docs/'                     => 'AUTH',
    '/docs/index.php'            => 'AUTH',
    '/help.html'                 => 'AUTH',
    '/'                          => 'AUTH',
    // The static portal served by capi-www. `/` alone is not enough: an exact
    // rule does not cover the document it serves or the stylesheet that
    // document loads, and deny-by-default means both would 403 the moment the
    // gate moved here — a portal with no CSS, which looks like an outage.
    // Enumerated against what capi-www actually holds, 2026-08-09.
    '/index.html'                => 'AUTH',
    '/portal.css'                => 'AUTH',

    // Operator documentation — readable by anyone with an account.
    // The admin portal guide is AUTH, not admin.users, on purpose: its first
    // section explains the forced password change, which every one of the 18
    // accounts hits at their next sign-in. Gating the explanation behind the
    // permission most of them lack would be perverse.
    '/docs/admin-portal-guide.html' => 'AUTH',
    '/docs/capi-manual.html'     => 'AUTH',
    '/docs/enumerator-guide.html'=> 'AUTH',
    '/docs/hcw-guide.html'       => 'AUTH',
    '/docs/hub-guide.html'       => 'AUTH',
    '/docs/pretest-guide.html'   => 'AUTH',
    '/docs/f1-crosswalk.html'    => 'AUTH',
    '/docs/f2-crosswalk.html'    => 'AUTH',
    '/docs/f3-crosswalk.html'    => 'AUTH',
    '/docs/f4-crosswalk.html'    => 'AUTH',

    // --- monitoring ----------------------------------------------------------
    '/docs/dashboard.html'       => 'monitoring.view',
    '/docs/map.html'             => 'monitoring.view',
    '/docs/sync-feed.json'       => 'monitoring.view',
    '/docs/plan.json'            => 'monitoring.view',
    '/docs/overview-status.json' => 'monitoring.view',
    // Facility coordinate intake, used from the Map. Set to monitoring.view to
    // preserve exactly who can reach it today (it sits on the field-tier gate).
    // Narrowing it is a deliberate decision, not a side effect of this migration.
    '/docs/coords.php'           => 'monitoring.view',

    // --- respondent-level detail --------------------------------------------
    '/docs/case.html'            => 'case.view',
    '/docs/f2-case.html'         => 'case.view',

    // The tabulations pages client-fetch this from inside a `tabulations.view`
    // page (csweb-tabulations-gen.py:398, credentials:'same-origin'). It lives
    // under /docs/data/, which the prefix rule below maps to `data.export` —
    // so field_supervisor and client_viewer would load the page and then get
    // 403 on its data, rendering a half-empty table with no error.
    //
    // It carries aggregate cells, not microdata, so `tabulations.view` is the
    // correct permission. ACL_EXACT is evaluated before ACL_PREFIX, so this
    // wins over /docs/data/ automatically. Found in review 2026-08-08.
    '/docs/data/tabulations-preview.json' => 'tabulations.view',
];

/**
 * Prefix rules, evaluated in order, first match wins.
 * MORE SPECIFIC PREFIXES MUST COME FIRST — '/docs/admin/users' before
 * '/docs/admin/', or the users screen would only ever need admin.system.
 */
const ACL_PREFIX = [
    // Static assets the gated pages need. AUTH, not PUBLIC: there is no reason
    // to serve them anonymously, and marking them PUBLIC would be the same
    // instinct that produced the FilesMatch holes. Without these two rules the
    // Map renders unstyled — leaflet.css lives here.
    ['/docs/assets/',            'AUTH'],
    ['/docs/img/',               'AUTH'],
    ['/docs/idp/assets/',       'PUBLIC'],   // only what the login page needs

    // The rest of the capi-www static portal. Same reasoning as the exact
    // rules above: these are directories the portal links to, and an
    // unlisted directory is a 403 the day the gate moves.
    ['/assets/',                 'AUTH'],
    ['/platform/',               'AUTH'],
    ['/uhc/',                    'AUTH'],
    ['/about/',                  'AUTH'],

    // The console's live pages now live at portal URLs (2026-08-09 unification,
    // Option A). These MUST precede the generic '/projects/' rule below, which
    // is AUTH — first match wins, so a rule appended after it would never be
    // reached and the data room would be readable by anyone with any account.
    // /monitoring/ covers /monitoring/map/ by prefix. The admin rules land
    // ahead of Slice 5 so the path can never exist ungated; /users before /
    // because an auditor-style split must stay expressible.
    ['/projects/uhc-y2/monitoring/', 'monitoring.view'],
    ['/projects/uhc-y2/data/',       'data.export'],
    ['/projects/uhc-y2/admin/users', 'admin.users'],
    ['/projects/uhc-y2/admin/',      'admin.system'],
    ['/projects/uhc-y2/tabulations/', 'tabulations.view'],
    ['/projects/',               'AUTH'],

    ['/docs/cases/',             'case.view'],
    ['/docs/f2/',                'case.view'],
    ['/docs/data/',              'data.export'],

    ['/docs/admin/users',        'admin.users'],
    ['/docs/admin/',             'admin.system'],

    // --- the admin API (E9-ADMIN-006) ---------------------------------------
    // The edge rule is coarse on purpose; admin.php re-checks the exact
    // permission per route in-process, and the two are allowed to differ only
    // in the safe direction (the edge may be no LOOSER than the route).
    // audit.view is listed first because an auditor may hold it without
    // holding admin.users — a distinction the coarse rule below would erase.
    ['/docs/idp/admin/audit',    'audit.view'],
    ['/docs/idp/admin',          'admin.users'],

    // Phase 2 service endpoints for F2 federation. Denied outright so that no
    // cookie session can ever reach them: they are bearer-authenticated and
    // will get their own nginx location with no auth_request (E9-ADMIN-046).
    // The rule ships now so the path cannot become reachable by accident.
    ['/docs/idp/svc/',           'DENY'],
];

/**
 * Resolve a request path to the permission it requires.
 *
 * @param string $path  raw request URI; query string is stripped here
 * @return string       a CONSOLE_PERMS entry, or PUBLIC | AUTH | PWCHANGE | DENY
 */
function acl_required_perm(string $path): string
{
    $p = acl_normalise($path);

    if (isset(ACL_EXACT[$p])) { return ACL_EXACT[$p]; }

    foreach (ACL_PREFIX as [$rule, $perm]) {
        if (str_starts_with($p, $rule)) { return $perm; }
    }
    return 'DENY';
}

/**
 * Normalise before matching. Every step closes a real bypass:
 *   - strip query/fragment   '/docs/data/x.csv?a=1' must still match the data rule
 *   - decode percent-escapes '%2e%2e%2f' must not survive as literal text
 *   - collapse '//'          '//docs//data/' must not miss the prefix
 *   - resolve '.' and '..'   '/docs/dashboard.html/../data/x.csv' must resolve to
 *                            /docs/data/x.csv rather than matching the dashboard
 *                            rule and handing over the data room
 *   - lowercase              paths are case-sensitive on Linux, but matching in
 *                            lowercase can only ever require MORE permission,
 *                            never less, so it is the safe direction
 */
function acl_normalise(string $path): string
{
    $p = (string) strtok($path, '?#');

    // Decode repeatedly: '%252e%252e' becomes '..' only after two passes.
    for ($i = 0; $i < 3; $i++) {
        $d = rawurldecode($p);
        if ($d === $p) { break; }
        $p = $d;
    }

    $p = str_replace('\\', '/', $p);
    $p = preg_replace('#/+#', '/', $p) ?? $p;
    if ($p === '' || $p[0] !== '/') { $p = '/' . $p; }

    $hadTrailing = str_ends_with($p, '/');

    $out = [];
    foreach (explode('/', $p) as $seg) {
        if ($seg === '' || $seg === '.') { continue; }
        if ($seg === '..') { array_pop($out); continue; }
        $out[] = $seg;
    }
    $norm = '/' . implode('/', $out);
    // Keep a trailing slash: '/docs/data/' and '/docs/data' differ for prefix
    // rules, and dropping it would make a bare directory request miss.
    if ($norm !== '/' && $hadTrailing) { $norm .= '/'; }

    return strtolower($norm);
}

/**
 * Should a successful read of this path be written to the audit trail?
 * Limited to respondent data and bulk microdata: logging every CSS file would
 * bury the entries that matter and cost a write on every request.
 */
function acl_is_auditable_read(string $path): bool
{
    $p = acl_normalise($path);
    foreach (['/docs/cases/', '/docs/f2/', '/docs/data/'] as $pre) {
        if (str_starts_with($p, $pre)) { return true; }
    }
    return in_array($p, ['/docs/case.html', '/docs/f2-case.html'], true);
}
