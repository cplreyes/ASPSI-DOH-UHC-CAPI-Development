#!/usr/bin/env python3
"""Pretest credential + assignment pack — built from Aidan's live schedule doc (2026-07-14).

Sources of truth:
  * Enumerators + per-day role assignments + targets: Aidan's Google Doc (pretest schedule).
  * Municipality PSGC: deliverables/CSPro/data/psgc/psgc_city_municipality.csv.

KEY CORRECTION vs the 2026-07-01 QN list: Laguna Provincial Hospital is in **BAY**
(Aidan's doc: "LPH-Bay District Hospital · Location: Bay, Laguna"), NOT Los Baños.
  Bay        = 0403402000  -> EA prefix 0403402
  Los Baños  = 0403411000  -> EA prefix 0403411
The first 7 digits of a 12-digit case key ARE the municipality and are geo-validated
on the tablet, so LPH is re-coded 040341120 -> **040340220**.

Targets also follow Aidan's doc (5 patients per facility), NOT the July-1 list (10).

Writes:
  pretest-users.csv        -> CSWeb Users dashboard bulk import
  pretest-credentials.md   -> the table to paste into Aidan's doc
  pretest-assignments.csv  -> input for generate_assignments.py
"""
from __future__ import annotations
import csv, secrets, string
from pathlib import Path

HERE = Path(__file__).resolve().parent

# --- enumerators (Aidan's doc order) -----------------------------------------
ENUMS = [
    ("se-001", "AAlmendral", "A.",  "Almendral"),
    ("se-002", "AParaiso",   "A.",  "Paraiso"),
    ("se-003", "ASalazar",   "A.",  "Salazar"),
    ("se-004", "DRamos",     "D.",  "Ramos"),
    ("se-005", "KPura",      "K.",  "Pura"),
    ("se-006", "SLait",      "S.",  "Lait"),
    ("se-007", "PCrudo",     "P.",  "Crudo"),
]
BY_SHORT = {short: uid for uid, short, _, _ in ENUMS}

# --- enumeration areas --------------------------------------------------------
# 9-digit EA code = 7-digit municipality PSGC + 2-digit facility/EA serial.
EAS = {
    "MAYONDON": ("040341101", "Brgy. Mayondon - Household",        "040341"),
    "LPH":      ("040340210", "LPH-Bay District Hospital",         "040340"),  # <-- BAY; serial 10 per ASPSI's issued QN docx (was 20, self-derived)
    "LBRHU":    ("040341130", "Los Banos RHU",                     "040341"),
}

# --- assignments: (ea, enumerator short, instrument, first_seq, last_seq) -----
# Facility-head keys are the ...000 key (CSPro convention). Patients start at 001.
ASSIGN = [
    # DAY 1 - Mayondon households, Jul 15 - 20 HH split across 6 enumerators
    ("MAYONDON", "DRamos",    "F4", 1,  3),
    ("MAYONDON", "SLait",     "F4", 4,  6),
    ("MAYONDON", "ASalazar",  "F4", 7,  9),
    ("MAYONDON", "PCrudo",    "F4", 10, 12),
    ("MAYONDON", "AParaiso",  "F4", 13, 15),
    ("MAYONDON", "KPura",     "F4", 16, 18),
    ("MAYONDON", "AAlmendral","F4", 19, 20),

    # DAY 2 - LPH-Bay, Jul 16-17 - 1 facility head + 5 patients (3 IP + 2 OP)
    ("LPH", "KPura",    "F1", 0, 0),    # Facility Head
    ("LPH", "ASalazar", "F3", 1, 2),    # Inpatient x2
    ("LPH", "PCrudo",   "F3", 3, 3),    # Inpatient x1
    ("LPH", "DRamos",   "F3", 4, 4),    # Outpatient x1
    ("LPH", "SLait",    "F3", 5, 5),    # Outpatient x1

    # DAY 3 - Los Banos RHU, Jul 17 - 1 facility head + 5 outpatients
    ("LBRHU", "AParaiso", "F1", 0, 0),  # Facility Head
    ("LBRHU", "SLait",    "F3", 1, 2),  # Outpatient x2
    ("LBRHU", "ASalazar", "F3", 3, 3),
    ("LBRHU", "PCrudo",   "F3", 4, 4),
    ("LBRHU", "AAlmendral","F3", 5, 5),
]

ALPHABET = string.ascii_letters + string.digits
# Typable on a tablet keyboard, no visually-ambiguous glyphs (0/O, 1/l/I).
TYPABLE = "abcdefghjkmnpqrstuvwxyz23456789"


def strong_pw(n: int = 14) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(n))


def hub_pw(n: int = 8) -> str:
    """Hub role-menu password — typed at every app open, so keep it short and
    unambiguous, but still CSPRNG-random. NEVER derive it from the username:
    the roster ships inside the app package, and a username-derived password is
    guessable by anyone who can read the app list."""
    return "".join(secrets.choice(TYPABLE) for _ in range(n))


