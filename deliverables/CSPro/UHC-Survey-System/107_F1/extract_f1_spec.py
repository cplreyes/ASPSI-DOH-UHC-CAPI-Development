"""extract_f1_spec.py — throwaway one-shot.

Read the archived hand-laid F1.fmf
(deliverables/.archive/pre-rebuild-2026-05-11/CSPro/F1/FacilityHeadSurvey.fmf)
and produce F1.spec.md with one verbatim Q-text block per item, in the format
question_text_loader.py expects.

Algorithm: walk [Field] blocks in order. For each [Field], find the nearest
following [Text] block and pair them. Emit:
    ### <Field.Name>
    <Text.Text>
"""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Worktree is several levels deep — main checkout's archived F1 dir is hardcoded
# below. Repointed 2026-05-12 after Sprint 005 R3 archive sequence moved the
# pre-rebuild F1 build under deliverables/.archive/pre-rebuild-2026-05-11/.
LEGACY_FMF = Path(
    r"C:\Users\analy\Documents\analytiflow\1_Projects\ASPSI-DOH-CAPI-CSPro-Development"
    r"\deliverables\.archive\pre-rebuild-2026-05-11\CSPro\F1\FacilityHeadSurvey.fmf"
)

FIELD_RE = re.compile(r"\[Field\]\nName=(\S+).*?(?=\[Field\]|\[Text\]|\Z)", flags=re.DOTALL)
TEXT_RE  = re.compile(r"\[Text\]\nPosition=[^\n]*\nText=([^\n]*)", flags=re.DOTALL)


def main():
    if not LEGACY_FMF.exists():
        raise SystemExit(f"legacy F1.fmf not found at {LEGACY_FMF}")

    content = LEGACY_FMF.read_text(encoding="utf-8")

    # Walk through the file, alternating Field/Text blocks
    out_lines = ["# F1 Verbatim Question Text\n"]
    out_lines.append(f"_Generated from {LEGACY_FMF.name} (hand-laid Designer reference) on 2026-05-08._\n")

    # Find all [Field]/[Text] blocks in order
    blocks = re.finditer(r"\[(Field|Text)\][^\[]+", content)
    pending_name = None
    item_count = 0
    for m in blocks:
        block_type = m.group(1)
        block_body = m.group(0)

        if block_type == "Field":
            name_m = re.search(r"Name=(\S+)", block_body)
            if name_m:
                pending_name = name_m.group(1).strip()
        elif block_type == "Text" and pending_name:
            text_m = re.search(r"Text=([^\n]*)", block_body)
            if text_m:
                text = text_m.group(1).strip()
                out_lines.append(f"### {pending_name}\n{text}\n")
                item_count += 1
                pending_name = None

    (HERE / "F1.spec.md").write_text("\n".join(out_lines), encoding="utf-8")
    print(f"wrote F1.spec.md with {item_count} items extracted from legacy fmf")


if __name__ == "__main__":
    main()
