#!/usr/bin/env python3
r"""
Aug-17 migration: build-side normalized tables.

Two independent parsers feeding the same `Row` schema (see rowspec.py):

  CSPro mode  (F1/F3/F4) -- reads the SHIPPED build artifacts straight from a
    checkout: `<Base>.dcf` (JSON dictionary: names/labels/valueSets -- the
    only source of TRUTH for options/qtype), `<Base>.ent.qsf` (YAML, literal
    EN question text -- preferred over the dcf label for `stem`, same
    approach as `data-harmonization/generate_codebook.py:load_qsf`),
    `<Base>.ent.apc` (skip-to / errmsg / range logic -- same PROC-splitting
    approach as `automation/skip_boundary_check.py:parse_apc` and the
    FIELD=N/`skip to` regexes from `automation/verify_questions.py:83-90`),
    `<Base>.ent.mgf` (errmsg number -> EN text, `Language = EN` section).

  PWA mode (F2) -- regex-scrapes `src/generated/items.ts` (one item per
    physical line -- confirmed empirically, not an assumption) +
    `src/generated/schema.ts` (min/max) + `src/lib/skip-logic.ts` (per-item
    show/hide predicates) + `src/lib/cross-field.ts` + `src/i18n/locales/
    en.ts` (crossField.* EN message strings). The `en: '...'` extraction
    regex is the one proven in `scripts/audit-translations.py`.

Both modes are BEST-EFFORT / regex-and-JSON, not full parsers -- the paper
side (paper_tables.py) already established the convention that build-side
output must be faithful to what's actually there, not corrected; the Task
0.4 diff engine owns reconciliation, not this tool.

Item-name -> qnum derivation (`derive_qnum`) is shared by both modes: strip
a leading `Q`, take the leading digit run, an optional trailing letter
(`Q71a` style), then an optional `_<digits>` sub-part (`Q10_1_STEM` ->
"10.1"). It is intentionally a single small regex, not a lookup table --
robust to both CSPro dcf item names (`Q10_1_STEM`) and PWA item ids
(`Q10_1`, `Q71a`) with no per-instrument special-casing.

Stem/instruction split (CSPro mode, R19 -- rev-1.4 close-out finding)
-----------------------------------------------------------------------
A qsf item's `questionText.EN` is raw HTML, one or more `<p>` blocks.
`generate_qsf.py` (the shipped build's own generator) bakes an enumerator-
instruction paragraph (`<p class="instruction">...</p>`) and/or a plain
section-intro paragraph into the SAME HTML block as the item's own printed
stem -- established convention across generate_qsf.py (tickets #1055/#1048/
#763/#776/#801/#1062/#1136-1137). The OLD `load_qsf_text` took the whole
block, HTML-stripped it flat, and stored the concatenation as `stem` -- so a
paper-vs-build STEM_DIFF was really diffing "paper's bare stem" against
"build's stem + baked-in instruction/intro text", a pure representation
artifact (confirmed on real F3 data: ~114 of 145 distinct F3 STEM_DIFF
qnums were exactly this).

Fix: `_split_qsf_paragraphs` splits the raw HTML into per-`<p>` text blocks
(structural -- keys on the HTML's own paragraph tags, NOT generate_qsf.py's
INSTRUCTIONS/SECTION_INTROS dicts, which this tool has no access to and
shouldn't couple to). `_STEM_PARAGRAPH_RE` identifies the TRUE stem
paragraph -- the one starting with the item's own printed number ("14. ",
"9. ", "97.1 ", "38.1. " -- validated against all 371 real F3 qsf items:
covers 106/109 multi-paragraph items with zero ambiguous multi-match
cases). Critically, the stem paragraph is NOT always first (`Q4_NAME`'s
real qsf: intro paragraph, then `class="instruction"` paragraph, then the
numbered stem LAST) and NOT always un-classed (`Q9_GROUP`'s real qsf: the
numbered stem is `<p>` with no class, followed by `class="instruction"`) --
so this is structural detection by content shape, not by paragraph
position or class attribute. Every OTHER paragraph becomes `instructions`
(joined, exposed as a separate Row field -- see rowspec.py). A single-
paragraph block, or a multi-paragraph block where NO paragraph matches the
stem pattern (3 real F3 cases: the consent-script and build-banner blocks,
which aren't real numbered items), degrades to the OLD whole-text-as-stem
behavior -- never a guess.
"""
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

from rowspec import Row, normalize_text, write_csv

SCRIPT_DIR = Path(__file__).resolve().parent

