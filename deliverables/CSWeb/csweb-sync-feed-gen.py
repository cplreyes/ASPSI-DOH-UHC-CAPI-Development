#!/usr/bin/env python3
"""Write /opt/app/lamp/www/docs/sync-feed.json — the recent device-sync events + data
quality ALERTS the Sync Dashboard's notification bell polls (~every 20s).

- events[]: one entry per device SYNC SESSION with per-instrument NEW vs EDITED case
  counts, e.g. "ASalazar se-003 synced · F4: 3 new cases" (first upload) vs "· F4: 3
  edited" (a re-sync of cases uploaded earlier). Attribution is STABLE and does not
  overwrite past entries:
    * NEW    -> the case's `created_time` (its FIRST CSWeb insert, fixed forever) ==
               the creating sync's timestamp.
    * EDITED -> the case's `modified_time` (last change) when it is later than
               `created_time` == the re-syncing sync's timestamp.
  Both `created_time`/`modified_time` on the case row equal the corresponding
  cspro_sync_history put's `created_time` exactly (same transaction), so cases match
  sync sessions by timestamp per dictionary — no per-run recompute can move a count.
- alerts[]: 🔕 no sync from an enumerator in 24-96 h (silence alarm, 2026-07-24; auto-expires) ·
  🔴 duplicate/colliding case key · 🔴 case outside the assignment plan,
  each attributing the enumerator(s).

Sources: cspro_sync_history + the primary <DICT> case tables + targets.json (all on box).
READ-ONLY — reads sync metadata, case KEYS/TIMESTAMPS/COUNTS, never case content.

Deploy: scp to /opt/ next to csweb-dashboard-gen.py; cron (every minute):
  * * * * * flock -n /tmp/csweb-sync-feed.lock bash -c "cd /opt/app && python3 /opt/csweb-sync-feed-gen.py" >> /var/log/csweb-sync-feed.log 2>&1
First built 2026-07-15 (bell); session-dedup; per-instrument counts; +dup/off-plan alerts;
new-vs-edited via created_time/modified_time (no retroactive overwrite).
"""
import subprocess, json, datetime
from collections import defaultdict
from pathlib import Path

ENV = "/opt/app/.env"
COMPOSE_DIR = "/opt/app"
OUT = "/opt/app/lamp/www/docs/sync-feed.json"
TARGETS = "/opt/targets.json"
LIMIT = 120          # sync-history puts pulled (attribution + display source)
WINDOW = 300         # seconds: uploads by the same device within this span = one session
MAX_ALERTS = 30

DICTS = {"4": ("F1", "FACILITYHEADSURVEY_DICT"),
         "5": ("F3", "PATIENTSURVEY_DICT"),
         "6": ("F4", "HOUSEHOLDSURVEY_DICT")}
INSTS = [lbl for lbl, _ in DICTS.values()]
INST_ORDER = {"F1": 1, "F3": 2, "F4": 3}
NAMES = {  # CSWeb sync login -> field name (pretest roster; unknown logins render with the login)
    "se-001": "AAlmendral", "se-002": "AParaiso", "se-003": "ASalazar", "se-004": "DRamos",
    "se-005": "KPura", "se-006": "SLait", "se-007": "PCrudo",
}


def rootpw():
    with open(ENV) as f:
        for line in f:
            if line.startswith("MYSQL_ROOT_PASSWORD"):
                return line.split("=", 1)[1].strip()
    raise SystemExit("MYSQL_ROOT_PASSWORD not found in " + ENV)


def q(sql):
    r = subprocess.run(
        ["docker", "compose", "exec", "-T", "database", "mysql", "-uroot",
         "-p" + rootpw(), "--batch", "-N", "-e", sql],
        cwd=COMPOSE_DIR, capture_output=True, text=True)
    return [ln.split("\t") for ln in r.stdout.splitlines() if ln.strip()]


def code9(key):
    k = (key or "").strip()
    return k.zfill(12)[:9] if k.isdigit() else k[:9]


