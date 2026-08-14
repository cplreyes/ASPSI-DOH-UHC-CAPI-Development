#!/usr/bin/env python3
"""Publish a PUBLIC status summary for the capi.asiansocial.org project Overview.

Reads the two artifacts the reporting layer already generates --
  /opt/app/lamp/www/docs/dashboard.html   (dash-data payload, 2-min cron, even minutes)
  /opt/app/lamp/www/docs/sync-feed.json   (alerts + sync events, 1-min cron)
-- and distills AGGREGATES ONLY into the portal's docroot, where the Overview
page hydrates from it same-origin:
  /opt/app/capi-www/projects/uhc-y2/status.json

Privacy contract (Carl, 2026-07-25): counts, percentages, timestamps and alert
COUNTS only. No enumerator names or logins, no facility names or codes, no
case keys. Enforced three ways (adversarial review, 2026-07-25):
  1. INSTS whitelist -- payload dict keys are never copied through verbatim;
     only the four known instrument keys reach the public file.
  2. No free-text pass-through -- plan provenance is reduced to booleans
     (plan_label was published-but-never-rendered, so it was dropped).
  3. A needle tripwire on serialized output as a last resort.

Failure semantics: stale beats garbage, garbage never ships. If EITHER input
is unreadable the run exits nonzero and the previous status.json stays in
place (a missing feed must not publish alerts:0 as a confident all-clear).
Staleness is DECLARED, not hidden: dash_age_min + dash_ok let the page warn
when the dashboard cron has died but this generator keeps succeeding.

Cron runs on ODD minutes ("1-59/2") so it reads the dashboard written on the
even minute before, never mid-write.
"""
import argparse, csv as _csv, datetime, html, json, os, re, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import activity_lib

DASH = "/opt/app/lamp/www/docs/dashboard.html"
FEED = "/opt/app/lamp/www/docs/sync-feed.json"
OUT = "/opt/app/capi-www/projects/uhc-y2/status.json"
DAYS = 11                       # sparkline window, ending "today" (Manila)
INSTS = ("f1", "f3", "f4", "f2")  # the ONLY payload keys allowed into public output
DASH_FRESH_MIN = 10             # dashboard payload older than this => dash_ok false
CSVDIR = "/opt/app/lamp/www/docs/data"  # phase column source (responses exports)


def activity_block(act_agg):
    """Public activities snapshot: registry (rosters stripped) + per-activity
    aggregate SLICES from the dashboard payload rows, so the Overview can
    filter its figures by activity. Aggregates only -- same privacy contract."""
    out = []
    def slice_of(g):
        return {"total": g["total"], "completed": g["completed"],
                "partial": g["partial"], "today": g["today"],
                "daily": g.get("daily") or [], "undated": g["undated"]}
    for a in activity_lib.public_view():
        g = act_agg.get(a["id"])
        a["cases"] = g["total"] if g else 0
        a["by_inst"] = g["by_inst"] if g else {}
        a["slice"] = slice_of(g) if g else None
        out.append(a)
    if "unassigned" in act_agg:
        g = act_agg["unassigned"]
        out.append({"id": "unassigned", "label": "Unassigned", "phase": None,
                    "kind": None, "start": None, "end": None, "planned": False,
                    "quotas": {}, "cases": g["total"], "by_inst": g["by_inst"],
                    "slice": slice_of(g)})
    return out


def phase_counts():
    """Aggregate the exports' phase column -- counts only, phases are not PII."""
    out = {}
    for inst in INSTS:
        try:
            with open(os.path.join(CSVDIR, "%s_responses.csv" % inst),
                      encoding="utf-8-sig") as fh:
                rd = _csv.reader(fh)
                h = next(rd)
                if "phase" not in h:
                    continue
                i = h.index("phase")
                for row in rd:
                    ph = row[i] if i < len(row) else ""
                    out[ph or "unphased"] = out.get(ph or "unphased", 0) + 1
        except OSError:
            continue
    return out


def load_payload(path):
    h = open(path, encoding="utf-8").read()
    m = re.search(r'<script type="application/json" id="dash-data">(.*?)</script>', h, re.S)
    if not m:
        raise ValueError("dash-data payload not found in %s" % path)
    return json.loads(html.unescape(m.group(1)))


def manila_today(now_utc):
    return (now_utc + datetime.timedelta(hours=8)).strftime("%Y%m%d")