# Default MAIN checkout -- CSPro compiles cannot happen inside this worktree
# (psgc_*.dat is gitignored; see reference_cspro_worktree_psgc_compile), but
# the .dcf/.ent.qsf/.ent.apc/.ent.mgf SOURCE files are plain tracked files,
# safe to read from either checkout. MAIN is used as the default per the
# task brief's CLI example; --cspro-dir overrides it.
DEFAULT_CSPRO_DIR = Path(
    r"C:\Users\analy\Documents\analytiflow\1_Projects\ASPSI-DOH-CAPI-CSPro-Development"
    r"\deliverables\CSPro"
)
DEFAULT_PWA_DIR = (SCRIPT_DIR / ".." / ".." / "F2" / "PWA" / "app").resolve()

INSTRUMENT_BASE = {
    "F1": "FacilityHeadSurvey",
    "F3": "PatientSurvey",
    "F4": "HouseholdSurvey",
}

# --- off-form / system item classification -------------------------------
#
# Every non-Q-prefixed dcf item that is NOT explicitly special-cased below
# (disposition/consent) is EXCLUDED from item-row emission -- these are
# case/CAPI bookkeeping fields with no printed paper item. Q-prefixed items
# and other content fields (e.g. F4 Section N's descriptive roster names,
# which carry no Q-prefix but ARE real survey content) are emitted with
# qnum="" when the name alone doesn't resolve one -- faithful-but-unresolved
# beats silently dropped; the crosswalk (Task 0.5) is where that gets fixed.

EXCLUDE_ITEMS = {
    # --- verify_questions.py KNOWN_OFFFORM (verbatim; CASE_DISPOSITION is
    # deliberately NOT copied here -- it is special-cased as kind=disposition
    # below instead) ---
    "LANGUAGE_USED", "REGION_CODE", "PROVINCE_HUC_CODE", "CITY_MUNICIPALITY_CODE",
    "FACILITY_NO", "CASE_SEQ", "REGION", "PROVINCE_HUC", "CITY_MUNICIPALITY",
    "FACILITY_NAME", "FACILITY_ADDRESS", "BARANGAY_NAME", "VERIFICATION_PHOTO_IMAGE",

    # --- GPS warm-radio capture fields (F1/F3 facility GPS, F3 patient-home
    # GPS, F4 household GPS) -- no paper equivalent, see
    # reference_cspro_gps_warm_radio ---
    "FACILITY_GPS_LATITUDE", "FACILITY_GPS_LONGITUDE", "FACILITY_GPS_ALTITUDE",
    "FACILITY_GPS_ACCURACY", "FACILITY_GPS_SATELLITES", "FACILITY_GPS_READTIME",
    "P_HOME_GPS_LATITUDE", "P_HOME_GPS_LONGITUDE", "P_HOME_GPS_ALTITUDE",
    "P_HOME_GPS_ACCURACY", "P_HOME_GPS_SATELLITES", "P_HOME_GPS_READTIME",
    "LATITUDE", "LONGITUDE", "HH_GPS_ALTITUDE", "HH_GPS_ACCURACY",
    "HH_GPS_SATELLITES", "HH_GPS_READTIME",

    # --- verification-photo capture plumbing (#713) ---
    "VERIFICATION_PHOTO_FILENAME", "CAPTURE_VERIFICATION_PHOTO",

    # --- PSGC cascade / derived-geo display duplicates feeding the
    # case-key gate (reference_cspro_casekey_psgc_gate); BARANGAY pairs with
    # BARANGAY_NAME above, same case-key-derived origin ---
    "REGION_NAME", "PROVINCE_NAME", "CITY_NAME", "CLASSIFICATION", "BARANGAY",
    "P_REGION", "P_PROVINCE_HUC", "P_CITY_MUNICIPALITY", "P_BARANGAY",

    # --- facility-context flags derived from facility master data, not
    # asked of the respondent (gate F3/F4's BUCAS/GAMOT item visibility) ---
    "AREA_HAS_BUCAS", "AREA_HAS_GAMOT",

    # --- cover-sheet / case-control metadata: printed on the paper form's
    # control sheet WITHOUT a numbered "N." prefix, so paper_tables.py's
    # ITEM_START_RE never emits a matching item row for these either. This
    # bucket is a build-tool judgment call (not sourced from
    # verify_questions.py's KNOWN_OFFFORM) -- flag to the controller if any
    # of these turn out to be printed as a numbered item on a given
    # instrument. ---
    "SURVEY_TEAM_LEADER_S_NAME", "ENUMERATOR_S_NAME", "FIELD_VALIDATED_BY",
    "FIELD_EDITED_BY", "TOTAL_NUMBER_OF_VISITS",
    "DATE_FIRST_VISITED_THE_FACILITY", "DATE_OF_FINAL_VISIT_TO_THE_FACILITY",
    "DATE_FIRST_VISITED", "DATE_FINAL_VISIT",
}

