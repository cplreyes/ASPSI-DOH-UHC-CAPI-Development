"""generate_fmf.py — SupervisorApp CSPro Form File generator (slim).

Emits SupervisorApp.generated.fmf — a COMPLETE, bindable CSPro 8.0 form file for
SupervisorApp.dcf, full-structure ([FormFile] -> [Form]s -> [Level] -> [Group]s with
[Field]+[Text] per item), mirroring the F1/F4 auto-layout. The repeating TOUCHPOINT
record is emitted as a ROSTER group (Type=Record / Max); the binary Image item
VERIFICATION_PHOTO_IMAGE is OFF-FORM (binary items can't sit on a form). Iron rule:
never hand-edit the .fmf — edit this generator and rerun.

Run:  python generate_fmf.py        # writes SupervisorApp.generated.fmf next to this file
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from generate_dcf import build_sv_dictionary
from cspro_helpers import _truncate_long_labels

DICT_LABEL = "SupervisorApp"
FF_NAME = "SUPERVISORAPP_FF"
DCF_REL_PATH = r".\SupervisorApp.dcf"

DEFAULT_FONT = ("DefaultTextFont=-013 0000 0000 0000 0700 0000 0000 0000 "
                "0000 0000 0000 0000 0000 Arial")
ENTRY_FONT = ("FieldEntryFont=0018 0000 0000 0000 0600 0000 0000 0000 "
              "0000 0000 0000 0000 0000 Courier New")

# Auto-layout geometry (mirrors the working F1/F4 .fmf).
ROW_H = 30; TOP_Y = 27; LABEL_X = 50; LABEL_X2 = 330
FIELD_X = 350; FIELD_TEXTBOX_X2 = 760; FIELD_RADIO_X2 = 365
FIELD_H = 20; TEXT_H = 16; FORM_W = 806

# Binary Image items cannot be placed on a form (capture is driven from the on-form
# CAPTURE_VERIFICATION_PHOTO trigger; the bytes sync to CSWeb off-form).
OFF_FORM_ITEMS = {"VERIFICATION_PHOTO_IMAGE"}

# Declarative form plan after FORM000 (the case-key id form): (form label, record).
FORM_PLAN = [
    ("Facility Visit Header",   "VISIT_HEADER"),
    ("Courtesy-Call Outcomes",  "COURTESY_CALL"),
    ("Facility Touchpoint Log", "TOUCHPOINT"),
]


def _form_height(n_items):
    return max(300, TOP_Y + n_items * ROW_H + 40)


def _emit_form(lines, num, label, item_names, height, roster=None):
    lines += ["[Form]", f"Name=FORM{num:03d}", f"Label={label}", "Level=1"]
    if roster:
        # Repeat= marks the form as repeating over the roster record; the [Group]
        # Type=Record alone is not enough (CSEntry rejects the reconcile otherwise).
        lines.append(f"Repeat={roster['type_name']}")
    lines += [f"Size={FORM_W},{height}", "  "]
    for n in item_names:
        lines.append(f"Item={n}")
    lines += ["  ", "[EndForm]", "  "]


def _emit_group(lines, sym, label, form_one_based, item_objs, dict_name, roster=None):
    lines += ["[Group]", "Required=Yes", f"Name={sym}", f"Label={label}",
              f"Form={form_one_based}"]
    if roster:
        lines += ["Type=Record", f"TypeName={roster['type_name']}", f"Max={roster['max']}"]
    else:
        lines.append("Max=1")
    if not item_objs:
        lines += ["[EndGroup]", "  "]
        return
    lines.append("  ")
    for i, it in enumerate(item_objs):
        y = TOP_Y + i * ROW_H
        coded = bool(it.get("valueSets"))
        is_alpha = it.get("contentType") == "alpha"
        x2 = FIELD_RADIO_X2 if coded else FIELD_TEXTBOX_X2
        capture = "RadioButton" if coded else "TextBox"
        text = (it["labels"][0]["text"] if it.get("labels") else it["name"]).replace("\n", " ").replace("\r", " ")
        lines += ["[Field]", f"Name={it['name']}",
                  f"Position={FIELD_X},{y},{x2},{y + FIELD_H}",
                  f"Item={it['name']},{dict_name}"]
        if not coded and is_alpha:
            lines.append("UseUnicodeTextBox=Yes")
        lines += [f"DataCaptureType={capture}", f"Form={form_one_based}", "  ",
                  "[Text]", f"Position={LABEL_X},{y + 3},{LABEL_X2},{y + 3 + TEXT_H}",
                  f"Text={text}", " ", "  "]
    lines += ["[EndGroup]", "  "]


def build_fmf():
    d = build_sv_dictionary()
    _truncate_long_labels(d)   # match the .dcf's 255-char label cap (CSPro max)
    dict_name = d["name"]
    level = d["levels"][0]
    level_name = level["name"]
    recs = {r["name"]: r for r in level["records"]}
    id_objs = list(level["ids"]["items"])

    def _roster_info(rn):
        occ = recs[rn].get("occurrences") or {}
        mx = occ.get("maximum", 1) if isinstance(occ, dict) else 1
        return {"type_name": rn, "max": mx} if (mx and mx > 1) else None

    # FORM000 = case-key id items (FACILITY_CODE), entered first.
    forms = [{"num": 0, "label": "Case Key (Facility Code)", "sym": "IDS0_FORM",
              "names": [it["name"] for it in id_objs], "objs": id_objs, "roster": None}]
    for idx, (label, rn) in enumerate(FORM_PLAN, start=1):
        objs = [it for it in recs[rn]["items"] if it["name"] not in OFF_FORM_ITEMS]
        forms.append({"num": idx, "label": label, "sym": f"{rn}_FORM",
                      "names": [it["name"] for it in objs], "objs": objs,
                      "roster": _roster_info(rn)})

    lines = ["[FormFile]", "Version=CSPro 8.0", f"Name={FF_NAME}", f"Label={DICT_LABEL}",
             DEFAULT_FONT, ENTRY_FONT, "Type=SystemControlled", "  ",
             "[Dictionaries]", f"File={DCF_REL_PATH}", "  "]
    for f in forms:
        _emit_form(lines, f["num"], f["label"], f["names"],
                   _form_height(len(f["objs"])), roster=f["roster"])
    lines += ["[Level]", f"Name={level_name}", f"Label={DICT_LABEL} Level", "  "]
    for f in forms:
        _emit_group(lines, f["sym"], f["label"], f["num"] + 1, f["objs"],
                    dict_name, roster=f["roster"])
    return "\r\n".join(lines) + "\r\n"


def main():
    out = Path(__file__).parent / "SupervisorApp.generated.fmf"
    out.write_text(build_fmf(), encoding="utf-8")
    sys.stderr.write(f"Wrote {out}\n")


if __name__ == "__main__":
    main()
