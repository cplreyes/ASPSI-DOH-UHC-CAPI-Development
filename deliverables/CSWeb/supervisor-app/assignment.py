"""Load the supervisor-maintained assignment/target lookup (the coverage 'plan')."""
import csv
from dataclasses import dataclass


@dataclass
class Assignment:
    enumerator_id: str
    facility: str
    instrument: str
    target: int


def load_assignments(csv_path):
    out = {}
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            inst = (row.get("INSTRUMENT") or "").strip()
            fac = (row.get("FACILITY_CODE") or "").strip()
            try:
                target = int((row.get("TARGET_COUNT") or "0").strip())
            except ValueError:
                target = 0
            out[(inst, fac)] = Assignment(
                enumerator_id=(row.get("ENUMERATOR_ID") or "").strip(),
                facility=fac, instrument=inst, target=target)
    return out