# EXCEPTION (brief): disposition machinery gets its own kind + full value
# sets, for the diff engine's DISPOSITION_DIFF check. ENUM_RESULT_FIRST_VISIT
# is not named in the brief but is structurally identical to
# ENUM_RESULT_FINAL_VISIT (same value set shape) -- included for symmetry.
DISPOSITION_ITEMS = {"ENUM_RESULT_FINAL_VISIT", "ENUM_RESULT_FIRST_VISIT", "BREAKOFF", "CASE_DISPOSITION"}

# Informed-consent screens.
CONSENT_ITEMS = {"ICF_PART1", "ICF_PART2"}

# Companion "other, specify" text fields ride on their parent item's qnum on
# paper (never a separately numbered item) -- see reference_cspro_other_txt_naming.
_OTHER_TXT_SUFFIX = "_OTHER_TXT"

_QNUM_DOTTED_RE = re.compile(r"^Q(\d+[a-z]?\.\d+)$", re.IGNORECASE)
_QNUM_RE = re.compile(r"^Q(\d+)([A-Za-z]?)(?:_(\d+))?")


def derive_qnum(name: str) -> str:
    """Item/id name -> paper-style qnum ('10', '10.1', '71a'), or '' if the
    name isn't Q-prefixed. See module docstring for the shared regex.

    PWA items.ts already spells some follow-up ids with a literal decimal
    ('Q13.1', 'Q24.2' -- conditional-on-parent items) -- that IS the paper
    qnum verbatim, checked first so it isn't reinterpreted by the
    underscore-derived rule below (which would collapse 'Q13.1' to '13',
    colliding with the base 'Q13' row)."""
    m_dot = _QNUM_DOTTED_RE.match(name)
    if m_dot:
        return m_dot.group(1).lower()
    m = _QNUM_RE.match(name)
    if not m:
        return ""
    num, letter, sub = m.groups()
    q = num + (letter.lower() if letter else "")
    if sub:
        q += "." + sub
    return q


def strip_html(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s or "")
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


# ============================================================================
# CSPro mode
# ============================================================================


def _en_label(o: dict) -> str:
    """labels list -> EN text, falling back to the first available label.
    Same rule as generate_codebook.py:_en."""
    for l in (o.get("labels") or []):
        if l.get("language") == "EN" and l.get("text"):
            return l["text"]
    for l in (o.get("labels") or []):
        if l.get("text"):
            return l["text"]
    return ""


def load_dcf_items(dcf_path: Path) -> dict:
    """dcf JSON -> {UPPER item name: (item dict, section string)}, in dcf
    order. `section` is the owning record's EN label, reshaped from CSPro's
    "X. Title" record-label convention to paper_tables.py's "X Title"
    format when it matches (record labels for real survey sections use this
    convention verbatim, e.g. "A. Introduction and Informed Consent" ->
    "A Introduction and Informed Consent"); left as-is otherwise (system
    record groups like "Field Control" carry no letter)."""
    d = json.load(open(dcf_path, encoding="utf-8"))
    out = {}
    section_re = re.compile(r"^([A-Z])\.\s*(.*)$")
    for lv in d.get("levels", []):
        if lv.get("ids"):
            for it in lv["ids"].get("items", []):
                out[it["name"].upper()] = (it, "")
        for rec in lv.get("records", []):
            en_label = _en_label(rec).strip()
            m = section_re.match(en_label)
            section = f"{m.group(1)} {m.group(2)}".strip() if m else en_label
            for it in rec.get("items", []):
                out[it["name"].upper()] = (it, section)
    return out


def build_options(item: dict) -> list:
    """dcf valueSets[0].values -> [{"code":..., "label":...}, ...]. Range
    pairs (`from`/`to`, rare) render as "from-to"."""
    vs = item.get("valueSets") or []
    if not vs:
        return []
    opts = []
    for v in vs[0].get("values", []):
        label = normalize_text(_en_label(v))
        for p in v.get("pairs", []):
            if "value" in p:
                opts.append({"code": str(p["value"]).strip(), "label": label})
            elif "from" in p:
                code = f"{p['from']}-{p.get('to', '')}"
                opts.append({"code": code, "label": label})
    return opts


