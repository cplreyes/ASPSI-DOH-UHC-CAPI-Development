#!/usr/bin/env python3
r"""Build capi.asiansocial.org — the unified ASPSI CAPI portal.

Structure decided by Carl 2026-07-22 (options diagram
`capi-portal-sitemap-options-2026-07-22.png`, spec `capi-portal-sitemap-spec-2026-07-22.md`):
Option A project-first + Option C's role welcome mat on the project home.

  /                                    CAPI at ASPSI + project cards
  /about/  /platform/  /projects/
  /projects/uhc-y2/                    project home = 4 role rows
        guides/{enumerator,supervisor,healthcare-worker}/
        manual/
        instruments/{f1,f3,f4,f2}/[crosswalk/]
        monitoring/                    -> the gated dashboard + map
        data/                          -> the gated data room
        archive/pretest-2026-07-15/

Two kinds of page:
  AUTHORED  written here, in the portal design system (src/styles.css).
  PORTED    the real content pages pulled from csweb (guides, manual, crosswalks,
            pretest). Their own layout/CSS is preserved — they are good pages — but
            a slim portal bar is injected and every internal link is rewritten to its
            new home, which is what makes the site feel like ONE site.

Step 3 of the migration is DONE (2026-07-28): the whole /docs console (dashboard, map,
data room, admin, sign-in) is now served from capi.asiansocial.org — csweb keeps only
the CSWeb app + CSEntry sync. All /docs links here point at CONSOLE.
NOTHING here touches /csweb/ or the tablet SyncUrl — pretest is running (Carl, 2026-07-22).

Usage:
  python build_portal.py                      # -> build/
  python build_portal.py --deploy             # + rsync to the capi-www docroot
"""
import argparse, os, re, shutil, subprocess, sys, datetime

# The shared chrome lives one directory up, beside the on-box generators that
# also import it. Inserting the parent on sys.path keeps ONE copy of the module
# rather than a build-time duplicate — a duplicate is how portal.css drifted
# between 2026-07-28 and 2026-08-09 (the portal copy missed the mobile topbar
# fix and every /projects/ page scrolled sideways on a phone).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import portal_shell as PS

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")
CSWEB_SRC = os.path.join(SRC, "csweb")
BUILD = os.path.join(HERE, "build")
DEPLOY_HOST = "root@207.148.65.115"
DEPLOY_PATH = "/opt/app/capi-www/"
KEY = os.path.expanduser("~/.ssh/aspsi-csweb")

CSWEB = "https://csweb.asiansocial.org"      # the CSWeb app + CSEntry sync ONLY
CONSOLE = "https://capi.asiansocial.org"     # the console: /docs dashboards, data room, admin
P = "/projects/uhc-y2"

# old csweb URL -> new portal path (order matters: longest first)
LINKMAP = [
    ("https://csweb.asiansocial.org/docs/data/", CONSOLE + "/docs/data/"),
    ("https://csweb.asiansocial.org/docs/dashboard.html", CONSOLE + "/docs/dashboard.html"),
    ("https://csweb.asiansocial.org/docs/map.html", CONSOLE + "/docs/map.html"),
    ("/docs/data/", CONSOLE + "/docs/data/"),
    ("/docs/dashboard.html", CONSOLE + "/docs/dashboard.html"),
    ("/docs/map.html", CONSOLE + "/docs/map.html"),
    ("/docs/capi-manual.html", P + "/archive/capi-manual-2026-07/"),
    ("/docs/enumerator-guide.html", P + "/guides/enumerator/"),
    ("/docs/hub-guide.html", P + "/guides/supervisor/"),
    ("/docs/hcw-guide.html", P + "/guides/healthcare-worker/"),
    ("/docs/pretest-guide.html", P + "/archive/pretest-2026-07-15/"),
    ("/docs/f1-crosswalk.html", P + "/instruments/f1/crosswalk/"),
    ("/docs/f2-crosswalk.html", P + "/instruments/f2/crosswalk/"),
    ("/docs/f3-crosswalk.html", P + "/instruments/f3/crosswalk/"),
    ("/docs/f4-crosswalk.html", P + "/instruments/f4/crosswalk/"),
    ("/csweb/", CSWEB + "/csweb/"),
    ("/help.html", P + "/"),
]

INSTRUMENTS = [
    {"k": "f1", "name": "Facility Head Survey", "ver": "1.1.4", "date": "2026-07-19",
     "vars": 316, "mode": "Tablet (CSEntry)", "who": "the officer in charge of a health facility",
     "about": "Facility-level implementation of UHC: service capacity, staffing, licensing, "
              "equipment and supplies, health-promotion and referral changes.",
     "cross": True},
    {"k": "f3", "name": "Patient Survey", "ver": "1.1.5", "date": "2026-07-19",
     "vars": 370, "mode": "Tablet (CSEntry)", "who": "patients exiting a sampled facility",
     "about": "The care experience as received: awareness of UHC programmes, services used, "
              "what was paid out of pocket, and satisfaction.",
     "cross": True},
    {"k": "f4", "name": "Household Survey", "ver": "1.4.4", "date": "2026-07-19",
     "vars": 299, "mode": "Tablet (CSEntry)", "who": "a knowledgeable adult in a sampled household",
     "about": "Health-seeking behaviour and the household economics of health: roster, insurance "
              "coverage, access to medicines, and health expenditure over several recall windows.",
     "cross": True},
    {"k": "f2", "name": "Health Care Worker Survey", "ver": "", "date": "",
     "vars": 130, "mode": "Web app (any phone)", "who": "health care workers, self-administered",
     "about": "Conditions of work and views on UHC implementation, answered privately by the "
              "worker on their own phone — no interviewer present.",
     "cross": True, "pwa": "https://uhc-hcw.asiansocial.org"},
]

PORTAL_BAR = (
    '<div style="background:#034d29;color:#fff;font:14px/1.5 \'Segoe UI\',system-ui,sans-serif">'
    '<div style="max-width:1080px;margin:0 auto;padding:8px 24px;display:flex;flex-wrap:wrap;'
    'gap:6px 20px;align-items:center">'
    '<a href="/" style="color:#fff;text-decoration:none;font-weight:700">ASPSI CAPI</a>'
    '<span style="opacity:.55">/</span>'
    '<a href="' + P + '/" style="color:#dcefe2;text-decoration:none">UHC Survey Y2</a>'
    '<a href="' + P + '/guides/" style="color:#dcefe2;text-decoration:none;margin-left:auto">Guides</a>'
    '<a href="' + P + '/instruments/" style="color:#dcefe2;text-decoration:none">Instruments</a>'
    '<a href="' + P + '/monitoring/" style="color:#dcefe2;text-decoration:none">Monitoring</a>'
    '<a href="' + P + '/data/" style="color:#dcefe2;text-decoration:none">Data</a>'
    '</div></div>'
)


# ---------------------------------------------------------------- authored pages
# (The pre-2026-07-22 "document-site" shell that used to sit here was dead code
# from the day the admin-portal shell below shadowed it. Deleted 2026-08-09 —
# a resurrectable third chrome is exactly what the unification removes.)
def hero(crumb, h1, lead):
    return ('<div class="hero"><div class="hero-inner"><div class="crumb">%s</div>'
            '<h1>%s</h1><p class="lead">%s</p></div></div>' % (crumb, h1, lead))


def home_page(skeleton_home):
    """Keep the existing home copy (it is good); repoint its nav + project card."""
    s = skeleton_home
    s = s.replace('<a class="link" href="/uhc/">UHC Survey 2026</a>\n    <a class="link" href="/docs/">Documentation</a>',
                  '<a class="link" href="%s/">UHC Survey Y2</a>\n    <a class="link" href="/platform/">What we build</a>\n    <a class="link" href="/about/">About</a>' % P)
    s = s.replace('href="/uhc/">Open project</a>', 'href="%s/">Open project</a>' % P)
    s = s.replace('<title>ASPSI CAPI Services</title>',
                  '<title>ASPSI CAPI — survey data systems</title>\n  <meta name="robots" content="noindex">')
    # the project card gains real facts
    s = s.replace('<p>Nationwide Universal Health Care study — four survey instruments covering\n        health facilities, health care workers, patients, and households.</p>',
                  '<p>Universal Health Care study for the Department of Health — four instruments '
                  'covering health facilities, health care workers, patients and households. '
                  'Fieldwork in progress; monitoring and analysis-ready data are live.</p>')
    s = s.replace('</footer>', '</footer>').replace(
        '<span><a href="https://asiansocial.org">asiansocial.org</a></span>',
        '<span><a href="%s/">UHC Survey Y2</a> &middot; <a href="https://asiansocial.org">asiansocial.org</a></span>' % P)
    return s


ROLES = [
    ("I'm collecting in the field", "Enumerator on a tablet (F1, F3, F4).",
     [("Enumerator guide", P + "/guides/enumerator/", "CSEntry, case entry, syncing, what to do when something goes wrong"),
      ("Supervisor hub guide", P + "/guides/supervisor/", "assignments, Bluetooth collect/relay, sending cases in"),
      ("Field manuals", P + "/manual/", "official enumerator + supervisor manuals")], ""),
    ("I'm a health care worker invited to the survey", "You answer on your own phone — no interviewer.",
     [("How to complete the survey", P + "/guides/healthcare-worker/", "what it asks, how long it takes, your privacy"),
      ("Open the survey app", "https://uhc-hcw.asiansocial.org", "works offline; submits when you have a signal")], ""),
    ("I'm supervising fieldwork", "ASPSI and DOH staff tracking collection as it happens.",
     [("Sync Dashboard", CONSOLE + "/docs/dashboard.html", "cases in, completed vs partial, coverage against plan, data quality"),
      ("Map Report", CONSOLE + "/docs/map.html", "where cases were collected, GPS quality flags"),
      ("Monitoring overview", P + "/monitoring/", "what each view answers")], "login"),
    ("I'm working with the data", "Analysts and data users.",
     [("Data room", P + "/data/", "CSV, SPSS, Stata and R exports, refreshed every ~2 minutes"),
      ("Codebooks", P + "/instruments/", "every variable: label, question, universe, codes, validation"),
      ("Instruments", P + "/instruments/", "questionnaires, dictionaries, runnable CSPro packages")], "login"),
]


