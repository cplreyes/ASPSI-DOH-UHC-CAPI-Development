#!/usr/bin/env python3
r"""F1 Facility Head Survey — combined-view [Block] plan rebuilder for the
hand-maintained FacilityHeadSurvey.fmf.

WHY THIS EXISTS (UAT R4 bugs GH #371 / #372, 2026-06-12):
The R4 combined-view blocks were injected by a one-time script
(tmp/inject_f1_blocks.py, since discarded) that chunked the section groups
into fixed 5-FIELD screens with no regard for question boundaries, skip
logic, or other-specify gating. On a DisplayTogether screen EVERY member
field renders regardless of skip/noinput logic (verified on-device, R4),
so that plan produced:
  * Q10/Q11 and Q13/Q14 on shared screens -> Q10='No' still showed Q11,
    Q13='No' left Q14 active (the postproc `skip to` can't un-render
    fields already on the same screen)                       (GH #371)
  * Q12 ended a screen while its YES/NO other-specify boxes opened the
    NEXT screen -> every Q12 answer "routed into" the specify box (#371)
  * Q19/Q21's _YES_OTHER_TXT / _NO_OTHER_TXT boxes shared screens with
    their parent (or the neighbouring question) -> the wrong-polarity
    box was always visible ("cross-wired")                   (GH #372)

THE PLAN RULES (mirrors F3/F4 generate_fmf.py derive_block_plan + its
R4 `_is_gated_text` fix, adapted to F1's hand-maintained .fmf):
  1. Gated free-text fields (*_TXT / *_SPECIFY, or any field whose .apc
     PROC carries a preproc `noinput` gate) -> their OWN screen, so the
     noinput gate can suppress the whole screen when not triggered.
  2. Multi-select option runs (<BASE>_O01..) -> one checklist screen.
  3. Everything else chunks at MAX_CHUNK=5 per screen, EXCEPT:
       - a field whose PROC contains `skip to` (a skip SOURCE) ENDS its
         screen — nothing it can skip over may share the screen;
       - a `skip to` TARGET field STARTS a new screen — nothing skipped
         over may already be rendered on the target's screen.

Only the section groups that already carry auto-generated DG_* blocks are
rebuilt (A-H survey body). FIELD_CONTROL's hand-made INTERVIEW_STAFF_BLOCK /
VISIT_RECORD_BLOCK and all non-blocked admin/geo/capture groups are untouched.
Position uses the Designer-verified `start + blocks-emitted-before (group
local)` formula from F3/F4 _emit_blocks.

Run AFTER generate_dcf.py / generate_apc.py (it reads the .apc for skip
sources/targets and noinput gates):

    python inject_blocks.py        # rewrites FacilityHeadSurvey.fmf in place
"""

import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
FMF = HERE / "FacilityHeadSurvey.fmf"
APC = HERE / "FacilityHeadSurvey.ent.apc"

