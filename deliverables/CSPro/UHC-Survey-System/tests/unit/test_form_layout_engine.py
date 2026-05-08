from shared.form_layout_engine import (
    next_row_position, FieldPosition, TextPosition, RowPosition,
)


def test_first_row_starts_at_y_30():
    pos = next_row_position(prev_y=0)
    assert pos.field == FieldPosition(x=1695, y=30, w=29, h=20)
    assert pos.text == TextPosition(x=50, y=30, w_max=1645, h=16)


def test_second_row_at_y_60():
    pos = next_row_position(prev_y=30)
    assert pos.field.y == 60
    assert pos.text.y == 60


def test_text_width_clamps_to_left_of_field():
    pos = next_row_position(prev_y=0)
    # Text must end before field starts (FIELD_X - LABEL_RIGHT_MARGIN)
    assert pos.text.x + pos.text.w_max <= pos.field.x - 0


def test_field_width_overridable_for_textbox():
    pos = next_row_position(prev_y=0, field_w=970)
    assert pos.field.w == 970
