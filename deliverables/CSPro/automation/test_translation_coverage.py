import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import translation_coverage as tc  # noqa: E402

SUMMARY = """Languages: EN, FIL, BCL, BIS, CEB, WAR, HIL, ILO
    FIL: 1104/1363 labels translated (81%)
    BCL: 1090/1363 labels translated (80%)
"""


def test_parse_generator_summary():
    assert tc.parse_generator_summary(SUMMARY) == {"FIL": (1104, 1363, 81), "BCL": (1090, 1363, 80)}


def test_f2_label_coverage(tmp_path):
    p = tmp_path / "items.ts"
    p.write_text("label: { en: 'A', fil: 'a', ceb: 'b' }, label: { en: 'B', fil: 'c' }", encoding="utf-8")
    total, per = tc.f2_label_coverage(p)
    assert total == 2 and per["fil"] == 2 and per["ceb"] == 1 and per["bcl"] == 0


def test_render_table_shows_delta():
    before = {"F1": {"FIL": 67}, "F2": {"fil": 75}}
    after = {"F1": {"FIL": 81}, "F2": {"fil": 88}}
    md = tc.render_table(before, after)
    assert "| F1 | FIL | 67% | 81% | +14 |" in md and "| F2 | fil | 75% | 88% | +13 |" in md


def test_f2_counts_agree_with_the_pwa_script():
    """The F2 row has ONE source of truth: deliverables/F2/PWA/app/scripts/f2-coverage.py.

    f2_label_coverage() re-implements that script's two regexes so the counting is unit
    testable against a fixture; this test runs the real script on the real items.ts and
    fails the moment the two drift apart (the pre-flight T22/T44 ruling).
    """
    assert tc.f2_from_script() == tc.f2_label_coverage(tc.F2_ITEMS)
