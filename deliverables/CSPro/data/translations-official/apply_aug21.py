#!/usr/bin/env python3
r"""Merge the Aug-21 paper extract into the name-scoped translation maps.

Rule per extracted (key, translation):
    key listed with "keep": null      -> NEVER written, new or existing (count OVERRIDE)
    key listed with "remove": true    -> DELETED from the map on --apply (count REMOVED), so
        the English label renders. Task 49: the only honest outcome for an option row the
        paper never translated distinctly and whose pre-wave value is a fragment. Replayable
        by construction - a second run finds the key gone and removes nothing.
    an override entry carrying "locales": [...] governs ONLY those locales; every other
        locale merges as if the entry were absent (Task 17 fix round 1)
    key absent in map                 -> WRITE
        ... unless key is listed in aug21-overrides.json -> write the "keep" text instead
    present and norm-equal            -> already_same
    present and different             -> REPLACE  (Aug-21 wins)
        ... unless key is listed in aug21-overrides.json -> keep current, count OVERRIDE
    key appears in {loc}_flagged.json -> never written (flagged_skipped)
        ... unless the key carries a "keep": "<text>" override -> that TEXT is written
            (count OVERRIDE): accepting a flagged span is an override, never a hand-copy
    "keep" may be locale-keyed ({"ilo": text, "ceb": text}): the entry governs exactly those
        locales, each with its own text (2026-08-27, #1335/#1338/#1343)
    key listed with "force": true     -> the "keep" text is written even when the key is neither
        flagged nor absent (extract and map both hold a wrong value; #1331/#1332, 2026-08-27).
        Replayable: a second run finds keep == current and counts already_same.
_meta is never a write target; _meta.sources.aug21 is stamped on --apply when something was written.

    python apply_aug21.py                      # dry run (default): per-locale table; touches NOTHING
    python apply_aug21.py --apply              # write the maps + _meta.sources.aug21
    python apply_aug21.py --apply --only F1
    python apply_aug21.py --only F3 --extract C:/path/to/out   # extractor out dir override
    python apply_aug21.py --only F3 --unmatched               # + dcf-unanchored column (reads the BUILT .dcf, no generator run)
    python apply_aug21.py --only F3 --seed findings.json      # candidate override rows
    python apply_aug21.py --only F1 --apply --maps-dir out-aug21/rehearsal/F1  # rehearse on a COPY
    python apply_aug21.py --only F4 --fail-on-pre              # STRICT duplicate-label gate (Tasks 49/50)
    python apply_aug21.py --compare-findings pre.json post.json   # scan_poisoned_keys per-reason delta gate

Exit code 2 means the duplicate-label gate BLOCKED - apply or dry run, nothing was written
and the last line reads BLOCKED. Every other run exits 0.

Post-apply, every wave runs run_aug21_gates.ps1 (scan per-reason delta + bridge_check B/C delta).
"""
import argparse
import datetime as _dt
import io
import json
import os
import re
import sys
from collections import Counter, OrderedDict, defaultdict
from dataclasses import dataclass, field

HERE = os.path.dirname(os.path.abspath(__file__))
CSPRO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, CSPRO)
sys.path.insert(0, HERE)
from apply_safe import norm, load_map, save_map          # noqa: E402
from aug21_overrides import load_overrides, OVERRIDES_PATH  # noqa: E402

