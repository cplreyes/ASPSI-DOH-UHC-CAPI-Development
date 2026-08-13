#!/usr/bin/env python3
"""Emit the two hub source-of-truth CSVs from the already-generated pretest pack.

Reads (does NOT regenerate — CSWeb is already seeded with these passwords):
  pretest-users.csv        -> CSWeb usernames (se-001..se-007)
  pretest-credentials.md   -> the hub role-menu passwords
  pretest-assignments.csv  -> the EA rows

Writes:
  ../../data/roster/roster-source.csv        (username,password,role,operator_id,cluster,supervisor_id)
  ../../data/assignments/assignments-source.csv (ea_facility_code,enumerator_id,instrument,target_count,ea_name,cluster)

Role model (Aidan, 2026-07-14): "Si Ate Ai Almendral po kase yung field manager,
the rest po ng RAs ay field enumerators for this pretest po."
  se-001 AAlmendral -> supervisor  (assign / collect / relay + conducts interviews:
                                    the supervisor menu's open_f1/f3/f4 are the SAME
                                    action keys the enumerator menu uses)
  se-002..se-007    -> enumerator  (supervised by se-001)
"""
from __future__ import annotations
import csv, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent.parent / "data"
CLUSTER = "04034"          # Laguna — spans Los Banos (040341) + Bay (040340)
SUPERVISOR = "se-001"      # AAlmendral, field manager

# --- hub passwords (from the generated credential sheet) ----------------------
md = (HERE / "pretest-credentials.md").read_text(encoding="utf-8")
hub_tbl = md.split("Hub login password")[1]
hub_pw = dict(re.findall(r"\|\s*(\w+)\s*\|\s*`([^`]+)`\s*\|", hub_tbl))   # short_name -> pw

users = list(csv.DictReader((HERE / "pretest-users.csv").open(encoding="utf-8")))
short_of = {  # username -> the short name used in the credential sheet
    "se-001": "AAlmendral", "se-002": "AParaiso", "se-003": "ASalazar",
    "se-004": "DRamos", "se-005": "KPura", "se-006": "SLait", "se-007": "PCrudo",
}

# --- roster -------------------------------------------------------------------
roster_dir = DATA / "roster"; roster_dir.mkdir(parents=True, exist_ok=True)
with (roster_dir / "roster-source.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["username", "password", "role", "operator_id", "cluster", "supervisor_id"])
    for u in users:
        un = u["username"]
        role = "supervisor" if un == SUPERVISOR else "enumerator"
        sup = "" if un == SUPERVISOR else SUPERVISOR
        w.writerow([un, hub_pw[short_of[un]], role, un, CLUSTER, sup])

# --- assignments (6-col shape the hub reads) ----------------------------------
asg_dir = DATA / "assignments"; asg_dir.mkdir(parents=True, exist_ok=True)
src = list(csv.DictReader((HERE / "pretest-assignments.csv").open(encoding="utf-8")))
with (asg_dir / "assignments-source.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["ea_facility_code", "enumerator_id", "instrument", "target_count", "ea_name", "cluster"])
    for r in src:
        w.writerow([r["facility_code"], r["enumerator_id"], r["instrument"],
                    r["target_count"], r["ea_name"], r["cluster"]])

# --- sanity: no enumerator may hold two rows for the same EA -------------------
# ASSIGNMENT_DICT is keyed by AS_FACILITY_CODE with occurrences.maximum=1, and is
# mapped to the enumerator's OWN MyAssignment.dat -> duplicate EA codes within one
# enumerator's file would collide.
seen, dupes = set(), []
for r in src:
    k = (r["enumerator_id"], r["facility_code"])
    if k in seen:
        dupes.append(k)
    seen.add(k)

print(f"roster-source.csv      : {len(users)} users "
      f"(1 supervisor + {len(users)-1} enumerators)")
print(f"assignments-source.csv : {len(src)} EA rows")
print(f"dup (enumerator, EA)   : {len(dupes)} {'OK' if not dupes else dupes}")
