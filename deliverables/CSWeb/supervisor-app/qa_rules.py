"""Five data-quality rules over normalized Case records → a flag worklist (PII-light)."""
from dataclasses import dataclass
from datetime import date

# Withdraw / refusal result codes per instrument (consent refusal == these codes).
WITHDRAW_CODES = {"F1": {"3"}, "F3": {"6"}, "F4": {"4"}}   # F1 Refused=3; F3/F4 Withdraw
STUCK_DAYS = 2


@dataclass
class Flag:
    case_key: str
    facility: str
    rule: str
    detail: str


def _days_between(yyyymmdd, today):
    try:
        a = date(int(yyyymmdd[0:4]), int(yyyymmdd[4:6]), int(yyyymmdd[6:8]))
        b = date(int(today[0:4]), int(today[4:6]), int(today[6:8]))
        return (b - a).days
    except (ValueError, IndexError):
        return 0


def run_rules(cases, today):
    flags = []
    for c in cases:
        if not c.has_gps:
            flags.append(Flag(c.case_key, c.facility, "no_gps", "no GPS fix"))
        if c.disposition == "complete" and not c.has_photo:
            flags.append(Flag(c.case_key, c.facility, "no_photo_completed",
                              "Completed but no verification photo"))
        if c.disposition in ("partial", "in_progress") and c.final_visit_date \
                and _days_between(c.final_visit_date, today) > STUCK_DAYS:
            flags.append(Flag(c.case_key, c.facility, "stuck_partial",
                              f"partial > {STUCK_DAYS} days (last visit {c.final_visit_date})"))
        if c.disposition == "complete" and not c.answers_present:
            flags.append(Flag(c.case_key, c.facility, "disposition_mismatch",
                              "Completed but the opening question is blank"))
        if c.result_code in WITHDRAW_CODES.get(c.instrument, set()) and c.answers_present:
            flags.append(Flag(c.case_key, c.facility, "consent_contradiction",
                              "Withdraw/Refused but answers are present"))
    return flags
