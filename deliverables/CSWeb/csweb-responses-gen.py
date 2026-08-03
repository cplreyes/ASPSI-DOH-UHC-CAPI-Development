#!/usr/bin/env python3
r"""Generate the RESPONSES DATA ROOM: full per-case response spreadsheets (CSV) +
an index page with previews, from the CSWeb breakout DBs + the csweb_f2 mirror.
Serves at https://csweb.asiansocial.org/docs/data/ — behind the SAME basic-auth
credential as the dashboard (Carl's call, 2026-07-18).

Output per instrument:
  f1_responses.csv          one row per case: questionnaire_number + EVERY item of
  f3_responses.csv          every SINGULAR record (~315/~330/~230 columns)
  f4_responses.csv
  f3_roster_<record>.csv    one row per QN x occurrence for each ROSTER record
  f4_roster_<record>.csv    (occurrence-suffixing would explode the wide sheet:
                             F4's household roster alone is 23 items x 20 occ)
  f2_responses.csv          csweb_f2.f2_responses verbatim (already flat)
  index.html                file list + first-N-row preview per wide sheet

Values are the RAW stored codes (1/2, not Male/Female) — the dcf codebook is the
labeling truth; the dashboard is the labeled view. CSVs are UTF-8 with BOM so
Excel renders enye names correctly. NOTE for Excel: open via Data > From Text if
you need the 12-digit QN column as text (plain double-click may show 1.028E+11).

Table discovery is DYNAMIC (information_schema), so a dictionary redeploy that
drops + recreates a breakout DB needs no generator change:
  - a record table = any table with a `level-1-id` column (skips cases/notes/
    cspro_* infra and the *_case_binary_data photo bytes automatically);
  - a ROSTER = a record table with an `occ` column;
  - column order inside a record follows ORDINAL_POSITION (= dict item order);
    record tables are emitted alphabetically, questionnaire_number first.

SAFETY GUARD: refuses to write into the live OUT_DIR unless OUT_DIR/.htaccess
exists — /docs/.htaccess only gates three filenames by FilesMatch, so a data/
dir WITHOUT its own .htaccess would serve every response publicly. The guard
makes a wiped/rebuilt box fail loudly instead of leaking quietly.

Deploy: scp to /opt/ next to csweb-dashboard-gen.py; cron (every 2 min):
  */2 * * * * flock -n /tmp/csweb-responses.lock bash -c "cd /opt/app && python3 /opt/csweb-responses-gen.py" >> /var/log/csweb-responses.log 2>&1
Off-box dev: no fixture mode — this generator is pure SQL->CSV; test on the box
with --out-dir /tmp/data-test (the .htaccess guard applies only to the live dir).
First built 2026-07-18 (Case drill-down follow-up: "all responses in a
spreadsheet + export to CSV", Option A+B).
"""
import subprocess, csv, io, os, sys, html, datetime, argparse, zipfile, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import phase_lib  # activity-phase classification (Carl, 2026-07-27)
import activity_lib  # Survey Activities: named windows w/ dates (2026-07-27)

ENV = "/opt/app/.env"
COMPOSE_DIR = "/opt/app"
OUT_DIR = "/opt/app/lamp/www/docs/data"
PREVIEW_ROWS = 20

# instrument -> breakout schema (F2 is the mirror, handled separately)
BREAKOUTS = {"f1": "csweb_f1_breakout", "f3": "csweb_f3_breakout", "f4": "csweb_f4_breakout"}
F2_SCHEMA = "csweb_f2"
NAMES = {"f1": "F1 — Facility Head", "f3": "F3 — Patient", "f4": "F4 — Household",
         "f2": "F2 — Healthcare Worker (PWA)"}
# columns that are breakout plumbing, not survey content
INTERNAL_COLS = {"id", "case-id", "level-1-id", "occ"}


def rootpw():
    with open(ENV) as f:
        for line in f:
            if line.startswith("MYSQL_ROOT_PASSWORD"):
                return line.split("=", 1)[1].strip()
    raise SystemExit("MYSQL_ROOT_PASSWORD not found in " + ENV)