def derive_qtype(item: dict) -> tuple:
    """(qtype, cardinality) from dcf contentType/valueSets. Empirically: a
    coded field is numeric+valueSets (single-select) or alpha+valueSets
    (CSPro Check Box multi-select, one 2-char position per code -- verified
    against every F3 alpha+valueSets Q-item: length == 2 * len(values) in
    every case, no exceptions found)."""
    ct = item.get("contentType")
    vs = item.get("valueSets") or []
    if ct == "image":
        return "image", "single"
    if vs:
        return ("multi", "multi") if ct == "alpha" else ("single", "single")
    if ct == "numeric":
        return "number", "single"
    return "text", "single"


def _strip_apc_comments(text: str) -> str:
    return re.sub(r"\{[^{}]*\}", " ", text)


_PROC_SPLIT_RE = re.compile(r"(?m)^PROC\s+([A-Z0-9_]+)\s*$")
_IF_RE = re.compile(r"^if\s+(.*?)\s+then\b", re.IGNORECASE)
_SKIP_TO_RE = re.compile(r"\bskip\s+to\s+([A-Z0-9_]+)", re.IGNORECASE)
_ENDIF_RE = re.compile(r"^(endif|endfor|enddo)\b", re.IGNORECASE)
_RANGE_RE = re.compile(
    r"\bif\s+(\w+)\s*(?:<|<=)\s*(-?\d+)\s+or\s+\1\s*(?:>|>=)\s*(-?\d+)\s+then",
    re.IGNORECASE,
)
_ERRMSG_CALL_RE = re.compile(r"errmsg\(\s*(\d+)[^;]*;\s*((?:\r?\n\s*)*)(reenter\s*;)?", re.M)


def _extract_skips(body: str) -> list:
    """Per-PROC skip text as 'IF <condition> GOTO <target>', condition
    taken from the nearest enclosing `if ... then` (same line or a prior
    line in the same block; reset at endif/endfor/enddo so a stale
    condition can't leak onto an unrelated later skip)."""
    skips = []
    last_if = None
    for raw in body.split("\n"):
        line = raw.strip()
        if not line:
            continue
        m_if = _IF_RE.match(line)
        if m_if:
            last_if = m_if.group(1)
        m_skip = _SKIP_TO_RE.search(line)
        if m_skip:
            cond = last_if if last_if else "<unconditional>"
            skips.append(normalize_text(f"IF {cond} GOTO {m_skip.group(1)}"))
        if _ENDIF_RE.match(line):
            last_if = None
    return skips


def _extract_validations(body: str) -> list:
    out = []
    for m in _RANGE_RE.finditer(body):
        _fld, lo, hi = m.groups()
        out.append(f"range {lo}..{hi}")
    return out


def _extract_errmsgs(body: str) -> list:
    """[(msgnum, is_hard)]; is_hard = the call is immediately followed by
    `reenter;` (blocks continuation until corrected) vs a soft warn-and-
    continue. Verified against F3's apc: every observed reenter-gated
    errmsg has `reenter;` as the literal next statement."""
    out = []
    for m in _ERRMSG_CALL_RE.finditer(body):
        out.append((m.group(1), m.group(3) is not None))
    return out


def parse_apc(apc_path: Path) -> dict:
    """.ent.apc -> {UPPER field name: {"skip": [...], "validation": [...],
    "errmsgs": [(msgnum, is_hard), ...]}}. PROC-splitting approach matches
    automation/skip_boundary_check.py:parse_apc. Returns {} if the file
    doesn't exist (keeps parse_dcf_qsf_apc usable against dcf-only
    fixtures)."""
    if not apc_path.exists():
        return {}
    txt = _strip_apc_comments(apc_path.read_text(encoding="utf-8"))
    procs = _PROC_SPLIT_RE.split(txt)
    info = {}
    for name, body in zip(procs[1::2], procs[2::2]):
        entry = info.setdefault(name.upper(), {"skip": [], "validation": [], "errmsgs": []})
        entry["skip"].extend(_extract_skips(body))
        entry["validation"].extend(_extract_validations(body))
        entry["errmsgs"].extend(_extract_errmsgs(body))
    return info


