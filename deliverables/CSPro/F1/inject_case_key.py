#!/usr/bin/env python3
"""Inject the case-key entry form into F1's static FacilityHeadSurvey.fmf.

WHY THIS EXISTS
---------------
F3/F4 build their .fmf from a generator (generate_fmf.py), so the case-key fix
(placing the level ID items on FORM000 / IDS0_FORM, entered FIRST, before the
consent form) lives in that generator. F1's .fmf is a hand-authored static file
with NO generator -- but it has the identical latent bug: FORM000 and its
IDS0_FORM group are EMPTY, so the case-key ID items
(REGION_CODE / PROVINCE_HUC_CODE / CITY_MUNICIPALITY_CODE / FACILITY_NO /
CASE_SEQ) are on no form and set by nothing. A consent refusal (which runs
`endlevel`) then dies with "Warning 1026: All of the ID fields were not filled"
because no case can save without a key.

This is a POST-PROCESSOR, not a hand-edit: it programmatically reads the dict's
level ID items and regenerates the FORM000 [Form] block and the IDS0_FORM
[Group] block. It is idempotent -- re-running rebuilds those two blocks from
scratch, so it stays in sync if the dict's ID items change. (IRON-RULE
compliant: we never hand-edit the .fmf; we generate the key-form portion.)

CSPro DOES put ID items on the first form as ordinary [Field]s -- cf. the CAPI
Census "Geocodes" form GEOCODES_FORM. The earlier "id items get stripped" note
was a misdiagnosis: the empty IDS0_FORM was simply never enterable.

Run:  python inject_case_key.py
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DCF = HERE / "FacilityHeadSurvey.dcf"
FMF = HERE / "FacilityHeadSurvey.fmf"

# Layout constants -- identical to F3/F4 generate_fmf.py so the key form matches.
ROW_H = 30          # vertical pitch between fields
TOP_Y = 27          # first field's top
LABEL_X = 50
LABEL_X2 = 330
FIELD_X = 350
FIELD_TEXTBOX_X2 = 760
FIELD_H = 20
TEXT_H = 16
FORM_W = 806

KEY_LABEL = "Case Key (Facility Head ID)"


def _form_height(n_items):
    return max(300, TOP_Y + n_items * ROW_H + 40)


def read_id_items():
    d = json.loads(DCF.read_text(encoding="utf-8"))
    items = d["levels"][0]["ids"]["items"]
    out = []
    for it in items:
        label = it["labels"][0]["text"] if it.get("labels") else it["name"]
        out.append({
            "name": it["name"],
            "label": label.replace("\n", " ").replace("\r", " ").strip(),
            "coded": bool(it.get("valueSets")),
            "alpha": it.get("contentType") == "alpha",
        })
    return out


def dict_name_from_fmf(text):
    """Reuse the exact dict symbol already referenced by the FMF's fields."""
    m = re.search(r"Item=[A-Z0-9_]+,([A-Z0-9_]+)\b", text)
    if not m:
        sys.exit("ERROR: could not find a dict symbol in any existing [Field] Item= line.")
    return m.group(1)


def build_form_block(item_names):
    height = _form_height(len(item_names))
    lines = [
        "[Form]",
        "Name=FORM000",
        f"Label={KEY_LABEL}",
        "Level=1",
        f"Size={FORM_W},{height}",
        "  ",
    ]
    lines += [f"Item={n}" for n in item_names]
    lines += ["  ", "[EndForm]"]
    return "\n".join(lines)


def build_group_block(items, dict_name):
    lines = [
        "[Group]",
        "Required=Yes",
        "Name=IDS0_FORM",
        f"Label={KEY_LABEL}",
        "Form=1",
        "Max=1",
        "  ",
    ]
    for i, it in enumerate(items):
        y = TOP_Y + i * ROW_H
        field_x2 = FIELD_TEXTBOX_X2  # all F1 id items are numeric TextBoxes
        capture = "RadioButton" if it["coded"] else "TextBox"
        lines.append("[Field]")
        lines.append(f"Name={it['name']}")
        lines.append(f"Position={FIELD_X},{y},{field_x2},{y + FIELD_H}")
        lines.append(f"Item={it['name']},{dict_name}")
        if not it["coded"] and it["alpha"]:
            lines.append("UseUnicodeTextBox=Yes")
        lines.append(f"DataCaptureType={capture}")
        lines.append("Form=1")
        lines.append("  ")
        lines.append("[Text]")
        lines.append(f"Position={LABEL_X},{y + 3},{LABEL_X2},{y + 3 + TEXT_H}")
        lines.append(f"Text={it['label']}")
        lines.append(" ")
        lines.append("  ")
    lines.append("[EndGroup]")
    return "\n".join(lines)


def main():
    items = read_id_items()
    text = FMF.read_text(encoding="utf-8")
    dict_name = dict_name_from_fmf(text)

    # Match the whole FORM000 [Form] block (idempotent: rebuilt each run).
    form_re = re.compile(r"\[Form\]\s*\nName=FORM000\b.*?\[EndForm\]", re.DOTALL)
    # Match the IDS0_FORM [Group] block (first group; preceded by Required=Yes).
    group_re = re.compile(
        r"\[Group\]\s*\nRequired=Yes\s*\nName=IDS0_FORM\b.*?\[EndGroup\]", re.DOTALL
    )

    if not form_re.search(text):
        sys.exit("ERROR: FORM000 [Form] block not found.")
    if not group_re.search(text):
        sys.exit("ERROR: IDS0_FORM [Group] block not found.")

    new_form = build_form_block([it["name"] for it in items])
    new_group = build_group_block(items, dict_name)

    text = form_re.sub(lambda _: new_form, text, count=1)
    text = group_re.sub(lambda _: new_group, text, count=1)

    FMF.write_text(text, encoding="utf-8")

    print(f"Injected case-key form into {FMF.name}")
    print(f"  dict symbol : {dict_name}")
    print(f"  FORM000 items ({len(items)}): " + ", ".join(it["name"] for it in items))
    print(f"  IDS0_FORM fields: {len(items)} [Field]/[Text] blocks")


if __name__ == "__main__":
    main()