def q(sql):
    """Run SQL via the box's MySQL container; rows of UNESCAPED cells.

    mysql --batch escapes tab/newline/backslash inside values (\\t \\n \\\\) and
    prints NULL as the literal string NULL — undo both, because free-text answers
    genuinely contain commas/newlines and must round-trip into quoted CSV."""
    # --default-character-set=utf8mb4: the client otherwise negotiates latin1 and the
    # server transcodes on output — an enye (U+00F1) arrives as byte 0xF1 and kills a
    # strict UTF-8 decode. errors="replace" is the last-ditch guard: never lose the
    # whole data room to one undecodable byte.
    r = subprocess.run(
        ["docker", "compose", "exec", "-T", "database", "mysql", "-uroot",
         "-p" + rootpw(), "--default-character-set=utf8mb4", "--batch", "-N", "-e", sql],
        cwd=COMPOSE_DIR, capture_output=True, text=True, errors="replace")
    if r.returncode != 0:
        raise RuntimeError((r.stderr or "mysql query failed").strip())
    rows = []
    for line in r.stdout.splitlines():
        cells = []
        for cell in line.split("\t"):
            if cell == "NULL":
                cells.append("")
                continue
            # unescape via placeholder so \\n stays a literal backslash-n
            cell = (cell.replace("\\\\", "\x00")
                        .replace("\\n", "\n").replace("\\t", "\t").replace("\\0", "")
                        .replace("\x00", "\\"))
            cells.append(cell)
        rows.append(cells)
    return rows


def bt(name):
    return "`" + name.replace("`", "") + "`"


def discover(schema):
    """(singular, rosters): each a list of (table, [content columns in dict order]).
    A record table has `level-1-id`; a roster additionally has `occ`."""
    cols = q("SELECT TABLE_NAME, COLUMN_NAME FROM information_schema.COLUMNS"
             " WHERE TABLE_SCHEMA='%s' ORDER BY TABLE_NAME, ORDINAL_POSITION" % schema)
    by_table = {}
    for t, c in cols:
        by_table.setdefault(t, []).append(c)
    singular, rosters = [], []
    for t in sorted(by_table):
        cs = by_table[t]
        if "level-1-id" not in cs or t == "level-1":
            continue
        # drop plumbing: the shared internals plus each table's own `<table>-id` PK
        content = [c for c in cs if c not in INTERNAL_COLS and c != t + "-id"]
        if not content:
            continue
        (rosters if "occ" in cs else singular).append((t, content))
    return singular, rosters


def qn_map(schema):
    """level-1-id -> questionnaire_number, non-deleted cases only."""
    rows = q("SELECT l.`level-1-id`, COALESCE(l.`questionnaire_number`,'')"
             " FROM %s.`level-1` l JOIN %s.cases c ON c.id=l.`case-id` AND c.deleted=0"
             % (schema, schema))
    return {r[0]: r[1] for r in rows}


def phase_map(schema):
    """level-1-id -> (phase, activity): the uploading login (roster wins) with
    the Manila sync day as fallback -- one shared rule, see phase/activity_lib."""
    reg = phase_lib.load()
    areg = activity_lib.load()
    rows = q("SELECT l.`level-1-id`, COALESCE(sh.username,''),"
             " COALESCE(DATE_FORMAT(DATE_ADD(sh.created_time, INTERVAL 8 HOUR),"
             " '%%Y-%%m-%%d'),'')"
             " FROM %s.`level-1` l JOIN %s.cases c ON c.id=l.`case-id` AND c.deleted=0"
             " LEFT JOIN csweb_uhc_y2.cspro_sync_history sh"
             " ON sh.revision = c.last_modified_revision AND sh.direction='put'"
             % (schema, schema))
    return {r[0]: (phase_lib.phase_of(r[1] or None, r[2] or None, reg),
                   activity_lib.activity_of(r[1] or None, r[2] or None, areg))
            for r in rows}


