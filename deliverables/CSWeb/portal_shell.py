# -*- coding: utf-8 -*-
"""portal_shell.py — single source of truth for the ASPSI CAPI surface chrome.

One shell, three surfaces. `build_portal.py` (static portal, built on the
workstation) and the two on-box cron generators (`csweb-dashboard-gen.py`,
`csweb-map-gen.py`) all import this module so the sidebar, topbar, footer,
brand palette and type scale are defined exactly once.

Design tokens + component CSS live in `portal.css` (the CSS source of truth);
this module holds the MARKUP source of truth and inlines that CSS so a
generated page is self-contained (no cross-origin stylesheet needed while the
dashboards are still served from csweb during pretest).

stdlib only — the box generators have no third-party deps.
"""
import os

# Canonical brand green. The two dashboards historically hard-coded #006b3f;
# they now retune to this so all three surfaces share one verde (Carl, 2026-07-25).
VERDE = "#046a38"
GOLD = "#e5b23b"

P = "/projects/uhc-y2"                       # the one project's route root
PORTAL_ORIGIN = "https://capi.asiansocial.org"

_HERE = os.path.dirname(os.path.abspath(__file__))

# Minimal fallback so the shell still renders if portal.css is not shipped
# alongside this module. The real design system is portal.css.
_CSS_FALLBACK = ":root{--verde:%s;--gold:%s}body{font-family:Segoe UI,sans-serif}" % (VERDE, GOLD)


def tokens_css():
    """The full design system CSS (portal.css), read from beside this module."""
    for cand in (os.path.join(_HERE, "portal.css"),
                 os.path.join(_HERE, "assets", "portal.css")):
        try:
            with open(cand, encoding="utf-8") as fh:
                return fh.read() + SIGNOUT_CSS + PERM_DIM_CSS
        except OSError:
            continue
    return _CSS_FALLBACK + SIGNOUT_CSS + PERM_DIM_CSS


FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' "
           "viewBox='0 0 40 40'%3E%3Crect width='40' height='40' rx='9' fill='%23046a38'/"
           "%3E%3Cpath d='M20 9l9 5v12l-9 5-9-5V14z' fill='%23e5b23b'/%3E%3C/svg%3E")


def _ico(d):
    return ('<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" '
            'aria-hidden="true">%s</svg>' % d)


# Navigation model — identical structure to the portal. Hrefs are stored
# project-relative / site-absolute; a `base` prefix (e.g. the portal origin)
# is applied at render time so the same nav works when served off-origin.
#
# The fourth slot is the permission acl.php requires for that path, or "" for
# entries any signed-in account may open. It used to hold the literal string
# "lock", which rendered a padlock on three entries regardless of who was
# looking — decorative, and misleading once the whole portal became gated on
# 2026-07-28. Now it drives data-perm, and PERM_DIM_JS dims what YOUR account
# cannot open.
#
# Admin console deliberately still points at /docs/admin/ — the portal URL
# /projects/uhc-y2/admin/ only starts existing when its nginx proxy lands
# (unification Slice 5), and a nav link must never point at a 404. Flip the
# href and the emit_php_partial default together in that slice.
_NAV = [
    ("Project", [
        ("Overview", P + "/", _ico('<path d="M3 10.5 12 4l9 6.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/>'), ""),
        ("Guides", P + "/guides/", _ico('<path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2z"/><path d="M8 7h7M8 11h7"/>'), ""),
        ("Instruments", P + "/instruments/", _ico('<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>'), ""),
        ("Manual", P + "/manual/", _ico('<path d="M6 3h9l5 5v13a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z"/><path d="M14 3v6h6"/>'), ""),
    ]),
    ("Operations", [
        ("Monitoring", P + "/monitoring/", _ico('<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>'), "monitoring.view"),
        ("Data &amp; exports", P + "/data/", _ico('<ellipse cx="12" cy="6" rx="8" ry="3"/><path d="M4 6v6c0 1.7 3.6 3 8 3s8-1.3 8-3V6"/><path d="M4 12v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/>'), "data.export"),
        ("Tabulations", P + "/tabulations/", _ico('<path d="M3 5h18v14H3z"/><path d="M3 10h18M9 5v14M15 5v14"/>'), "tabulations.view"),
        ("Archive", P + "/archive/pretest-2026-07-15/", _ico('<rect x="3" y="4" width="18" height="4" rx="1"/><path d="M5 8v11a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8"/><path d="M10 12h4"/>'), ""),
    ]),
    ("Administration", [
        ("Admin console", "/docs/admin/", _ico('<path d="M4 7h9M17 7h3M4 12h3M11 12h9M4 17h9M17 17h3"/><circle cx="15" cy="7" r="2"/><circle cx="9" cy="12" r="2"/><circle cx="15" cy="17" r="2"/>'), "admin.system"),
    ]),
    # The two working systems behind their own credentials. They lived as cards
    # on the monitoring signpost until Slice 3 deleted it — the rail is now the
    # one place every surface shares, so the links live here. sidebar() renders
    # any http(s) href with target=_blank + a "separate sign-in" title: an
    # external system opens in its own tab and never inherits console identity.
    ("Systems", [
        ("F2 admin portal", "https://uhc-hcw.asiansocial.org/admin", _ico('<rect x="3" y="3" width="8" height="8" rx="1.5"/><rect x="13" y="3" width="8" height="8" rx="1.5"/><rect x="3" y="13" width="8" height="8" rx="1.5"/><path d="M13 13h3v3h-3zM18 13h3M13 18h3M18 18h3v3h-3z"/>'), ""),
        ("CSWeb", "https://csweb.asiansocial.org/csweb/", _ico('<ellipse cx="12" cy="5.5" rx="8" ry="2.8"/><path d="M4 5.5V12c0 1.6 3.6 2.8 8 2.8s8-1.2 8-2.8V5.5"/><path d="M4 12v6.5c0 1.6 3.6 2.8 8 2.8s8-1.2 8-2.8V12"/>'), ""),
    ]),
    ("Platform", [
        ("All projects", "/projects/", _ico('<path d="m12 3 9 5-9 5-9-5z"/><path d="m3 13 9 5 9-5"/>'), ""),
        ("What we build", "/platform/", _ico('<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>'), ""),
        ("About", "/about/", _ico('<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>'), ""),
    ]),
]