# ---------------------------------------------------------------- credentials
def existing_passwords():
    """Passwords already issued -> REUSE them.

    Every run used to mint fresh secrets. Once credentials have been handed to a
    field team, re-running to fix an unrelated code would silently rotate every
    password and lock all seven enumerators out, with nothing in the output to
    say so. Read back what was issued and keep it; only mint for new people.
    """
    out = {}
    f = HERE / "pretest-users.csv"
    if f.exists():
        with f.open(newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                if r.get("username") and r.get("password"):
                    out[r["username"]] = r["password"]
    hub = {}
    m = HERE / "pretest-credentials.md"
    if m.exists():
        rows = [l for l in m.read_text(encoding="utf-8").splitlines()
                if l.startswith("|") and "`" in l]
        for line in rows:
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) == 2 and cells[1].startswith("`"):   # hub table: | name | `pw` |
                hub[cells[0]] = cells[1].strip("`")
    return out, hub


_pw, _hub = existing_passwords()
if _pw:
    print("  reusing %d already-issued CSWeb password(s) - NOT rotating" % len(_pw))

creds = []
for uid, short, first, last in ENUMS:
    creds.append({
        "enumerator": short,
        "username": uid,
        "csweb_pw": _pw.get(uid) or strong_pw(),
        "hub_pw": _hub.get(short) or hub_pw(),   # random; typed at every hub login
        "first": first, "last": last,
    })

with (HERE / "pretest-users.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["username", "first name", "last name", "user role", "password", "email", "phone"])
    for c in creds:
        w.writerow([c["username"], c["first"], c["last"], "Field Sync", c["csweb_pw"], "", ""])

# ---------------------------------------------------------------- assignments
rows = []
for ea_key, short, instr, lo, hi in ASSIGN:
    fac, ea_name, cluster = EAS[ea_key]
    rows.append({
        "facility_code": fac,
        "enumerator_id": BY_SHORT[short],
        "enumerator_name": short,
        "instrument": instr,
        "target_count": hi - lo + 1,
        "ea_name": ea_name,
        "cluster": cluster,
        "first_case_key": f"{fac}{lo:03d}",
        "last_case_key": f"{fac}{hi:03d}",
    })

cols = ["facility_code", "enumerator_id", "enumerator_name", "instrument",
        "target_count", "ea_name", "cluster", "first_case_key", "last_case_key"]
with (HERE / "pretest-assignments.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)

# ---------------------------------------------------------------- doc tables
lines = ["# Pretest credentials + assigned codes (generated 2026-07-14)", "",
         "## Enum_Credentials", "",
         "| Enumerator Name | Username | Password |", "| --- | --- | --- |"]
for c in creds:
    lines.append(f"| {c['enumerator']} | `{c['username']}` | `{c['csweb_pw']}` |")
lines += ["", "> Username + Password above = the **CSWeb login** (install the app + sync).",
          "> Each enumerator also has a **hub login** used every time the app opens:", ""]
lines += ["| Enumerator | Hub login password |", "| --- | --- |"]
for c in creds:
    lines.append(f"| {c['enumerator']} | `{c['hub_pw']}` |")

day = {"MAYONDON": "D1_Mayondon_July15", "LPH": "D2_LPH_July16-17", "LBRHU": "D3_LB RHU_July17"}
for ea_key in ("MAYONDON", "LPH", "LBRHU"):
    fac, ea_name, _ = EAS[ea_key]
    lines += ["", f"## {day[ea_key]} — assigned codes", "",
              f"**EA code {fac}** — {ea_name}", "",
              "| For Interview | Enumerator | Instrument | Assigned Codes | N |",
              "| --- | --- | --- | --- | --- |"]
    for ea2, short, instr, lo, hi in ASSIGN:
        if ea2 != ea_key:
            continue
        role = {"F1": "Facility Head", "F3": "Patient", "F4": "Household"}[instr]
        keys = f"`{fac}{lo:03d}`" if lo == hi else f"`{fac}{lo:03d}` – `{fac}{hi:03d}`"
        lines.append(f"| {role} | {short} | {instr} | {keys} | {hi-lo+1} |")

(HERE / "pretest-credentials.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

print(f"enumerators : {len(creds)}")
print(f"assignments : {len(rows)} rows")
print(f"total keys  : {sum(r['target_count'] for r in rows)}")
print()
for ea_key in ("MAYONDON", "LPH", "LBRHU"):
    fac, name, _ = EAS[ea_key]
    n = sum(r["target_count"] for r in rows if r["facility_code"] == fac)
    print(f"  {fac}  {name:<34} {n:>3} cases")
print()
print("wrote: pretest-users.csv · pretest-assignments.csv · pretest-credentials.md")