def write_csv(path, header, rows):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def build_instrument(inst, schema, out_dir):
    """Write the wide CSV + roster CSVs for one breakout; return manifest entries."""
    singular, rosters = discover(schema)
    qns = qn_map(schema)
    phases = phase_map(schema)
    made = []

    # ---- wide sheet: one row per case, all singular-record items ----
    # per-table fetch composed in Python (a single 30-table JOIN is fragile);
    # disambiguate only colliding column names with a table__ prefix
    seen, clash = set(), set()
    for _, cs in singular:
        for c in cs:
            (clash if c in seen else seen).add(c)
    header, parts = ["questionnaire_number", "phase", "activity"], []
    for t, cs in singular:
        data = {}
        for row in q("SELECT `level-1-id`, %s FROM %s.%s"
                     % (", ".join(bt(c) for c in cs), schema, bt(t))):
            data[row[0]] = row[1:]
        parts.append((cs, data))
        header += [("%s__%s" % (t, c)) if c in clash else c for c in cs]
    wide = []
    for lid, qn in sorted(qns.items(), key=lambda kv: kv[1]):
        ph, act = phases.get(lid, (phase_lib.UNKNOWN, activity_lib.UNKNOWN))
        row = [qn, ph, act]
        for cs, data in parts:
            row += list(data.get(lid, [""] * len(cs)))
        wide.append(row)
    fn = "%s_responses.csv" % inst
    write_csv(os.path.join(out_dir, fn), header, wide)
    made.append({"file": fn, "rows": len(wide), "cols": len(header),
                 "kind": "wide", "header": header,
                 "preview": wide[:PREVIEW_ROWS]})

    # ---- one CSV per roster record: QN x occurrence ----
    for t, cs in rosters:
        rows = []
        for row in q("SELECT `level-1-id`, `occ`, %s FROM %s.%s ORDER BY `level-1-id`,`occ`"
                     % (", ".join(bt(c) for c in cs), schema, bt(t))):
            if row[0] not in qns:            # deleted case
                continue
            rows.append([qns[row[0]], row[1]] + row[2:])
        fn = "%s_roster_%s.csv" % (inst, t)
        write_csv(os.path.join(out_dir, fn), ["questionnaire_number", "occ"] + cs, rows)
        made.append({"file": fn, "rows": len(rows), "cols": len(cs) + 2, "kind": "roster"})
    return made


def build_f2(out_dir):
    cols = [c[1] for c in q(
        "SELECT ORDINAL_POSITION, COLUMN_NAME FROM information_schema.COLUMNS"
        " WHERE TABLE_SCHEMA='%s' AND TABLE_NAME='f2_responses' ORDER BY ORDINAL_POSITION"
        % F2_SCHEMA)]
    # #831: voided responses (admin void action) stay out of the analysis export;
    # the Sheet + F2_Audit keep the full record.
    rows = q("SELECT %s FROM %s.f2_responses WHERE COALESCE(`status`,'') <> 'voided'"
             " ORDER BY qn, submitted_at_server"
             % (", ".join(bt(c) for c in cols), F2_SCHEMA))
    # phase/activity: F2 has no CSWeb login -- classify by Manila submission day
    reg = phase_lib.load()
    areg = activity_lib.load()
    si = cols.index("submitted_at_server") if "submitted_at_server" in cols else None
    def f2_phase(r):
        if si is None or not r[si]:
            return (phase_lib.UNKNOWN, activity_lib.UNKNOWN)
        try:
            d = (datetime.datetime.strptime(r[si][:19], "%Y-%m-%d %H:%M:%S")
                 + datetime.timedelta(hours=8)).strftime("%Y-%m-%d")
        except ValueError:
            return (phase_lib.UNKNOWN, activity_lib.UNKNOWN)
        return (phase_lib.phase_of(None, d, reg),
                activity_lib.activity_of(None, d, areg))
    cols = cols + ["phase", "activity"]
    rows = [r + list(f2_phase(r)) for r in rows]
    fn = "f2_responses.csv"
    write_csv(os.path.join(out_dir, fn), cols, rows)
    return [{"file": fn, "rows": len(rows), "cols": len(cols), "kind": "wide",
             "header": cols, "preview": rows[:PREVIEW_ROWS]}]


FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 40 40'%3E"
           "%3Crect width='40' height='40' rx='8' fill='%23006b3f'/%3E"
           "%3Cpath d='M20 9l9 5v12l-9 5-9-5V14z' fill='%23e5b23b'/%3E%3C/svg%3E")