# href -> required permission, for anything that renders nav links outside
# sidebar() (tests, and any future consumer that needs the mapping).
NAV_PERMS = {href: perm for _sec, items in _NAV
             for _label, href, _icon, perm in items if perm}


def _href(h, base):
    """Prefix an internal path with `base` (portal origin) when set."""
    if not base or h.startswith("http"):
        return h
    return base.rstrip("/") + h


def sidebar(active, base=""):
    """The persistent left rail. `active` is a stored nav path; `base` prefixes
    every internal link so the rail works when the page is served off-origin."""
    o = ['<aside class="sidebar">',
         '<a class="sb-brand" href="%s"><span class="sb-mark">A</span><span><b>ASPSI CAPI</b>'
         '<span>capi.asiansocial.org</span></span></a>' % _href("/", base),
         '<div class="sb-proj"><a class="sb-proj-card" href="%s"><div class="k">Active project</div>'
         '<div class="v">UHC Survey Year 2</div></a></div>' % _href(P + "/", base),
         '<nav class="sb-nav">']
    for sec, items in _NAV:
        o.append('<div class="sb-sec">%s</div>' % sec)
        for label, href, icon, perm in items:
            dp = ' data-perm="%s"' % perm if perm else ""
            ext = (' target="_blank" rel="noopener" title="Opens in a new tab '
                   '&mdash; separate sign-in"') if href.startswith("http") else ""
            o.append('<a class="%s" href="%s"%s%s>%s<span>%s</span></a>'
                     % ("on" if href == active else "", _href(href, base), dp, ext, icon, label))
    o.append('</nav><div class="sb-foot">Asian Social Project Services, Inc.<br>'
             '<a href="https://asiansocial.org">asiansocial.org</a>'
             '<div class="sb-powered">Powered by Analytiflow.</div></div></aside>')
    return "".join(o)


def crumbs_html(crumbs, base=""):
    """crumbs: list of (label, href-or-None)."""
    c = []
    for i, (label, href) in enumerate(crumbs):
        if i:
            c.append('<span class="sep">/</span>')
        c.append('<a href="%s">%s</a>' % (_href(href, base), label) if href
                 else '<span class="cur">%s</span>' % label)
    return "".join(c)


SIGNOUT_CSS = (
    '.tb-user{display:none;align-items:center;gap:8px;font-size:12.5px;color:var(--ink-3);'
    'padding-left:12px;margin-left:4px;border-left:1px solid var(--line)}'
    '.tb-user.on{display:inline-flex}'
    '.tb-user b{color:var(--ink-2);font-weight:650}'
    '.tb-user .tier{font-size:10px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;'
    'padding:2px 7px;border-radius:5px;background:var(--verde-100,#eefaf3);color:var(--verde);'
    'border:1px solid #cfe6d8}'
    '.tb-user a{color:var(--verde);text-decoration:none;font-weight:650}'
    '.tb-user a:hover{text-decoration:underline}'
)

