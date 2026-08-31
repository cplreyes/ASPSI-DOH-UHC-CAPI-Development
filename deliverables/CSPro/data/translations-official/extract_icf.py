#!/usr/bin/env python3
"""ICF (informed consent) paragraph translations from the Aug-21 translated PDFs.

Anchor set = the English paragraphs in ../../icf_content.py SCREENS (not the paper's own
English: the paper opens "Hello, my name is ... I work for" where the build reads "We work
for ...", so paragraph 1 is found by its identical TAIL). Translation = the text between
the end of one located English paragraph and the start of the next located one, trimmed
at PART headings / ballot glyphs / contact-table furniture ("Office Email Contact No",
SJREB rows - the <b> contact blocks are printed cell-by-cell and are never located).
An anchor whose trailing punctuation the paper drops ("... you can contact Kung aduna ..."
for "... you can contact:") still counts as a whole match, and a prefix match walks the
anchor's leftover tail off the head of the window: either way no English word survives at
the head of a stored paragraph, where the enumerator would read it aloud.

Acceptance is NOT extract_notes.looks_english(): every locale keeps the English program
names ("Guaranteed and Accessible Medications for Outpatient Treatment", "Department of
Health") inside paragraph 1, which alone trips the >=3-function-word rule. reads_english()
strips those names first and additionally rejects a candidate whose head repeats the
English paragraph's head (the F1-Tagalog paper defect: F3's English coverage sentence is
printed above the CORRECT F1 Tagalog - the auto-drop is right, the Tagalog is seeded via
aug21-overrides.json icf:1:1:FIL).

These are read-aloud paragraphs, so the terminal punctuation polish() strips is restored.
':' counts as terminal too: the ethics-contact lead-in ends "... you may contact:" and the
word in front of that colon is a clause word in every locale ("... kontakin ang:"), which
is exactly what polish()'s DANGLING guard blanks - see finish(). The Ilocano F3/F4 papers
additionally bracket each translated paragraph whole ("(<Ilocano>.)"), which unwrap() takes
off, and the version-footer / PSA-clearance lines are dropped per LINE, exactly as
extract_notes.dump_source() drops them from its text dumps.

    python extract_icf.py --source "C:/.../raw/Survey-Instruments-2026-08-21/Translations"
    python extract_icf.py --source ... --json icf.json --report icf-report.json

--overrides  aug21-overrides.json (default: next to this file). icf:<p>:<i>:<LOC> rows
             replace the extracted value; "keep": "" stores an empty value, which
             icf_content.screens_for() renders as English.
--merge-into prior icf.json (default: next to this file) whose values are carried forward
             for any paragraph this run cannot extract; --json is what actually gets
             written, so a dry run reads the prior file and writes nothing.
"""
import argparse
import io
import json
import os
import re
import sys
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
CSPRO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, CSPRO)
from extract_notes import norm, looks_english, polish, PAPER_LANG, PAPER_NAME, pdf_lines, load_overrides, DUMP_NOISE  # noqa: E402
import icf_content  # noqa: E402

TAG = re.compile(r"<[^>]+>")
STOP = re.compile(r"\bPART\s+I{1,3}\b|[\u2610\u2611\u2612\u25a1]|\bVERIFICATION\b"
                  r"|\bOffice\s+Email\b|\bEmail:|\bContact No\b"
                  r"|Single Joint Research Ethics Board|\bSJREB\b")
# English proper names every locale keeps verbatim inside the consent text. Two of them
# are printed with small per-locale variations that still have to be stripped, or their
# "and"/"for" alone reach the >=3-function-word threshold and drop a good paragraph:
# F1-Bisaya prints "Medication for Outpatient Treatment" (singular) and F1-Waray prints
# "Bagong Urgent HEALTH Care ... Ambulatory Services"; the connector inside that name is
# the locale's own ("and"/"ug"/"ngan"/"at"/"kag"), hence \w{2,4}.
PROGRAM_NAMES = re.compile(
    r"Yaman ng Kalusugan Program|No Balance Billing|Zero Balance Billing"
    r"|Bagong Urgent (?:Health )?Care \w{2,4} Ambulatory Services"
    r"|Guaranteed and Accessible Medications? for Outpatient Treatment"
    r"|Department of Health|Asian Social Project Services,? Inc\.?|Universal Health Care"
    r"|Single Joint Research Ethics Board|data collector", re.I)
HEAD = 60
# Stand-in for the sentence a colon-terminated paragraph never gets, so polish() can trim
# the leading debris without its DANGLING guard firing on the clause word before the colon.
SENTINEL = "zqxend"


def plain(para):
    return norm(TAG.sub(" ", para))


