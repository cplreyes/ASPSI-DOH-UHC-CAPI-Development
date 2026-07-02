"""Coverage vs plan, per (instrument, facility). Enumerator id comes from the assignment."""
from dataclasses import dataclass


@dataclass
class CoverageRow:
    instrument: str
    facility: str
    enumerator_id: str
    done: int
    partial: int
    target: int
    remaining: int
    behind: bool


def compute_coverage(cases, assignments):
    agg = {}   # (instrument, facility) -> [done, partial]
    for c in cases:
        d = agg.setdefault((c.instrument, c.facility), [0, 0])
        if c.disposition == "complete":
            d[0] += 1
        else:
            d[1] += 1
    # include assigned facilities even with zero cases synced
    keys = set(agg) | set(assignments)
    rows = []
    for k in sorted(keys):
        inst, fac = k
        done, partial = agg.get(k, [0, 0])
        a = assignments.get(k)
        target = a.target if a else 0
        rows.append(CoverageRow(
            instrument=inst, facility=fac,
            enumerator_id=a.enumerator_id if a else "(unassigned)",
            done=done, partial=partial, target=target,
            remaining=max(target - done, 0), behind=done < target))
    return rows
