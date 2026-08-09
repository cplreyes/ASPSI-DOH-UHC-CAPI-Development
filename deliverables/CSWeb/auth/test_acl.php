<?php
/**
 * ACL unit tests — plan step 3's verification gate.          Carl, 2026-08-08
 *
 *   php test_acl.php      # exit 0 = all pass
 *
 * No database and no web server: the ACL is a pure function, so it can be
 * tested exhaustively and cheaply. That matters because this map is the whole
 * access-control decision — if it is wrong, everything downstream is wrong.
 *
 * Three groups:
 *   1. paths resolve to the permission the plan says they do
 *   2. normalisation defeats the usual bypasses (traversal, double-encoding,
 *      duplicate slashes, query strings)
 *   3. the role x path decision matrix matches plan §3.4
 */
declare(strict_types=1);

require_once __DIR__ . '/acl.php';
require_once __DIR__ . '/lib.php';   // no side effects at include time; auth_db() is lazy

$pass = 0;
$fail = 0;

function check(string $what, $got, $want): void
{
    global $pass, $fail;
    if ($got === $want) {
        $pass++;
        return;
    }
    $fail++;
    printf("FAIL  %-58s got=%-18s want=%s\n", $what, var_export($got, true), var_export($want, true));
}

// ---------------------------------------------------------------------------
// 1. Path -> permission
// ---------------------------------------------------------------------------
$paths = [
    // public — the sign-in surface must work with no session
    '/docs/idp/login'                        => 'PUBLIC',
    '/docs/idp/logout'                       => 'PUBLIC',
    '/favicon.ico'                            => 'PUBLIC',

    // password change is reachable while must_change = 1, nothing else is
    '/docs/idp/change-password'              => 'PWCHANGE',

    // signed in, no permission needed
    '/'                                       => 'AUTH',
    '/docs/'                                  => 'AUTH',
    '/docs/index.php'                         => 'AUTH',
    '/help.html'                              => 'AUTH',
    '/docs/idp/me'                           => 'AUTH',
    '/docs/capi-manual.html'                  => 'AUTH',
    '/projects/uhc-y2/'                       => 'AUTH',

    // assets the gated pages need — without these the Map renders unstyled
    '/docs/assets/leaflet.css'                => 'AUTH',
    '/docs/assets/MarkerCluster.Default.css'  => 'AUTH',
    '/docs/img/logo.png'                      => 'AUTH',

    // monitoring
    '/docs/dashboard.html'                    => 'monitoring.view',
    '/docs/map.html'                          => 'monitoring.view',
    '/docs/plan.json'                         => 'monitoring.view',
    '/docs/sync-feed.json'                    => 'monitoring.view',
    '/docs/coords.php'                        => 'monitoring.view',

    // respondent-level detail
    '/docs/case.html'                         => 'case.view',
    '/docs/f2-case.html'                      => 'case.view',
    '/docs/cases/f1/300101001.json'           => 'case.view',
    '/docs/cases/f1/_labels.json'             => 'case.view',
    '/docs/f2/abc123.json'                    => 'case.view',

    // bulk microdata
    '/docs/data/'                             => 'data.export',
    '/docs/data/f1_responses.csv'             => 'data.export',
    '/docs/data/f1-cases-spss.zip'            => 'data.export',

    // …but the tabulations preview blob lives under /docs/data/ while being
    // fetched from a tabulations.view page. Exact rule must beat the prefix,
    // or field_supervisor / client_viewer get a half-rendered table.
    '/docs/data/tabulations-preview.json'     => 'tabulations.view',

    // admin — the users rule must win over the general admin rule
    '/docs/admin/users.php'                   => 'admin.users',
    '/docs/admin/'                            => 'admin.system',
    '/docs/admin/api.php'                     => 'admin.system',

    // tabulations must beat the generic /projects/ rule
    '/projects/uhc-y2/tabulations/t01.html'   => 'tabulations.view',

    // THE REGRESSION TEST: anything not named is denied. This is the whole
    // point of the migration — under FilesMatch a new file was PUBLIC.
    '/docs/newthing.json'                     => 'DENY',
    '/docs/secret-export.csv'                 => 'DENY',
    '/docs/backups/dump.sql'                  => 'DENY',
    '/some/random/path'                       => 'DENY',
];
foreach ($paths as $p => $want) {
    check("perm($p)", acl_required_perm($p), $want);
}

