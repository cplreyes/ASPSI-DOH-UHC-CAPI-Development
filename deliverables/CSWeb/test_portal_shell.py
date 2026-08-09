# -*- coding: utf-8 -*-
"""Unit tests for the shared shell. Plain script, stdlib only.

    python test_portal_shell.py      # exit 0 = all pass

Same conventions as auth/test_acl.php: a check() helper, a running count, and
a non-zero exit on any failure. No pytest — the box generators have no
third-party deps and neither do their tests.
"""
import sys
import portal_shell as PS

_pass = 0
_fail = 0


def check(what, got, want):
    global _pass, _fail
    if got == want:
        _pass += 1
        return
    _fail += 1
    print("FAIL  %-52s got=%r want=%r" % (what, got, want))


def contains(what, haystack, needle):
    check(what, needle in haystack, True)


def missing(what, haystack, needle):
    check(what, needle in haystack, False)


# --- css mode --------------------------------------------------------------
h_inline = PS.head("T", css="inline")
h_link = PS.head("T", css="link")
contains("inline mode emits a style block", h_inline, "<style>")
missing("inline mode has no stylesheet link", h_inline, 'rel="stylesheet"')
contains("link mode emits the stylesheet", h_link, '<link rel="stylesheet" href="/portal.css">')
missing("link mode inlines no tokens", h_link, "--verde")
check("inline is the default", PS.head("T"), h_inline)

# --- nav permission model --------------------------------------------------
check("monitoring needs monitoring.view", PS.NAV_PERMS.get(PS.P + "/monitoring/"), "monitoring.view")
check("data needs data.export", PS.NAV_PERMS.get(PS.P + "/data/"), "data.export")
check("tabulations needs tabulations.view", PS.NAV_PERMS.get(PS.P + "/tabulations/"), "tabulations.view")
# Deliberately still /docs/admin/: the portal URL for admin only starts working
# in Slice 5 (nginx proxy), and a nav link must never point at a 404. The flip
# to P + "/admin/" happens in the same task that creates the proxy.
check("admin needs admin.system", PS.NAV_PERMS.get("/docs/admin/"), "admin.system")
check("overview needs nothing", PS.NAV_PERMS.get(PS.P + "/"), None)

side = PS.sidebar(PS.P + "/monitoring/")
contains("permissioned entry carries data-perm", side, 'data-perm="monitoring.view"')
missing("unpermissioned entry carries none", side,
        '<a class="" href="/projects/uhc-y2/guides/" data-perm')
contains("active entry is marked", side, 'class="on" href="/projects/uhc-y2/monitoring/"')
missing("the decorative padlock is gone", side, '<span class="lk">')

print("%d passed, %d failed" % (_pass, _fail))
sys.exit(1 if _fail else 0)
