#!/usr/bin/env python3
"""aug21-overrides.json — keys the Aug-21 import must NOT replace.

Schema:  { "F1"|"F3"|"F4": { "<key>": { "keep": "<current text>"|null, "reason": "<why>",
                                          "locales": ["hil", ...] (optional) } },
           "F2": { "<loc>": { "<exact English>": { "keep": "<text>"|null, "reason": "<why>",
                                                     "scope": "consent"|"survey" (optional) } } } }
F1/F3/F4 keys are name-scoped (item:/vs:/val:, must contain ':') or the notes/ICF keys
note:<key>:<LOC> / icf:<p>:<i>:<LOC> (for which keep == "" means "render English").
keep == null means "never write this key", whether or not the map already holds it — the
only lever that reaches a key the map does not have yet (Task 16c).
An entry may instead carry "remove": true (locale-scopable): the key is
DELETED from the map on --apply, so the tablet renders the English label. Task 49: the
Aug-21 paper carries no distinct translation for a handful of option rows that inherited a
neighbouring row's text, and their pre-wave values are truncated fragments — an English
option label beats a wrong one, and "keep" cannot express that because it only ever writes.
A remove entry needs no "keep" and must not carry keep TEXT (one deletes the row, the other
writes it).
"keep" may also be a LOCALE-KEYED dict, {"ilo": "<text>", "ceb": "<text>"} (2026-08-27, #1335/#1338/#1343):
one key, a different reviewer text per locale - the same held stem needs its own composition in
each paper. The dict IS the scope (no "locales" list with it); every value is keep text or null
and applies exactly as a plain keep would in that locale. "force" applies to every listed locale.
An entry with keep TEXT may also carry "force": true (2026-08-27, #1331/#1332): the text is
written even when the key is neither flagged nor absent - the extract proposes one value and
the map holds another (or the same) and BOTH are wrong. Without it, keep text on such a key
only ever means "hold the current value" (a drifted keep is reported stale, never written).
A reviewer ruling, so it needs keep text (never null, never with remove) and a reason.
The optional "locales" list scopes an entry to a subset of the seven maps (Task 17 fix
round 1). Without it an entry governs all seven, which is right when the defect is in the
key (a value-set offset the English label shares), and wrong when the defect is in ONE
paper (one translator's typo on a key whose other six locales are correct) — holding such a
key for all seven suppresses the correct writes too. Locale codes are the map basenames.
F2 keys are the flat exact-English strings the PWA store uses, nested by locale; keep null
means "never write this key", and "remove": true means the same as it does for F1/F3/F4 --
apply-paper-translations.py DELETES the key from that one locale map so the English option
renders (Task 51 fix round 1; the F2 block is already locale-nested, so no "locales" list is
needed, and --retire stays the all-seven-maps lever it always was). The optional "scope" field ("consent" | "survey") lets Tasks
21/22 target the ICF-consent flow separately from the survey-body flow. Every entry needs a
non-empty reason — an override without a reason is a silent defect carrier.
"""
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OVERRIDES_PATH = os.path.join(HERE, "aug21-overrides.json")
INSTRUMENTS = ("F1", "F3", "F4", "F2")
F2_SCOPES = ("consent", "survey")
LOCALES = ("fil", "bcl", "bis", "ceb", "war", "hil", "ilo")


def _check_reason(errs, where, ent):
    if not isinstance(ent.get("reason"), str) or not ent.get("reason", "").strip():
        errs.append(f"{where}: 'reason' must be a non-empty string")


def _check_locales(errs, where, ent):
    """Optional "locales" list: the entry governs only these maps. Validated strictly —
    a typo'd or empty list would silently widen or void the hold it was written to express."""
    if "locales" not in ent:
        return
    locs = ent["locales"]
    if not isinstance(locs, list) or not locs:
        errs.append(f"{where}: 'locales' must be a non-empty list of locale codes")
        return
    for loc in locs:
        if not isinstance(loc, str) or loc not in LOCALES:
            errs.append(f"{where}: 'locales' entry {loc!r} is not a known locale")
    if len(set(locs)) != len(locs):
        errs.append(f"{where}: 'locales' has duplicate entries")