// ---------------------------------------------------------------------------
// 2. Normalisation / bypass attempts
// ---------------------------------------------------------------------------
$bypass = [
    // query string must not hide the real path
    '/docs/data/x.csv?download=1'                   => 'data.export',
    '/docs/data/x.csv#frag'                         => 'data.export',
    // duplicate slashes
    '//docs//data//x.csv'                           => 'data.export',
    // traversal out of a low-permission page into a high-permission tree
    '/docs/dashboard.html/../data/x.csv'            => 'data.export',
    '/docs/./data/x.csv'                            => 'data.export',
    '/docs/assets/../data/x.csv'                    => 'data.export',
    // percent-encoded traversal
    '/docs/assets/%2e%2e/data/x.csv'                => 'data.export',
    // double-encoded traversal
    '/docs/assets/%252e%252e/data/x.csv'            => 'data.export',
    // encoded separators must not smuggle a path segment
    '/docs%2fdata%2fx.csv'                          => 'data.export',
    // backslash treated as a separator (Windows-style smuggling)
    '/docs\\data\\x.csv'                            => 'data.export',
    // climbing above root must not escape into a permissive rule
    '/../../docs/data/x.csv'                        => 'data.export',
    // case variation must not evade the rule
    '/DOCS/DATA/X.CSV'                              => 'data.export',
    // trailing-slash handling must not turn a case dir into something else
    '/docs/cases/'                                  => 'case.view',
];
foreach ($bypass as $p => $want) {
    check("bypass($p)", acl_required_perm($p), $want);
}

// audit selection
check('audit(/docs/cases/f1/1.json)', acl_is_auditable_read('/docs/cases/f1/1.json'), true);
check('audit(/docs/data/x.csv)',      acl_is_auditable_read('/docs/data/x.csv'),      true);
check('audit(/docs/case.html)',       acl_is_auditable_read('/docs/case.html'),       true);
check('audit(/docs/dashboard.html)',  acl_is_auditable_read('/docs/dashboard.html'),  false);
check('audit(/docs/assets/a.css)',    acl_is_auditable_read('/docs/assets/a.css'),    false);

// ---------------------------------------------------------------------------
// 3. Role x path decision matrix (plan §3.4)
// ---------------------------------------------------------------------------
$grants = [
    'owner'            => ['monitoring.view','case.view','data.export','tabulations.view',
                           'admin.users','admin.system','audit.view'],
    'programme_admin'  => ['monitoring.view','case.view','data.export','tabulations.view',
                           'admin.users','admin.system','audit.view'],
    'analyst'          => ['monitoring.view','case.view','data.export','tabulations.view'],
    'field_supervisor' => ['monitoring.view','case.view','tabulations.view'],
    'client_viewer'    => ['monitoring.view','tabulations.view'],
];

/** Mirrors authz.php's decision for a signed-in, password-current user. */
function decision(array $perms, string $path): string
{
    $need = acl_required_perm($path);
    if ($need === 'DENY')                         { return '403'; }
    if (in_array($need, ['PUBLIC','AUTH','PWCHANGE'], true)) { return '204'; }
    return in_array($need, $perms, true) ? '204' : '403';
}

$matrix = [
    // path                                  owner  prog   analyst  fieldsup  client
    '/docs/dashboard.html'            => ['204','204','204','204','204'],
    '/projects/uhc-y2/tabulations/a'  => ['204','204','204','204','204'],
    '/docs/case.html'                 => ['204','204','204','204','403'],
    '/docs/cases/f1/1.json'           => ['204','204','204','204','403'],
    '/docs/f2/1.json'                 => ['204','204','204','204','403'],
    // Field Supervisor reads a case for QC but must NOT take the microdata set
    '/docs/data/f1_responses.csv'     => ['204','204','204','403','403'],
    // The regression this guards: these two must be able to READ the preview
    // blob even though it sits under /docs/data/, or their tabulations page
    // silently renders empty.
    '/docs/data/tabulations-preview.json' => ['204','204','204','204','204'],
    '/docs/admin/'                    => ['204','204','403','403','403'],
    '/docs/admin/users.php'           => ['204','204','403','403','403'],
    '/docs/newthing.json'             => ['403','403','403','403','403'],
];
$roles = array_keys($grants);
foreach ($matrix as $path => $wants) {
    foreach ($roles as $i => $role) {
        check(sprintf('%-14s %s', $role, $path), decision($grants[$role], $path), $wants[$i]);
    }
}

// Every granted permission must be a real one — catches typos in the seed.
foreach ($grants as $role => $perms) {
    foreach ($perms as $perm) {
        check("known perm $role/$perm", in_array($perm, CONSOLE_PERMS, true), true);
    }
}

// ---------------------------------------------------------------------------
// 4. Open-redirect guard on ?next= (auth_safe_next)
// ---------------------------------------------------------------------------
$nexts = [
    // legitimate destinations survive intact
    '/docs/dashboard.html'                => '/docs/dashboard.html',
    '/docs/case.html?inst=f1&qn=300101001'=> '/docs/case.html?inst=f1&qn=300101001',
    '/docs/data/'                         => '/docs/data/',
    '/'                                   => '/',

    // absolute URLs never redirect off-site
    'http://evil.example/x'               => '/',
    'https://evil.example'                => '/',
    'javascript:alert(1)'                 => '/',
    '//evil.example'                      => '/',

    // THE FINDING: browsers fold '\' to '/' in the authority, so these resolve
    // as protocol-relative and would leave the site.
    '/\\evil.example'                     => '/',
    '/\\/evil.example'                    => '/',
    '/docs/\\evil.example'                => '/',

    // header injection
    "/docs/x\r\nSet-Cookie: a=b"          => '/',
    "/docs/x\nLocation: http://evil"      => '/',
    "/docs/x\ty"                          => '/',
    "/docs/x\0y"                          => '/',

    // must not bounce back into the auth endpoints
    '/docs/idp/login'                    => '/',
    '/docs/idp/change-password'          => '/',

    // malformed / empty
    ''                                    => '/',
    'docs/dashboard.html'                 => '/',   // not site-relative
];
foreach ($nexts as $raw => $want) {
    check('next(' . str_replace(["\r", "\n", "\t", "\0"], ['\r', '\n', '\t', '\0'], $raw) . ')',
          auth_safe_next($raw), $want);
}