def rev_user_map():
    m = {}
    for row in q("SELECT revision, username FROM csweb_uhc_y2.cspro_sync_history WHERE direction='put'"):
        if len(row) >= 2:
            try:
                m[int(row[0])] = row[1]
            except ValueError:
                pass
    return m


def load_targets():
    try:
        return json.load(open(TARGETS, encoding="utf-8")).get("targets", {})
    except Exception:
        return {}


def case_time_index():
    """Per instrument: {created_time: count} (NEW) and {modified_time: count} (EDITED)."""
    new_ct = {inst: {} for inst in INSTS}
    edt_ct = {inst: {} for inst in INSTS}
    for _dic, (inst, tbl) in DICTS.items():
        for row in q("SELECT created_time, modified_time FROM csweb_uhc_y2.`%s` WHERE deleted=0" % tbl):
            if len(row) < 2:
                continue
            ct, mt = (row[0] or "").strip(), (row[1] or "").strip()
            if ct and ct != "NULL":
                new_ct[inst][ct] = new_ct[inst].get(ct, 0) + 1
            if mt and mt != "NULL" and ct and mt > ct:   # changed after creation -> a re-sync
                edt_ct[inst][mt] = edt_ct[inst].get(mt, 0) + 1
    return new_ct, edt_ct


def compute_alerts(rev2user, targets):
    alerts = []
    for _dic, (inst, tbl) in DICTS.items():
        for row in q("SELECT caseids, COUNT(*), GROUP_CONCAT(DISTINCT revision) FROM csweb_uhc_y2.`%s` "
                     "WHERE deleted=0 GROUP BY caseids HAVING COUNT(*)>1" % tbl):
            if len(row) < 3:
                continue
            key, n, revs = row[0], int(row[1]), row[2]
            rv = [int(r) for r in (revs or "").split(",") if r.strip().isdigit()]
            alerts.append({"type": "dup", "inst": inst, "key": key, "n": n,
                           "users": sorted({rev2user.get(r, "?") for r in rv}),
                           "rev": max(rv) if rv else 0, "id": "dup|%s|%s" % (inst, key)})
        plan = targets.get(inst.lower(), {})
        if plan:
            off = {}
            for row in q("SELECT caseids, revision FROM csweb_uhc_y2.`%s` WHERE deleted=0" % tbl):
                if len(row) < 2:
                    continue
                key = row[0]
                try:
                    rev = int(row[1])
                except ValueError:
                    rev = 0
                c9 = code9(key)
                if c9 and c9 not in plan:
                    g = off.setdefault(c9, {"n": 0, "users": set(), "rev": 0, "example": key})
                    g["n"] += 1
                    g["users"].add(rev2user.get(rev, "?"))
                    g["rev"] = max(g["rev"], rev)
            for c9, g in off.items():
                alerts.append({"type": "offplan", "inst": inst, "code9": c9, "n": g["n"],
                               "example": g["example"], "users": sorted(g["users"]),
                               "rev": g["rev"], "id": "offplan|%s|%s" % (inst, c9)})
    alerts.sort(key=lambda a: a["rev"], reverse=True)
    return alerts[:MAX_ALERTS]


SYNC_SQL = ("SELECT revision, username, dictionary_id, device, created_time "
            "FROM csweb_uhc_y2.cspro_sync_history WHERE direction='put' "
            "ORDER BY revision DESC LIMIT %d" % LIMIT)


