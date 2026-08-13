# -*- coding: utf-8 -*-
"""activity_lib.py -- Survey Activities: named fieldwork periods with dates.

Carl, 2026-07-27 (full-scheduler decision, benchmark-backed): activities are
the concrete scheduled operations -- "Pretest", "Training of Trainers",
"Survey Wave 1" -- each with start/end dates, an optional login roster, and
optional per-instrument quotas. Every activity rolls up to one of the three
PHASE buckets (pretest/training/survey), so the phase system built on
2026-07-27 keeps working unchanged: phase_lib delegates here when
activities.json exists.

No CAPI platform benchmarked (Survey Solutions, SurveyCTO, ODK, Kobo, CSWeb)
has this concept; the DDI standard does (collDate start/end + cycle), and the
codebook emits each activity as a DDI collection event.

Classification rule (same hybrid as phases): roster login wins, date window
falls back. First matching activity in file order wins on overlap -- put the
more specific activity first.
"""
import json

# SSOT lives in the auth-gated admin dir so the Survey Activity Manager
# (docs/admin/index.php, admin logins only) can edit it; generators read the
# same file from the host side. Legacy /opt path kept as a read fallback.
REGISTRY = "/opt/app/lamp/www/docs/admin/activities-registry.json"
LEGACY = "/opt/activities.json"
UNKNOWN = "unassigned"


def load(path=REGISTRY):
    for p in (path, LEGACY) if path == REGISTRY else (path,):
        try:
            return json.load(open(p, encoding="utf-8")).get("activities") or []
        except Exception:
            continue
    return []


def _in_window(a, day):
    lo, hi = a.get("start"), a.get("end")
    if not lo:
        return False
    return day >= lo and (not hi or day <= hi)


def activity_of(login=None, day=None, reg=None):
    """-> activity id, or UNKNOWN. Roster wins; date window falls back."""
    reg = reg if reg is not None else load()
    if login:
        for a in reg:
            if login in (a.get("logins") or []):
                return a["id"]
    if day:
        for a in reg:
            if _in_window(a, day):
                return a["id"]
    return UNKNOWN


def by_id(reg=None):
    reg = reg if reg is not None else load()
    return {a["id"]: a for a in reg}


def phase_of_activity(act_id, reg=None):
    a = by_id(reg).get(act_id)
    return a.get("phase") if a else None


def public_view(reg=None):
    """The registry minus rosters -- safe for the public portal snapshot.
    Names, phases, kinds, dates and quotas are operational facts, not PII;
    login rosters never leave the box."""
    reg = reg if reg is not None else load()
    # "label" (not "name") in the public shape: the status generator's privacy
    # tripwire treats a bare "name" key as a potential person/facility leak,
    # and it should stay that strict.
    return [{"id": a.get("id"), "label": a.get("name"), "phase": a.get("phase"),
             "kind": a.get("kind"), "start": a.get("start"), "end": a.get("end"),
             "planned": a.get("planned"), "quotas": a.get("quotas") or {}}
            for a in reg]