# Fills the chip from the session. Kept tiny and defensive: any failure just
# leaves the chip hidden rather than showing a broken control.
#
# /docs/idp/me and /docs/idp/logout are the canonical endpoints since the
# 2026-08-08 cutover; whoami.php and /docs/auth/logout are legacy shims kept
# alive only so old bookmarks resolve. me.php returns a FLAT object --
# {signed_in, user, roles, perms, must_change, can{}, tier, logout} -- NOT the
# {ok,data,request_id} envelope the admin API wraps around everything. Reading
# d.data here would not throw (the .catch() is deliberately empty), it would
# just silently blank the chip on every page. me.php emits `tier` precisely so
# this chip keeps working (me.php:44-55).
SIGNOUT_CHIP = '<span class="tb-user" id="tbUser"></span>'

SIGNOUT_JS = (
    '<script>(function(){var e=document.getElementById("tbUser");if(!e)return;'
    'fetch("/docs/idp/me",{credentials:"same-origin"})'
    '.then(function(r){return r.ok?r.json():null})'
    '.then(function(d){if(!d||!d.signed_in)return;'
    'var u=document.createElement("b");u.textContent=d.user;'
    'var t=document.createElement("span");t.className="tier";t.textContent=d.tier||"user";'
    'var a=document.createElement("a");a.href=d.logout||"/docs/idp/logout";'
    'a.textContent="Sign out";'
    'e.appendChild(u);e.appendChild(t);e.appendChild(a);e.className="tb-user on";'
    '}).catch(function(){});})();</script>'
)

PILL_LIVE = '<span class="pill live"><span class="dot"></span>Fieldwork live</span>'
# PILL_LOCK is gone deliberately. It claimed "Sign-in required" on two pages
# while the WHOLE portal has required sign-in since 2026-07-28 -- so the ten
# pages without it read as public. Status pills state facts; access is shown
# per-account by PERM_DIM_JS below.

# A padlock on a nav entry told every reader the same thing regardless of who
# they were, which is decoration. This dims the entries YOUR account cannot
# open. It fails open: if /docs/idp/me is unreachable, nothing is dimmed and
# the edge still enforces -- a cosmetic script must never be the gate.
PERM_DIM_CSS = (
    '.sb-nav a.sb-off{opacity:.45}'
    '.sb-nav a.sb-off span{text-decoration:none}'
)

PERM_DIM_JS = (
    '<script>(function(){'
    'var links=document.querySelectorAll(".sb-nav a[data-perm]");if(!links.length)return;'
    'fetch("/docs/idp/me",{credentials:"same-origin"})'
    '.then(function(r){return r.ok?r.json():null})'
    '.then(function(d){if(!d||!d.signed_in)return;'
    'var held=d.perms||[];'
    'Array.prototype.forEach.call(links,function(a){'
    'if(held.indexOf(a.getAttribute("data-perm"))<0){a.className+=" sb-off";'
    'a.setAttribute("title","Your account does not have access to this");}});'
    '}).catch(function(){});})();</script>'
)


def head(title, desc="", extra_css="", robots="noindex", css="inline"):
    """<!doctype> through </head>.

    css="inline" bakes portal.css into the document. That was required while
    the dashboards were served from csweb and the portal from capi — a
    cross-origin stylesheet would have needed CORS. Everything is same-origin
    since 2026-07-28, so css="link" is now viable and is what the static
    portal uses; the on-box generators stay on "inline" so their output is
    self-contained even if /portal.css is mid-deploy.

    `extra_css` (page-specific styles — dashboard tables, bell, Leaflet
    overrides) follows the design system so page rules can layer on the
    shared tokens."""
    extra = ("\n<style>%s</style>" % extra_css) if extra_css else ""
    sheet = ('<style>%s</style>' % tokens_css()) if css == "inline" \
        else '<link rel="stylesheet" href="/portal.css">'
    return ('<!doctype html>\n<html lang="en">\n<head>\n'
            '<meta charset="UTF-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<meta name="robots" content="%s">\n'
            '<title>%s</title>\n'
            '<meta name="description" content="%s">\n'
            '%s%s\n'
            '<link rel="icon" href="%s">\n'
            '</head>' % (robots, title, desc, sheet, extra, FAVICON))