def project_home():
    rows = []
    for title, sub, links, gate in ROLES:
        ls = "".join(
            '<li><a href="%s">%s</a> — <span>%s</span></li>' % (u, t, d) for t, u, d in links)
        badge = '<span class="badge soon">login needed</span>' if gate else ""
        rows.append('<div class="rolerow"><div class="roletitle"><h3>%s</h3>%s</div>'
                    '<p class="rolesub">%s</p><ul class="rolelinks">%s</ul></div>'
                    % (title, badge, sub, ls))
    body = (hero("Project · Department of Health",
                 "UHC Survey Year 2",
                 "A nationwide Universal Health Care study collecting evidence from four "
                 "perspectives — the facility, the health care worker, the patient and the "
                 "household — on one integrated CAPI platform.")
            + '<main><section><h2>Start here</h2>'
              '<p class="sub">Pick the row that describes you.</p>'
            + "".join(rows) +
            '</section>'
            '<section><h2>What the survey covers</h2>'
            '<p class="sub">Four instruments, one questionnaire number, one data set.</p>'
            '<table class="plain"><tr><th>Form</th><th>Instrument</th><th>Answered by</th>'
            '<th>Mode</th><th>Variables</th></tr>'
            + "".join('<tr><td><a href="%s/instruments/%s/">%s</a></td><td>%s</td><td>%s</td>'
                      '<td>%s</td><td>%d</td></tr>'
                      % (P, i["k"], i["k"].upper(), i["name"], i["who"], i["mode"], i["vars"])
                      for i in INSTRUMENTS) +
            '</table></section>'
            '<section><h2>Project record</h2><div class="grid">'
            '<div class="card"><h3>Field manuals</h3><p>The official enumerator and supervisor '
            'field manuals — the reference for training and fieldwork.</p>'
            '<a class="go" href="%s/manual/">Open the manuals</a></div>'
            '<div class="card"><h3>Instruments &amp; codebooks</h3><p>Per instrument: the paper↔CAPI '
            'comparison, the codebook, the dictionary and a runnable CSPro package.</p>'
            '<a class="go" href="%s/instruments/">Browse instruments</a></div>'
            '<div class="card"><h3>Archive</h3><p>Superseded material kept for the record — '
            'the CAPI system manual and the July 2026 pretest field guide.</p>'
            '<a class="go" href="%s/archive/capi-manual-2026-07/">CAPI system manual</a>'
            ' &middot; <a class="go" href="%s/archive/pretest-2026-07-15/">Pretest guide</a></div>'
            '</div></section></main>' % (P, P, P, P))
    return shell("UHC Survey Year 2 — ASPSI CAPI",
                 "Project home for the ASPSI × DOH Universal Health Care Survey Year 2 — guides, "
                 "instruments, monitoring and data.", body, active=P + "/")


def guides_index():
    cards = [
        ("Enumerator guide", P + "/guides/enumerator/",
         "Using CSEntry on the tablet: opening the application, starting and resuming a case, "
         "capturing GPS and the verification photo, and syncing to the data hub."),
        ("Supervisor hub guide", P + "/guides/supervisor/",
         "The Supervisor Hub: logging in, assigning work, collecting cases over Bluetooth from "
         "enumerators with no signal, and relaying them to the server."),
        ("Health care worker guide", P + "/guides/healthcare-worker/",
         "For respondents of the F2 survey — what it asks, how long it takes, and how privacy "
         "is handled. Public, shareable with respondents."),
    ]
    body = (hero("UHC Survey Y2", "Guides",
                 "Step-by-step instructions for everyone who touches the survey.")
            + '<main>'
            + '<section><h2>Operating the software</h2>'
              '<p class="sub">How to run the tablet and the applications &mdash; written and '
              'maintained by the CAPI team, and updated as the builds change.</p>'
              '<div class="grid">'
            + "".join('<div class="card"><h3>%s</h3><p>%s</p><a class="go" href="%s">Open</a></div>'
                      % (t, d, u) for t, u, d in cards)
            + '</div></section>'
            + '<section><h2>Official field manuals</h2>'
              '<p class="sub">How to conduct the survey &mdash; authored by the ASPSI / UP study '
              'team. <b>Approved by ASPSI, though not yet final.</b> Where a manual and a software '
              'guide differ on field procedure, the manual governs.</p>'
              '<div class="grid">'
              '<div class="card"><h3>Field manuals</h3><p>The enumerator and supervisor field '
              'manuals &mdash; pre-fieldwork preparation, respondent selection and listing, '
              'handling ineligibles and refusals, team management and quality control. '
              'Version 1.1, 24 July 2026.</p>'
              '<a class="go" href="' + P + '/manual/">Open</a></div>'
            + '</div></section></main>')
    return shell("Guides — UHC Survey Y2", "Field and reference guides for the UHC Survey Year 2.",
                 body, active=P + "/guides/")


def instruments_index():
    rows = "".join(
        '<tr><td><a href="%s/instruments/%s/">%s</a></td><td>%s</td><td>%s</td><td>%s</td>'
        '<td>%d</td></tr>'
        % (P, i["k"], i["k"].upper(), i["name"], i["mode"],
           ("v%s (%s)" % (i["ver"], i["date"])) if i["ver"] else "web app, continuously deployed",
           i["vars"]) for i in INSTRUMENTS)
    body = (hero("UHC Survey Y2", "Instruments",
                 "Each instrument has one page: what it asks, how the paper questionnaire maps to "
                 "the CAPI application, its codebook, its dictionary, and a package you can run yourself.")
            + '<main><section><table class="plain">'
              '<tr><th>Form</th><th>Instrument</th><th>Mode</th><th>Current build</th><th>Variables</th></tr>'
            + rows + '</table></section>'
            '<section><h2>Documentation that applies to all four</h2><div class="grid">'
            '<div class="card"><h3>Codebooks</h3><p>Variable, label, the literal question, universe '
            '(who was asked), value codes, special codes and the validation rules the tablet enforces '
            '— documented to the DDI-Codebook 2.5 element set that the PSA Data Archive uses.</p>'
            '<a class="go" href="' + CONSOLE + '/docs/data/">Download (login)</a></div>'
            '<div class="card"><h3>Data dictionaries</h3><p>The CSPro <code>.dcf</code> dictionaries '
            'themselves — the machine-readable definition every export is derived from.</p>'
            '<a class="go" href="' + CONSOLE + '/docs/data/uhc-year2-cspro-dictionaries.zip">Download (login)</a></div>'
            '<div class="card"><h3>Run the instruments yourself</h3><p>Complete CSPro application '
            'packages — compiled app, Designer source and lookup files. Extract, double-click the '
            '<code>.pff</code>, and it opens with an empty local case file.</p>'
            '<a class="go" href="' + CONSOLE + '/docs/data/">Download (login)</a></div>'
            '</div></section></main>')
    return shell("Instruments — UHC Survey Y2",
                 "The four UHC Survey Year 2 instruments: crosswalks, codebooks, dictionaries and "
                 "CSPro packages.", body, active=P + "/instruments/")


def instrument_page(i):
    k = i["k"]
    dl = []
    if i["ver"]:
        dl.append(('CSPro application package', CONSOLE + '/docs/data/%s-cspro-app.zip' % k,
                   'compiled app + Designer source + lookups — runs locally with an empty case file'))
    dl.append(('Codebook (Excel)', CONSOLE + '/docs/data/', 'every variable, label, question, universe, codes, validation'))
    dl.append(('Codebook (PDF)', CONSOLE + '/docs/data/', 'the same, printable'))
    dl.append(('Case exports', CONSOLE + '/docs/data/', 'CSV, SPSS .sav, Stata .dta and R .rds, refreshed every ~2 min'))
    items = "".join('<li><a href="%s">%s</a> — <span>%s</span></li>' % (u, t, d) for t, u, d in dl)
    cross = ('<div class="card"><h3>Paper ↔ CAPI comparison</h3><p>Side-by-side: every printed '
             'question and how it appears on the device, so reviewers can confirm nothing changed '
             'in translation.</p><a class="go" href="%s/instruments/%s/crosswalk/">Open the crosswalk</a></div>'
             % (P, k)) if i.get("cross") else ""
    pwa = ('<div class="card"><h3>The live survey app</h3><p>F2 is self-administered in the browser '
           '— installable, works offline, submits when a signal appears.</p>'
           '<a class="go" href="%s">Open the app</a></div>' % i["pwa"]) if i.get("pwa") else ""
    ver = ("v%s, deployed %s" % (i["ver"], i["date"])) if i["ver"] else "continuously deployed"
    body = (hero("UHC Survey Y2 · Instrument", "%s — %s" % (k.upper(), i["name"]), i["about"])
            + '<main><section><table class="plain">'
              '<tr><th>Answered by</th><td>%s</td></tr>'
              '<tr><th>Mode</th><td>%s</td></tr>'
              '<tr><th>Current build</th><td>%s</td></tr>'
              '<tr><th>Variables documented</th><td>%d</td></tr></table></section>'
              '<section><h2>Documentation</h2><div class="grid">%s%s</div></section>'
              '<section><h2>Downloads</h2><p class="sub">Data files are behind the survey login.</p>'
              '<ul class="rolelinks">%s</ul></section></main>'
              % (i["who"], i["mode"], ver, i["vars"], cross, pwa, items))
    return shell("%s %s — UHC Survey Y2" % (k.upper(), i["name"]),
                 "%s (%s) — crosswalk, codebook, dictionary and downloads." % (i["name"], k.upper()),
                 body, active=P + "/instruments/")


def monitoring_index():
    body = (hero("UHC Survey Y2", "Monitoring",
                 "Live views of fieldwork — rebuilt from the database every two minutes — "
                 "plus the two consoles that operate it. Everything here requires the survey login.")
            + '<main><section><div class="grid">'
              '<div class="card project"><span class="badge soon">login needed</span>'
              '<h3>Sync Dashboard</h3><p>Cases collected, completed vs partial, visited today, '
              'coverage against the assignment plan (region → province → facility), enumerator '
              'productivity, data-quality alerts, a searchable case list, and every data download.</p>'
              '<a class="go" href="' + CONSOLE + '/docs/dashboard.html">Open the dashboard</a></div>'
              '<div class="card project"><span class="badge soon">login needed</span>'
              '<h3>Map Report</h3><p>Where cases were actually collected: a pin per case coloured by '
              'status, clustering, coverage choropleth by province, and flags for weak GPS fixes or '
              'cases far from their assigned facility.</p>'
              '<a class="go" href="' + CONSOLE + '/docs/map.html">Open the map</a></div>'
              '</div></section>'
              # Carl, 2026-07-27: the two working consoles moved in from the old
              # csweb front door, so Monitoring is the single operational hub.
              '<section><h2>Operate</h2>'
              '<p class="sub">The working consoles behind the views — for administering '
              'collection, not just watching it.</p>'
              '<div class="grid">'
              '<div class="card project"><span class="badge soon">login needed</span>'
              '<h3>F2 Admin Portal</h3><p>Runs the healthcare-worker web survey: facility '
              'links and QR codes, reminder waves, submission review, the coverage report, '
              'and app settings.</p>'
              '<a class="go" href="https://uhc-hcw.asiansocial.org/admin">Open the F2 admin portal</a></div>'
              '<div class="card project"><span class="badge soon">login needed</span>'
              '<h3>CSWeb</h3><p>The CSPro sync server itself — the system of record the '
              'tablets sync into: raw case data per instrument, user accounts and roles, '
              'and the sync report.</p>'
              '<a class="go" href="' + CSWEB + '/csweb/">Open CSWeb</a></div>'

              '</div></section>'
              '<section><h2>How to read them</h2>'
              '<p class="sub">Three things that surprise people the first time.</p>'
              '<ul class="rolelinks">'
              '<li><b>The filter bar drives everything below it</b> — <span>set instrument, region, '
              'supervisor, enumerator, status or visit dates once and the whole page follows. '
              'Coverage-vs-plan deliberately ignores the enumerator filter, because the plan assigns '
              'facilities, not people.</span></li>'
              '<li><b>&ldquo;Today&rdquo; is Manila time</b> — <span>and F2 is self-administered, so it never '
              'counts as missing GPS and is always recorded as completed.</span></li>'
              '<li><b>Counts follow your filters</b> — <span>so they can differ from the raw case count '
              'in CSWeb\'s own Data tab. Both are correct; they answer different questions.</span></li>'
              '</ul></section></main>')
    return shell("Monitoring — UHC Survey Y2",
                 "Live fieldwork monitoring for UHC Survey Year 2: sync dashboard and map report.",
                 body, active=P + "/monitoring/")


