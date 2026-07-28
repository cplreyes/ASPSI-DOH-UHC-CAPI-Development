# -*- coding: utf-8 -*-
"""phase_lib.py -- single source of truth for activity-phase classification.

Carl, 2026-07-27: pretest stays the open reference phase until its close is
DECLARED; August training and the survey proper must never mix into it. Every
reporting generator imports this one helper so a case is classified the same
way on every surface (dashboard, exports, overview, tabulations).

Rule (Option C, hybrid): the uploading CSWeb login wins if it appears in a
phase roster; otherwise the case falls back to the date windows (F2, which has
no logins, always classifies by date). Declaring a phase transition = editing
/opt/phases.json -- no code change, no tablet change.

phases.json shape:
{
  "phases": [
    {"name": "pretest",  "from": "2026-07-15", "to": null,
     "logins": ["se-001", ...]},
    {"name": "training", "from": null, "to": null, "logins": []},
    {"name": "survey",   "from": null, "to": null, "logins": []}
  ]
}
"from"/"to" are inclusive Manila dates (YYYY-MM-DD); null "to" = open-ended;
null "from" = phase not started. Order matters: first matching window wins.
"""
import json

REGISTRY = "/opt/phases.json"
UNKNOWN = "unphased"


def load(path=REGISTRY):
    # Survey Activities (2026-07-27): when activities.json exists it is the
    # SSOT -- derive the coarse phase buckets from it (union of rosters,
    # min start / max end per phase; any open activity keeps the phase open)
    # so every existing phase consumer works unchanged.
    if path == REGISTRY:
        try:
            import activity_lib
            acts = activity_lib.load()
            if acts:
                order, buckets = [], {}
                for a in acts:
                    ph = a.get("phase")
                    if not ph:
                        continue
                    if ph not in buckets:
                        buckets[ph] = {"name": ph, "from": None, "to": None,
                                       "logins": [], "_ends": [], "_open": False}
                        order.append(ph)
                    b = buckets[ph]
                    if a.get("start") and (not b["from"] or a["start"] < b["from"]):
                        b["from"] = a["start"]
                    if a.get("start") and not a.get("end"):
                        b["_open"] = True
                    elif a.get("end"):
                        b["_ends"].append(a["end"])
                    b["logins"] += [x for x in (a.get("logins") or [])
                                    if x not in b["logins"]]
                out = []
                for ph in order:
                    b = buckets[ph]
                    b["to"] = None if (b.pop("_open") or not b["_ends"]) else max(b["_ends"])
                    b.pop("_ends")
                    out.append(b)
                return out
        except Exception:
            pass
    try:
        return json.load(open(path, encoding="utf-8")).get("phases") or []
    except Exception:
        return []


def phase_names(reg=None):
    return [p["name"] for p in (reg if reg is not None else load())]


def _in_window(p, day):
    lo, hi = p.get("from"), p.get("to")
    if not lo:
        return False
    return day >= lo and (not hi or day <= hi)


def phase_of(login=None, day=None, reg=None):
    """Classify one case. `login` = uploading CSWeb account (or None, e.g. F2);
    `day` = Manila date 'YYYY-MM-DD' (sync date preferred, visit date as
    fallback). Roster membership wins; date window falls back."""
    reg = reg if reg is not None else load()
    if login:
        for p in reg:
            if login in (p.get("logins") or []):
                return p["name"]
    if day:
        for p in reg:
            if _in_window(p, day):
                return p["name"]
    return UNKNOWN