MAX_CHUNK = 5
_MULTISELECT_RE = re.compile(r"^(.+?)_O\d+$")
# TRUE Check Box multi-select fields (single alpha, codes concatenated) — each gets
# its OWN DisplayTogether screen, mirroring F3 generate_fmf._CHECKBOX_FIELDS, so the
# tick-list renders alone (its trailing _OTHER_TXT is gated -> already isolated by
# _is_gated_text). GH #377/#378/#379 Check Box redesign of Q49/Q50/Q53/Q58.
_CHECKBOX_FIELDS = {"Q49_QUALITY_CHALL", "Q50_ACCESS_CHALL",
                    "Q53_YK_PACKAGE", "Q58_PERF_INDICATORS",
                    # #529 multi-select conversion
                    "Q64_APPLY_REASON", "Q75_ENROLL_RESPONSIBILITY",
                    "Q76_ENROLL_INITIATIVES", "Q78_ENROLL_CHALL_LIST",
                    "Q79_NOT_ACCRED_REASON", "Q94_CHARGE_ADDL_CAP_REASONS",
                    "Q96_NOT_RECEIVED_REASONS", "Q98_PAYMENT_CHALL_LIST",
                    "Q99_EXPAND_NEXT",
                    "Q65_ACCRED_DIFFICULT", "Q66_WHY_DIFF_PREVENTIVE", "Q67_WHY_DIFF_LAB", "Q68_WHY_DIFF_MEDS", "Q69_WHY_DIFF_INFRA", "Q70_WHY_DIFF_EQUIPMENT", "Q71_WHY_DIFF_HR", "Q72_WHY_DIFF_HIS", "Q73_WHY_DIFF_DOCS", "Q74_WHY_DIFF_DOH_LIC",
                    # #542 Section E (BUCAS / GAMOT)
                    "Q104_BUCAS_SERVICES", "Q105_BUCAS_FACTORS", "Q111_GAMOT_FACTORS",
                    # Section E/G DO-NOT-READ select-all -> Check Box
                    "Q117_ADDR_STOCKOUT_HOW", "Q151_LGU_NOT_SAT_WHY", "Q162_NOT_SATISFIED_WHY",
                    # #636 Section C: Q34 reports-used select_all -> single Check Box.
                    "Q34_DATA_REPORTS_USED",
                    # #576 Carl 'finish F1': 11 more Section G/H select_all -> Check Box.
                    # (#586: Q144 re-added as Check Box per PAPI; Q160 stays single.)
                    "Q144_DIFFICULT_REASON",
                    "Q137_NBB_BARRIERS", "Q140_ZBB_BARRIERS", "Q146_MALASAKIT_WHY",
                    "Q147_NO_MALASAKIT_WHY", "Q149_LGU_SUPPORT_FORMS", "Q155_SEND_REFERRAL_HOW",
                    "Q156_REFERRAL_FORM_TYPE", "Q159_RECEIVE_REFERRAL_HOW", "Q163_HR_CHALL",
                    "Q165_PD_DOCTORS", "Q166_PD_NURSES",
                    # #567 parts 1 & 2: Section F DOH-licensing why-difficult battery
                    # (Q121 gate + Q122-134 per-topic "why"), select_all -> Check Box.
                    "Q121_DOH_LIC_DIFFICULT",
                    "Q122_WHY_DIFF_PT_RIGHTS", "Q123_WHY_DIFF_PT_CARE", "Q124_WHY_DIFF_LEADERSHIP",
                    "Q125_WHY_DIFF_HRM", "Q126_WHY_DIFF_INFO_MGMT", "Q127_WHY_DIFF_SAFE",
                    "Q128_WHY_DIFF_PERF", "Q129_WHY_DIFF_PHYS_PLANT", "Q130_WHY_DIFF_PRICE_INFO",
                    "Q131_WHY_DIFF_EQUIPMENT", "Q132_WHY_DIFF_NAT_LAWS", "Q133_WHY_DIFF_EMERG_CART",
                    "Q134_WHY_DIFF_ADDONS"}


def _is_gated_text(name, noinput_gated):
    """Other-specify / specify free-texts carry a preproc noinput gate — they
    MUST sit on their own screen (see module docstring, rule 1). Suffix match
    is the F3-parity fallback; the .apc noinput scan is authoritative."""
    return name.endswith("_TXT") or name.endswith("_SPECIFY") or name in noinput_gated


def parse_apc():
    """-> (skip_sources, skip_targets, noinput_gated) from the generated .apc."""
    txt = APC.read_text(encoding="utf-8")
    txt = re.sub(r"\{[^{}]*\}", " ", txt)          # strip CSPro comments
    sources, targets, gated = set(), set(), set()
    procs = re.split(r"(?m)^PROC\s+([A-Z0-9_]+)\s*$", txt)
    # procs = [preamble, name1, body1, name2, body2, ...]
    for name, body in zip(procs[1::2], procs[2::2]):
        if re.search(r"\bskip\s+to\b", body):
            sources.add(name)
        if re.search(r"\bnoinput\b", body):
            gated.add(name)
    targets.update(re.findall(r"\bskip\s+to\s+([A-Z0-9_]+)", txt))
    return sources, targets, gated


def qlabel(fields):
    qs = [m.group(1) for m in (re.match(r"Q(\d+)", f) for f in fields) if m]
    if not qs:
        return fields[0]
    return f"Q{qs[0]}" if qs[0] == qs[-1] else f"Q{qs[0]}-Q{qs[-1]}"


def derive_plan(fields, sources, targets, gated):
    """[(label, [member fields])] — every field in exactly one block, contiguous."""
    plan, i, n = [], 0, len(fields)
    while i < n:
        nm = fields[i]
        ms = _MULTISELECT_RE.match(nm)
        if _is_gated_text(nm, gated) or nm in _CHECKBOX_FIELDS:   # gated text / Check Box -> own screen
            plan.append((qlabel([nm]), [nm])); i += 1
        elif ms:
            base, run = ms.group(1), []
            while i < n:
                m2 = _MULTISELECT_RE.match(fields[i])
                if m2 and m2.group(1) == base and not _is_gated_text(fields[i], gated):
                    run.append(fields[i]); i += 1
                else:
                    break
            plan.append((qlabel(run), run))
        else:
            chunk = []
            while i < n and len(chunk) < MAX_CHUNK:
                nn = fields[i]
                if _MULTISELECT_RE.match(nn) or nn in _CHECKBOX_FIELDS or _is_gated_text(nn, gated):
                    break                          # next block kind
                if chunk and nn in targets:
                    break                          # skip TARGET starts a screen
                chunk.append(nn); i += 1
                if nn in sources:
                    break                          # skip SOURCE ends a screen
            plan.append((qlabel(chunk), chunk))
    return plan