PAGE_TOP = """<!doctype html>
<html lang="en"><head><meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<meta name="robots" content="noindex" />
<link rel="icon" href="__FAVICON__" />
<title>UHC Survey Year 2 — Responses Data Room</title>
<style>
 :root{--g:#006b3f;--gd:#004d2c;--gold:#e5b23b;--ink:#1c2b25;--muted:#5b6b63;--line:#dfe7e2;--bg:#f4f7f5;--card:#fff}
 *{box-sizing:border-box}body{margin:0;font:15px/1.5 system-ui,Segoe UI,Roboto,sans-serif;color:var(--ink);background:var(--bg)}
 header{background:var(--g);color:#fff;padding:20px 24px}
 header h1{margin:0;font-size:20px}header .s{opacity:.85;font-size:13px;margin-top:4px}
 main{max-width:1180px;margin:0 auto;padding:22px}
 h2{font-size:17px;color:var(--gd);border-bottom:2px solid var(--g);padding-bottom:6px;margin:28px 0 8px}
 .note{background:#fffaf0;border:1px solid var(--gold);border-radius:8px;padding:10px 14px;color:#6b5418;font-size:13px;margin:14px 0}
 table.files{width:100%;border-collapse:collapse;font-size:13px;background:var(--card);border:1px solid var(--line);border-radius:12px;overflow:hidden}
 .files th,.files td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left}
 .files th{background:#eef3f0;color:var(--gd);font-size:12px}
 .files td.n{text-align:right}.files a{color:var(--g);font-weight:600;text-decoration:none}.files a:hover{text-decoration:underline}
 .prevwrap{overflow:auto;max-height:420px;border:1px solid var(--line);border-radius:12px;background:var(--card);margin:8px 0 4px}
 /* On a phone the file table's name+size+format columns do not fit, and it widened
    the whole document instead of scrolling. (.prev was already safe inside
    .prevwrap.) display:block makes the table its own scroller; display:table on
    the sections keeps the header aligned with the body. */
 @media(max-width:620px){
   table.files{display:block;overflow-x:auto}
   table.files>tbody,table.files>thead{display:table;width:100%;min-width:460px}
 }
 table.prev{border-collapse:collapse;font:12px ui-monospace,Consolas,monospace;white-space:nowrap}
 .prev th,.prev td{padding:4px 8px;border:1px solid #eef3f0}
 .prev th{background:#eef3f0;color:var(--gd);position:sticky;top:0;z-index:1}
 .prev td:first-child,.prev th:first-child{position:sticky;left:0;background:#f7faf8;font-weight:600}
 .sub{color:var(--muted);font-size:12.5px;margin:2px 0 14px}
 footer{max-width:1180px;margin:0 auto;padding:14px 22px 40px;color:var(--muted);font-size:12.5px}
 footer a{color:var(--g)}
.tb-user{display:none;align-items:center;gap:8px;font-size:12.5px;margin-top:8px}.tb-user.on{display:inline-flex}.tb-user b{font-weight:650}.tb-user .tier{font-size:10px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;padding:2px 7px;border-radius:5px;background:#eefaf3;color:#046a38;border:1px solid #cfe6d8}.tb-user a{color:#046a38;font-weight:650}</style></head><body>
<header><h1>UHC Survey Year 2 — Responses Data Room</h1>
<div class="s">Full response spreadsheets · raw stored codes · staff tier — signed in through the CAPI console</div><div id="tbUser" class="tb-user"></div></header>
<main>
<div class="note">One <b>wide CSV per instrument</b> (a row per case, every singular-record item) plus a
<b>CSV per roster record</b> (a row per case &times; occurrence). Values are the <b>raw codes</b> — labels live in
the questionnaire codebook; the <a href="/docs/dashboard.html" style="color:#6b5418"><b>Sync Dashboard</b></a> is the labeled view.
Prefer stats-ready files? The <b>labeled exports</b> below carry the same cases as SPSS .sav / Stata .dta
(labels embedded) and R .rds (+ codebook CSV). Excel tip: import CSVs via <i>Data &rarr; From Text/CSV</i> and set
<code>questionnaire_number</code> to Text, or the 12-digit key renders as 1.02E+11.
Regenerated every ~2 min from the live breakout DBs.</div>
"""


def esc(s):
    return html.escape(str(s if s is not None else ""), quote=False)


def fmt_zip(m, fmt):
    """Per-format zip name from a stats-manifest instrument entry; tolerates the
    legacy spss-only manifest shape during a deploy window."""
    return (m.get("zips") or {}).get(fmt) or (m.get("zip") if fmt == "spss" else None)