def locate(low, en, min_words=8):
    """(start, end, kind) of `en` (lowercased) in `low`: exact (bar trailing punctuation the
    paper may not print), else longest prefix, else longest suffix of >= min_words words.
    None when absent."""
    enl = en.lower()
    p = low.find(enl)
    if p >= 0:
        return p, p + len(enl), "exact"
    # The paper prints the anchor in FULL but drops its trailing punctuation and runs the
    # translation straight on: F1-Bisaya/Cebuano print "... you can contact Kung aduna ..."
    # for an anchor that ends "... you can contact:". That is a whole-anchor match, not a
    # prefix - and it has to be taken here, because the prefix loop below splits on
    # whitespace, so "contact:" != "contact" costs the WHOLE last word: it stays at the head
    # of the window and polish() keeps it (one English word read aloud before the Bisaya).
    bare = enl.rstrip(" .:;,")
    if bare != enl:
        p = low.find(bare)
        if p >= 0:
            return p, p + len(bare), "exact"
    words = enl.split()
    for k in range(len(words) - 1, min_words - 1, -1):
        probe = " ".join(words[:k])
        p = low.find(probe)
        if p >= 0:
            return p, p + len(probe), "prefix"
    for k in range(len(words) - 1, min_words - 1, -1):
        probe = " ".join(words[-k:])
        p = low.find(probe)
        if p >= 0:
            return p, p + len(probe), "suffix"
    return None


def reads_english(cand, en):
    """True when the candidate is (still) the English paragraph, not a translation."""
    c, e = norm(cand).lower(), norm(en).lower()
    if c[:HEAD] == e[:HEAD]:
        return True                                    # starts by repeating the English
    if len(c) >= HEAD and c[:HEAD] in e:
        return True                                    # starts mid-English (prefix-anchor tail)
    return looks_english(PROGRAM_NAMES.sub(" ", cand))


def _drop_anchor_tail(window, tail):
    """Strip the words of the anchor's unmatched `tail` off the head of `window`.

    A `prefix` match stops mid-anchor, so whatever of the anchor the paper still prints sits
    in front of the translation. The suffix re-match in extract_screens() takes that off in
    one go when the anchor's own tail is long enough for locate() (>= min_words); when only a
    word or two of the tail is left over, nothing removes it and polish()'s lead trim keeps
    it (looks_english() needs >= 3 function words to call a lead English). This walks the
    tail token by token and stops at the first token the window does not repeat, so it can
    only ever remove text the anchor itself continues with.
    """
    out = window.lstrip(" .:-)")
    for w in tail.split():
        wl = w.lower().strip(".,:;()'\"?!")
        if not wl:
            continue
        m = re.match(r"(\S+)\s*", out)
        if not m or m.group(1).lower().strip(".,:;()'\"?!") != wl:
            break
        out = out[m.end():]
    return out


def unwrap(s):
    """Drop the parentheses a bilingual paper wraps a WHOLE translated paragraph in.

    The Aug-21 Ilocano F3/F4 papers print every consent paragraph as "(<Ilocano>.)" - the
    bracket belongs to the layout, not to the sentence, and rendering it on the read-aloud
    screen just tells the enumerator to read a stray "(". Inner brackets ("(data
    collector's name)", "(UHC)") are left alone: only a leading "(" that closes at the very
    end - or, where the paper forgot the closer, never closes at all - is a wrapper.
    """
    while len(s) > 2 and s.startswith("("):
        depth, close = 0, -1
        for i, ch in enumerate(s):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    close = i
                    break
        if close == len(s) - 1:
            s = s[1:-1].strip()
        elif close < 0:
            s = s[1:].strip()
        else:
            break                      # the opening bracket closes mid-paragraph: not a wrapper
    return s


def finish(raw):
    """polish() for leading debris, then put back the terminal punctuation it strips.

    '.', '?', '!' and ':' all count as terminals. A colon-terminated paragraph cannot go
    through polish() unaided: it ends on a clause word ("... maaari mong kontakin ang:"),
    which polish()'s DANGLING guard reads as a page-break truncation and blanks. Such a
    paragraph is polished with SENTINEL standing in for the sentence that never comes, so
    the leading-debris trim still runs and the guard cannot fire.
    """
    raw = unwrap(norm(raw))
    probe = re.sub(r"\s+[A-Za-z]$", "", raw)      # stray initial of the next English word
    tail = probe[-1] if probe and probe[-1] in ".?!:" else ""
    if tail == ":":
        s = polish(probe + " " + SENTINEL + ".")
        return s[:-len(SENTINEL)].rstrip() if s.endswith(SENTINEL) else s
    s = polish(raw)
    if s and tail and not s.endswith((".", "?", "!")):
        s += tail
    return s


def _anchors(instrument):
    """[(pkey|None, plain_en)] in screen order; contact blocks (<b>) are boundaries only."""
    out = []
    for part, paras in enumerate(icf_content.SCREENS[instrument], start=1):
        for i, para in enumerate(paras):
            key = None if para.lstrip().startswith("<b>") else icf_content.paragraph_key(part, i)
            out.append((key, plain(para)))
    return out