def load_qsf_text(qsf_path: Path) -> dict:
    """.ent.qsf -> {UPPER item name: literal EN question text}. Same
    approach as data-harmonization/generate_codebook.py:load_qsf (YAML,
    utf-8-sig, dict.item name, first conditions[].questionText.EN,
    HTML-stripped). Returns {} if missing."""
    if not qsf_path.exists():
        return {}
    import yaml  # local import: only needed for CSPro mode

    d = yaml.safe_load(open(qsf_path, encoding="utf-8-sig"))
    out = {}
    for q in d.get("questions", []):
        name = (q.get("name") or "").split(".")[-1].upper()
        for c in q.get("conditions", []):
            t = strip_html((c.get("questionText") or {}).get("EN", ""))
            if name and t:
                out[name] = t
                break
    return out


def load_mgf_en(mgf_path: Path) -> dict:
    """.ent.mgf `Language = EN` section -> {msgnum: text}. Returns {} if
    missing."""
    if not mgf_path.exists():
        return {}
    text = mgf_path.read_text(encoding="utf-8-sig", errors="replace")
    out = {}
    in_en = False
    for raw in text.split("\n"):
        s = raw.strip()
        if not s or s.startswith("{"):
            continue
        m_lang = re.match(r"Language\s*=\s*(\w+)", s)
        if m_lang:
            in_en = m_lang.group(1).upper() == "EN"
            continue
        if not in_en:
            continue
        m_msg = re.match(r"(\d+)\s+(.*)$", s)
        if m_msg:
            num, txt = m_msg.groups()
            txt = txt.strip()
            if len(txt) >= 2 and txt[0] == txt[-1] == '"':
                txt = txt[1:-1]
            out[num] = normalize_text(txt)
    return out


def parse_dcf_qsf_apc(inst_dir: Path, base: str) -> list:
    """The four build artifacts for one instrument -> list[Row]."""
    inst = inst_dir.name  # "F1"/"F3"/"F4" -- the folder name IS the code
    dcf_items = load_dcf_items(inst_dir / f"{base}.dcf")
    qsf_text = load_qsf_text(inst_dir / f"{base}.ent.qsf")
    apc_info = parse_apc(inst_dir / f"{base}.ent.apc")
    mgf_en = load_mgf_en(inst_dir / f"{base}.ent.mgf")

    rows = []
    for upper_name, (item, section) in dcf_items.items():
        name = item.get("name", upper_name)
        if name.upper().endswith(_OTHER_TXT_SUFFIX):
            continue  # companion field, shares its parent's qnum
        if upper_name in EXCLUDE_ITEMS:
            continue

        if upper_name in DISPOSITION_ITEMS:
            kind = "disposition"
        elif upper_name in CONSENT_ITEMS:
            kind = "consent"
        else:
            kind = "item"

        stem = qsf_text.get(upper_name) or _en_label(item)
        stem = normalize_text(strip_html(stem))
        options = build_options(item)
        qtype, cardinality = derive_qtype(item)
        qnum = derive_qnum(name)

        apc_e = apc_info.get(upper_name, {})
        skip = "; ".join(apc_e.get("skip", []))
        validation = "; ".join(apc_e.get("validation", []))
        msg_parts = []
        for num, is_hard in apc_e.get("errmsgs", []):
            text = mgf_en.get(num, f"[unresolved errmsg {num}]")
            msg_parts.append(f"{'E' if is_hard else 'W'}: {text}")
        messages = "; ".join(msg_parts)

        rows.append(Row(
            inst=inst, qnum=qnum, item_name=name, section=section, kind=kind,
            stem=stem, options=options, qtype=qtype, cardinality=cardinality,
            skip=skip, validation=validation, messages=messages,
        ))
    return rows


# ============================================================================
# PWA mode
# ============================================================================

# Objects with exactly one level of brace nesting (an item/choice/subField's
# own `{...}` plus its `label: {...}` sub-object) -- every shape seen in
# items.ts fits this; deeper nesting doesn't occur.
_OBJ_RE = re.compile(r"\{(?:[^{}]|\{[^{}]*\})*\}")
_EN_RE = re.compile(r"en:\s*'((?:[^'\\]|\\.)*)'")  # proven in audit-translations.py


def _ts_unescape(s: str) -> str:
    return s.replace("\\'", "'").replace('\\\\', '\\')


def _en_text(block: str) -> str:
    m = _EN_RE.search(block or "")
    return _ts_unescape(m.group(1)) if m else ""


