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
                return fh.read() + SIGNOUT_CSS
        except OSError:
            continue
    return _CSS_FALLBACK + SIGNOUT_CSS


FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' "
           "viewBox='0 0 40 40'%3E%3Crect width='40' height='40' rx='9' fill='%23046a38'/"
           "%3E%3Cpath d='M20 9l9 5v12l-9 5-9-5V14z' fill='%23e5b23b'/%3E%3C/svg%3E")


def _ico(d):
    return ('<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" '
            'aria-hidden="true">%s</svg>' % d)


# Navigation model — identical structure to the portal. Hrefs are stored
# project-relative / site-absolute; a `base` prefix (e.g. the portal origin)
# is applied at render time so the same nav works when served from csweb.
_NAV = [
    ("Project", [
        ("Overview", P + "/", _ico('<path d="M3 10.5 12 4l9 6.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/>'), ""),
        ("Guides", P + "/guides/", _ico('<path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2z"/><path d="M8 7h7M8 11h7"/>'), ""),
        ("Instruments", P + "/instruments/", _ico('<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>'), ""),
        ("Manual", P + "/manual/", _ico('<path d="M6 3h9l5 5v13a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z"/><path d="M14 3v6h6"/>'), ""),
    ]),
    ("Operations", [
        ("Monitoring", P + "/monitoring/", _ico('<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>'), "lock"),
        ("Data &amp; exports", P + "/data/", _ico('<ellipse cx="12" cy="6" rx="8" ry="3"/><path d="M4 6v6c0 1.7 3.6 3 8 3s8-1.3 8-3V6"/><path d="M4 12v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/>'), "lock"),
        ("Tabulations", P + "/tabulations/", _ico('<path d="M3 5h18v14H3z"/><path d="M3 10h18M9 5v14M15 5v14"/>'), ""),
        ("Archive", P + "/archive/pretest-2026-07-15/", _ico('<rect x="3" y="4" width="18" height="4" rx="1"/><path d="M5 8v11a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8"/><path d="M10 12h4"/>'), ""),
    ]),
    ("Administration", [
        ("Admin console", "https://capi.asiansocial.org/docs/admin/", _ico('<path d="M4 7h9M17 7h3M4 12h3M11 12h9M4 17h9M17 17h3"/><circle cx="15" cy="7" r="2"/><circle cx="9" cy="12" r="2"/><circle cx="15" cy="17" r="2"/>'), "lock"),
    ]),
    ("Platform", [
        ("All projects", "/projects/", _ico('<path d="m12 3 9 5-9 5-9-5z"/><path d="m3 13 9 5 9-5"/>'), ""),
        ("What we build", "/platform/", _ico('<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>'), ""),
        ("About", "/about/", _ico('<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>'), ""),
    ]),
]


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
        for label, href, icon, lock in items:
            lk = '<span class="lk">&#128274;</span>' if lock else ""
            o.append('<a class="%s" href="%s">%s<span>%s</span>%s</a>'
                     % ("on" if href == active else "", _href(href, base), icon, label, lk))
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
SIGNOUT_CHIP = '<span class="tb-user" id="tbUser"></span>'

SIGNOUT_JS = (
    '<script>(function(){var e=document.getElementById("tbUser");if(!e)return;'
    'fetch("/docs/whoami.php",{credentials:"same-origin"})'
    '.then(function(r){return r.ok?r.json():null})'
    '.then(function(d){if(!d||!d.signed_in)return;'
    'var u=document.createElement("b");u.textContent=d.user;'
    'var t=document.createElement("span");t.className="tier";t.textContent=d.tier;'
    'var a=document.createElement("a");a.href="/docs/auth/logout";a.textContent="Sign out";'
    'e.appendChild(u);e.appendChild(t);e.appendChild(a);e.className="tb-user on";'
    '}).catch(function(){});})();</script>'
)

PILL_LIVE = '<span class="pill live"><span class="dot"></span>Fieldwork live</span>'
PILL_LOCK = '<span class="pill lock">&#128274; Sign-in required</span>'


def head(title, desc="", extra_css="", robots="noindex"):
    """<!doctype> through </head>. The design system is inlined; `extra_css`
    (page-specific styles — dashboard tables, bell, Leaflet overrides) follows
    it so page rules can layer on the shared tokens."""
    extra = ("\n<style>%s</style>" % extra_css) if extra_css else ""
    return ('<!doctype html>\n<html lang="en">\n<head>\n'
            '<meta charset="UTF-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<meta name="robots" content="%s">\n'
            '<title>%s</title>\n'
            '<meta name="description" content="%s">\n'
            '<style>%s</style>%s\n'
            '<link rel="icon" href="%s">\n'
            '</head>' % (robots, title, desc, tokens_css(), extra, FAVICON))


def open_shell(title, desc="", active="", crumbs=None, tb_right="",
               extra_css="", base="", head_extra=""):
    """Everything from <!doctype> to the open of the content canvas.

    Pair with close_shell(). `tb_right` fills the topbar's right slot (status
    pill, notification bell, view toggles). `head_extra` injects markup just
    before </head> (e.g. Leaflet stylesheet links for the map)."""
    crumbs = crumbs or [("ASPSI CAPI", None)]
    h = head(title, desc, extra_css)
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
    return ('%s\n</div>\n</div>\n</div>\n%s\n%s\n</body>\n</html>\n'
            % (foot, body_extra, SIGNOUT_JS))