// ---------------------------------------------------------------------------
// The admin API surface (E9-ADMIN-006). The edge rule is coarse — admin.php
// re-checks per route — but it must never be LOOSER than the route it fronts,
// and the audit rule must not be swallowed by the users rule that follows it.
// ---------------------------------------------------------------------------
$adminPaths = [
    '/docs/idp/admin/users'              => 'admin.users',
    '/docs/idp/admin/users/12'           => 'admin.users',
    '/docs/idp/admin/users/12/roles'     => 'admin.users',
    '/docs/idp/admin/users/12/password'  => 'admin.users',
    '/docs/idp/admin/sessions'           => 'admin.users',
    '/docs/idp/admin/roles'              => 'admin.users',
    '/docs/idp/admin/ping'               => 'admin.users',
    '/docs/idp/admin.php'                => 'admin.users',

    // audit.view is a separate grant; an auditor may hold it without holding
    // admin.users, so this must not fall through to the users rule.
    '/docs/idp/admin/audit'              => 'audit.view',
    '/docs/idp/admin/audit/csv'          => 'audit.view',
    '/docs/idp/admin/audit.csv'          => 'audit.view',
    '/docs/idp/admin/audit?actor=carl'   => 'audit.view',

    // Phase 2 service endpoints: no cookie session may ever reach them.
    '/docs/idp/svc/f2/users'             => 'DENY',
    '/docs/idp/svc/'                     => 'DENY',

    // The subrequest target itself stays denied to real traffic.
    '/docs/idp/authz.php'                => 'DENY',

    // Traversal out of the audit rule must not land on something looser.
    '/docs/idp/admin/audit/../users'     => 'admin.users',
    '/docs/idp/admin/../../dashboard.html' => 'monitoring.view',
];
foreach ($adminPaths as $path => $want) {
    check('acl(' . $path . ')', acl_required_perm($path), $want);
}

// ---------------------------------------------------------------------------
// The capi-www static portal (location /). Deny-by-default means every
// document and asset it serves needs a rule — a portal that renders without
// its stylesheet looks like an outage, not like a permissions problem.
// Enumerated against the container's actual docroot on 2026-08-09.
// ---------------------------------------------------------------------------
$portalPaths = [
    '/'                        => 'AUTH',
    '/index.html'              => 'AUTH',
    '/portal.css'              => 'AUTH',
    '/assets/docs.css'         => 'AUTH',
    '/assets/crosswalk.css'    => 'AUTH',
    '/platform/'               => 'AUTH',
    '/platform/index.html'     => 'AUTH',
    '/uhc/'                    => 'AUTH',
    '/about/'                  => 'AUTH',
    '/projects/'               => 'AUTH',
    '/projects/uhc-y2/'        => 'AUTH',
    '/projects/uhc-y2/tabulations/t01.html' => 'tabulations.view',
    // Must stay reachable anonymously, or a wrong URL reads as a logout.
    '/404.html'                => 'PUBLIC',
    '/robots.txt'              => 'PUBLIC',
    '/favicon.ico'             => 'PUBLIC',
    // Still denied: an unlisted path under the portal fails closed.
    '/secret-new-page.html'    => 'DENY',
];
foreach ($portalPaths as $path => $want) {
    check('portal acl(' . $path . ')', acl_required_perm($path), $want);
}

// Operator guides. The admin portal guide must be reachable by EVERY account,
// because it is where "why am I being asked to change my password" is
// answered — and that applies to all 18, most of whom hold no admin
// permission at all.
foreach (['/docs/admin-portal-guide.html', '/docs/capi-manual.html',
          '/docs/enumerator-guide.html', '/docs/hcw-guide.html'] as $g) {
    check('guide acl(' . $g . ')', acl_required_perm($g), 'AUTH');
}

// Admin API traffic is not a respondent-data read; logging it here would
// double-count against the audit rows the endpoints write themselves.
foreach (['/docs/idp/admin/users', '/docs/idp/admin/audit'] as $p) {
    check('auditable(' . $p . ')', acl_is_auditable_read($p) ? 'yes' : 'no', 'no');
}

printf("\n%d passed, %d failed\n", $pass, $fail);
exit($fail === 0 ? 0 : 1);
