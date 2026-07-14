#!/usr/bin/env python
r"""Build one printable handout per enumerator for the CAPI pretest.

WHY THIS EXISTS
---------------
Each enumerator needs three things in their hand at 08:00: their login, their
questionnaire numbers, and the handful of things that go silently wrong. Putting
those in a shared document means every password reaches every person, and the
Sync Dashboard attributes cases by CSWeb sync username -- so shared logins would
make per-enumerator monitoring meaningless. A per-person sheet keeps each
password on exactly one piece of paper.

The PLAN lives in this file (no secrets -- it is derived from ASPSI's
"Pretest Staff Deployment_July14" plus the corrected code list). The PASSWORDS
live in a gitignored CSV you fill in locally and that never enters git.

USAGE
-----
  1. cp pretest-credentials.template.csv pretest-credentials.csv
  2. fill in the password column (the file is gitignored)
  3. py build_pretest_handouts.py
  4. open out-pretest/handouts.html -> Ctrl+P -> Save as PDF -> print

Run it WITHOUT the credentials file and it still works: the password line prints
as a blank rule for the supervisor to write on by hand. That is a perfectly good
way to do this, and it means the passwords never touch a computer at all.
"""
import csv
import html
import pathlib

HERE = pathlib.Path(__file__).parent
CREDS = HERE / "pretest-credentials.csv"          # gitignored; may be absent
OUTDIR = HERE / "out-pretest"                     # gitignored
OUT = OUTDIR / "handouts.html"

GUIDE = "https://csweb.asiansocial.org/docs/pretest-guide.html"
TRACKER = "#839"

# ---------------------------------------------------------------------------
# THE PLAN. Source: ASPSI "Pretest Staff Deployment_July14" (days, sites, roles)
# + "Unique Question Number for Pre-testing_1" (codes), with ONE correction:
# the patient codes printed under Laguna Provincial Hospital - Bay were Los
# Banos Doctors Hospital's codes copied verbatim (040341110001-10). Same case
# key + same F3 dictionary from two hospitals = collision on sync, silently.
# Corrected to the Bay range 040340210001-10 (geo prefix 0403402 = Bay), which
# was verified against the live instrument.
# ---------------------------------------------------------------------------
ENUMERATORS = ["DRamos", "SLait", "ASalazar", "PCrudo", "AParaiso", "KPura", "AAlmendral"]

USERNAMES = {n: n.lower() for n in ENUMERATORS}

# day -> (title, when, where, list of (enumerator, role, app, codes))
DAYS = [
    ("DAY 1", "Wed 15 July", "Brgy. Mayondon, Los Baños", [
        ("DRamos",    "Household", "F4", "040341101001 – 040341101003"),
        ("SLait",     "Household", "F4", "040341101004 – 040341101006"),
        ("ASalazar",  "Household", "F4", "040341101007 – 040341101009"),
        ("PCrudo",    "Household", "F4", "040341101010 – 040341101012"),
        ("AParaiso",  "Household", "F4", "040341101013 – 040341101015"),
        ("KPura",     "Household", "F4", "040341101016 – 040341101018"),
        ("AAlmendral","Household", "F4", "040341101019 – 040341101020"),
    ]),
    ("DAY 2", "Thu 16–17 July", "Laguna Provincial Hospital – Bay  (Bay, Laguna)", [
        ("KPura",     "Facility Head", "F1", "040340210000"),
        ("AParaiso",  "HCW",           "F2", "— web app, no code —"),
        ("DRamos",    "Outpatient",    "F3", "040340210001"),
        ("SLait",     "Outpatient",    "F3", "040340210002"),
        ("ASalazar",  "Inpatient",     "F3", "040340210003, 040340210004"),
        ("PCrudo",    "Inpatient",     "F3", "040340210005"),
        ("AAlmendral","Office-based",  "—", "—"),
    ]),
    ("DAY 3", "Fri 17 July", "Los Baños Rural Health Unit", [
        ("AParaiso",  "Facility Head", "F1", "040341130000"),
        ("DRamos",    "HCW",           "F2", "— web app, no code —"),
        ("SLait",     "Outpatient",    "F3", "040341130001"),
        ("ASalazar",  "Outpatient",    "F3", "040341130002"),
        ("PCrudo",    "Outpatient",    "F3", "040341130003"),
        ("AAlmendral","Outpatient",    "F3", "040341130004"),
        ("KPura",     "Office-based",  "—", "—"),
    ]),
    ("DAY 4", "Mon 20 July", "Brgy. Mayondon, Los Baños  (target set on the day)", [
        ("DRamos",    "Household", "F4", "040341101021"),
        ("SLait",     "Household", "F4", "040341101022"),
        ("ASalazar",  "Household", "F4", "040341101023"),
        ("PCrudo",    "Household", "F4", "040341101024"),
        ("AParaiso",  "Household", "F4", "040341101025"),
        ("KPura",     "Household", "F4", "040341101026"),
        ("AAlmendral","Office-based", "—", "—"),
    ]),
    ("LBDH", "date TBD", "Los Baños Doctors Hospital", [
        ("AAlmendral","Facility Head", "F1", "040341110000"),
        ("KPura",     "HCW",           "F2", "— web app, no code —"),
        ("AParaiso",  "Outpatient",    "F3", "040341110001, 040341110002"),
        ("DRamos",    "Outpatient",    "F3", "040341110003"),
        ("SLait",     "Inpatient",     "F3", "040341110004"),
        ("ASalazar",  "Inpatient",     "F3", "040341110005"),
        ("PCrudo",    "Office-based",  "—", "—"),
    ]),
    ("ST. JUDE", "date TBD", "St. Jude Hospital, Los Baños", [
        ("DRamos",    "Facility Head", "F1", "040341140000"),
        ("SLait",     "HCW",           "F2", "— web app, no code —"),
        ("ASalazar",  "Outpatient",    "F3", "040341140001, 040341140002"),
        ("PCrudo",    "Outpatient",    "F3", "040341140003"),
        ("AParaiso",  "Inpatient",     "F3", "040341140004"),
        ("KPura",     "Inpatient",     "F3", "040341140005"),
        ("AAlmendral","Office-based",  "—", "—"),
    ]),
]

