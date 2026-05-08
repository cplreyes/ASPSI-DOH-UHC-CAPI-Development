"""form_layout_engine.py — position + control-type math for Designer-free .fmf emission.

The existing F1 .fmf (Designer-laid-out, 9020 lines) is the reference for what
"good enough" looks like; this module emits the same structural shapes via
single-column auto-layout per Form-Layout-Principles.md sec 2.
"""
from dataclasses import dataclass


# Layout constants — derived from Carl's existing F1 .fmf
LABEL_X = 50          # text labels start at x=50
LABEL_H = 16          # text label height
FIELD_X = 1695        # control starts at x=1695 (single-column right-rail layout)
FIELD_H = 20          # control height
ROW_DELTA = 30        # each row is 30 pixels tall


@dataclass(frozen=True)
class FieldPosition:
    x: int
    y: int
    w: int
    h: int


@dataclass(frozen=True)
class TextPosition:
    x: int
    y: int
    w_max: int   # max width before colliding with the field
    h: int


@dataclass(frozen=True)
class RowPosition:
    field: FieldPosition
    text: TextPosition


def pick_capture_type(value_set_size: int, item_type: str, item_length: int) -> str:
    """Return the CSPro DataCaptureType for a dictionary item.

    Per Form-Layout-Principles.md sec 4:
      - value_set_size == 0  -> TextBox (numeric uses numpad, alpha uses keyboard)
      - value_set_size 2-7   -> RadioButton
      - value_set_size 8+    -> DropDown
      - multi-select         -> CheckBox  (caller signals via item_type='multi')
    """
    if item_type == "multi":
        return "CheckBox"
    if value_set_size == 0:
        return "TextBox"
    if value_set_size <= 7:
        return "RadioButton"
    return "DropDown"


def next_row_position(prev_y: int, field_w: int = 29) -> RowPosition:
    """Compute the (x, y, w, h) for the next row's label and control.

    prev_y: y-coordinate of the previous row (0 for the first row -> starts at y=30).
    field_w: control width — caller decides per control type (radio = 29, textbox = wider).
    """
    y = prev_y + ROW_DELTA
    field = FieldPosition(x=FIELD_X, y=y, w=field_w, h=FIELD_H)
    text = TextPosition(
        x=LABEL_X,
        y=y,
        w_max=FIELD_X - LABEL_X,   # max width before colliding with the field
        h=LABEL_H,
    )
    return RowPosition(field=field, text=text)