def data_index():
    body = (hero("UHC Survey Y2", "Data",
                 "Analysis-ready exports of everything collected so far, rebuilt from the database "
                 "every two minutes and documented variable by variable.")
            + '<main><section><div class="grid">'
              '<div class="card project"><span class="badge soon">login needed</span>'
              '<h3>Data room</h3><p>Wide and roster CSVs per instrument, labelled SPSS '
              '<code>.sav</code>, Stata <code>.dta</code> and R <code>.rds</code> exports, the '
              'codebooks, the CSPro dictionaries and the application packages — with a preview of '
              'each table in the browser.</p>'
              '<a class="go" href="' + CONSOLE + '/docs/data/">Open the data room</a></div>'
              '<div class="card"><h3>Codebook</h3><p>What every variable means: label, the literal '
              'question, universe (who was asked it), value codes, Don\'t-know / Refused codes, and '
              'the validation rules enforced during the interview. Excel and PDF.</p>'
              '<a class="go" href="%s/instruments/">Per instrument</a></div>'
              '</div></section>'
              '<section><h2>Before you analyse</h2><ul class="rolelinks">'
              '<li><b>Values are raw stored codes</b> — <span>1 / 2, not Male / Female. The SPSS and '
              'Stata files carry the labels embedded; the R files ship with a codebook CSV.</span></li>'
              '<li><b>Missing values are coded, not blank</b> — <span>categorical items use 8 / 98 for '
              'Don\'t know and 9 / 99 for Refused; amount fields use −98 and −99 so no real amount is '
              'ever confused with a refusal.</span></li>'
              '<li><b>The questionnaire number is a 12-digit string</b> — <span>keep it as text; Excel '
              'will otherwise render it as 1.02E+11.</span></li>'
              '<li><b>Everything is a snapshot of live fieldwork</b> — <span>counts move as tablets '
              'sync. Each file carries the timestamp it was generated.</span></li>'
              '</ul></section></main>' % P)
    return shell("Data — UHC Survey Y2",
                 "Analysis-ready exports and codebooks for UHC Survey Year 2.", body, active=P + "/data/")


def platform_page():
    body = (hero("ASPSI", "How we build CAPI",
                 "The same system every engagement gets: instrument, field hub, monitoring, and "
                 "documented, analysis-ready data.")
            + '<main><section><h2>The pipeline</h2>'
              '<p class="sub">Paper questionnaire in, documented data set out.</p>'
              '<table class="plain">'
              '<tr><th>Stage</th><th>What happens</th></tr>'
              '<tr><td>Instrument</td><td>The approved paper questionnaire becomes a tablet '
              'application — skip logic, range and consistency checks, and multi-language question '
              'text — generated from scripts, so a change is re-generated rather than hand-edited.</td></tr>'
              '<tr><td>Field</td><td>Enumerators work offline on CSEntry; supervisors assign and '
              'collect cases, over Bluetooth where there is no signal, and relay them to the server.</td></tr>'
              '<tr><td>Sync</td><td>A central CSWeb hub receives cases, keeps every revision, and '
              'breaks them out into relational tables for reporting.</td></tr>'
              '<tr><td>Monitor</td><td>Dashboards and maps rebuild every two minutes: coverage against '
              'plan, productivity, and data-quality alerts while the team is still in the field.</td></tr>'
              '<tr><td>Deliver</td><td>Exports in CSV, SPSS, Stata and R with labels embedded, plus a '
              'codebook documented to the DDI standard used by the PSA Data Archive.</td></tr>'
              '</table></section>'
              '<section><h2>Standards we work to</h2><div class="grid">'
              '<div class="card"><h3>Documentation</h3><p>DDI-Codebook 2.5 elements for every '
              'variable — label, question, universe, categories, missing codes — so a data set can be '
              'deposited in a national archive without being re-documented.</p></div>'
              '<div class="card"><h3>Data quality</h3><p>Validation at the point of entry, not at '
              'encoding: hard blocks for impossible values, soft warnings for implausible ones, and '
              'GPS plus verification photos to confirm the visit happened.</p></div>'
              '<div class="card"><h3>Reproducibility</h3><p>Instruments, exports and documentation are '
              'generated by scripts under version control. Any build can be regenerated exactly, and '
              'every deployed version is stamped on the device.</p></div>'
              '</div></section></main>')
    return shell("What we build — ASPSI CAPI",
                 "How ASPSI builds and operates CAPI systems: pipeline, standards and outputs.",
                 body, active="/platform/")


def about_page():
    body = (hero("ASPSI", "About this platform",
                 "capi.asiansocial.org is the working home of ASPSI's computer-assisted personal "
                 "interviewing projects — one place for the guides, the instruments, the live "
                 "monitoring and the data.")
            + '<main><section><h2>Who runs it</h2>'
              '<p class="sub">Asian Social Project Services, Inc. (ASPSI) is a Philippine social-research '
              'organisation. This platform hosts the survey systems ASPSI builds and operates for its '
              'partners; the UHC Survey Year 2 is conducted for the Department of Health.</p></section>'
              '<section><h2>What is public, what is not</h2>'
              '<p class="sub">Guides, instrument documentation and this description are open — field '
              'staff and respondents need them without a password. Live monitoring and the data room '
              'hold survey responses and are behind a login held by the survey team. No respondent '
              'name or address is published anywhere on this site.</p></section>'
              '<section><h2>Contact</h2><p class="sub">For access, corrections or questions about a '
              'survey, contact the ASPSI survey team through '
              '<a href="https://asiansocial.org">asiansocial.org</a>.</p></section></main>')
    return shell("About — ASPSI CAPI", "About the ASPSI CAPI platform and its access model.",
                 body, active="/about/")


def projects_index():
    body = (hero("Portfolio", "Projects",
                 "CAPI engagements operated on this platform.")
            + '<main><section><div class="grid">'
              '<div class="card project"><span class="badge live">Active</span>'
              '<h3>UHC Survey Year 2</h3><p>Universal Health Care study for the Department of Health '
              '— four instruments covering facilities, health care workers, patients and households. '
              'Fieldwork in progress.</p><a class="go" href="%s/">Open project</a></div>'
              '<div class="card future"><h3>Your project here</h3><p>The platform hosts multiple '
              'engagements side by side — each with its own instruments, guides, monitoring and data, '
              'kept separate from the others.</p></div>'
              '</div></section></main>' % P)
    return shell("Projects — ASPSI CAPI", "CAPI projects operated by ASPSI.", body, active="/projects/")


def redirect_stub(to, label):
    return ("""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="robots" content="noindex"><meta http-equiv="refresh" content="0; url=%s">
<link rel="canonical" href="%s"><title>Moved — %s</title></head>
<body style="font:16px/1.6 'Segoe UI',system-ui,sans-serif;padding:48px;max-width:640px;margin:0 auto">
<p>%s has moved to <a href="%s">%s</a>.</p></body></html>""" % (to, to, label, label, to, to))


# ------------------------------------------------------------------ ported pages
def port(name, out_rel):
    """Re-home a csweb content page: inject the portal bar, rewrite internal links."""
    src = os.path.join(CSWEB_SRC, name)
    s = open(src, encoding="utf-8").read()
    for old, new in LINKMAP:
        s = s.replace('href="%s"' % old, 'href="%s"' % new)
    # bare-text URL mentions (link labels showing the address) follow the console move too
    s = s.replace("csweb.asiansocial.org/docs/", "capi.asiansocial.org/docs/")
    s = s.replace("Back to help", "Back to project home")
    i = s.lower().find("<body")
    j = s.find(">", i)
    s = s[:j + 1] + "\n" + PORTAL_BAR + s[j + 1:]
    write(out_rel, s)