def sync_sessions(new_ct, edt_ct):
    rows = []
    for row in q(SYNC_SQL):
        if len(row) < 5:
            continue
        rev, user, dic, dev, ts = row[0], row[1], row[2], row[3], (row[4] or "").strip()
        inst = DICTS.get(str(dic), ("dict " + str(dic), None))[0]
        try:
            when = datetime.datetime.strptime(ts, "%Y-%m-%d %H:%M:%S") if ts and ts != "NULL" else None
        except ValueError:
            when = None
        rows.append({"rev": int(rev), "user": user, "name": NAMES.get(user, ""), "inst": inst,
                     "device": (dev or "")[:8], "when": when, "ts": ts,
                     "new": new_ct.get(inst, {}).get(ts, 0), "edited": edt_ct.get(inst, {}).get(ts, 0)})

    clusters = []
    by = defaultdict(list)
    for r in rows:
        by[(r["user"], r["device"])].append(r)
    for evs in by.values():
        evs.sort(key=lambda e: e["rev"], reverse=True)
        cur = None
        for e in evs:
            near = (cur is not None and cur["start"] is not None and e["when"] is not None
                    and (cur["start"] - e["when"]).total_seconds() <= WINDOW)
            if not near:
                if cur:
                    clusters.append(cur)
                cur = {"rev": e["rev"], "user": e["user"], "name": e["name"], "device": e["device"],
                       "items": {}, "start": e["when"], "ts": e["ts"]}
            cur["rev"] = max(cur["rev"], e["rev"])
            it = cur["items"].setdefault(e["inst"], {"new": 0, "edited": 0})
            it["new"] += e["new"]
            it["edited"] += e["edited"]
        if cur:
            clusters.append(cur)
    clusters.sort(key=lambda c: c["rev"], reverse=True)

    events = []
    for c in clusters:
        items = [{"inst": inst, "new": c["items"][inst]["new"], "edited": c["items"][inst]["edited"]}
                 for inst in sorted(c["items"], key=lambda i: (INST_ORDER.get(i, 9), i))]
        iso = c["ts"].replace(" ", "T") + "Z" if c["ts"] and c["ts"] != "NULL" else ""
        events.append({"rev": c["rev"], "user": c["user"], "name": c["name"], "device": c["device"],
                       "items": items, "time": iso,
                       "total_new": sum(i["new"] for i in items),
                       "total_edited": sum(i["edited"] for i in items)})
    return events



# --- silence alarm + Slack delivery (2026-07-24) -----------------------------
# Carl, 2026-07-24: the bell only ever announced ACTIVITY, so a fleet that had
# been silent for 45.8 h looked identical to a calm one. These two additions
# close that: a per-enumerator "no sync in N hours" alert, and an off-page
# delivery path so alerts reach a phone instead of an unopened dashboard tab.

SILENCE_HOURS = 24          # per-enumerator threshold (Carl's call, 2026-07-24)
SILENCE_EXPIRE_HOURS = 96   # stop nagging past this: 24h-96h = 'went quiet' (actionable);
                            # beyond 4 days it means 'finished', not a live problem. Prevents
                            # a permanent red bell as fieldwork winds down (Carl, 2026-07-24).
ALERT_CONF = "/opt/csweb-alerts.conf"       # KEY=VALUE; SLACK_WEBHOOK_URL=...
ALERT_STATE = "/opt/csweb-alert-state.json"  # ids already delivered off-page
MAX_PUSH = 6                # never fire-hose a channel from one cron tick