def parse_sections(text):
    """fmf text -> ordered [(header_or_None, [lines])] chunks, verbatim."""
    lines = text.split("\n")
    chunks, cur = [], (None, [])
    for ln in lines:
        if re.match(r"^\[[A-Za-z]+\]\s*$", ln):
            if cur[1]:
                chunks.append(cur)
            cur = (ln.strip()[1:-1], [ln])
        else:
            cur[1].append(ln)
    if cur[1]:
        chunks.append(cur)
    return chunks


def main():
    sources, targets, gated = parse_apc()
    raw = FMF.read_bytes()
    crlf = b"\r\n" in raw                      # detect BEFORE newline translation
    text = raw.decode("utf-8-sig").replace("\r\n", "\n")
    chunks = parse_sections(text)

    # First pass: per group, ordered fields + whether it has DG_ blocks.
    group_fields, group_has_dg, order = {}, set(), []
    cur_group = None
    for kind, lines in chunks:
        body = "\n".join(lines)
        if kind == "Group":
            m = re.search(r"(?m)^Name=(\S+)", body)
            cur_group = m.group(1) if m else None
            if cur_group:
                order.append(cur_group)
                group_fields.setdefault(cur_group, [])
        elif kind == "EndGroup":
            cur_group = None
        elif kind == "Field" and cur_group:
            m = re.search(r"(?m)^Name=(\S+)", body)
            if m:
                group_fields[cur_group].append(m.group(1))
        elif kind == "Block" and cur_group:
            m = re.search(r"(?m)^Name=(\S+)", body)
            if m and m.group(1).startswith("DG_"):
                group_has_dg.add(cur_group)

    rebuild = [g for g in order if g in group_has_dg]

    # Second pass: drop DG_ blocks; insert fresh plan before each [EndGroup].
    out, cur_group, counter = [], None, 0
    for kind, lines in chunks:
        body = "\n".join(lines)
        if kind == "Group":
            m = re.search(r"(?m)^Name=(\S+)", body)
            cur_group = m.group(1) if m else None
        elif kind == "Block" and cur_group in rebuild:
            m = re.search(r"(?m)^Name=(\S+)", body)
            if m and m.group(1).startswith("DG_"):
                continue                            # strip old auto block
        elif kind == "EndGroup" and cur_group not in rebuild:
            cur_group = None
        elif kind == "EndGroup" and cur_group in rebuild:
            fields = group_fields[cur_group]
            plan = derive_plan(fields, sources, targets, gated)
            emitted, pos = 0, 0
            for label, members in plan:
                start = fields.index(members[0])
                assert fields[start:start + len(members)] == members
                out.append(("Block", [
                    "[Block]",
                    f"Name=DG_{cur_group}_{counter}",
                    f"Label={label}",
                    "DisplayTogether=Yes",
                    f"Position={start + emitted}",
                    f"Length={len(members)}",
                    "  ",
                ]))
                emitted += 1
                counter += 1
            cur_group = None
        out.append((kind, lines))

    new_text = "\n".join("\n".join(lines) for _, lines in out)
    # parse_sections/join round-trip keeps original line structure; chunks we
    # inject already end with the "  " separator line followed by the next
    # section's header, matching the surrounding style.
    if crlf:
        new_text = new_text.replace("\n", "\r\n")
    FMF.write_bytes(b"\xef\xbb\xbf" + new_text.encode("utf-8"))

    # Report
    nblocks = counter
    print(f"Rebuilt DG_ blocks in {len(rebuild)} groups -> {nblocks} blocks")
    for g in rebuild:
        fields = group_fields[g]
        plan = derive_plan(fields, sources, targets, gated)
        covered = sum(len(m) for _, m in plan)
        assert covered == len(fields), (g, covered, len(fields))
        print(f"  {g}: {len(fields)} fields -> {len(plan)} screens")
    return 0


if __name__ == "__main__":
    sys.exit(main())