def dash_age_minutes(P, path, now):
    """Age of the dashboard DATA in minutes -- from its own stamp, else file mtime."""
    try:
        dt = datetime.datetime.strptime(P.get("generated", ""), "%Y-%m-%d %H:%M UTC")
        return max(0, int((now.replace(tzinfo=None) - dt).total_seconds() // 60))
    except ValueError:
        mt = datetime.datetime.utcfromtimestamp(os.path.getmtime(path))
        return max(0, int((now.replace(tzinfo=None) - mt).total_seconds() // 60))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dash", default=DASH)
    ap.add_argument("--feed", default=FEED)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()

    # either input unreadable -> exit nonzero, previous status.json survives
    P = load_payload(a.dash)
    feed = json.load(open(a.feed, encoding="utf-8"))

    now = datetime.datetime.now(datetime.timezone.utc)
    today = manila_today(now)
    data = P.get("data") or {}

    # ---- case aggregates (whitelisted instruments ONLY) --------------------
    total = completed = partial = 0
    per_day, today_by_inst, collected = {}, {}, {}
    undated = 0
    act_agg = {}          # per-activity slices, so the Overview can FILTER by activity
    for inst in INSTS:
        rows = data.get(inst) or []
        collected[inst] = len(rows)
        total += len(rows)
        t = 0
        for r in rows:
            aid = r.get("activity") or "unassigned"
            g = act_agg.setdefault(aid, {"total": 0, "completed": 0, "partial": 0,
                                         "today": 0, "per_day": {}, "undated": 0,
                                         "by_inst": {}})
            g["total"] += 1
            g["by_inst"][inst] = g["by_inst"].get(inst, 0) + 1
            st = (r.get("status") or "").lower()
            if st.startswith("complet"):
                completed += 1
                g["completed"] += 1
            elif st.startswith("part"):
                partial += 1
                g["partial"] += 1
            d = r.get("date") or ""
            if d.isdigit() and len(d) == 8 and d != "00000000":
                per_day[d] = per_day.get(d, 0) + 1
                g["per_day"][d] = g["per_day"].get(d, 0) + 1
                if d == today:
                    t += 1
                    g["today"] += 1
            else:
                undated += 1
                g["undated"] += 1
        today_by_inst[inst] = t

    # continuous daily series, zeros filled, ending today (Manila)
    end = datetime.datetime.strptime(today, "%Y%m%d")
    daily = []
    win = []
    for i in range(DAYS - 1, -1, -1):
        d = (end - datetime.timedelta(days=i)).strftime("%Y%m%d")
        win.append(d)
        daily.append({"date": "%s-%s-%s" % (d[:4], d[4:6], d[6:8]), "n": per_day.get(d, 0)})
    for g in act_agg.values():
        g["daily"] = [{"date": "%s-%s-%s" % (d[:4], d[4:6], d[6:8]),
                       "n": g["per_day"].get(d, 0)} for d in win]
        del g["per_day"]

    # ---- targets + provenance (booleans only -- no free text) --------------
    targets = P.get("targets") or {}
    plan = P.get("plan") or {}
    prov = plan.get("provisional")
    instruments = {}
    for k in INSTS:
        tgt = None
        if k in targets:
            tgt = sum(int(x.get("target") or 0) for x in targets[k].values())
        p = prov.get(k, False) if isinstance(prov, dict) else bool(prov)
        instruments[k] = {"collected": collected.get(k, 0), "target": tgt,
                          "provisional": bool(p and tgt is not None)}

    # ---- sync recency ------------------------------------------------------
    events = feed.get("events") or []
    tablet_last = max((e.get("time") or "" for e in events), default="") or None

    f2meta = P.get("f2meta") or {}
    f2_last = f2meta.get("last") or ""
    f2_last_iso = ("%s-%s-%s" % (f2_last[:4], f2_last[4:6], f2_last[6:8])
                   if len(f2_last) == 8 and f2_last.isdigit() else None)

    # ---- alert counts (counts ONLY -- the privacy boundary) ----------------
    alerts = feed.get("alerts") or []
    by_type = {}
    for al in alerts:
        by_type[al.get("type") or "?"] = by_type.get(al.get("type") or "?", 0) + 1
    alert_counts = {"total": len(alerts),
                    "offplan": by_type.get("offplan", 0),
                    "silence": by_type.get("silence", 0),
                    "dup": by_type.get("dup", 0)}

    age_min = dash_age_minutes(P, a.dash, now)
    out = {
        "generated": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "dash_generated": P.get("generated"),
        "dash_age_min": age_min,
        "dash_ok": age_min <= DASH_FRESH_MIN,
        "total": total, "completed": completed, "partial": partial,
        "today": sum(today_by_inst.values()), "today_by_inst": today_by_inst,
        "today_date": "%s-%s-%s" % (today[:4], today[4:6], today[6:8]),
        "tablet_last_sync": tablet_last,
        "f2_last_date": f2_last_iso, "f2_n": f2meta.get("n"),
        "f2_api_ok": f2meta.get("api"),
        "alerts": alert_counts,
        "instruments": instruments,
        "daily": daily, "undated": undated,
        "phases": phase_counts(),
        "activities": activity_block(act_agg),
    }

    # last-resort tripwire; the whitelist above is the real boundary
    blob = json.dumps(out)
    for needle in ('"user"', '"name"', '"facility"', '"code9"', '"key"'):
        if needle in blob:
            sys.exit("REFUSING to write: private field %s leaked into summary" % needle)

    outdir = os.path.dirname(os.path.abspath(a.out))
    os.makedirs(outdir, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=outdir, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(out, fh, separators=(",", ":"))
    os.replace(tmp, a.out)
    os.chmod(a.out, 0o644)
    print("wrote %s (%d cases, %d alerts, dash_age=%dmin%s)"
          % (a.out, total, alert_counts["total"], age_min,
             "" if out["dash_ok"] else " STALE"))


if __name__ == "__main__":
    main()