def open_shell(title, desc="", active="", crumbs=None, tb_right="",
               extra_css="", base="", head_extra="", css="inline"):
    """Everything from <!doctype> to the open of the content canvas.

    Pair with close_shell(). `tb_right` fills the topbar's right slot (status
    pill, notification bell, view toggles). `head_extra` injects markup just
    before </head> (e.g. Leaflet stylesheet links for the map). `css` is
    passed through to head() — see there."""
    crumbs = crumbs or [("ASPSI CAPI", None)]
    h = head(title, desc, extra_css, css=css)
    if head_extra:
        h = h.replace("</head>", head_extra + "\n</head>")
    return ('%s\n<body>\n<div class="app">\n%s\n<div class="main">\n'
            '<div class="topbar"><div class="crumbs">%s</div>'
            '<div class="tb-right">%s<span class="tb-user" id="tbUser"></span></div></div>\n'
            '<div class="canvas">\n'
            % (h, sidebar(active, base), crumbs_html(crumbs, base), tb_right))


def close_shell(footer_html="", body_extra=""):
    """Close the canvas/main/app and the document. `footer_html` renders inside
    the canvas as a page footer; `body_extra` (fixed-position widgets, scripts)
    is emitted after .app but before </body>."""
    foot = ('<footer class="page-foot">%s</footer>' % footer_html) if footer_html else ""
    return ('%s\n</div>\n</div>\n</div>\n%s\n%s%s\n</body>\n</html>\n'
            % (foot, body_extra, SIGNOUT_JS, PERM_DIM_JS))


# ---------------------------------------------------------------------------
# Generated PHP partial (admin console chrome)
# ---------------------------------------------------------------------------

_PHP_TEMPLATE = """<?php
// GENERATED by portal_shell.py -- do not edit. Regenerate with:
//     python -c "import portal_shell; portal_shell.emit_php_partial('%(path)s')"
//
// Why this file exists: admin/index.php is PHP and portal_shell.py is Python,
// and hand-copying the nav into PHP is exactly how the console ended up with
// five different chromes. The markup keeps ONE source; this is a mechanical
// transcription of it, rewritten on every deploy.
declare(strict_types=1);

const CAPI_SHELL_HEAD = <<<'CAPIHTML'
%(head)s
CAPIHTML;

const CAPI_SHELL_SIDEBAR = <<<'CAPIHTML'
%(sidebar)s
CAPIHTML;

const CAPI_SHELL_CRUMB_PREFIX = <<<'CAPIHTML'
%(crumbs)s
CAPIHTML;

const CAPI_SHELL_SIGNOUT_JS = <<<'CAPIHTML'
%(signout)s
CAPIHTML;

function capi_shell_open(string $title, string $crumbLeaf): string
{
    $t = htmlspecialchars($title, ENT_QUOTES, 'UTF-8');
    $l = htmlspecialchars($crumbLeaf, ENT_QUOTES, 'UTF-8');
    $head = str_replace('__CAPI_TITLE__', $t, CAPI_SHELL_HEAD);
    return $head . "\\n<body>\\n<div class=\\"app\\">\\n" . CAPI_SHELL_SIDEBAR
        . "\\n<div class=\\"main\\">\\n<div class=\\"topbar\\"><div class=\\"crumbs\\">"
        . CAPI_SHELL_CRUMB_PREFIX . '<span class="sep">/</span><span class="cur">' . $l
        . "</span></div>"
        . '<div class="tb-right"><span class="tb-user" id="tbUser"></span></div></div>'
        . "\\n<div class=\\"canvas\\">\\n";
}

function capi_shell_close(): string
{
    return "\\n</div>\\n</div>\\n</div>\\n" . CAPI_SHELL_SIGNOUT_JS . "\\n</body>\\n</html>\\n";
}
"""


def emit_php_partial(path, active="/docs/admin/", base=""):
    """Write the shell as a generated PHP include for admin/index.php.

    Nowdoc (<<<'CAPIHTML') is used deliberately: it does not interpolate, so
    markup containing $ or backslashes survives untouched. sidebar() joins
    without newlines, so no emitted line can equal the terminator; the guard
    below is belt-and-braces for the day that stops being true.

    `active` defaults to the admin console's CURRENT nav href. When the nav
    entry flips to the portal URL (unification Slice 5), flip this default in
    the same commit or the sidebar stops highlighting.
    """
    body = _PHP_TEMPLATE % {
        "path": path.replace("\\", "/"),
        "head": head("__CAPI_TITLE__", "", css="link"),
        "sidebar": sidebar(active, base),
        "crumbs": crumbs_html([("Console", _href("/", base)),
                               ("UHC Survey Year 2", _href(P + "/", base))], ""),
        "signout": SIGNOUT_JS,
    }
    for line in body.splitlines():
        if line.strip() == "CAPIHTML;" and line != "CAPIHTML;":
            raise ValueError("php partial: indented nowdoc terminator would truncate")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)
    return len(body.encode("utf-8"))