APP_NAME = {
    "F1": "Facility Head Survey (CSEntry)",
    "F3": "Patient Survey (CSEntry)",
    "F4": "Household Survey (CSEntry)",
    "F2": "HCW Survey — WEB APP, not CSEntry",
}


def load_passwords():
    """Return {name: password}. Absent file -> blank, printed as a write-on rule."""
    if not CREDS.exists():
        print("  ! %s not found - printing blank password rules for hand-writing." % CREDS.name)
        return {}
    out = {}
    with CREDS.open(encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            name = (row.get("enumerator_name") or "").strip()
            if name:
                out[name] = (row.get("password") or "").strip()
    missing = [n for n in ENUMERATORS if not out.get(n)]
    if missing:
        print("  ! no password for: %s (blank rule printed)" % ", ".join(missing))
    return out


def rows_for(name):
    """Every day this enumerator appears in, in order."""
    out = []
    for title, when, where, assigns in DAYS:
        for who, role, app, codes in assigns:
            if who == name:
                out.append((title, when, where, role, app, codes))
    return out


def esc(s):
    return html.escape(str(s), quote=False)


CSS = """
@page { size: A4; margin: 12mm; }
* { box-sizing: border-box; }
body { font-family: "Segoe UI", Roboto, Arial, sans-serif; color:#1b1b1b; margin:0; }
.sheet { page-break-after: always; padding: 4mm 2mm; }
.sheet:last-child { page-break-after: auto; }
h1 { font-size: 19pt; margin:0 0 1mm; }
.sub { color:#555; font-size:9.5pt; margin:0 0 4mm; }
.cred { border:2px solid #111; border-radius:6px; padding:4mm 5mm; margin:0 0 5mm; }
.cred .row { display:flex; align-items:baseline; gap:6mm; margin:1.5mm 0; }
.cred .k { width:26mm; font-size:9pt; text-transform:uppercase; letter-spacing:.6px; color:#555; }
.cred .v { font-family:Consolas,monospace; font-size:14pt; font-weight:700; }
.rule { flex:1; border-bottom:1.4px solid #111; height:14px; }
.pw-note { font-size:8.5pt; color:#777; margin:2mm 0 0; }
table { width:100%; border-collapse:collapse; font-size:9.5pt; margin:0 0 5mm; }
th,td { border:1px solid #bbb; padding:2mm 2.5mm; text-align:left; vertical-align:top; }
th { background:#eef1f6; font-size:8.5pt; text-transform:uppercase; letter-spacing:.5px; }
td.code { font-family:Consolas,monospace; font-weight:700; white-space:nowrap; }
.f2 { background:#fff6e5; }
.warn { border-left:4px solid #c0392b; background:#fdf1ef; padding:3mm 4mm; margin:0 0 3mm; font-size:9.5pt; }
.warn b { color:#a5281b; }
.ok { border-left:4px solid #2d7a3e; background:#f0f7f1; padding:3mm 4mm; margin:0 0 3mm; font-size:9.5pt; }
.foot { font-size:8.5pt; color:#666; border-top:1px solid #ddd; padding-top:2mm; }
.cut { text-align:center; color:#aaa; font-size:8pt; letter-spacing:3px; }
"""


def sheet(name, pw_map):
    rows = rows_for(name)
    pw = pw_map.get(name, "")
    pw_html = ('<span class="v">%s</span>' % esc(pw)) if pw else '<span class="rule"></span>'

    trs = []
    for title, when, where, role, app, codes in rows:
        cls = ' class="f2"' if app == "F2" else ""
        app_label = app if app == "—" else "<b>%s</b> — %s" % (app, esc(APP_NAME.get(app, app)))
        trs.append(
            "<tr%s><td><b>%s</b><br><span style='color:#666'>%s</span></td>"
            "<td>%s</td><td>%s</td><td>%s</td><td class='code'>%s</td></tr>"
            % (cls, esc(title), esc(when), esc(where), esc(role), app_label, esc(codes))
        )

    return """
    <div class="sheet">
      <h1>%(name)s</h1>
      <p class="sub">UHC Survey Year 2 &middot; CAPI Pretest &middot; Los Ba&ntilde;os / Bay, Laguna &middot; 15&ndash;20 July 2026</p>

      <div class="cred">
        <div class="row"><div class="k">Username</div><div class="v">%(user)s</div></div>
        <div class="row"><div class="k">Password</div>%(pw)s</div>
        <p class="pw-note">This sheet is yours alone. Do not share your login &mdash; every case you sync is
        recorded against it, and that is how your work is credited.</p>
      </div>

      <table>
        <thead><tr><th>Day</th><th>Where</th><th>Who you interview</th><th>App to open</th><th>Your codes</th></tr></thead>
        <tbody>%(rows)s</tbody>
      </table>

      <div class="warn">
        <b>Before 08:00 &mdash; remove the app and add it again.</b> Tapping &ldquo;Update Installed
        Applications&rdquo; does <b>not</b> reliably pick up the new build: the tablet keeps yesterday&rsquo;s
        version, everything looks normal, and today&rsquo;s changes are simply not there.
        Re-add from CSWeb, then check: <b>F1 v1.1.0 &middot; F3 v1.1.0 &middot; F4 v1.4.0</b>.
        If the version is wrong, <b>stop</b> and tell your STL.
      </div>

      <div class="warn">
        <b>Household (F4): your code does not set the barangay.</b> It only carries the municipality.
        You must still <b>pick the barangay from the dropdown &mdash; Mayondon</b>. A wrong pick still looks
        like a valid case number, so check it.
        <br><b>Bay is a different municipality from Los Ba&ntilde;os.</b> Its codes start <b>0403402</b>,
        not 0403411. At Laguna Provincial Hospital, a code starting 0403411 is the <b>wrong code</b> &mdash;
        stop and tell your STL before you enter it.
      </div>

      <div class="ok">
        <b>If the interview cannot happen &mdash; still open the case.</b> On the <b>Interview status</b>
        screen pick <b>Not interviewed &mdash; refused / not found / ineligible</b>. The app records it as
        <b>Replaced</b> and ends the case. <b>Do not just skip the household and move on</b> &mdash; if no case
        is opened, the office cannot see that you went, or why it failed.
        <i>A unit you could not interview is still work you did.</i>
        (&ldquo;Postponed / reschedule&rdquo; is for when you <i>are</i> coming back.)
      </div>

      <p class="foot">
        Full guide: <b>%(guide)s</b> &nbsp;&middot;&nbsp; Report anything odd on tracker <b>%(tracker)s</b>.
        This is a <b>pretest</b>: a question the respondent did not understand, or one you had to explain
        twice, is more valuable to us than a bug. Write it down.
      </p>
      <p class="cut">&#9986; &nbsp; - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -</p>
    </div>
    """ % {
        "name": esc(name),
        "user": esc(USERNAMES[name]),
        "pw": pw_html,
        "rows": "".join(trs),
        "guide": GUIDE,
        "tracker": TRACKER,
    }


def main():
    pw_map = load_passwords()
    OUTDIR.mkdir(exist_ok=True)
    body = "".join(sheet(n, pw_map) for n in ENUMERATORS)
    doc = (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<title>CAPI Pretest — enumerator handouts</title>"
        "<style>%s</style></head><body>%s</body></html>" % (CSS, body)
    )
    OUT.write_text(doc, encoding="utf-8")
    print("wrote %s" % OUT)
    print("  %d handouts (one page each): %s" % (len(ENUMERATORS), ", ".join(ENUMERATORS)))
    print("  open it, Ctrl+P, Save as PDF -> print -> hand out one page per person.")


if __name__ == "__main__":
    main()