_SECTION_ID_RE = re.compile(r"^\s*id:\s*'([A-Za-z0-9]+)',?\s*$")
_SECTION_TITLE_RE = re.compile(r"^\s*title:\s*\{([^{}]*)\},?\s*$")
_ITEM_LINE_RE = re.compile(r"^\s*\{\s*id:\s*'([^']+)'")
_TYPE_RE = re.compile(r"\btype:\s*'([^']+)'")
_REQUIRED_RE = re.compile(r"\brequired:\s*(true|false)")
_LABEL_BLOCK_RE = re.compile(r"\blabel:\s*\{([^{}]*)\}")
_CHOICES_BLOCK_RE = re.compile(r"\bchoices:\s*\[([^\[\]]*)\]")
_SUBFIELDS_BLOCK_RE = re.compile(r"\bsubFields:\s*\[([^\[\]]*)\]")
_VALUE_RE = re.compile(r"\bvalue:\s*'((?:[^'\\]|\\.)*)'")
_ID_RE = re.compile(r"\bid:\s*'([^']+)'")
_KIND_RE = re.compile(r"\bkind:\s*'([^']*)'")

# type -> (qtype, cardinality); everything else (unrecognized) -> ('text','single')
_PWA_QTYPE_MAP = {
    "single": ("single", "single"),
    "multi": ("multi", "multi"),
    "number": ("number", "single"),
    "long-text": ("text", "single"),
    "partial-date": ("date", "single"),
    "multi-field": ("grid", "multi"),  # bundles subFields, see below
}


def parse_items_ts(text: str, inst: str = "F2") -> list:
    """One item per physical line (empirically confirmed, not assumed).
    subFields (Q1's Last/First/Middle-name style multi-field items) emit
    their own child Row per subfield, qnum = "<parent>.<position>" -- the
    same convention as CSPro's Q10_1_STEM -> "10.1"."""
    rows = []
    section_id = ""
    section_title = ""
    for raw in text.split("\n"):
        line = raw.rstrip("\n")

        if not line.lstrip().startswith("{"):
            m_sec = _SECTION_ID_RE.match(line)
            if m_sec:
                section_id = m_sec.group(1)
                continue
            m_title = _SECTION_TITLE_RE.match(line)
            if m_title:
                section_title = _en_text(m_title.group(1))
                continue

        m_item = _ITEM_LINE_RE.match(line)
        if not m_item:
            continue

        item_id = m_item.group(1)
        type_m = _TYPE_RE.search(line)
        qtype_raw = type_m.group(1) if type_m else ""
        qtype, cardinality = _PWA_QTYPE_MAP.get(qtype_raw, ("text", "single"))

        required_m = _REQUIRED_RE.search(line)
        required = (required_m.group(1) == "true") if required_m else True

        label_m = _LABEL_BLOCK_RE.search(line)
        stem = _en_text(label_m.group(1)) if label_m else ""

        options = []
        choices_m = _CHOICES_BLOCK_RE.search(line)
        if choices_m:
            for obj in _OBJ_RE.findall(choices_m.group(1)):
                cl_m = _LABEL_BLOCK_RE.search(obj)
                cv_m = _VALUE_RE.search(obj)
                if not cv_m:
                    continue
                value = _ts_unescape(cv_m.group(1))
                label = (_en_text(cl_m.group(1)) if cl_m else "") or value
                options.append({"code": value, "label": normalize_text(label)})

        qnum = derive_qnum(item_id)
        section = f"{section_id} {section_title}".strip() if section_id else ""
        validation = "required" if required else ""

        rows.append(Row(
            inst=inst, qnum=qnum, item_name=item_id, section=section,
            kind="item" if qnum else "instruction",
            stem=normalize_text(stem), options=options, qtype=qtype,
            cardinality=cardinality, skip="", validation=validation, messages="",
        ))

        subfields_m = _SUBFIELDS_BLOCK_RE.search(line)
        if subfields_m:
            for idx, obj in enumerate(_OBJ_RE.findall(subfields_m.group(1)), start=1):
                sid_m = _ID_RE.search(obj)
                if not sid_m:
                    continue
                sub_id = sid_m.group(1)
                sl_m = _LABEL_BLOCK_RE.search(obj)
                sub_stem = _en_text(sl_m.group(1)) if sl_m else ""
                sk_m = _KIND_RE.search(obj)
                sub_qtype = "number" if (sk_m and sk_m.group(1) == "number") else "text"
                sub_qnum = f"{qnum}.{idx}" if qnum else ""
                rows.append(Row(
                    inst=inst, qnum=sub_qnum, item_name=sub_id, section=section,
                    kind="item", stem=normalize_text(sub_stem), options=[],
                    qtype=sub_qtype, cardinality="single", skip="", validation="", messages="",
                ))
    return rows