def last_sync_per_user():
    """login -> datetime of its most recent upload (put)."""
    out = {}
    for row in q("SELECT username, MAX(created_time) FROM csweb_uhc_y2.cspro_sync_history "
                 "WHERE direction='put' GROUP BY username"):
        if len(row) < 2 or not row[1] or row[1] == "NULL":
            continue
        try:
            out[row[0]] = datetime.datetime.strptime(row[1].strip(), "%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass
    return out


def compute_silence_alerts(now=None):
    """One alert per enumerator who HAS synced before but not in SILENCE_HOURS.

    Deliberately scoped to logins with sync history: a login that has never
    synced has no established rhythm to break, and alerting on it would fire
    forever. The alert id carries the last-sync timestamp, so an ongoing
    silence notifies ONCE, while a new silent spell after a fresh sync is a
    genuinely new alert. Alerts auto-expire past SILENCE_EXPIRE_HOURS so a
    wound-down fleet does not leave the bell permanently red."""
    # naive-UTC to match cspro_sync_history.created_time, which MySQL stores
    # without a zone; utcnow() is deprecated so derive it explicitly
    now = now or datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    out = []
    for user, when in last_sync_per_user().items():
        hours = (now - when).total_seconds() / 3600.0
        if hours < SILENCE_HOURS or hours >= SILENCE_EXPIRE_HOURS:
            continue          # only the actionable window: recently went quiet
        out.append({
            "type": "silence", "user": user, "name": NAMES.get(user, user),
            "hours": int(hours), "since": when.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "level": "high" if hours >= 72 else "warn",   # 3+ days = escalate
            "id": "silence|%s|%s" % (user, when.strftime("%Y%m%dT%H%M%S")),
            "rev": 0,
        })
    out.sort(key=lambda a: -a["hours"])
    return out


def _conf(path):
    d = {}
    try:
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                d[k.strip()] = v.strip()
    except OSError:
        pass
    return d


def _alert_line(a):
    """One human sentence per alert — this is what lands on someone's phone."""
    if a["type"] == "silence":
        return (":no_bell: *No sync from %s* (`%s`) in *%d h* — last upload %s UTC"
                % (a.get("name") or a["user"], a["user"], a["hours"],
                   a["since"].replace("T", " ").rstrip("Z")))
    who = (" · " + ", ".join(a["users"])) if a.get("users") else ""
    if a["type"] == "dup":
        return (":warning: *Duplicate case key* `%s` · %s · %d cases%s"
                % (a.get("key"), a.get("inst"), a.get("n", 0), who))
    return (":warning: *Case outside the plan* · facility `%s` · %s · %d case(s)%s"
            % (a.get("code9"), a.get("inst"), a.get("n", 0), who))


def push_alerts(alerts):
    """Deliver NEW alerts off-page (Slack incoming webhook).

    No-ops silently when no webhook is configured, so this is safe to ship
    before the URL exists. State file keeps a delivered-id list so the same
    alert is never posted twice, and MAX_PUSH caps one tick's noise."""
    import urllib.request
    hook = _conf(ALERT_CONF).get("SLACK_WEBHOOK_URL", "")
    if not hook:
        return 0, "no webhook configured"
    try:
        seen = set(json.loads(Path(ALERT_STATE).read_text(encoding="utf-8")))
    except Exception:
        seen = set()
    fresh = [a for a in alerts if a.get("id") and a["id"] not in seen]
    if not fresh:
        return 0, "nothing new"
    # First ever run must not replay history into the channel; record and stay quiet.
    if not seen:
        Path(ALERT_STATE).write_text(json.dumps([a["id"] for a in alerts if a.get("id")]),
                                     encoding="utf-8")
        return 0, "primed state (%d existing alerts suppressed)" % len(fresh)
    sent = 0
    for a in fresh[:MAX_PUSH]:
        body = json.dumps({"text": _alert_line(a)}).encode("utf-8")
        req = urllib.request.Request(hook, data=body,
                                     headers={"Content-Type": "application/json"})
        try:
            urllib.request.urlopen(req, timeout=10).read()
            seen.add(a["id"])
            sent += 1
        except Exception as e:
            print("WARN: slack post failed: %s" % str(e)[:160])
            break
    if len(fresh) > MAX_PUSH:
        print("NOTE: %d alert(s) held back this tick (MAX_PUSH=%d)"
              % (len(fresh) - MAX_PUSH, MAX_PUSH))
    Path(ALERT_STATE).write_text(json.dumps(sorted(seen)[-500:]), encoding="utf-8")
    return sent, "ok"

def main():
    rev2user = rev_user_map()
    new_ct, edt_ct = case_time_index()
    targets = load_targets()
    events = sync_sessions(new_ct, edt_ct)
    alerts = compute_silence_alerts() + compute_alerts(rev2user, targets)
    payload = {"generated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
               "count": len(events), "events": events, "alerts": alerts}
    Path(OUT).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    nsil = sum(1 for a in alerts if a["type"] == "silence")
    sent, how = push_alerts(alerts)
    print("wrote %s (%d sessions: %d w/new, %d w/edited; %d alerts incl. %d silence) "
          "| pushed %d (%s)"
          % (OUT, len(events), sum(1 for e in events if e["total_new"] > 0),
             sum(1 for e in events if e["total_edited"] > 0), len(alerts), nsil, sent, how))


if __name__ == "__main__":
    main()