def zip_cells(zips):
    return "".join('<td><a href="%s" download>%s</a></td>' % (z, esc(z)) if z else "<td></td>"
                   for z in zips)


def index_html(manifests, generated, spss=None, cspro=None, cbook=None):
    out = [PAGE_TOP.replace("__FAVICON__", FAVICON)]
    # Labeled-exports band (written by csweb-spss-gen.py on the odd minutes; this
    # index just reflects its manifest, so a stopped stats cron simply hides it)
    insts = (spss or {}).get("instruments") or {}
    if any(fmt_zip(m, "spss") for m in insts.values()):
        out.append("<h2>Labeled exports — SPSS · Stata · R</h2>")
        out.append('<div class="sub">The same cases as the CSVs below, packaged for the stats tools: '
                   'SPSS <b>.sav</b> and Stata <b>.dta</b> carry variable labels (question text) and value '
                   'labels (code &rarr; answer) embedded from the questionnaire codebook — no lookup needed; '
                   'the R zips hold typed <b>.rds</b> files (raw codes) plus a per-instrument '
                   '<code>*_codebook.csv</code> with both label sets. Each zip holds the wide file plus its '
                   'roster files; every file is also served individually at its filename. Generated %s.</div>'
                   % esc((spss or {}).get("generated", "")))
        out.append('<table class="files"><tr><th>Instrument</th><th class="n">Cases</th>'
                   '<th>SPSS (.sav)</th><th>Stata (.dta)</th><th>R (.rds)</th></tr>')
        for inst in ("f1", "f3", "f4", "f2"):
            m = insts.get(inst) or {}
            if not fmt_zip(m, "spss"):
                continue
            out.append('<tr><td>%s</td><td class="n">%d</td>%s</tr>'
                       % (esc(NAMES[inst]), m.get("cases", 0),
                          zip_cells(fmt_zip(m, f) for f in ("spss", "stata", "r"))))
        combz = (spss or {}).get("combined_zips") or {}
        comb = [combz.get(f) or ((spss or {}).get("combined") if f == "spss" else None)
                for f in ("spss", "stata", "r")]
        if any(comb):
            out.append('<tr><td>All instruments (one zip per format)</td><td class="n"></td>%s</tr>'
                       % zip_cells(comb))
        out.append("</table>")
    # Codebook band (static, built by data-harmonization/generate_codebook.py;
    # hidden until codebook-manifest.json lands)
    cbi = (cbook or {}).get("instruments") or {}
    if any(m.get("xlsx") for m in cbi.values()):
        out.append("<h2>Codebook — what every variable means</h2>")
        out.append('<div class="sub">The official variable documentation for all four instruments: '
                   'variable name, label, the literal question text, <b>universe</b> (who was asked, '
                   'i.e. the skip logic), outbound <b>routing</b>, value categories, special codes '
                   '(Don\'t know / Refused) and the <b>CAPI validation rules</b>. Documented to the '
                   '<b>DDI-Codebook 2.5</b> element set that the PSA Data Archive (PSADA/NADA) uses, '
                   'presented in DHS recode-manual table style. Generated from the deployed build of '
                   'each instrument — the version below is the instrument it documents. Packaged %s.</div>'
                   % esc((cbook or {}).get("generated", "")))
        out.append('<table class="files"><tr><th>Instrument</th><th>Documents build</th>'
                   '<th class="n">Variables</th><th>Excel</th><th>PDF</th></tr>')
        for inst in ("f1", "f3", "f4", "f2"):
            m = cbi.get(inst) or {}
            if not m.get("xlsx"):
                continue
            ver = m.get("version") or ""
            vtxt = ("v%s (%s)" % (ver, m.get("date", "")) if ver and ver != "PWA"
                    else "PWA (in-app spec)")
            out.append('<tr><td>%s</td><td>%s</td><td class="n">%d</td>'
                       '<td><a href="%s" download>%s</a></td><td>%s</td></tr>'
                       % (esc(m.get("name", inst)), esc(vtxt), m.get("variables", 0),
                          m["xlsx"], esc(m["xlsx"]),
                          ('<a href="%s" download>%s</a>' % (m["pdf"], esc(m["pdf"])))
                          if m.get("pdf") else ""))
        comb = (cbook or {}).get("combined") or {}
        if comb.get("pdf") or comb.get("zip"):
            links = []
            if comb.get("pdf"):
                links.append('<a href="%s" download>%s</a>' % (comb["pdf"], esc(comb["pdf"])))
            if comb.get("zip"):
                links.append('<a href="%s" download>%s</a>' % (comb["zip"], esc(comb["zip"])))
            out.append('<tr><td>All instruments in one book</td><td></td><td class="n"></td>'
                       '<td>%s</td><td>%s</td></tr>'
                       % (links[-1] if comb.get("zip") else "", links[0] if comb.get("pdf") else ""))
        out.append("</table>")
    # CSPro band (static packages built by gen-cspro-packages.py, re-scp'd on
    # instrument redeploys; hidden until cspro-manifest.json lands)
    cins = (cspro or {}).get("instruments") or {}
    if any(m.get("zip") for m in cins.values()):
        out.append("<h2>CSPro applications &amp; dictionaries</h2>")
        out.append('<div class="sub">Run the actual CAPI instruments locally: each app package is the complete '
                   'CSPro 8.0 entry application — compiled <b>.pen</b>, versioned <b>.pff</b>, Designer source '
                   '(.ent / .apc / .qsf / .fmf / .dcf) and the PSGC/facility lookup files. Extract and '
                   'double-click the .pff: it opens with an <b>empty local case file</b> — no sync, no '
                   'credentials in the package. Dictionaries (<b>.dcf</b>, CSPro 8.0 JSON) are also served '
                   'individually for data users. F2 is a PWA (no CSPro app); its codebook is '
                   '<code>f2_codebook.csv</code>. Packaged %s.</div>'
                   % esc((cspro or {}).get("generated", "")))
        out.append('<table class="files"><tr><th>Instrument</th><th>Version</th><th>App package</th>'
                   '<th>Dictionary (.dcf)</th></tr>')
        for inst in ("f1", "f3", "f4"):
            m = cins.get(inst) or {}
            if not m.get("zip"):
                continue
            out.append('<tr><td>%s</td><td>v%s (%s)</td><td><a href="%s" download>%s</a></td>'
                       '<td><a href="%s" download>%s</a></td></tr>'
                       % (esc(m.get("app") or NAMES.get(inst, inst)), esc(m.get("version", "?")),
                          esc(m.get("date", "")), m["zip"], esc(m["zip"]), m["dcf"], esc(m["dcf"])))
        dz = (cspro or {}).get("dictionaries_zip")
        if dz:
            out.append('<tr><td>All dictionaries in one zip</td><td></td><td></td>'
                       '<td><a href="%s" download>%s</a></td></tr>' % (dz, esc(dz)))
        out.append("</table>")
    for inst in ("f1", "f3", "f4", "f2"):
        entries = manifests.get(inst) or []
        out.append("<h2>%s</h2>" % esc(NAMES[inst]))
        if not entries:
            out.append('<div class="sub">query failed — see /var/log/csweb-responses.log; other instruments unaffected</div>')
            continue
        out.append('<table class="files"><tr><th>File</th><th class="n">Rows</th><th class="n">Columns</th><th>Contents</th></tr>')
        for e in entries:
            what = ("all singular-record items, one row per case" if e["kind"] == "wide"
                    else "roster record, one row per case &times; occurrence")
            out.append('<tr><td><a href="%s" download>%s</a></td><td class="n">%d</td><td class="n">%d</td><td>%s</td></tr>'
                       % (e["file"], esc(e["file"]), e["rows"], e["cols"], what))
        out.append("</table>")
        for e in entries:
            if e["kind"] != "wide" or "preview" not in e:
                continue
            out.append('<div class="sub">Preview — first %d of %d rows (scroll sideways for all %d columns):</div>'
                       % (min(PREVIEW_ROWS, e["rows"]), e["rows"], e["cols"]))
            out.append('<div class="prevwrap"><table class="prev"><tr>%s</tr>'
                       % "".join("<th>%s</th>" % esc(h) for h in e["header"]))
            for row in e["preview"]:
                out.append("<tr>%s</tr>" % "".join("<td>%s</td>" % esc(c) for c in row))
            out.append("</table></div>")
    out.append('</main><footer>Generated %s UTC · source: F1/F3/F4 breakout DBs + <code>csweb_f2</code> mirror · '
               'back to the <a href="/docs/dashboard.html">Sync Dashboard</a>.</footer><script>(function(){var e=document.getElementById("tbUser");if(!e)return;fetch("/docs/whoami.php",{credentials:"same-origin"}).then(function(r){return r.ok?r.json():null}).then(function(d){if(!d||!d.signed_in)return;var u=document.createElement("b");u.textContent=d.user;var t=document.createElement("span");t.className="tier";t.textContent=d.tier;var a=document.createElement("a");a.href="/docs/auth/logout";a.textContent="Sign out";e.appendChild(u);e.appendChild(t);e.appendChild(a);e.className="tb-user on";}).catch(function(){});})();</script></body></html>' % esc(generated))
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description="Generate the responses data room (CSVs + index).")
    ap.add_argument("--out-dir", default=OUT_DIR, help="output dir (default: %(default)s)")
    a = ap.parse_args()
    live = os.path.abspath(a.out_dir) == os.path.abspath(OUT_DIR)
    os.makedirs(a.out_dir, exist_ok=True)
    if live and not os.path.exists(os.path.join(OUT_DIR, ".htaccess")):
        sys.exit("REFUSING to write: %s/.htaccess is missing — the parent /docs/.htaccess only "
                 "gates three filenames, so this dir would serve every response PUBLICLY. "
                 "Restore the auth stanza first (see deliverables/CSWeb docs)." % OUT_DIR)

    manifests = {}
    for inst, schema in BREAKOUTS.items():
        try:
            manifests[inst] = build_instrument(inst, schema, a.out_dir)
        except Exception as e:
            manifests[inst] = []
            print("WARN: %s failed: %s" % (inst, str(e)[:300]))
    try:
        manifests["f2"] = build_f2(a.out_dir)
    except Exception as e:
        manifests["f2"] = []
        print("WARN: f2 failed: %s" % str(e)[:300])

    generated = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M")
    try:
        with open(os.path.join(a.out_dir, "spss-manifest.json"), encoding="utf-8") as f:
            spss = json.load(f)
    except Exception:
        spss = None
    try:
        with open(os.path.join(a.out_dir, "cspro-manifest.json"), encoding="utf-8") as f:
            cspro = json.load(f)
    except Exception:
        cspro = None
    try:
        with open(os.path.join(a.out_dir, "codebook-manifest.json"), encoding="utf-8") as f:
            cbook = json.load(f)
    except Exception:
        cbook = None
    with open(os.path.join(a.out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html(manifests, generated, spss, cspro, cbook))

    # ---- per-instrument zip bundles + manifest.json (dashboard Downloads band) ----
    # zipped AFTER the CSVs so a bundle is always internally consistent; the dashboard
    # generator reads manifest.json to label its download buttons (2026-07-18).
    NL = chr(10)
    zips = {}
    for inst in ("f1", "f3", "f4", "f2"):
        entries = manifests.get(inst) or []
        if not entries:
            continue
        zname = "%s-cases.zip" % inst
        readme = NL.join([
            NAMES[inst],
            "Generated %s UTC from the live CSWeb store." % generated,
            "Cases: %d" % entries[0]["rows"],
            "",
            "One wide CSV (a row per case, every singular-record item) plus one CSV per",
            "roster record (a row per case x occurrence). Values are RAW stored codes;",
            "labels live in the questionnaire codebook.",
            "Excel: import via Data > From Text/CSV and set questionnaire_number to Text,",
            "or the 12-digit key renders as 1.02E+11.",
            ""])
        with zipfile.ZipFile(os.path.join(a.out_dir, zname), "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("README.txt", readme)
            for e in entries:
                z.write(os.path.join(a.out_dir, e["file"]), e["file"])
        zips[inst] = {"zip": zname, "cases": entries[0]["rows"], "files": len(entries) + 1}
    with open(os.path.join(a.out_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump({"generated": generated + " UTC", "instruments": zips}, f)
    total = sum(len(v) for v in manifests.values())
    print("wrote %d csv files + index.html to %s ; rows: %s"
          % (total, a.out_dir,
             " ".join("%s=%s" % (k, (v[0]["rows"] if v else "FAIL")) for k, v in manifests.items())))


if __name__ == "__main__":
    main()