_NUMBER_FIELD_RE = re.compile(
    r"^\s*(\w+):\s*z\.coerce\.number\([^)]*\)((?:\.(?:min|max)\(-?\d+(?:\.\d+)?\))*)",
    re.M,
)
_MINMAX_RE = re.compile(r"\.(min|max)\((-?\d+(?:\.\d+)?)\)")


def parse_schema_ts(text: str) -> dict:
    """z.coerce.number(...).min(N).max(M) lines -> {field_id: (lo, hi)}
    (either side may be None). Returns {} if the file doesn't exist --
    caller passes '' for a missing file."""
    out = {}
    for m in _NUMBER_FIELD_RE.finditer(text):
        field_id, chain = m.groups()
        lo = hi = None
        for mm in _MINMAX_RE.finditer(chain):
            if mm.group(1) == "min":
                lo = mm.group(2)
            else:
                hi = mm.group(2)
        if lo is not None or hi is not None:
            out[field_id] = (lo, hi)
    return out


_SECTION_OPEN_RE = re.compile(r"^\s{2}([A-Z]):\s*\{\s*$")
_SECTION_CLOSE_RE = re.compile(r"^\s{2}\},\s*$")
_PREDICATE_RE = re.compile(r"^\s{4}(Q\d+[a-z]?):\s*\(v\)\s*=>\s*(.+?),?\s*$")


def parse_skip_logic_ts(text: str) -> dict:
    """The `predicates` map's per-item arrow-function source ->
    {item_id: predicate source text}. Scoped to the `const predicates =
    { ... }` block only (stops at `export function shouldShow`, before the
    unrelated shouldShowSection/filterChoices logic)."""
    start = text.find("const predicates")
    if start == -1:
        return {}
    end = text.find("\nexport function shouldShow", start)
    block = text[start: end if end != -1 else len(text)]

    out = {}
    in_section = False
    for line in block.split("\n"):
        if _SECTION_OPEN_RE.match(line):
            in_section = True
            continue
        if in_section and _SECTION_CLOSE_RE.match(line):
            in_section = False
            continue
        if in_section:
            m = _PREDICATE_RE.match(line)
            if m:
                out[m.group(1)] = m.group(2).rstrip(",")
    return out