if hasattr(sys.stdout, "buffer") and (sys.stdout.encoding or "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)

LOCALES = ["fil", "bcl", "bis", "ceb", "war", "hil", "ilo"]
CSPRO_INSTRUMENTS = ("F1", "F3", "F4")
DCF_FILE = {"F1": "FacilityHeadSurvey.dcf", "F3": "PatientSurvey.dcf", "F4": "HouseholdSurvey.dcf"}
EXTRACT_ROOT = os.path.join(HERE, "out-aug21")      # anchor_extract.py --out root (Task 1)


@dataclass
class MergeResult:
    writes: "OrderedDict" = field(default_factory=OrderedDict)
    replaced: list = field(default_factory=list)      # (key, old, new)
    overridden: list = field(default_factory=list)    # (key, current, proposed)
    removes: list = field(default_factory=list)        # keys `remove: true` deletes
    flagged_skipped: int = 0
    already_same: int = 0
    unmatched: list = field(default_factory=list)     # printed as `dcf-unanchored`:
    # BUILT-dcf keys the extract produced nothing for. Informational, never a STOP.
    override_stale: list = field(default_factory=list)


def override_for(overrides, key, loc):
    """The override entry that governs `key` in locale `loc`, or None.

    An entry may carry an optional `"locales": [...]` list (Task 17 fix round 1). When it
    does, the entry governs ONLY those locales and every other locale merges normally - the
    lever a key-scoped-only block did not have. The 19 HIL rows of one paper's stutter had to
    be held without also suppressing the 95 correct writes the same 19 keys carry in the other
    six locales; a key-scoped `keep: null` could only do both or neither.
    An entry with no `locales` list still governs every locale, so every existing row keeps
    its meaning.
    """
    ov = overrides.get(key)
    if ov is None:
        return None
    locs = ov.get("locales")
    if locs and loc is not None and loc not in locs:
        return None
    keep = ov.get("keep")
    if isinstance(keep, dict):                 # 2026-08-27: locale-keyed keep = its own scope
        if loc is None or loc not in keep:
            return None
        ov = dict(ov, keep=keep[loc])
    return ov


def merge_locale(current, pairs, flagged_keys, overrides, all_keys=None, loc=None):
    r = MergeResult()
    seen = set()
    for key, tr in pairs.items():
        if key == "_meta" or ":" not in key:
            continue
        val = norm(tr)
        if not val:
            continue
        seen.add(key)
        cur = current.get(key)
        ov = override_for(overrides, key, loc)
        if ov is not None and ov.get("remove"):
            continue                     # counted once, by the removal pass below
        keep = ov.get("keep") if ov is not None else None
        # Task 16c (fix round 1): overrides are consulted BEFORE the flagged check too.
        # The plan's conflicts rule says accepted flagged spans are expressed as overrides,
        # never hand-copied - so a `keep: "<text>"` on a flagged key must WRITE that text.
        # `keep: null` still never writes; no override at all still skips the flagged key.
        # 2026-08-27 (#1331/#1332): "force": true is the reviewer ruling for a key that is
        # neither flagged nor absent - the extract proposes one value, the map holds another
        # (or the same) and both are wrong ('San a amo' for the paper's 'Saan ko nga ammo').
        # Plain keep text on such a key only ever holds the current value; force writes it.
        if ov is not None and ov.get("force") and norm(keep):
            if cur is not None and norm(cur) == norm(keep):
                r.already_same += 1
            else:
                r.writes[key] = norm(keep)
            r.overridden.append((key, cur, val))
            continue
        if key in flagged_keys:
            if ov is not None and keep is not None and norm(keep):
                if cur is not None and norm(cur) == norm(keep):
                    r.already_same += 1
                else:
                    r.writes[key] = norm(keep)
                r.overridden.append((key, cur, val))
            else:
                r.flagged_skipped += 1
            continue
        # Task 16c: overrides are consulted BEFORE the "key absent -> write" branch.
        # 79 of the 249 defective values Task 17 measured were keys the map does not hold
        # yet, and this function used to reach `r.writes[key] = val` without ever looking
        # at aug21-overrides.json - so there was no lever to hold them back at all.
        if ov is not None and keep is None:
            r.overridden.append((key, cur, val))   # `keep: null` = never write, new or not
            continue
        if cur is None:
            if ov is not None:                     # `keep: "<text>"` on a key the map does
                if norm(keep):                     # not have names the text to write
                    r.writes[key] = norm(keep)
                r.overridden.append((key, cur, val))
                continue
            r.writes[key] = val
            continue
        if norm(cur) == val:
            r.already_same += 1
            if ov is not None and norm(keep) != norm(cur):
                r.override_stale.append(key)
            continue
        if ov is not None:
            r.overridden.append((key, cur, val))
            if norm(keep) != norm(cur):
                r.override_stale.append(key)
            continue
        r.replaced.append((key, cur, val))
        r.writes[key] = val
    # <loc>.json and <loc>_flagged.json are disjoint (anchor_extract writes a key to one or
    # the other), so THIS is where a flagged key normally lands. Same rule as above: a
    # `keep: "<text>"` override is how a reviewer accepts a flagged span (never by hand-copy).
    for key in flagged_keys:
        if key in pairs:
            continue
        ov = override_for(overrides, key, loc)
        if ov is not None and ov.get("remove"):
            continue                     # counted once, by the removal pass below
        keep = ov.get("keep") if ov is not None else None
        if ov is not None and keep is not None and norm(keep):
            cur = current.get(key)
            if cur is not None and norm(cur) == norm(keep):
                r.already_same += 1
            else:
                r.writes[key] = norm(keep)
            r.overridden.append((key, cur, None))   # no Aug-21 proposal: the span was flagged
        else:
            r.flagged_skipped += 1
    # force on a key the extract is silent about (neither proposed nor flagged): still written.
    for key in overrides:
        ov = override_for(overrides, key, loc)
        if ov is None or not ov.get("force") or key in seen or key in flagged_keys:
            continue
        keep = norm(ov.get("keep") or "")
        if not keep:
            continue
        cur = current.get(key)
        if cur is not None and norm(cur) == keep:
            r.already_same += 1
        else:
            r.writes[key] = keep
        r.overridden.append((key, cur, None))
        seen.add(key)
    seen |= set(flagged_keys)
    # Task 49: the removal pass runs over the OVERRIDES, not over the extract, because a row
    # the paper stopped anchoring is still on the tablet - removal is about the MAP. A key
    # the map does not hold removes nothing, which is what makes a replay a no-op.
    for key in overrides:
        ov = override_for(overrides, key, loc)
        if ov is None or not ov.get("remove"):
            continue
        if key != "_meta" and key in current:
            r.removes.append(key)
    if all_keys is not None:
        r.unmatched = sorted(k for k in all_keys if k not in seen)
    return r


EXCLUSIONS_PATH = os.path.join(HERE, "recovery_exclusions.json")
OFFICIAL_PATH = os.path.join(HERE, "official_translations.json")


def _items_with_vs(src, qnum):
    pat = re.compile(rf"^Q{re.escape(qnum.replace('.', ''))}_")
    hits = []
    for lvl in src.get("levels", []) or []:
        pool = list((lvl.get("ids") or {}).get("items", []) or [])
        for rec in lvl.get("records", []) or []:
            pool.extend(rec.get("items", []) or [])
        for it in pool:
            if pat.match(it.get("name", "")) and it.get("valueSets"):
                hits.append(it)
    return hits


def resolve_exclusion_id(src, ex_id, official=None):
    """'INST|LOC|QNUM|OPTION_INDEX' -> ('val:<VS>:<code>', 'ok') via the pre-apply dictionary.
    OPTION_INDEX is authored as a position in the OFFICIAL ENGLISH option list
    (official_translations.json[inst][qnum]['EN']['options'][idx] — see extract_official.py's
    `_i`), NOT as a position in any one Q<QNUM>_* item's value set — the dictionary's value-set
    order can diverge from (or be transposed relative to) the official English order even when
    only one item carries a value set for this qnum, so position is never trusted on its own.
    Every Q<QNUM>_* item that carries a value set is searched for the value whose label equals
    (norm+casefold) the official English text at idx; a unique match across all candidate items
    resolves ('ok'), no match is ('en-mismatch') and 2+ matches is ('ambiguous:<n_items>') —
    this also covers items whose value-set length differs from the English option count (e.g. a
    single non-option EN string against a multi-value set), which used to be trusted blindly."""
    from cspro_helpers import _value_pair_key
    parts = ex_id.split("|")
    if len(parts) != 4:
        return None, "malformed"
    inst, _loc, qnum, idx = parts[0], parts[1], parts[2], int(parts[3])
    hits = _items_with_vs(src, qnum)
    if not hits:
        return None, "absent"

    en_opts = (((official or {}).get(inst, {}).get(qnum, {}) or {}).get("EN", {}) or {}).get("options") or []
    if not (0 <= idx < len(en_opts)):
        return None, "index-out-of-range"
    want = norm(en_opts[idx]).casefold()

    matched = []
    for it in hits:
        vs = it["valueSets"][0]
        for v in (vs.get("values") or []):
            lab = ((v.get("labels") or [{}])[0].get("text") or "").strip()
            if norm(lab).casefold() == want:
                matched.append(f"val:{vs.get('name')}:{_value_pair_key(v)}")
    if len(matched) == 1:
        return matched[0], "ok"
    if not matched:
        return None, "en-mismatch"
    return None, f"ambiguous:{len(hits)}"


def seed_candidates(inst, findings_path, results, src=None, exclusions=None, official=None):
    """Candidate override rows = repair-list keys that the Aug-21 extract would REPLACE.
    Prints ready-to-paste aug21-overrides.json rows; the human confirms each one.
    Every recovery_exclusions id that cannot be mapped is printed as a WARN so the seed is
    never silently incomplete."""
    findings = json.loads(io.open(findings_path, encoding="utf-8").read()) if findings_path else []
    if exclusions is None:
        exclusions = json.loads(io.open(EXCLUSIONS_PATH, encoding="utf-8").read()).get("exclusions", {})
    if official is None:
        official = (json.loads(io.open(OFFICIAL_PATH, encoding="utf-8").read())
                    if os.path.exists(OFFICIAL_PATH) else {})
    if src is None:
        src = json.loads(io.open(os.path.join(CSPRO, inst, DCF_FILE[inst]), encoding="utf-8").read())
    replaced = {(loc, k): (old, new) for loc, r in results.items() for k, old, new in r.replaced}
    rows = []
    for f in findings:
        if f.get("instrument") != inst:
            continue
        hit = (f.get("locale", "").lower(), f.get("key"))
        if hit in replaced:
            old, new = replaced[hit]
            rows.append({"locale": hit[0], "key": hit[1], "keep": old, "proposed": new,
                         "reason": f"scan_poisoned_keys {f.get('reason')} on the Aug-14/17 pass; Aug-21 re-introduces it"})
    unresolved = []
    for ex_id, ent in exclusions.items():
        p = ex_id.split("|")
        if len(p) != 4 or p[0] != inst:
            continue
        key, status = resolve_exclusion_id(src, ex_id, official)
        if key is None:
            unresolved.append((ex_id, status))
            continue
        hit = (p[1].lower(), key)
        if hit in replaced:
            old, new = replaced[hit]
            rows.append({"locale": hit[0], "key": key, "keep": old, "proposed": new,
                         "reason": f"recovery_exclusions {ex_id} ({ent.get('test')}): {ent.get('why', '')[:120]}"})
    for ex_id, status in unresolved:
        print(f"  WARN unresolved exclusion {ex_id}: {status} - check by hand against aug21_apply_diff.json")
    print(f"\n  {inst}: {len(rows)} candidate override row(s), {len(unresolved)} unresolved exclusion id(s) — "
          f"paste the ones you confirm into aug21-overrides.json[{inst!r}]")
    for row in rows:
        print(f"    [{row['locale']}] proposed: {row['proposed'][:80]!r}")
        print("    " + json.dumps({row["key"]: {"keep": row["keep"], "reason": row["reason"]}},
                                  ensure_ascii=False))
    return rows


def compare_findings(pre_path, post_path):
    """scan_poisoned_keys per-reason delta gate. The scan compares against the JUNE-5 cleared
    corpus (official_translations.json), so Aug-21 rewordings can be legitimate suspects; the
    gate is therefore post <= pre per reason, not zero. Prints new keys for any reason that grew."""
    def load(p):
        rows = json.loads(io.open(p, encoding="utf-8").read())
        return rows, Counter(r.get("reason", "?") for r in rows)
    pre_rows, pre = load(pre_path)
    post_rows, post = load(post_path)
    pre_keys = {(r.get("instrument"), r.get("locale"), r.get("key")) for r in pre_rows}
    ok = True
    print(f"\n  {'reason':<18}{'pre':>6}{'post':>6}{'delta':>7}")
    for reason in sorted(set(pre) | set(post)):
        d = post[reason] - pre[reason]
        tag = "  GREW" if d > 0 else ""
        ok = ok and d <= 0
        print(f"  {reason:<18}{pre[reason]:>6}{post[reason]:>6}{d:>+7}{tag}")
        if d > 0:
            for r in post_rows:
                if r.get("reason") == reason and (r.get("instrument"), r.get("locale"), r.get("key")) not in pre_keys:
                    print(f"      NEW {r.get('instrument')}/{r.get('locale')} {r.get('key')}: {str(r.get('value'))[:80]!r}")
    print(f"  scan gate: {'OK' if ok else 'FAILED'} (total {sum(pre.values())} -> {sum(post.values())})")
    return ok


def load_extract(extract_dir, loc):
    clean = os.path.join(extract_dir, f"{loc}.json")
    flagged = os.path.join(extract_dir, f"{loc}_flagged.json")
    if not os.path.exists(clean):
        return {}, set()
    pairs = json.loads(io.open(clean, encoding="utf-8").read())
    pairs.pop("_meta", None)
    fk = set()
    if os.path.exists(flagged):
        for row in json.loads(io.open(flagged, encoding="utf-8").read()):
            if row.get("key"):
                fk.add(row["key"])
    return pairs, fk


def stamp_meta(m, file, r, date):
    meta = m.get("_meta")
    if not isinstance(meta, dict):
        meta = OrderedDict()
        m["_meta"] = meta
        m.move_to_end("_meta", last=False)
    meta.setdefault("sources", OrderedDict())["aug21"] = OrderedDict([
        ("date", date), ("file", file),
        ("n_written", len(r.writes) - len(r.replaced)),
        ("n_replaced", len(r.replaced)),
        ("n_overridden", len(r.overridden)),
        ("n_removed", len(r.removes)),
        ("n_flagged_skipped", r.flagged_skipped)])


VAL_KEY = re.compile(r"^val:(.+):([^:]+)$")

# Pre-existing duplicate-label sets a HUMAN has ruled benign, keyed
# <inst> -> "<locale>/<value_set>" -> {"codes": [...], "reason": "..."}. Task 48 fix
# round 1: without it `--fail-on-pre` would be all-or-nothing, and an instrument with one
# untouchable legacy collision could never publish again. A ruling is data, carries a
# reason, and is reviewable in the diff - which is the whole point of not hard-coding it.
ACCEPTED_PRE_PATH = os.path.join(HERE, "duplicate_label_accepted.json")


def load_accepted_pre(path=ACCEPTED_PRE_PATH):
    """{inst: {(locale, value_set): (frozenset(codes), reason)}}; {} when the file is absent.

    Every entry MUST carry a non-empty reason and an explicit code list: a ruling that does
    not say WHY, or that waives a whole value set forever, is how a defect class comes back.
    """
    try:
        raw = io.open(path, encoding="utf-8").read()
    except OSError:
        return {}
    out = {}
    for inst, block in json.loads(raw).items():
        if inst.startswith("_"):
            continue
        if not isinstance(block, dict):
            raise ValueError(f"{path}: {inst} must be an object")
        rows = {}
        for scope, ent in block.items():
            if "/" not in scope:
                raise ValueError(f"{path}: {inst}/{scope!r} must be '<locale>/<value_set>'")
            codes = (ent or {}).get("codes")
            reason = ((ent or {}).get("reason") or "").strip()
            if not codes:
                raise ValueError(f"{path}: {inst} {scope} needs a non-empty 'codes' list")
            if not reason:
                raise ValueError(f"{path}: {inst} {scope} needs a non-empty 'reason'")
            loc, vs = scope.split("/", 1)
            rows[(loc, vs)] = (frozenset(str(c) for c in codes), reason)
        out[inst] = rows
    return out


def accepted_pre_reason(row, accepted):
    """The ruling that covers this gate row, or None. The row's codes must be a SUBSET of
    the ruled ones - a set that grew a third colliding code is a new defect, not a ruling."""
    ent = (accepted or {}).get((row.get("locale"), row["value_set"]))
    if ent and set(row["codes"]) <= ent[0]:
        return ent[1]
    return None


def duplicate_label_rows(values, english, written=()):
    """The value sets of `values` where two codes would carry the SAME translated label.

    Task 48, the permanent gate under the row-inheritance defect class. A value set whose
    codes 03 and 05 both read `Mababayaran han PhilHealth an gastos han pagtambal` gives
    the respondent two choices that are impossible to tell apart, and the analyst two
    codes that cannot be distinguished after the fact. anchor_extract.py now holds the
    rows it can see, but the extractor only ever sees ONE side of a collision: the F3 CEB
    row it shipped collided with a value the map already held, and the F4 WAR rows
    collided across two value sets. This function judges the map the apply WOULD leave
    behind, which is the only place both sides are visible.

    Two exemptions, and only two:
      * identical ENGLISH — the zero-padded `01`/`1` pair, the legacy `8`/`99`
        "Other (specify)" pair: those codes MUST read the same;
      * a key the dictionary no longer defines. It renders nothing on the tablet, so it
        cannot collide with anything - and it is what makes most of the legacy padded
        pairs benign, because the duplicate partner is a dead map row, not a choice.

    `written` names the keys this apply would write. A group that contains one is the
    apply's business and blocks it (RED); a group that contains none is a pre-existing
    defect this apply does not touch, reported and counted but never a STOP.
    """
    written = set(written)
    by_vs = defaultdict(list)
    for key, val in values.items():
        m = VAL_KEY.match(key)
        if m and key in english and isinstance(val, str) and val.strip():
            by_vs[m.group(1)].append((m.group(2), key, val))
    rows = []
    for vs in sorted(by_vs):
        by_val = defaultdict(list)
        for code, key, val in by_vs[vs]:
            by_val[norm(val)].append((code, key, val))
        for nv in sorted(by_val):
            grp = sorted(by_val[nv])
            if len(grp) < 2:
                continue
            if len({norm(english[k]).casefold() for _c, k, _v in grp}) < 2:
                continue
            rows.append({"value_set": vs, "value": grp[0][2],
                         "codes": [c for c, _k, _v in grp],
                         "keys": [k for _c, k, _v in grp],
                         "english": [english[k] for _c, k, _v in grp],
                         "written": sorted(k for _c, k, _v in grp if k in written)})
    return rows


def print_duplicate_label_gate(inst, gate, accepted=None, fail_on_pre=False):
    """Print the gate and return True when it BLOCKS.

    Three severities, because "every collision is RED" and "only my own writes are RED" are
    both wrong (Task 48 fix round 1, review finding 2):

      RED     the group contains a key THIS apply writes - always blocks;
      pre     a pre-existing group over a LIVE value set that nobody has ruled on. The
              default keeps it a report, so the wave can see its own writes; `--fail-on-pre`
              makes it block, and that is the path an instrument PUBLISHES on - the shipped
              F4 war Q128/Q134 collision is a `pre` group, and it must not be publishable;
      ok-pre  a pre-existing group `duplicate_label_accepted.json` rules benign WITH a
              reason - never blocks, in either mode.
    """
    ruling = (accepted or {}).get(inst)
    red, unruled, ok = [], [], []
    for g in gate:
        g["accepted"] = None if g["written"] else accepted_pre_reason(g, ruling)
        (red if g["written"] else ok if g["accepted"] else unruled).append(g)
    print(f"\n{inst}  duplicate-label gate: {len(red)} violation(s) on a row this apply "
          f"writes, {len(unruled)} un-ruled pre-existing set(s) it does not touch"
          f"{' (STRICT: these block too)' if fail_on_pre else ''}, "
          f"{len(ok)} ruled benign")
    for g in gate:
        if g["written"]:
            mark = "RED"
            note = " writes " + ",".join(k.rsplit(":", 1)[1] for k in g["written"])
        elif g["accepted"]:
            mark, note = "ok-pre", ""
        else:
            mark, note = ("RED-pre" if fail_on_pre else "pre"), ""
        print(f"    {mark} {g['locale']}/{g['value_set']} codes "
              f"{','.join(g['codes'])}{note}: {g['value'][:70]!r}")
        for en, code in zip(g["english"], g["codes"]):
            print(f"        {code}: {en[:78]!r}")
        if g["accepted"]:
            print(f"        ruled benign: {g['accepted'][:96]}")
    return bool(red) or (fail_on_pre and bool(unruled))


def run(inst, extract_dir, map_dir, overrides, apply, all_keys, date, english=None):
    """(merge results, duplicate-label gate rows).

    Task 48: every locale is merged BEFORE anything is written, because the gate has to
    judge the whole fleet and a half-written fleet is the one state no replay can undo.
    """
    out, pending = {}, []
    for loc in LOCALES:
        path = os.path.join(map_dir, f"{loc}.json")
        pairs, flagged = load_extract(extract_dir, loc)
        if not pairs and not flagged:
            continue
        if not os.path.exists(path):
            print(f"  {inst}/{loc}: no map file - skipped")
            continue
        m, indent, crlf = load_map(path)
        r = merge_locale(m, pairs, flagged, overrides, all_keys, loc)
        out[loc] = r
        pending.append((loc, path, m, indent, crlf, r))
    gate = []
    for loc, _path, m, _indent, _crlf, r in pending:
        after = dict(m)
        after.update(r.writes)
        for key in r.removes:            # the gate judges the map the apply LEAVES BEHIND
            after.pop(key, None)
        for row in duplicate_label_rows(after, english or {}, r.writes):
            row["locale"] = loc
            gate.append(row)
    if apply and not any(g["written"] for g in gate):
        for loc, path, m, indent, crlf, r in pending:
            if not r.writes and not r.removes:      # override-only / same-only locales: file untouched
                continue
            for k, v in r.writes.items():
                m[k] = v                              # existing keys keep position; new ones append
            for k in r.removes:
                m.pop(k, None)
            stamp_meta(m, f"{loc}.json", r, date)
            save_map(path, m, indent, crlf)
    return out, gate


def dcf_english(inst):
    """{key: English label} from the already-built F<n>/<App>.dcf (JSON) — NO generator run,
    so a dry run never rewrites the .dcf. Requires the .dcf to be current (it is regenerated
    by every generate_dcf.py / scan_poisoned_keys.py run). It is both the anchor denominator
    and the duplicate-label gate's answer to "do these two codes share an English label?"."""
    from cspro_helpers import walk_labeled_nodes
    path = os.path.join(CSPRO, inst, DCF_FILE[inst])
    d = json.loads(io.open(path, encoding="utf-8").read())
    out = {}
    for key, node in walk_labeled_nodes(d):
        labs = node.get("labels") or []
        text = (labs[0].get("text") or "").strip() if labs else ""
        if text:
            out[key] = text
    return out


def built_dcf_keys(inst):
    return set(dcf_english(inst))


def print_table(inst, results):
    print(f"\n{inst}  {'locale':<7}{'written':>8}{'replaced':>9}{'override':>9}"
          f"{'removed':>8}{'same':>6}{'flagged':>8}{'dcf-unanchored':>15}")
    for loc, r in results.items():
        print(f"    {loc:<7}{len(r.writes) - len(r.replaced):>8}{len(r.replaced):>9}"
              f"{len(r.overridden):>9}{len(r.removes):>8}{r.already_same:>6}"
              f"{r.flagged_skipped:>8}{len(r.unmatched):>15}")
        for key in r.override_stale:
            print(f"      WARN override 'keep' != current map value: {key}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write maps (default = dry run)")
    ap.add_argument("--only", choices=CSPRO_INSTRUMENTS)
    ap.add_argument("--extract",
                    help="extractor out dir for ONE instrument (requires --only; "
                         "default out-aug21/<inst>/)")
    ap.add_argument("--maps-dir",
                    help="translation-map dir for ONE instrument (requires --only; "
                         "default F<n>/translations/) - used to rehearse --apply on a COPY")
    ap.add_argument("--unmatched", action="store_true",
                    help="add the dcf-unanchored column: BUILT-dcf keys the extract produced "
                         "nothing for (reads the built .dcf; no generator run). INFORMATIONAL - "
                         "non-zero by construction (container keys, sub-MIN_EMIT labels, labels "
                         "the paper never prints verbatim), never a STOP condition. The drift "
                         "check is anchor_extract.py's own 'keys not in dcf: []' line.")
    ap.add_argument("--fail-on-pre", action="store_true",
                    help="STRICT duplicate-label gate: a PRE-EXISTING collision over a live "
                         "value set blocks too, unless duplicate_label_accepted.json rules "
                         "it benign with a reason. Publishing waves (Tasks 49/50) run this; "
                         "a blocked run writes nothing and exits 2.")
    ap.add_argument("--report", default=os.path.join(HERE, "aug21_apply_diff.json"))
    ap.add_argument("--seed", help="scan_poisoned_keys --apply-report JSON; print candidate override rows")
    ap.add_argument("--compare-findings", nargs=2, metavar=("PRE", "POST"),
                    help="per-reason delta gate between two scan_poisoned_keys reports; exit 1 if any reason grew")
    a = ap.parse_args()

    # --extract names ONE instrument's extractor out dir, so it is meaningless
    # without --only; erroring out beats silently applying the default extract.
    if a.extract and not a.only:
        ap.error("--extract requires --only (it names one instrument's extract dir)")
    # Same reasoning for --maps-dir: pointing ONE instrument's rehearsal copy at every
    # instrument would merge F1's extract into F3's and F4's maps.
    if a.maps_dir and not a.only:
        ap.error("--maps-dir requires --only (it names one instrument's translations dir)")

    if a.compare_findings:
        ok = compare_findings(*a.compare_findings)      # Task 7
        raise SystemExit(0 if ok else 1)

    overrides_all = load_overrides(OVERRIDES_PATH)
    accepted_pre = load_accepted_pre()
    date = _dt.date.today().isoformat()
    diff = {}
    blocked = False
    for inst in CSPRO_INSTRUMENTS:
        if a.only and inst != a.only:
            continue
        extract_dir = a.extract or os.path.join(EXTRACT_ROOT, inst)   # a.extract implies --only
        if not os.path.isdir(extract_dir):
            print(f"  {inst}: no extract dir {extract_dir} - skipped")
            continue
        english = dcf_english(inst)
        all_keys = set(english) if a.unmatched else None
        map_dir = a.maps_dir or os.path.join(CSPRO, inst, "translations")   # a.maps_dir implies --only
        results, gate = run(inst, extract_dir, map_dir, overrides_all.get(inst, {}),
                            a.apply, all_keys, date, english=english)
        print_table(inst, results)
        blocked = print_duplicate_label_gate(inst, gate, accepted_pre,
                                             a.fail_on_pre) or blocked
        diff[inst] = {loc: {"writes": r.writes,
                            "replaced": [{"key": k, "was": o, "now": n} for k, o, n in r.replaced],
                            "overridden": [{"key": k, "current": c, "proposed": p} for k, c, p in r.overridden],
                            "removed": r.removes,
                            "unmatched": r.unmatched, "flagged_skipped": r.flagged_skipped,
                            "already_same": r.already_same}
                      for loc, r in results.items()}
        if a.seed:
            src = None
            if not a.apply:
                # Seeding needs the PRE-APPLY dictionary; the built .dcf already reflects the
                # current (pre-apply) maps, so read it instead of running the generator.
                src = json.loads(io.open(os.path.join(CSPRO, inst, DCF_FILE[inst]), encoding="utf-8").read())
            seed_candidates(inst, a.seed, results, src=src)
    report = os.path.abspath(a.report)
    with io.open(report, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(diff, fh, ensure_ascii=False, indent=1)
    if blocked:
        print("\nduplicate-label gate RED - two codes of one value set would carry the same "
              "label. Nothing was written; fix the extract, hold the row in "
              "aug21-overrides.json, or - for a pre-existing set - rule it in "
              "duplicate_label_accepted.json with a reason.")
    # The last line says what HAPPENED, not what was asked for: a blocked --apply wrote
    # nothing, so calling it APPLIED (as this line did before fix round 1) hands the next
    # task a false green. A blocked DRY RUN exits 2 for the same reason - the gate result
    # has to survive being read by a script that only sees the exit code.
    print(f"\n{'BLOCKED' if blocked else 'APPLIED' if a.apply else 'DRY RUN'}"
          f" - diff written to {report}")
    if blocked:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
