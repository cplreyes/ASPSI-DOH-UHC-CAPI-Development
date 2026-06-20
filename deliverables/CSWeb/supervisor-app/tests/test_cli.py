import os, shutil
from supervisor_qa_report import build_report

HERE = os.path.dirname(__file__)
FIX = os.path.join(HERE, "fixtures")


def test_build_report_combines_instruments(tmp_path):
    exp = tmp_path / "exports"
    exp.mkdir()
    shutil.copy(os.path.join(FIX, "f3_sample.csv"), exp / "F3.csv")
    shutil.copy(os.path.join(FIX, "f4_sample.csv"), exp / "F4.csv")
    assign = tmp_path / "a.csv"
    assign.write_text("ENUMERATOR_ID,FACILITY_CODE,INSTRUMENT,TARGET_COUNT\n"
                      "se-004,01-02-800-01,F3,10\nse-050,01-02-800-02,F4,5\n", encoding="utf-8")
    html = build_report(str(exp), str(assign), cluster="01028", today="20260621")
    assert "Coverage vs plan" in html
    assert "Withdrew" in html          # F3 case 002 + F4 case 002
    assert "se-004" in html and "se-050" in html
    assert "Juan Dela Cruz" not in html and "Ana Cruz" not in html   # PII-light