def load_crossfield_messages(en_ts_path: Path) -> dict:
    """i18n/locales/en.ts's `crossField: { ... }` block -> {key: EN text}.
    Brace-matched (not regex-bounded) since some values wrap across two
    lines (`key:\\n  'value',`)."""
    if not en_ts_path.exists():
        return {}
    text = en_ts_path.read_text(encoding="utf-8")
    start = text.find("crossField:")
    if start == -1:
        return {}
    brace_start = text.find("{", start)
    if brace_start == -1:
        return {}
    depth = 0
    end = brace_start
    for i in range(brace_start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                end = i
                break
    block = text[brace_start + 1: end]
    out = {}
    for m in re.finditer(r"(\w+):\s*'((?:[^'\\]|\\.)*)'", block):
        out[m.group(1)] = _ts_unescape(m.group(2))
    return out


_PUSH_RE = re.compile(r"out\.push\(\{(.*?)\}\);", re.S)
_RULE_ID_RE = re.compile(r"\bid:\s*'([^']+)'")
_SEVERITY_RE = re.compile(r"\bseverity:\s*'([^']+)'")
_MSGKEY_RE = re.compile(r"\bkey:\s*'([^']+)'")
_FIELDS_RE = re.compile(r"\bfields:\s*\[([^\]]*)\]")
_QUOTED_RE = re.compile(r"'([^']+)'")


def parse_cross_field_ts(text: str, en_messages: dict) -> list:
    """Each `out.push({ id, severity, message: { key }, fields })` rule ->
    (rule_id, severity, EN message text, [field ids]). `fields` arrays that
    end in a `.filter(...)` spread (e.g. `[..., ...SET.filter((f) =>
    isFilled(values[f]))]`) only yield their literal leading entries -- the
    `[f]` inside the filter callback truncates the non-greedy `[^\\]]*`
    match early. Harmless here: the spread members aren't quoted literals
    either, so they'd contribute nothing extra even with a fully-balanced
    capture; documented as a known limitation of the regex-only PWA parser."""
    rules = []
    for m in _PUSH_RE.finditer(text):
        block = m.group(1)
        id_m = _RULE_ID_RE.search(block)
        sev_m = _SEVERITY_RE.search(block)
        key_m = _MSGKEY_RE.search(block)
        if not (id_m and sev_m and key_m):
            continue
        fields_m = _FIELDS_RE.search(block)
        fields = _QUOTED_RE.findall(fields_m.group(1)) if fields_m else []
        rules.append((id_m.group(1), sev_m.group(1), en_messages.get(key_m.group(1), ""), fields))
    return rules


def parse_pwa(app_dir: Path) -> list:
    """Orchestrates the PWA-side sub-parsers into one list[Row]."""
    items_path = app_dir / "src" / "generated" / "items.ts"
    schema_path = app_dir / "src" / "generated" / "schema.ts"
    skip_path = app_dir / "src" / "lib" / "skip-logic.ts"
    crossfield_path = app_dir / "src" / "lib" / "cross-field.ts"
    en_path = app_dir / "src" / "i18n" / "locales" / "en.ts"

    rows = parse_items_ts(items_path.read_text(encoding="utf-8"), inst="F2")
    by_id = {r.item_name: r for r in rows}

    if schema_path.exists():
        minmax = parse_schema_ts(schema_path.read_text(encoding="utf-8"))
        for field_id, (lo, hi) in minmax.items():
            r = by_id.get(field_id)
            if r is None:
                continue
            piece = f"range {lo or ''}..{hi or ''}"
            r.validation = f"{r.validation}; {piece}" if r.validation else piece

    if skip_path.exists():
        predicates = parse_skip_logic_ts(skip_path.read_text(encoding="utf-8"))
        for item_id, predicate in predicates.items():
            r = by_id.get(item_id)
            if r is not None:
                r.skip = f"visible-if: {predicate}"

    en_messages = load_crossfield_messages(en_path)
    if crossfield_path.exists():
        rules = parse_cross_field_ts(crossfield_path.read_text(encoding="utf-8"), en_messages)
        for rule_id, severity, msg_text, fields in rules:
            tag = "E" if severity == "error" else "W"
            for field_id in fields:
                r = by_id.get(field_id)
                if r is None:
                    continue
                note = f"{tag}: {rule_id} {msg_text}".strip()
                r.messages = f"{r.messages}; {note}" if r.messages else note
                mark = f"cross-field:{rule_id}"
                r.validation = f"{r.validation}; {mark}" if r.validation else mark

    return rows


# ============================================================================
# CLI
# ============================================================================


def _summarize(inst: str, rows: list, out_path: Path) -> None:
    items = [r for r in rows if r.kind == "item"]
    kinds = {}
    for r in rows:
        kinds[r.kind] = kinds.get(r.kind, 0) + 1
    qnum_counts = {}
    for r in items:
        if r.qnum:
            qnum_counts[r.qnum] = qnum_counts.get(r.qnum, 0) + 1
    unique_qnums = len(qnum_counts)
    dupes = sorted(q for q, c in qnum_counts.items() if c > 1)
    unresolved = sum(1 for r in items if not r.qnum)
    print(f"{inst}: {len(rows)} rows -> {out_path}")
    print(f"  items={len(items)}  kinds={kinds}  unresolved_qnum={unresolved}")
    print(f"  unique_qnums={unique_qnums}  duplicate_qnum_groups={len(dupes)}: {dupes}")


def main():
    ap = argparse.ArgumentParser(description="Parse Aug-17 build artifacts into normalized/F{n}-build.csv")
    ap.add_argument("instrument", choices=["F1", "F2", "F3", "F4"])
    ap.add_argument("--cspro-dir", type=Path, default=DEFAULT_CSPRO_DIR, help="CSPro/ checkout root (F1/F3/F4)")
    ap.add_argument("--pwa-dir", type=Path, default=DEFAULT_PWA_DIR, help="F2 PWA app/ root")
    ap.add_argument("--data-dir", type=Path, default=None, help="output instruments-aug17-extract dir (default: ../instruments-aug17-extract relative to this script)")
    args = ap.parse_args()

    data_dir = (args.data_dir or (SCRIPT_DIR / ".." / "instruments-aug17-extract")).resolve()

    if args.instrument == "F2":
        rows = parse_pwa(args.pwa_dir.resolve())
    else:
        inst_dir = (args.cspro_dir / args.instrument).resolve()
        base = INSTRUMENT_BASE[args.instrument]
        rows = parse_dcf_qsf_apc(inst_dir, base)

    out_path = data_dir / "normalized" / f"{args.instrument}-build.csv"
    write_csv(rows, out_path)
    _summarize(args.instrument, rows, out_path)


if __name__ == "__main__":
    main()
