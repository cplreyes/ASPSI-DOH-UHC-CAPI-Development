from shared.form_layout_engine import (
    next_row_position, FieldPosition, TextPosition, RowPosition,
    pick_capture_type, emit_field_block, emit_text_block,
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


def test_pick_capture_type_yes_no_is_radiobutton():
    assert pick_capture_type(value_set_size=2, item_type="numeric", item_length=1) == "RadioButton"


def test_pick_capture_type_5_option_single_select_is_radiobutton():
    assert pick_capture_type(value_set_size=5, item_type="numeric", item_length=1) == "RadioButton"


def test_pick_capture_type_10_option_single_select_is_dropdown():
    assert pick_capture_type(value_set_size=10, item_type="numeric", item_length=2) == "DropDown"


def test_pick_capture_type_short_alpha_is_textbox():
    assert pick_capture_type(value_set_size=0, item_type="alpha", item_length=80) == "TextBox"


def test_pick_capture_type_long_alpha_is_multiline_textbox():
    assert pick_capture_type(value_set_size=0, item_type="alpha", item_length=200) == "TextBox"


def test_pick_capture_type_numeric_no_value_set_is_textbox():
    assert pick_capture_type(value_set_size=0, item_type="numeric", item_length=4) == "TextBox"


def test_pick_capture_type_multi_select_is_checkbox():
    assert pick_capture_type(value_set_size=5, item_type="multi", item_length=1) == "CheckBox"


def test_emit_field_block_radio():
    result = emit_field_block(
        item_name="Q4_SEX",
        dict_name="FACILITYHEADSURVEY_DICT",
        position=FieldPosition(x=1695, y=120, w=29, h=20),
        capture_type="RadioButton",
        form_index=8,
    )
    assert "[Field]" in result
    assert "Name=Q4_SEX" in result
    assert "Position=1695,120,1724,140" in result
    assert "Item=Q4_SEX,FACILITYHEADSURVEY_DICT" in result
    assert "DataCaptureType=RadioButton" in result
    assert "Form=8" in result


def test_emit_field_block_textbox_unicode_marker():
    result = emit_field_block(
        item_name="Q15_OTHER_TXT",
        dict_name="FACILITYHEADSURVEY_DICT",
        position=FieldPosition(x=1695, y=387, w=970, h=20),
        capture_type="TextBox",
        form_index=8,
    )
    assert "UseUnicodeTextBox=Yes" in result
    assert "DataCaptureType=TextBox" in result


def test_emit_text_block():
    result = emit_text_block(
        position=TextPosition(x=50, y=120, w_max=1645, h=16),
        text="4. What is your sex?",
    )
    assert result.startswith("[Text]\n")
    assert "Position=50,120," in result
    assert "Text=4. What is your sex?" in result
