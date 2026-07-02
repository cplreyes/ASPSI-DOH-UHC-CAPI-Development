import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from generate_apc import build_apc


def test_apc_inlines_helper_into_single_proc_global():
    apc = build_apc()
    # Exactly one PROC GLOBAL *header line* (helper inlined, not #included).
    # Count header lines, not the substring — the word may also appear in comments.
    header_lines = [ln for ln in apc.splitlines() if ln.strip() == "PROC GLOBAL"]
    assert len(header_lines) == 1
    # No actual #include DIRECTIVE (a directive starts the line; the word may
    # legitimately appear inside a { } comment explaining why we inline).
    assert not [ln for ln in apc.splitlines() if ln.strip().startswith("#include")]
    # The inlined GPS + photo helper functions are present
    assert "function ReadGPSReading" in apc
    assert "function TakeVerificationPhoto" in apc


def test_apc_auto_stamps_and_protects_on_tp_type():
    apc = build_apc()
    assert "PROC TP_TYPE" in apc
    assert "ReadGPSReading(120, 20)" in apc
    assert 'sysdate("YYYYMMDD")' in apc and 'systime("HHMM")' in apc
    # captured-once guard + protect of the stamped fields
    assert "if length(strip(TP_TIMESTAMP)) = 0 then" in apc
    assert "protect(TP_GPS_LATITUDE, true)" in apc
    assert "protect(TP_TIMESTAMP, true)" in apc


def test_apc_line_index_and_other_note_gate_and_photo():
    apc = build_apc()
    assert "PROC TP_LINE" in apc and "TP_LINE = curocc();" in apc
    assert "PROC TP_OUTCOME_NOTE" in apc and "TP_TYPE = 8" in apc and "reenter;" in apc
    assert "PROC CAPTURE_VERIFICATION_PHOTO" in apc and "TakeVerificationPhoto(fn)" in apc