def write(rel, content):
    p = os.path.join(BUILD, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


EXTRA_CSS = """
/* ---- role welcome mat (project home) ---- */
.rolerow { background: var(--card); border: 1px solid var(--line); border-left: 5px solid var(--verde);
  border-radius: 10px; padding: 18px 22px; margin-bottom: 14px; }
.roletitle { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.roletitle h3 { font-size: 1.12rem; color: var(--verde-dark); }
.rolesub { color: var(--ink-soft); font-size: 0.93rem; margin: 2px 0 10px; }
ul.rolelinks { list-style: none; display: flex; flex-direction: column; gap: 7px; }
ul.rolelinks li { font-size: 0.95rem; padding-left: 16px; position: relative; }
ul.rolelinks li::before { content: "→"; position: absolute; left: 0; color: var(--verde); }
ul.rolelinks a { font-weight: 600; text-decoration: none; }
ul.rolelinks a:hover { text-decoration: underline; }
ul.rolelinks span { color: var(--ink-soft); }
.nav a.link.on { color: #fff; font-weight: 700; border-bottom: 2px solid #e5b23b; }
table.plain th[scope], table.plain tr > th:first-child:not(:only-child) { white-space: nowrap; }
code { background: var(--verde-pale); padding: 1px 5px; border-radius: 4px; font-size: 0.92em; }
"""


# ---------------------------------------------------------------------------
# OFFICIAL FIELD MANUALS (Carl, 2026-07-27: "upload the Manuals sent by Ma'am
# Silva. This is the official one.") — the enumerator + supervisor field
# manuals authored by the ASPSI/UP study team (Dr. Ma. Esmeralda Silva-Javier),
# v1.1 (24 Jul 2026). Published as viewable PDF + editable Word under /manual/.
# The prior CAPI system manual is archived at /archive/capi-manual-2026-07/ and
# a finalized CAPI manual is anticipated later, per the ASPSI RAs.
# ---------------------------------------------------------------------------
MANUAL_FILES = P + "/manual/files"
_OFFICIAL_MANUALS = [
    ("Field Enumerator's Manual",
     "For enumerators running F1/F3/F4 in the field: pre-fieldwork preparation, respondent "
     "selection and listing, conducting the interview on the tablet, handling ineligibles and "
     "refusals, and end-of-day procedures.",
     "UHC-Y2-Field-Enumerators-Manual-v1.1-2026-07-24", "41 pp", "1.0 MB", "526 KB"),
    ("Field Supervisor's Manual",
     "For field supervisors and team leaders: team management, assignment and quota tracking, "
     "daily quality-control checks, replacement approval, and the supervisory workflow.",
     "UHC-Y2-Field-Supervisors-Manual-v1.1-2026-07-24", "50 pp", "1.6 MB", "917 KB"),
]

# Status of the official manuals (Carl, 2026-07-28: "The two Manual are ASPSI
# approved even if not yet final"). Approved for use, but v1.1 is not the last word.
_APPROVED_BANNER = (
    '<div style="background:#eefaf3;border:1px solid #b9e2cb;border-left:5px solid #046a38;'
    'border-radius:8px;padding:12px 16px;margin:0 0 18px;color:#14532d;font-size:.95rem">'
    '<b>ASPSI-approved &mdash; not yet final.</b> Version 1.1 is approved by ASPSI for training '
    'and field use, and is the reference to work from today. It is not the final version; a '
    'later revision is expected and will be published here, keeping these same links.</div>')

# Precedence, shown on every software guide. The guides and the manuals answer different
# questions; without this a reader has two plausible authorities and no tie-breaker.
_GUIDE_BANNER = (
    '<div style="background:#f4f8fb;border:1px solid #d5e2ec;border-left:5px solid #2c6b91;'
    'border-radius:8px;padding:12px 16px;margin:0 0 18px;color:#1e3a4c;font-size:.95rem">'
    '<b>How to operate the software.</b> This guide covers the tablet and the applications. '
    'For field procedure &mdash; respondent selection, eligibility, refusals, replacements and '
    'quality control &mdash; the ASPSI <a href="' + P + '/manual/">field manuals</a> are the '
    'approved reference and take precedence.</div>')

_ARCHIVE_BANNER = (
    '<div style="background:#fff8e1;border:1px solid #e5b23b;border-left:5px solid #e5b23b;'
    'border-radius:8px;padding:12px 16px;margin:0 0 18px;color:#5a4a1a;font-size:.95rem">'
    '<b>Archived &mdash; superseded.</b> This is the CAPI system reference manual as of July 2026. '
    'The official field manuals now live on the <a href="' + P + '/manual/">Manual page</a>; '
    'a finalized CAPI manual is in preparation with the ASPSI research assistants.</div>')


def official_manual_index():
    cards = "".join(
        '<div class="card"><h3>%s</h3><p>%s</p>'
        '<a class="go" href="%s/%s.pdf" target="_blank" rel="noopener">View PDF (%s, %s)</a><br>'
        '<a class="go" href="%s/%s.docx" download>Download Word (%s)</a></div>'
        % (title, desc, MANUAL_FILES, base, pp, pdfsz, MANUAL_FILES, base, docxsz)
        for title, desc, base, pp, pdfsz, docxsz in _OFFICIAL_MANUALS)
    body = (hero("UHC Survey Y2", "Field Manuals",
                 "The official field manuals for the UHC Survey Year 2, prepared by the ASPSI / "
                 "UP study team — the reference for training design and field practice.")
            + '<main><section>'
            + _APPROVED_BANNER
            + '<p class="sub">Version 1.1 (24 July 2026), authored by the study component lead, '
              'Dr. Ma. Esmeralda Silva-Javier. View the PDF on any device, or download the Word '
              'file. These supersede the earlier CAPI system manual, now in the '
              '<a href="' + P + '/archive/capi-manual-2026-07/">archive</a>.</p>'
            + '<div class="grid">' + cards + '</div>'
            + '</section></main>')
    return shell("Field Manuals — UHC Survey Y2",
                 "Official UHC Survey Year 2 field manuals — enumerator and supervisor.",
                 body, active=P + "/manual/")


def main():
    ap = argparse.ArgumentParser(description="Build the capi.asiansocial.org portal.")
    ap.add_argument("--deploy", action="store_true", help="rsync build/ to the capi-www docroot")
    ap.add_argument("--check", action="store_true",
                    help="assert the shared chrome is in use, then exit")
    a = ap.parse_args()
    if a.check:
        # The regression this guards against is the one that produced five
        # chromes in the first place: someone pasting the nav back in "just for
        # one page". ops/verify-chrome.sh runs the same grep from the outside.
        import inspect
        src = inspect.getsource(sys.modules[__name__])
        bad = [n for n in ("\n_NAV = [", "\ndef _sidebar(", "\n_PILL_LOCK") if n in src]
        if bad:
            print("FAIL: build_portal.py has regrown its own chrome: %s" % ", ".join(bad))
            sys.exit(1)
        print("ok: chrome comes from portal_shell (%s)" % PS.__file__)
        sys.exit(0)
    if os.path.isdir(BUILD):
        shutil.rmtree(BUILD)
    os.makedirs(BUILD)

    # capi-www serves /portal.css. It must be the SAME file the on-box
    # generators inline, or the two halves of the site drift — which is exactly
    # what happened between 2026-07-28 and 2026-08-09 (the portal copy missed
    # the mobile topbar fix). The canonical sheet lives beside portal_shell.py.
    shutil.copyfile(os.path.join(os.path.dirname(PS.__file__), "portal.css"),
                    os.path.join(BUILD, "portal.css"))

    # assets the ported pages depend on — copied so the portal is self-contained
    # (docs.css / crosswalk.css + the 113 crosswalk screenshots). Paths are kept
    # identical to the old site, so no <img src> rewriting is needed.
    shutil.copytree(os.path.join(SRC, "assets"), os.path.join(BUILD, "assets"))
    shutil.copytree(os.path.join(SRC, "img"), os.path.join(BUILD, "docs", "img"))
    # paper questionnaires (20 Apr 2026 submission) published under the project
    _q = os.path.join(SRC, "questionnaires")
    if os.path.isdir(_q):
        shutil.copytree(_q, os.path.join(BUILD, "projects", "uhc-y2", "questionnaires"))

    # authored pages
    write("index.html", home_page(open(os.path.join(SRC, "index.html"), encoding="utf-8").read()))
    write("about/index.html", about_page())
    write("platform/index.html", platform_page())
    write("projects/index.html", projects_index())
    write("projects/uhc-y2/index.html", project_home())
    write("projects/uhc-y2/guides/index.html", guides_index())
    write("projects/uhc-y2/instruments/index.html", instruments_index())
    for i in INSTRUMENTS:
        write("projects/uhc-y2/instruments/%s/index.html" % i["k"], instrument_page(i))
    write("projects/uhc-y2/monitoring/index.html", monitoring_index())
    # tabulations/index.html is OWNED by csweb-tabulations-gen.py since 2026-07-28
    # (hourly cron bakes fresh preview counts; a static build here would go stale
    # and clobber it). tabulations_index() kept for reference only.
    # write("projects/uhc-y2/tabulations/index.html", tabulations_index())
    write("projects/uhc-y2/data/index.html", data_index())

    # ported content pages
    port("enumerator-guide.html", "projects/uhc-y2/guides/enumerator/index.html")
    port("hub-guide.html", "projects/uhc-y2/guides/supervisor/index.html")
    port("hcw-guide.html", "projects/uhc-y2/guides/healthcare-worker/index.html")
    # The prior CAPI system manual is archived; the official ASPSI field manuals
    # (Ma. Esmeralda Silva-Javier, v1.1 2026-07-24) now occupy /manual/.
    port("capi-manual.html", "projects/uhc-y2/archive/capi-manual-2026-07/index.html")
    port("pretest-guide.html", "projects/uhc-y2/archive/pretest-2026-07-15/index.html")
    write("projects/uhc-y2/manual/index.html", official_manual_index())
    shutil.copytree(os.path.join(SRC, "manuals"),
                    os.path.join(BUILD, "projects", "uhc-y2", "manual", "files"))
    for i in INSTRUMENTS:
        port("%s-crosswalk.html" % i["k"],
             "projects/uhc-y2/instruments/%s/crosswalk/index.html" % i["k"])

    # legacy in-portal paths from the July skeleton
    write("uhc/index.html", redirect_stub(P + "/", "UHC Survey 2026"))
    write("docs/index.html", redirect_stub(P + "/guides/", "Documentation"))

    write("robots.txt", "User-agent: *\nDisallow: /\n")
    write("404.html", shell("Page not found — ASPSI CAPI", "Not found",
                            hero("404", "That page isn't here",
                                 "It may have moved when the site was reorganised.")
                            + '<main><section><ul class="rolelinks">'
                              '<li><a href="/">Portal home</a></li>'
                              '<li><a href="%s/">UHC Survey Y2 project home</a></li>'
                              '<li><a href="%s/guides/">Guides</a></li>'
                              '</ul></section></main>' % (P, P)))

    n = sum(len(f) for _, _, f in os.walk(BUILD))
    print("built %d files -> %s" % (n, BUILD))
    for root, _, files in sorted(os.walk(BUILD)):
        for f in sorted(files):
            p = os.path.join(root, f)
            print("  %-58s %5dKB" % (os.path.relpath(p, BUILD).replace("\\", "/"),
                                     os.path.getsize(p) // 1024))
    if a.deploy:
        cmd = ["scp", "-q", "-i", KEY, "-r"] + \
              [os.path.join(BUILD, x) for x in os.listdir(BUILD)] + \
              ["%s:%s" % (DEPLOY_HOST, DEPLOY_PATH)]
        subprocess.run(cmd, check=True)
        print("deployed -> %s%s" % (DEPLOY_HOST, DEPLOY_PATH))


# ============================================================================
# ADMIN-PORTAL PRESENTATION (Carl, 2026-07-22: "make it an admin portal like,
# modern, and built like a SaaS"). Overrides the earlier document-site shell:
# a persistent sidebar, sticky topbar with breadcrumbs + status pills, and stat
# tiles. Defined after the originals so these win at call time.
# ============================================================================


# The chrome — sidebar, topbar, head, pills — comes from portal_shell, the
# same module the on-box generators import. These aliases exist because the
# ported-page injection (port(), below) and the home page reference the old
# private names; they are the shared functions, not copies.
_sidebar = PS.sidebar
_crumbs_html = PS.crumbs_html
_PILL_LIVE = PS.PILL_LIVE


# Crumb trails for the authored pages. The shell itself comes from portal_shell.
# The monitoring/ and data/ keys die with their signpost pages in unification
# Slices 3 and 4 — the live generators own those URLs from then on.
_CRUMBS = {
    "/": [("Console", None)],
    "/projects/": [("Projects", None)],
    "/platform/": [("Platform", None), ("What we build", None)],
    "/about/": [("Platform", None), ("About", None)],
    P + "/": [("Projects", "/projects/"), ("UHC Survey Year 2", None)],
    P + "/guides/": [("UHC Survey Year 2", P + "/"), ("Guides", None)],
    P + "/manual/": [("UHC Survey Year 2", P + "/"), ("Manual", None)],
    P + "/instruments/": [("UHC Survey Year 2", P + "/"), ("Instruments", None)],
    P + "/monitoring/": [("UHC Survey Year 2", P + "/"), ("Monitoring", None)],
    P + "/data/": [("UHC Survey Year 2", P + "/"), ("Data &amp; exports", None)],
    P + "/tabulations/": [("UHC Survey Year 2", P + "/"), ("Tabulations", None)],
}


def tiles(items):
    return '<div class="tiles">%s</div>' % "".join(
        '<div class="tile"><div class="k">%s</div><div class="v">%s</div><div class="s">%s</div></div>'
        % t for t in items)


def shell(title, desc, body, crumb="", active=""):
    """App shell. Markup and CSS both come from portal_shell; this function is
    now only a crumb lookup and a css-mode choice.

    css="link" because these pages are static files served by capi-www and a
    shared stylesheet is cached once for the whole site. The on-box generators
    keep css="inline" — see portal_shell.head(). The pill is always PILL_LIVE:
    the lock pill it used to show on two pages was a lie by omission once the
    whole portal became sign-in-gated (2026-07-28)."""
    return (PS.open_shell(title, desc,
                          active=active,
                          crumbs=_CRUMBS.get(active) or [("ASPSI CAPI", None)],
                          tb_right=PS.PILL_LIVE,
                          css="link")
            + body
            + PS.close_shell())


_TOTAL_VARS = sum(i["vars"] for i in INSTRUMENTS)


def _home_act_chip():
    """Current-activity line on the home project card, baked from the live feed."""
    import datetime as _dt
    st = _ov_fetch_status()
    for a in (st or {}).get("activities") or []:
        if a.get("start") and not a.get("planned"):
            today = _dt.date.today().isoformat()
            if not a.get("end") or a["end"] >= today:
                d = (_dt.date.today() - _dt.date.fromisoformat(a["start"])).days + 1
                return ('<div class="home-actchip"><span class="dot"></span>%s &middot; '
                        'day %d &middot; %s cases</div>'
                        % (a.get("label") or a["id"], d, "{:,}".format(a.get("cases") or 0)))
    return ""


def home_page(skeleton_home):
    """Console home — platform overview + project cards, in the admin shell."""
    body = (hero("Console", "ASPSI CAPI",
                 "Survey data systems for evidence that decision-makers can trust. ASPSI designs "
                 "and operates computer-assisted personal interviewing systems for large-scale "
                 "social research — from questionnaire to clean, monitored, analysis-ready data.")
            + tiles([("Active projects", "1", "UHC Survey Year 2 &middot; DOH"),
                     ("Instruments in field", "4", "three on tablets, one on the web"),
                     ("Variables documented", "{:,}".format(_TOTAL_VARS), "to the DDI / PSADA convention"),
                     ("Monitoring refresh", "~2 min", "rebuilt from the live database")])
            + '<div class="sec"><div class="sec-head"><h2>Projects</h2>'
              '<a class="more" href="/projects/">All projects &rarr;</a></div>'
              '<div class="grid">'
              '<div class="card"><span class="tag live">Active</span><h3>UHC Survey Year 2</h3>'
              + _home_act_chip() +
              '<p>Universal Health Care study for the Department of Health — facilities, health care '
              'workers, patients and households. Fieldwork in progress; monitoring and analysis-ready '
              'data are live.</p><a class="go" href="%s/">Open project</a></div>'
              '<div class="card ghost"><h3>Your project here</h3><p>The platform hosts multiple '
              'engagements side by side — each with its own instruments, guides, monitoring and data, '
              'kept separate from the others.</p></div></div></div>' % P
            + '<div class="sec"><h2>What we build</h2><p class="sub">Every engagement covers the full '
              'field-data lifecycle, delivered as an integrated system rather than loose tools.</p>'
              '<div class="grid">'
              '<div class="card"><h3>CAPI instruments</h3><p>Paper questionnaires become tablet '
              'applications with skip logic, validation and multi-language question text — errors are '
              'caught at the doorstep, not at encoding.</p></div>'
              '<div class="card"><h3>Field data hub</h3><p>A secure central server receives data synced '
              'from the field. Supervisors assign workloads, track completion and relay cases even from '
              'areas with no connectivity.</p></div>'
              '<div class="card"><h3>Monitoring &amp; dashboards</h3><p>Live dashboards and maps show '
              'sync status, coverage and data quality per area and per team — problems surface in hours, '
              'not after fieldwork ends.</p></div>'
              '<div class="card"><h3>Documented data</h3><p>Exports in CSV, SPSS, Stata and R with '
              'labels embedded, plus a codebook documented to the DDI standard the PSA Data Archive '
              'uses.</p><a class="go" href="/platform/">How we build it</a></div>'
              '</div></div>')
    return shell("ASPSI CAPI — console", "ASPSI CAPI platform console.", body, active="/")


_project_home_doc = project_home


def project_home():
    """Project console: the documented page plus a stat strip under the hero."""
    s = _project_home_doc()
    strip = tiles([("Instruments", "4", "F1 &middot; F3 &middot; F4 on tablets, F2 on the web"),
                   ("Variables documented", "{:,}".format(_TOTAL_VARS), "labels, universes, codes, validation"),
                   ("Export formats", "5", "CSV &middot; SPSS &middot; Stata &middot; R &middot; CSPro"),
                   ("Monitoring refresh", "~2 min", "rebuilt from the live database")])
    return s.replace('<main>', '<main>' + strip, 1)


_SHELL_CSS = """
<link rel="stylesheet" href="/portal.css">
<style>
  body { margin: 0 !important; background: var(--paper) !important; }
  .pshell { display: flex; min-height: 100vh; align-items: flex-start; }
  .pshell > .doc { flex: 1; min-width: 0; background: #fff; }
  .pshell .doc-bar { position: sticky; top: 0; z-index: 30; display: flex; align-items: center;
    gap: 10px; height: 52px; padding: 0 24px; background: rgba(255,255,255,.92);
    backdrop-filter: saturate(1.4) blur(10px); border-bottom: 1px solid var(--line);
    font-family: var(--sans); font-size: 13px; color: var(--ink-3); }
  .pshell .doc-bar a { color: var(--ink-3); text-decoration: none; }
  .pshell .doc-bar a:hover { color: var(--verde); }
  .pshell .doc-bar .cur { color: var(--ink); font-weight: 600; }
  .pshell .doc-bar .sep { opacity: .45; }
  @media (max-width: 900px) { .pshell { display: block; } }
</style>
"""

_PORT_META = {
    "enumerator-guide.html": ([("UHC Survey Year 2", P + "/"), ("Guides", P + "/guides/"),
                               ("Enumerator guide", None)], P + "/guides/"),
    "hub-guide.html": ([("UHC Survey Year 2", P + "/"), ("Guides", P + "/guides/"),
                        ("Supervisor hub", None)], P + "/guides/"),
    "hcw-guide.html": ([("UHC Survey Year 2", P + "/"), ("Guides", P + "/guides/"),
                        ("Health care worker", None)], P + "/guides/"),
    "capi-manual.html": ([("UHC Survey Year 2", P + "/"), ("Archive", None),
                          ("CAPI system manual", None)], P + "/archive/capi-manual-2026-07/"),
    "pretest-guide.html": ([("UHC Survey Year 2", P + "/"), ("Archive", None),
                            ("Pretest &middot; 15 Jul 2026", None)],
                           P + "/archive/pretest-2026-07-15/"),
}
for _i in INSTRUMENTS:
    _PORT_META["%s-crosswalk.html" % _i["k"]] = (
        [("UHC Survey Year 2", P + "/"), ("Instruments", P + "/instruments/"),
         (_i["k"].upper(), "%s/instruments/%s/" % (P, _i["k"])), ("Crosswalk", None)],
        P + "/instruments/")


def port(name, out_rel):
    """Wrap a ported csweb page in the same app shell; rewrite internal links."""
    s = open(os.path.join(CSWEB_SRC, name), encoding="utf-8").read()
    for old, new in LINKMAP:
        s = s.replace('href="%s"' % old, 'href="%s"' % new)
    # bare-text URL mentions (link labels showing the address) follow the console move too
    s = s.replace("csweb.asiansocial.org/docs/", "capi.asiansocial.org/docs/")
    s = s.replace("Back to help", "Back to project home")
    crumbs, active = _PORT_META.get(name, ([("UHC Survey Year 2", P + "/")], P + "/"))
    h = s.lower().find("</head>")
    s = s[:h] + _SHELL_CSS + s[h:]
    b = s.lower().find("<body")
    bo = s.find(">", b) + 1
    be = s.lower().rfind("</body>")
    bar = ('<div class="doc-bar">%s<span style="margin-left:auto">'
           '<a href="%s/">&larr; Project home</a></span></div>' % (_crumbs_html(crumbs), P))
    if name == "capi-manual.html":
        banner = _ARCHIVE_BANNER
    elif name in ("enumerator-guide.html", "hub-guide.html", "hcw-guide.html"):
        banner = _GUIDE_BANNER
    else:
        banner = ""
    s = (s[:bo] + '<div class="pshell">' + _sidebar(active) + '<div class="doc">' + bar + banner
         + s[bo:be] + '</div></div>' + s[be:])
    write(out_rel, s)




# ---------------------------------------------------------------------------
# PAPER QUESTIONNAIRES (Carl, 2026-07-22: "include the paper-questionnaire of
# all instruments, downloadable with the latest version").
# Source: raw/Project-Deliverable-1_Apr20-submitted/ — the 20 April 2026
# submission to DOH, which is the baseline the CAPI applications were built
# from (the April 8 set is superseded; later files are Filipino translations).
# ---------------------------------------------------------------------------
Q_DIR = "/projects/uhc-y2/questionnaires"
Q_VERSION = "20 April 2026 submission"
Q_FILES = {
    "f1": ("UHC-Y2-F1-Facility-Head-Questionnaire-2026-04-20.pdf", "1.1 MB"),
    "f2": ("UHC-Y2-F2-Healthcare-Worker-Questionnaire-2026-04-20.pdf", "839 KB"),
    "f3": ("UHC-Y2-F3-Patient-Questionnaire-2026-04-20.pdf", "1.2 MB"),
    "f4": ("UHC-Y2-F4-Household-Questionnaire-2026-04-20.pdf", "1.0 MB"),
}
# F3b Patient Listing Protocol deliberately NOT published — not implemented yet
# in the CAPI build (Carl, 2026-07-22). Re-add here when it ships.
Q_EXTRA = {}
Q_ZIP = "UHC-Y2-Paper-Questionnaires-2026-04-20.zip"


def _q_card(k):
    fn, size = Q_FILES[k]
    extra = ""
    if k in Q_EXTRA:
        efn, elabel, esize = Q_EXTRA[k]
        extra = ('<br><a class="go" href="%s/%s" download>%s (PDF, %s)</a>'
                 % (Q_DIR, efn, elabel, esize))
    return ('<div class="card"><span class="tag arch">Paper</span>'
            '<h3>Paper questionnaire</h3>'
            '<p>The printed instrument this CAPI application was built from — '
            '<b>%s</b>, the version submitted to DOH. Use it to read question wording '
            'exactly as approved, or to work on paper when a device is unavailable.</p>'
            '<a class="go" href="%s/%s" download>Download PDF (%s)</a>%s</div>'
            % (Q_VERSION, Q_DIR, fn, size, extra))


_instrument_page_prev = instrument_page


def instrument_page(i):
    """Instrument page + its paper questionnaire as the first download card."""
    s = _instrument_page_prev(i)
    card = _q_card(i["k"])
    return s.replace('<div class="grid">', '<div class="grid">' + card, 1)


_instruments_index_prev = instruments_index


def instruments_index():
    """Instruments index: paper questionnaires alongside the digital artefacts."""
    s = _instruments_index_prev()
    rows = "".join(
        '<tr><td><b>%s</b></td><td>%s</td>'
        '<td><a href="%s/%s" download>PDF, %s</a></td></tr>'
        % (k.upper(),
           dict((x["k"], x["name"]) for x in INSTRUMENTS)[k],
           Q_DIR, Q_FILES[k][0], Q_FILES[k][1])
        for k in ("f1", "f3", "f4", "f2"))
    block = ('<section><div class="sec-head"><h2>Paper questionnaires</h2>'
             '<a class="more" href="%s/%s" download>Download all (ZIP, 3.3 MB) &rarr;</a></div>'
             '<p class="sub">The printed instruments the CAPI applications were built from — '
             '<b>%s</b>, the version submitted to DOH. English; the Filipino translations are '
             'maintained separately.</p>'
             '<div class="tbl-wrap"><table class="tbl">'
             '<thead><tr><th>Form</th><th>Instrument</th><th>Questionnaire</th></tr></thead>'
             '<tbody>%s</tbody></table></div></section>'
             % (Q_DIR, Q_ZIP, Q_VERSION, rows))
    # place it directly after the instrument table, before the shared-docs section
    anchor = '<section><h2>Documentation that applies to all four</h2>'
    assert anchor in s, "instruments-index anchor moved"
    return s.replace(anchor, block + anchor, 1)


# ============================================================================
# LIVE PROJECT OVERVIEW (Carl, 2026-07-25: "audit the overview... SaaS CAPI").
# The project home is now a console surface: a status band, live KPIs,
# per-instrument progress, a cases-per-day chart and an attention panel --
# hydrated same-origin from /projects/uhc-y2/status.json, which
# csweb-overview-status-gen.py publishes into this docroot every 2 minutes
# (AGGREGATES ONLY -- counts, ages, percentages; the named detail stays behind
# the csweb sign-in). Values are also baked at build time from the same URL so
# the page is meaningful with JavaScript off; ages bake as em-dashes because a
# baked age is a lie by the time anyone reads it.
# ============================================================================

OV_STATUS_URL = "https://capi.asiansocial.org/projects/uhc-y2/status.json"
OV_DASH = CONSOLE + "/docs/dashboard.html"
OV_MAP = CONSOLE + "/docs/map.html"
OV_F2_APP = "https://uhc-hcw.asiansocial.org"


def _ov_fetch_status():
    """Build-time bake of the live figures; None (em-dash page) if unreachable."""
    import urllib.request, json, time as _t
    # The whole portal is sign-in-gated (2026-07-28), so an anonymous HTTP fetch
    # now gets the login redirect. Prefer a fresh local copy (scp status.json to
    # src/ before building); the HTTP path remains as a fallback.
    local = os.path.join(SRC, "status.json")
    if os.path.exists(local):
        try:
            st = json.load(open(local, encoding="utf-8"))
            if isinstance(st, dict) and {"total", "completed", "alerts",
                                         "instruments", "daily"} <= set(st):
                return st
        except Exception as e:
            print("NOTE: local status.json unreadable (%s), trying HTTP" % str(e)[:60])
    try:
        with urllib.request.urlopen(OV_STATUS_URL + "?_=%d" % _t.time(), timeout=8) as r:
            st = json.loads(r.read().decode("utf-8"))
        # shape gate: a probe file, an error page or a partial write must not
        # crash the build -- anything without the core keys bakes as placeholders
        if not isinstance(st, dict) or not {"total", "completed", "alerts",
                                            "instruments", "daily"} <= set(st):
            raise ValueError("status.json lacks expected keys")
        return st
    except Exception as e:
        print("NOTE: no live status for bake (%s) -- building with placeholders" % str(e)[:80])
        return None


def _ov_pbar(collected, target, provisional):
    if target is None:
        return '<span class="ov-open">open &mdash; no fixed target</span>'
    pct = collected / target * 100 if target else 0.0
    cls = "full" if pct >= 100 else ("low" if pct < 40 else "")
    badge = '<span class="ov-prov">provisional</span>' if provisional else ""
    return ('<span class="ov-pbar"><span class="%s" style="width:%.1f%%"></span></span>'
            '<span class="ov-pct">%s%%</span>%s'
            % (cls, min(pct, 100), ("%.0f" % pct) if pct >= 1 else "%.1f" % pct, badge))


def _ov_spark(daily):
    if not daily:
        return '<span class="ov-open">waiting for live data&hellip;</span>'
    mx = max((d["n"] for d in daily), default=0) or 1
    cols = []
    for i, d in enumerate(daily):
        n = d["n"]
        cls = " now" if i == len(daily) - 1 else (" zero" if n == 0 else "")
        cols.append('<div class="col%s" title="%s"><span class="vl">%s</span>'
                    '<div class="bar" style="height:%.0fpx"></div>'
                    '<span class="dl">%s</span></div>'
                    % (cls, d["date"], n if n else "", max(3, n / mx * 64), d["date"][8:]))
    return "".join(cols)


_OV_INST_ORDER = ("f1", "f3", "f4", "f2")

# Hydration: textContent/classList only -- no innerHTML with fetched values.
_OV_JS = r"""
(function(){
'use strict';
var URL='/projects/uhc-y2/status.json';
function $(id){return document.getElementById(id);}
function age(iso){if(!iso)return null;var ms=Date.now()-Date.parse(iso);
 if(!isFinite(ms)||ms<0)return null;var m=Math.floor(ms/6e4),h=Math.floor(m/60),d=Math.floor(h/24);
 return d>0?d+'d '+(h%24)+'h':h>0?h+'h '+(m%60)+'m':m+'m';}
function chip(el,st){el.classList.toggle('ov-ok',st==='ok');el.classList.toggle('ov-warn',st==='warn');}
function num(n){return (n==null)?'—':Number(n).toLocaleString('en-US');}
var scope=null,lastSt=null;
function dataSlice(st){
 if(scope){var a=(st.activities||[]).filter(function(x){return x.id===scope;})[0];
  if(a&&a.slice){return{total:a.slice.total,completed:a.slice.completed,
   partial:a.slice.partial,today:a.slice.today,daily:a.slice.daily||[],
   undated:a.slice.undated||0,by_inst:a.by_inst||{},label:a.label||a.id};}
  scope=null;}
 return{total:st.total,completed:st.completed,partial:st.partial,today:st.today,
  daily:st.daily||[],undated:st.undated||0,by_inst:null,label:null};}
function apply(st){
 lastSt=st;var ds=dataSlice(st);
 var al=st.alerts||{},tAge=age(st.tablet_last_sync),quiet=false;
 if(st.tablet_last_sync){quiet=(Date.now()-Date.parse(st.tablet_last_sync))>864e5;}
 var f2n=(st.today_by_inst||{}).f2,f2Active=f2n>0||(st.f2_last_date&&st.f2_last_date===st.today_date);
 var drift=(Date.now()-Date.parse(st.generated||''))/6e4;
 if(!isFinite(drift)||drift<0)drift=0;
 var ageMin=(st.dash_age_min||0)+drift,stale=st.dash_ok===false||ageMin>10;
 $('ovChipTabV').textContent=tAge?tAge+' ago':'—';
 chip($('ovChipTab'),tAge?(quiet?'warn':'ok'):'none');
 $('ovChipF2V').textContent=(f2n>0)?f2n+' today':(st.f2_last_date?'last '+st.f2_last_date:'—');
 chip($('ovChipF2'),f2Active?'ok':(st.f2_last_date?'warn':'none'));
 $('ovChipAlV').textContent=(al.total==null)?'—':al.total;
 chip($('ovChipAl'),al.total==null?'none':(al.total===0?'ok':'warn'));
 $('ovKTotal').textContent=num(ds.total);
 var ts=$('ovKTodayS');ts.textContent='';var b=document.createElement('b');
 b.textContent='+'+num(ds.today);ts.appendChild(b);
 ts.appendChild(document.createTextNode(scope?' today · '+ds.label:' today · all instruments'));
 $('ovKComp').textContent=num(ds.completed);
 $('ovKCompS').textContent=(ds.total?Math.round(ds.completed/ds.total*100)+'%':'—')+
   ' of collected · '+num(ds.partial)+' partial';
 $('ovKSync').textContent=tAge||'—';
 $('ovKSyncS').textContent=quiet?(f2Active?'web form still submitting':'web form quiet too'):'tablets F1 / F3 / F4';
 $('ovKSyncBox').classList.toggle('ov-attn',quiet);
 $('ovKAl').textContent=(al.total==null)?'—':al.total;
 $('ovKAlS').textContent=(al.offplan||0)+' off‑plan · '+(al.silence||0)+
   ' silent · '+(al.dup||0)+' duplicate';
 $('ovKAlBox').classList.toggle('ov-attn',al.total>0);
 var ins=st.instruments||{};
 ['f1','f3','f4','f2'].forEach(function(k){
  var d=ins[k];if(!d)return;
  var got=ds.by_inst?(ds.by_inst[k]||0):d.collected;
  $('ovC-'+k).textContent=num(got);
  $('ovT-'+k).textContent=(d.target==null)?'–':num(d.target);
  var cell=$('ovP-'+k);cell.textContent='';
  if(d.target==null){var o=document.createElement('span');o.className='ov-open';
   o.textContent='open — no fixed target';cell.appendChild(o);return;}
  var pct=d.target?got/d.target*100:0;
  var bar=document.createElement('span');bar.className='ov-pbar';
  var fill=document.createElement('span');
  fill.className=pct>=100?'full':(pct<40?'low':'');fill.style.width=Math.min(pct,100)+'%';
  bar.appendChild(fill);cell.appendChild(bar);
  var pt=document.createElement('span');pt.className='ov-pct';
  pt.textContent=(pct>=1?Math.round(pct):pct.toFixed(1))+'%';cell.appendChild(pt);
  if(d.provisional){var pv=document.createElement('span');pv.className='ov-prov';
   pv.textContent='provisional';cell.appendChild(pv);}
 });
 var sp=$('ovSpark');sp.textContent='';
 var daily=ds.daily||[],mx=1;daily.forEach(function(d){if(d.n>mx)mx=d.n;});
 daily.forEach(function(d,i){
  var col=document.createElement('div');
  col.className='col'+(i===daily.length-1?' now':(d.n===0?' zero':''));col.title=d.date;
  var vl=document.createElement('span');vl.className='vl';vl.textContent=d.n||'';
  var bar=document.createElement('div');bar.className='bar';
  bar.style.height=Math.max(3,d.n/mx*64)+'px';
  var dl=document.createElement('span');dl.className='dl';dl.textContent=d.date.slice(8);
  col.appendChild(vl);col.appendChild(bar);col.appendChild(dl);sp.appendChild(col);
 });
 var un=$('ovUndated');
 if(ds.undated>0){un.hidden=false;un.textContent=(ds.undated===1?
  '1 case has':ds.undated+' cases have')+
  ' no usable visit date and are not plotted'+(scope?' (within '+ds.label+')':'')+'.';}
 else{un.hidden=true;}
 var list=$('ovAttnList');list.textContent='';
 function li(n,rest){var el=document.createElement('li');var bb=document.createElement('b');
  bb.textContent=n;el.appendChild(bb);el.appendChild(document.createTextNode(rest));
  list.appendChild(el);}
 var box=$('ovAttnBox');
 if(al.total===0){box.classList.add('ov-clear');
  $('ovAttnH').textContent='Nothing is waiting on anyone';
  li('All clear',' — no off-plan cases, no silent enumerators, no duplicate questionnaire numbers.');}
 else if(al.total!=null){box.classList.remove('ov-clear');
  $('ovAttnH').textContent='item'+(al.total===1?'':'s')+' waiting on someone';
  if(al.offplan)li(al.offplan+' case'+(al.offplan===1?'':'s'),
   ' completed at facilities that are not in the assignment plan');
  if(al.silence)li(al.silence+' enumerator'+(al.silence===1?'':'s'),
   ' not synced in more than 24 hours');
  if(al.dup)li(al.dup+' duplicate questionnaire number'+(al.dup===1?'':'s'),'');}
 $('ovAttnN').textContent=(al.total==null)?'—':al.total;

 var ac=$('ovActs');
 if(ac&&st.activities){ac.textContent='';
  st.activities.forEach(function(a){
   var row=document.createElement('div');
   var today=new Date().toISOString().slice(0,10),stt,cls;
   if(a.planned||!a.start){stt='planned';cls='plan';row.className='ov-act planned';}
   else if(a.end&&a.end<today){stt='ended';cls='done';row.className='ov-act';}
   else{var dn=Math.floor((Date.now()-Date.parse(a.start))/864e5)+1;
    stt='active · day '+dn;cls='on';row.className='ov-act';}
   if(scope===a.id)row.className+=' sel';
   row.style.cursor='pointer';
   row.title=scope===a.id?'Click to clear the activity filter':'Click to filter the console figures to this activity';
   row.onclick=function(){scope=(scope===a.id?null:a.id);if(lastSt)apply(lastSt);};
   var l1=document.createElement('div');l1.className='l1';
   var nm=document.createElement('span');nm.className='nm';nm.textContent=a.label||a.id;
   var phc=document.createElement('span');phc.className='ph p-'+(a.phase||'');
   phc.textContent=a.phase||'?';
   var stc=document.createElement('span');stc.className='st '+cls;stc.textContent=stt;
   l1.appendChild(nm);l1.appendChild(phc);l1.appendChild(stc);row.appendChild(l1);
   var l2=document.createElement('div');l2.className='l2';
   var dt=document.createElement('span');dt.className='dates';
   dt.textContent=(a.start||'TBD')+' → '+(a.end||(a.start?'open':'TBD'));
   l2.appendChild(dt);
   var cs=document.createElement('span');
   cs.textContent=(a.cases||0).toLocaleString('en-US')+' case'+(a.cases===1?'':'s');
   l2.appendChild(cs);
   var bi=a.by_inst||{},bits=['f1','f3','f4','f2'].filter(function(k){return k in bi;})
     .map(function(k){return k.toUpperCase()+' '+bi[k];}).join(' · ');
   if(bits){var bs=document.createElement('span');bs.textContent=bits;l2.appendChild(bs);}
   row.appendChild(l2);
   var quo=a.quotas||{};var qk=Object.keys(quo);
   if(qk.length){var tot=0,got=0;qk.forEach(function(k){tot+=quo[k];got+=(bi[k]||0);});
    var qd=document.createElement('div');qd.className='q';
    var bar=document.createElement('span');bar.className='ov-pbar';
    var fill=document.createElement('span');fill.style.width=Math.min(100,tot?got/tot*100:0)+'%';
    bar.appendChild(fill);qd.appendChild(bar);
    var qt=document.createElement('span');
    qt.textContent='quota: '+qk.map(function(k){return k.toUpperCase()+' '+(bi[k]||0)+'/'+quo[k];}).join(' · ');
    qd.appendChild(qt);row.appendChild(qd);}
   ac.appendChild(row);});}
 var pill=$('ovPill');
 if(pill){pill.textContent='';var pd=document.createElement('span');pd.className='dot';
  pill.appendChild(pd);
  var msg,lock=false,neutral=false;
  if(stale){msg='⚠ Data stale '+(ageMin>=60?Math.floor(ageMin/60)+'h':Math.round(ageMin)+'m');lock=true;}
  else if(quiet){msg='⚠ Tablets quiet '+tAge;lock=true;}
  else if(al.total>0){msg='⚠ '+al.total+' need'+(al.total===1?'s':'')+' attention';lock=true;}
  else if(!tAge&&!f2Active){msg='Status —';neutral=true;}
  else{msg='Fieldwork live';}
  pill.appendChild(document.createTextNode(msg));
  pill.classList.toggle('lock',lock);pill.classList.toggle('live',!lock&&!neutral);}
 var stq=$('ovStamp');
 stq.dataset.live='1';
 stq.textContent=(stale?'⚠ Dashboard data is stale — treat figures as of '+(st.dash_generated||'—')+' only. ':
  'Figures refreshed from the live database · data as of '+(st.dash_generated||'—')+' · ')+
  'checked '+(st.generated||'').replace('T',' ').replace('Z',' UTC')+
  (scope?' · figures filtered to '+ds.label:'');
}
function tick(){
 fetch(URL+'?_='+Date.now(),{cache:'no-store'}).then(function(r){
  if(!r.ok)throw new Error(r.status);return r.json();}).then(apply)
 .catch(function(){var s=$('ovStamp');
  if(s&&!s.dataset.live&&!s.dataset.err){s.dataset.err='1';
   s.textContent=s.textContent+' · live refresh unavailable';}});
}
tick();setInterval(tick,12e4);
})();
"""


def _ov_act_rows(st):
    """Baked Survey Activities rows; the JS rebuilds these from the live feed."""
    import datetime as _dt
    acts = (st or {}).get("activities") or []
    if not acts:
        return ('<div class="ov-act planned"><div class="l1"><span class="nm">'
                'Activities appear here once declared</span></div></div>')
    out = []
    today = _dt.date.today()
    for a in acts:
        ph = a.get("phase") or ""
        if a.get("planned") or not a.get("start"):
            stt, cls, planned = "planned", "plan", True
        elif a.get("end") and a["end"] < today.isoformat():
            stt, cls, planned = "ended", "done", False
        else:
            d = (today - _dt.date.fromisoformat(a["start"])).days + 1
            stt, cls, planned = "active &middot; day %d" % d, "on", False
        dates = ((a.get("start") or "TBD") + " &rarr; "
                 + (a.get("end") or ("open" if a.get("start") else "TBD")))
        bi = a.get("by_inst") or {}
        bit = " &middot; ".join("%s %d" % (k.upper(), bi[k])
                                for k in ("f1", "f3", "f4", "f2") if k in bi)
        q = ""
        quo = a.get("quotas") or {}
        if quo:
            per = " &middot; ".join("%s %d/%d" % (k.upper(), bi.get(k, 0), v)
                                    for k, v in quo.items())
            tot = sum(quo.values())
            got = sum(bi.get(k, 0) for k in quo)
            pct = min(100, got / tot * 100 if tot else 0)
            q = ('<div class="q"><span class="ov-pbar"><span style="width:%.0f%%">'
                 '</span></span><span>quota: %s</span></div>' % (pct, per))
        out.append(
            '<div class="ov-act%s"><div class="l1"><span class="nm">%s</span>'
            '<span class="ph p-%s">%s</span><span class="st %s">%s</span></div>'
            '<div class="l2"><span class="dates">%s</span><span>%s case%s</span>%s</div>%s</div>'
            % (" planned" if planned else "", a.get("label") or a.get("id"),
               ph, ph or "?", cls, stt, dates, "{:,}".format(a.get("cases") or 0),
               "" if a.get("cases") == 1 else "s",
               ("<span>%s</span>" % bit) if bit else "", q))
    return "".join(out)


def project_home():
    """Console overview: live status first, orientation second, reference third."""
    st = _ov_fetch_status()
    by = {i["k"]: i for i in INSTRUMENTS}

    al = (st or {}).get("alerts") or {}
    al_total = al.get("total")
    today = (st or {}).get("today")
    total = "{:,}".format(st["total"]) if st else "&mdash;"
    comp = "{:,}".format(st["completed"]) if st else "&mdash;"
    part = str(st["partial"]) if st else "&mdash;"
    comp_pct = ("%.0f%%" % (st["completed"] / st["total"] * 100)
                if st and st.get("total") else "&mdash;")

    rows = []
    for k in _OV_INST_ORDER:
        i = by[k]
        ins = ((st or {}).get("instruments") or {}).get(k) or {}
        got, tgt = ins.get("collected"), ins.get("target")
        rows.append(
            '<tr><td><span class="ov-fchip">%s</span></td>'
            '<td><b>%s</b><div style="font-size:12px;color:var(--ink-3)">%s</div></td>'
            '<td>%s</td>'
            '<td class="num" id="ovC-%s">%s</td>'
            '<td class="num" id="ovT-%s">%s</td>'
            '<td class="ov-prog" id="ovP-%s">%s</td></tr>'
            % (k.upper(), i["name"], i["who"],
               "Web" if k == "f2" else "Tablet", k,
               "{:,}".format(got) if got is not None else "&mdash;", k,
               "{:,}".format(tgt) if tgt is not None else ("&mdash;" if st is None else "&ndash;"),
               k, _ov_pbar(got, tgt, ins.get("provisional")) if got is not None
               else '<span class="ov-open">&mdash;</span>'))

    attn_items = []
    if st:
        if al.get("offplan"):
            attn_items.append("<li><b>%d case%s</b> completed at facilities that are not in "
                              "the assignment plan</li>"
                              % (al["offplan"], "" if al["offplan"] == 1 else "s"))
        if al.get("silence"):
            attn_items.append("<li><b>%d enumerator%s</b> not synced in more than 24 hours</li>"
                              % (al["silence"], "" if al["silence"] == 1 else "s"))
        if al.get("dup"):
            attn_items.append("<li><b>%d duplicate questionnaire number%s</b></li>"
                              % (al["dup"], "" if al["dup"] == 1 else "s"))
    clear = bool(st) and al_total == 0
    if clear:
        attn_items = ["<li>No off-plan cases, no silent enumerators, no duplicate "
                      "questionnaire numbers.</li>"]
    if not attn_items:
        attn_items = ["<li>Waiting for live data&hellip;</li>"]

    stamp = ("Figures refreshed from the live database &middot; data as of %s."
             % st["dash_generated"]) if st else \
            "Live figures will appear once the status feed is reachable."

    body = ('''
<div class="page-head">
  <div class="eyebrow">Project &middot; Department of Health</div>
  <h1>UHC Survey Year 2</h1>
  <p class="lead">A nationwide Universal Health Care study collecting evidence from four
  perspectives &mdash; the facility, the health care worker, the patient and the household.</p>
  <div class="ov-band" role="status">
    <span class="ov-chip" id="ovChipTab"><span class="dot"></span><span class="lb">Tablet sync</span>
      <span class="vl" id="ovChipTabV">&mdash;</span></span>
    <span class="ov-chip" id="ovChipF2"><span class="dot"></span><span class="lb">Web form (F2)</span>
      <span class="vl" id="ovChipF2V">&mdash;</span></span>
    <span class="ov-chip" id="ovChipAl"><span class="dot"></span><span class="lb">Needs attention</span>
      <span class="vl" id="ovChipAlV">@ALTOT@</span></span>
  </div>
</div>

<div class="ov-kpis">
  <div class="ov-kpi"><div class="k">Cases collected</div><div class="v" id="ovKTotal">@TOTAL@</div>
    <div class="s" id="ovKTodayS"><b>@TODAY@</b> today &middot; all instruments</div></div>
  <div class="ov-kpi"><div class="k">Completed</div><div class="v" id="ovKComp">@COMP@</div>
    <div class="s" id="ovKCompS">@COMPPCT@ of collected &middot; @PART@ partial</div></div>
  <div class="ov-kpi" id="ovKSyncBox"><div class="k">Last tablet sync</div>
    <div class="v" id="ovKSync">&mdash;</div>
    <div class="s" id="ovKSyncS">tablets F1 / F3 / F4</div></div>
  <div class="ov-kpi" id="ovKAlBox"><div class="k">Needs attention</div>
    <div class="v" id="ovKAl">@ALTOT@</div>
    <div class="s" id="ovKAlS">@ALSUB@</div>
    <a class="act" href="@DASH@">&#128274; Review in Sync Dashboard &rarr;</a></div>
</div>

<div class="sec">
  <div class="sec-head"><h2>Collection progress</h2>
    <a class="more" href="@DASH@">Sync Dashboard &rarr;</a></div>
  <p class="sub">Every instrument, and how far it has got. Percentages marked
  <span class="ov-prov">provisional</span> are measured against the pretest assignment plan,
  not ASPSI&rsquo;s final EA plan.</p>
  <div class="tbl-wrap"><table class="tbl">
    <thead><tr><th>Form</th><th>Instrument</th><th>Mode</th>
      <th class="right">Collected</th><th class="right">Target</th><th>Progress</th></tr></thead>
    <tbody>@ROWS@</tbody>
  </table></div>
</div>

<div class="sec">
  <div class="sec-head"><h2>Cases per day</h2></div>
  <p class="sub">Last 11 days, by visit date.</p>
  <div class="ov-spark" id="ovSpark">@SPARK@</div>
  @UNDATED@
</div>

<div class="sec">
  <div class="sec-head"><h2>Survey activities</h2></div>
  <p class="sub">Named fieldwork periods with start and end dates &mdash; cases classify to the
  activity that was running when they were collected. <b>Click a row to filter the
  figures above to that activity</b>; operational health (sync age, alerts) stays global.</p>
  <div class="ov-acts" id="ovActs">@ACTS@</div>
</div>

<div class="sec">
  <div class="sec-head"><h2>Needs attention</h2></div>
  <div class="ov-attnbox@CLEARCLS@" id="ovAttnBox">
    <h3><span class="n" id="ovAttnN">@ALTOT@</span><span id="ovAttnH">@ATTNH@</span></h3>
    <ul class="ov-attnlist" id="ovAttnList">@ATTNITEMS@</ul>
    <a class="cta" href="@DASH@">&#128274; Open the Sync Dashboard &rarr;</a>
    <div class="gated">&#128274; Which enumerator, and which facilities, are shown after sign-in.</div>
  </div>
</div>

<div class="sec">
  <div class="sec-head"><h2>Start here</h2></div>
  <p class="sub">Pick the row that describes you.</p>
  <div class="ov-roles">
    <div class="ov-role"><h3>I&rsquo;m collecting in the field</h3>
      <div class="who">Enumerator on a tablet (F1, F3, F4).</div>
      <ul><li><a href="@P@/guides/enumerator/">Enumerator guide</a></li>
          <li><a href="@P@/guides/supervisor/">Supervisor hub guide</a></li>
          <li><a href="@P@/manual/">CAPI manual</a></li></ul></div>
    <div class="ov-role"><h3>I&rsquo;m a health care worker</h3>
      <div class="who">You answer on your own phone &mdash; no interviewer.</div>
      <ul><li><a href="@P@/guides/healthcare-worker/">How to complete the survey</a></li>
          <li><a href="@F2APP@">Open the survey app</a></li></ul></div>
    <div class="ov-role"><h3>I&rsquo;m supervising fieldwork <span class="tag lock">sign-in</span></h3>
      <div class="who">ASPSI and DOH staff tracking collection.</div>
      <ul><li><a href="@DASH@">Sync Dashboard</a></li>
          <li><a href="@MAP@">Map report</a></li>
          <li><a href="@P@/monitoring/">Monitoring overview</a></li></ul></div>
    <div class="ov-role"><h3>I&rsquo;m working with the data <span class="tag lock">sign-in</span></h3>
      <div class="who">Analysts and data users.</div>
      <ul><li><a href="@P@/data/">Data room</a></li>
          <li><a href="@P@/instruments/">Codebooks &amp; instruments</a></li></ul></div>
  </div>
  <div class="ov-reflinks">
    <a href="@P@/manual/">CAPI manual</a>
    <a href="@P@/instruments/">Instruments &amp; codebooks</a>
    <a href="@P@/archive/pretest-2026-07-15/">Archive</a>
  </div>
  <div class="upd ov-foot" id="ovStamp">@STAMP@</div>
</div>
<script>@JS@</script>'''
        .replace("@TOTAL@", total).replace("@COMP@", comp)
        .replace("@PART@", part).replace("@COMPPCT@", comp_pct)
        .replace("@TODAY@", ("+%d" % today) if today is not None else "&mdash;")
        .replace("@ALTOT@", str(al_total) if al_total is not None else "&mdash;")
        .replace("@ALSUB@", ("%d off&#8209;plan &middot; %d silent &middot; %d duplicate"
                             % (al.get("offplan", 0), al.get("silence", 0), al.get("dup", 0)))
                 if st else "&mdash;")
        .replace("@ATTNH@", "Nothing is waiting on anyone" if clear
                 else (("item%s waiting on someone" % ("" if al_total == 1 else "s"))
                       if al_total is not None else "Live status pending"))
        .replace("@CLEARCLS@", " ov-clear" if clear else "")
        .replace("@ATTNITEMS@", "".join(attn_items))
        .replace("@UNDATED@",
                 ('<div class="ov-foot" id="ovUndated">%s</div>'
                  % ("1 case has no usable visit date and is not plotted."
                     if st["undated"] == 1 else
                     "%d cases have no usable visit date and are not plotted." % st["undated"]))
                 if st and st.get("undated") else
                 '<div class="ov-foot" id="ovUndated" hidden></div>')
        .replace("@ACTS@", _ov_act_rows(st))
        .replace("@ROWS@", "".join(rows))
        .replace("@SPARK@", _ov_spark((st or {}).get("daily")))
        .replace("@STAMP@", stamp).replace("@JS@", _OV_JS)
        .replace("@DASH@", OV_DASH).replace("@MAP@", OV_MAP)
        .replace("@F2APP@", OV_F2_APP).replace("@P@", P))

    s = shell("UHC Survey Year 2 — ASPSI CAPI",
              "Live status, collection progress and guides for the UHC Survey Year 2 "
              "CAPI programme.", body, active=P + "/")
    # the static "Fieldwork live" pill was the audit's sharpest finding -- on this
    # page it becomes a measurement, hydrated with everything else
    return s.replace(_PILL_LIVE,
                     '<span class="pill" id="ovPill"><span class="dot"></span>Status &mdash;</span>', 1)




def tabulations_index():
    """DOH tabulations: full PSA-committed catalog (public titles), gated Excel."""
    import csv as _csv
    plan = list(_csv.DictReader(open(os.path.join(
        HERE, "..", "..", "tabulation-plan", "tabulation-plan.csv"),
        encoding="utf-8-sig")))
    ann = {}
    for r in plan:
        ann.setdefault(r["instrument"], []).append(r)
    body = ('<div class="page-head"><div class="eyebrow">UHC Survey Year 2</div>'
            '<h1>Tabulations</h1>'
            '<p class="lead">The output tables committed to the PSA (SSRCS Form 1 SII-9), '
            'catalogued in full and generated from synced instrument data. Official tables '
            'are produced by the weighted Stata lane; unweighted pretest previews are '
            'downloadable now.</p></div>'
            + tiles([("Committed tables", "%d" % len(plan), "PSA SSRCS Form 1 SII-9"),
                     ("Preview tables", "10", "unweighted pretest frequencies"),
                     ("Built (official)", "0", "weighted Stata lane - in progress"),
                     ("Refresh", "hourly", "from synced instrument data")])
            + '<div class="sec"><div class="sec-head"><h2>Preview downloads</h2></div>'
              '<p class="sub">Unweighted frequencies from live pretest data - stamped '
              'PRETEST PREVIEW on every sheet. Same sign-in as the dashboard.</p>'
              '<div class="grid">')
    for k, nm in (("F1", "Facility Head"), ("F3", "Patient"), ("F4", "Household")):
        body += ('<div class="card"><span class="tag lock">sign-in</span><h3>%s (%s)</h3>'
                 '<p>Preview workbook - one sheet per table, TOC, n and %%.</p>'
                 '<a class="go" href="%s/docs/data/tabulations/UHC-Y2-Tabulations-%s-preview.xlsx">'
                 'Download .xlsx</a></div>' % (nm, k, CONSOLE, k))
    body += ('<div class="card ghost"><h3>Health Care Worker (F2)</h3>'
             '<p>Preview pending - F2 answers need the item-label explode before '
             'tabulation.</p></div></div></div>')
    for anx, insts in (("Annex 1 - Facility level (F1)", "F1"),
                       ("Annex 2 - Patient level (F3)", "F3"),
                       ("Annex 3 - Household level (F4)", "F4"),
                       ("Annex 4 - Health care worker (F2)", "F2")):
        rows = "".join('<tr><td class="mono"><b>%s</b></td><td>%s</td><td>%s</td></tr>'
                       % (r["no"], html_escape(r["description"]), r["stat_type"])
                       for r in ann.get(insts, []))
        body += ('<div class="sec"><div class="sec-head"><h2>%s</h2>'
                 '<span class="tag arch">%d tables - planned</span></div>'
                 '<div class="tbl-wrap"><table class="tbl">'
                 '<thead><tr><th>No.</th><th>Table (verbatim from the SSRCS commitment)</th>'
                 '<th>Type</th></tr></thead><tbody>%s</tbody></table></div></div>'
                 % (anx, len(ann.get(insts, [])), rows))
    return shell("Tabulations — UHC Survey Y2",
                 "The PSA-committed output tables for UHC Survey Year 2, with "
                 "downloadable Excel previews.", body, active=P + "/tabulations/")


def html_escape(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


if __name__ == "__main__":
    main()