def extract_screens(lines, instrument):
    # Same page-furniture drop extract_notes.dump_source() applies to its text dumps: the
    # ICF page carries the two-line version footer and the PSA clearance line, and on the
    # F3/F4 papers they land BETWEEN the "you can contact:" paragraph and the contact
    # table - inside the window, so cutting at the table furniture would not remove them.
    # Dropped by LINE (not cut at) so a paragraph broken across the footer rejoins.
    blob = norm(" ".join(ln for ln in lines if not DUMP_NOISE.search(ln)))
    low = blob.lower()
    anchors = _anchors(instrument)
    found = []
    for key, en in anchors:
        loc = locate(low, en)
        found.append((key, en, loc))
    trans, report = OrderedDict(), OrderedDict()
    for n, (key, en, loc) in enumerate(found):
        if key is None:
            continue
        if loc is None:
            report[key] = "missing"
            continue
        start, end, kind = loc
        nxt = next((l[0] for _, _, l in found[n + 1:] if l is not None and l[0] > end), len(blob))
        window = blob[end:nxt]
        if kind == "prefix":
            # The paper prints MORE English than the anchor (F3-Hiligaynon's privacy
            # paragraph adds "...your family's or child's personal information outside of
            # the study team"), so the match stopped mid-paragraph and the rest of the
            # paper's English still sits in front of the translation. That English ends
            # where the anchor's own TAIL ends - when the tail is on the page at all;
            # when it is not (F1-Tagalog prints F3's coverage sentence instead of F1's),
            # nothing moves and the candidate is dropped as English, as it should be.
            more = locate(window.lower(), en)
            if more and more[2] == "suffix":
                window = window[more[1]:]
            else:
                # The anchor tail is too short for locate() (or is not on the page at all):
                # walk it off token by token instead, so a one- or two-word remainder cannot
                # ride at the head of the stored paragraph. A tail that is absent stops the
                # walk on its first token and the candidate is dropped as English, as before.
                window = _drop_anchor_tail(window, en[end - start:])
        cand = window.lstrip(" .:-)")
        m = STOP.search(cand)
        if m:
            cand = cand[:m.start()]
        cand = finish(cand[:int(len(en) * 2.5) + 40])
        if len(cand) < 20:
            report[key] = "dropped-short"
        elif reads_english(cand, en):
            report[key] = "dropped-english"
        else:
            trans[key] = cand
            report[key] = kind
    return trans, report


def build_icf(source_dir, overrides, prior):
    icf = OrderedDict((k, OrderedDict(v)) for k, v in prior.items() if k != "_provenance")
    report = OrderedDict()
    counts = {"written": 0, "replaced": 0, "overridden": 0, "kept_prior": 0}
    files = OrderedDict()
    for name in sorted(os.listdir(source_dir)):
        m = PAPER_NAME.match(name)
        if not m or m.group(2) not in PAPER_LANG:
            continue
        inst, loc = m.group(1), PAPER_LANG[m.group(2)]
        files[f"{inst}_{loc}"] = name
        trans, rep = extract_screens(pdf_lines(os.path.join(source_dir, name)), inst)
        block = icf.setdefault(inst, OrderedDict())
        ov = overrides.get(inst, {})
        for key, en in ((k, e) for k, e in _anchors(inst) if k):
            entry = block.setdefault(key, OrderedDict())
            if entry.get("EN") != en:          # SCREENS reworded since the prior file
                entry.clear()
                entry["EN"] = en
            val = trans.get(key)
            okey = f"{key}:{loc}"
            if okey in ov:
                entry[loc] = ov[okey].get("keep", entry.get(loc, val))   # "" = render English
                counts["overridden"] += 1
                rep[key] = "override"
            elif val:
                if entry.get(loc) and norm(entry[loc]) != norm(val):
                    counts["replaced"] += 1
                elif not entry.get(loc):
                    counts["written"] += 1
                entry[loc] = val
            elif entry.get(loc):
                counts["kept_prior"] += 1
        report.setdefault(inst, OrderedDict())[loc] = rep
    icf["_provenance"] = OrderedDict(prior.get("_provenance", {}))
    icf["_provenance"]["aug21"] = OrderedDict(
        [("date", "2026-08-25"), ("source", source_dir), ("files", files),
         ("n_written", counts["written"]), ("n_replaced", counts["replaced"]),
         ("n_overridden", counts["overridden"]), ("n_kept_prior", counts["kept_prior"])])
    return icf, report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--json")
    ap.add_argument("--report", default=os.path.join(HERE, "icf-report.json"))
    ap.add_argument("--overrides", default=os.path.join(HERE, "aug21-overrides.json"))
    ap.add_argument("--merge-into", default=os.path.join(HERE, "icf.json"))
    a = ap.parse_args()
    prior = json.load(io.open(a.merge_into, encoding="utf-8")) if os.path.exists(a.merge_into) else {}
    icf, report = build_icf(a.source, load_overrides(a.overrides), prior)
    for inst in report:
        for loc, rep in report[inst].items():
            kinds = {}
            for k in rep.values():
                kinds[k] = kinds.get(k, 0) + 1
            print(f"[{inst} {loc}] " + "  ".join(f"{k} {v}" for k, v in sorted(kinds.items())))
    print("aug21 icf: " + ", ".join(f"{k} {v}" for k, v in icf["_provenance"]["aug21"].items()
                                    if k.startswith("n_")))
    with io.open(a.report, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)
    if a.json:
        with io.open(a.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(icf, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        print(f"Wrote {a.json}")


if __name__ == "__main__":
    main()