def validate_overrides(data):
    errs = []
    if not isinstance(data, dict):
        return ["top level must be an object keyed by instrument"]
    for inst, block in data.items():
        if inst.startswith("_"):
            continue                       # _readme / _seeded provenance blocks
        if inst not in INSTRUMENTS:
            errs.append(f"{inst}: unknown instrument")   # no INSTRUMENTS echo: keeps prefix-matching clean
            continue
        if not isinstance(block, dict):
            errs.append(f"{inst}: block must be an object keyed by translation key")
            continue
        if inst == "F2":
            # locale-nested: {loc: {English: {keep: str|null, reason, scope?}}} (apply-paper-translations.py)
            for loc, sub in block.items():
                if not isinstance(sub, dict):
                    errs.append(f"{inst}/{loc!r}: locale block must be an object keyed by English string")
                    continue
                for key, ent in sub.items():
                    if not isinstance(ent, dict):
                        errs.append(f"{inst}/{loc}/{key!r}: entry must be an object with keep + reason")
                        continue
                    removing = "remove" in ent             # Task 51 fix round 1
                    if removing:
                        if ent["remove"] is not True:
                            errs.append(f"{inst}/{loc}/{key!r}: 'remove' must be true "
                                        f"(omit the field to keep the row)")
                        if isinstance(ent.get("keep"), str):
                            errs.append(f"{inst}/{loc}/{key!r}: an entry cannot carry both "
                                        f"'remove' and 'keep' text - one deletes the row, "
                                        f"the other writes it")
                    if "keep" not in ent and not removing:
                        errs.append(f"{inst}/{loc}/{key!r}: entry must name 'keep' "
                                    f"(use null to mean never write)")
                    elif "keep" in ent and not (ent["keep"] is None or isinstance(ent["keep"], str)):
                        errs.append(f"{inst}/{loc}/{key!r}: 'keep' must be a string or null")
                    if "scope" in ent and ent.get("scope") not in F2_SCOPES:
                        errs.append(f"{inst}/{loc}/{key!r}: 'scope' must be one of {F2_SCOPES}")
                    _check_reason(errs, f"{inst}/{loc}/{key!r}", ent)
            continue
        for key, ent in block.items():
            if ":" not in key:
                errs.append(f"{inst}/{key!r}: CSPro override key must be name-scoped (contain ':')")
            if not isinstance(ent, dict):
                errs.append(f"{inst}/{key!r}: entry must be an object with keep + reason")
                continue
            removing = "remove" in ent                      # Task 49: delete the key
            if removing:
                if ent["remove"] is not True:
                    errs.append(f"{inst}/{key!r}: 'remove' must be true "
                                f"(omit the field to keep the row)")
                if isinstance(ent.get("keep"), str):
                    errs.append(f"{inst}/{key!r}: an entry cannot carry both 'remove' and "
                                f"'keep' text - one deletes the row, the other writes it")
            if "force" in ent:                              # 2026-08-27 (#1331/#1332)
                if ent["force"] is not True:
                    errs.append(f"{inst}/{key!r}: 'force' must be true (omit the field otherwise)")
                if removing or not (isinstance(ent.get("keep"), (str, dict)) and ent["keep"]):
                    errs.append(f"{inst}/{key!r}: 'force' needs 'keep' text - it writes that text "
                                f"on a key the extract and the map both hold (differently)")
            empty_ok = key.startswith(("note:", "icf:"))     # "" = render English (Tasks 8/10)
            # Task 16c: null = "never write this key", new or existing - the only lever
            # that can hold back a defective value on a key the map does not have yet.
            # The field must still be PRESENT: a typo'd or omitted `keep` would otherwise
            # read as null and silently suppress the import instead of failing the gate.
            if "keep" not in ent and not removing:
                errs.append(f"{inst}/{key!r}: entry must name 'keep' "
                            f"(use null to mean never write)")
                _check_locales(errs, f"{inst}/{key!r}", ent)
                _check_reason(errs, f"{inst}/{key!r}", ent)
                continue
            keep = ent.get("keep")
            if isinstance(keep, dict):                     # 2026-08-27: locale-keyed keep
                if not keep:
                    errs.append(f"{inst}/{key!r}: locale-keyed 'keep' must not be empty")
                if "locales" in ent:
                    errs.append(f"{inst}/{key!r}: a locale-keyed 'keep' is its own scope - drop 'locales'")
                if removing:
                    errs.append(f"{inst}/{key!r}: an entry cannot carry both 'remove' and a locale-keyed 'keep'")
                for lc, txt in keep.items():
                    if lc not in LOCALES:
                        errs.append(f"{inst}/{key!r}: 'keep' locale {lc!r} is not a known locale")
                    if txt is not None and (not isinstance(txt, str) or (not txt.strip() and not empty_ok)):
                        errs.append(f"{inst}/{key!r}: 'keep'[{lc!r}] must be a non-empty string or null")
                if "force" in ent and not all(isinstance(t, str) and t.strip() for t in keep.values()):
                    errs.append(f"{inst}/{key!r}: 'force' needs keep text in every listed locale")
                _check_reason(errs, f"{inst}/{key!r}", ent)
                continue
            if keep is not None and (not isinstance(keep, str)
                                     or (not keep.strip() and not empty_ok)):
                errs.append(f"{inst}/{key!r}: 'keep' must be a non-empty string or null")
            _check_locales(errs, f"{inst}/{key!r}", ent)
            _check_reason(errs, f"{inst}/{key!r}", ent)
    return errs


def load_overrides(path=OVERRIDES_PATH):
    if not os.path.exists(path):
        return {}
    data = json.loads(io.open(path, encoding="utf-8").read())
    errs = validate_overrides(data)
    if errs:
        raise SystemExit("aug21-overrides.json invalid:\n  " + "\n  ".join(errs))
    return {k: v for k, v in data.items() if not k.startswith("_")}


if __name__ == "__main__":
    errs = validate_overrides(json.loads(io.open(OVERRIDES_PATH, encoding="utf-8").read()))
    print("OK" if not errs else "\n".join(errs))
    raise SystemExit(1 if errs else 0)
