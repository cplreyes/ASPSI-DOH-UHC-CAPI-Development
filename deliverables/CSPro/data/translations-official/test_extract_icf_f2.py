"""extract_icf_f2.py — the F2 PWA consent screen (chrome `consent.*`) from the Aug-21 papers.

The fixtures are the REAL strings, not simplified stand-ins: `en.ts` carries CAPI-only
sentences the paper never prints ("The survey may take more or less than an hour to
complete." / "Your progress is saved automatically on this device …") and the paper
answers them with its own read-aloud variants ("The interview may last for more or less
than an hour."). An extractor tested only against a fixture whose English matches the
paper word for word would pass here and ship the paper's leftover English at the head of
every stored paragraph, which is exactly what this file exists to prevent.
"""

import os
import sys
import textwrap

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from conftest import make_pdf  # noqa: E402
import extract_icf_f2 as m  # noqa: E402

# --- en.ts, verbatim (src/i18n/locales/en.ts `consent`, read 2026-08-26) -------------
EN_STUDY = (
    "The Asian Social Project Services, Inc. (ASPSI) requests your participation in a study on "
    "Universal Health Care (UHC). This study aims to generate evidence on the overall experience "
    "of the healthcare service providers and the general public to support continuous monitoring, "
    "evaluation, and learning of the implementation of the UHC Act, its Implementing Rules and "
    "Regulations (IRR), and packages of programs like Yaman ng Kalusugan Program (YAKAP), No "
    "Balance Billing (NBB), Zero Balance Billing (ZBB), Bagong Urgent Care and Ambulatory Services "
    "(BUCAS) centers, and Guaranteed and Accessible Medications for Outpatient Treatment (GAMOT). "
    "The Department of Health funded this study. The survey may take more or less than an hour to "
    "complete. The questions will cover your professional profile, UHC awareness, changes in "
    "facility operations since 2019, specialized programs (YAKAP/Konsulta, NBB/ZBB, BUCAS, GAMOT), "
    "referral systems, professional fee charging, task sharing, and your overall job satisfaction, "
    "including compensation, work environment, and professional development opportunities. Your "
    "progress is saved automatically on this device — you can pause and continue at any time "
    "before submitting.")
EN_RIGHTS = ("You are free to decline participation or to stop at any time before submitting the form. "
             "Choosing not to participate will not result in any penalty, and you will not have to pay "
             "anything to take part in this study.")
EN_CONTACT = "If you have concerns or questions about your rights as a participant, you can contact:"
ANCHORS = {"infoStudy": EN_STUDY, "infoRights": EN_RIGHTS, "contactsHeading": EN_CONTACT}

# --- the paper, verbatim (F2-Tagalog_..._Aug21.pdf p.1, read 2026-08-26) -------------
# The paper is a read-aloud script: it swaps the two CAPI-only sentences for interview
# wording and stops before the "Your progress …" tail. Both edits sit MID-paragraph, so
# locate() stops on a prefix and the rest of the paper's English trails the anchor.
PAPER_STUDY = EN_STUDY.replace(
    "The survey may take more or less than an hour to complete.",
    "The interview may last for more or less than an hour.").split(" Your progress")[0]
PAPER_RIGHTS = EN_RIGHTS.replace(" before submitting the form", "")
FIL_STUDY = (
    "Ang Asian Social Project Services, Inc. (ASPSI) ay inaanyayahan kayong lumahok sa isang "
    "interbyu bilang bahagi ng pag-aaral tungkol sa Universal Health Care (UHC). Layunin ng "
    "pag-aaral na ito na makakuha ng impormasyon tungkol sa karanasan ng mga tagapagbigay ng "
    "serbisyong pangkalusugan at ng publiko upang makatulong sa patuloy na pagsubaybay at "
    "pagsusuri sa pagpapatupad ng UHC Act, mga Implementing Rules and Regulations (IRR) nito, at "
    "mga programang tulad ng Yaman ng Kalusugan Program (YAKAP), No Balance Billing (NBB)/Zero "
    "Balance Billing (ZBB), Bagong Urgent Care and Ambulatory Services (BUCAS), at Guaranteed and "
    "Accessible Medications for Outpatient Treatment (GAMOT). Ang pag-aaral na ito ay pinondohan "
    "ng Kagawaran ng Kalusugan.")
FIL_RIGHTS = ("Malaya kang tumanggi sa paglahok o huminto anumang oras. Ang pagpili na hindi sumali ay "
              "hindi magreresulta sa anumang parusa, at hindi ka kailangang magbayad para makibahagi "
              "sa pag-aaral na ito.")
FIL_CONTACT = ("Kung mayroon kang mga isyu o tanong tungkol sa iyong mga karapatan bilang kalahok, "
               "maaari kang makipag-ugnayan sa:")
CONTACT_TABLE = ["Office Email Contact No.",
                 "Single Joint Research Ethics Board (SJREB) | Department of Health sjreb@doh.gov.ph"]


def paper_pdf(path, paras):
    """A synthetic Aug-21 paper: one paragraph per line group, wrapped to the page."""
    lines = []
    for para in paras:
        lines.extend(textwrap.wrap(para, 95) or [""])
    make_pdf(path, lines)
    return str(path)


def test_en_consent_reads_the_five_paragraphs_from_en_ts(tmp_path):
    ts = tmp_path / "en.ts"
    ts.write_text(
        "export const en = {\n  chrome: { x: 'a' },\n  consent: {\n    heading: 'H',\n"
        "    infoStudy:\n      'It\\'s a study. Line two.',\n    infoPrivacy: \"We are committed.\",\n"
        "    infoBenefits: 'B',\n    infoRights: 'R',\n    contactsHeading:\n      'C:',\n  },\n} as const;\n",
        encoding="utf-8")
    en = m.en_consent(str(ts))
    assert list(en) == m.CONSENT_PARAGRAPH_KEYS
    assert en["infoStudy"] == "It's a study. Line two."
    assert en["infoPrivacy"] == "We are committed."


def test_en_consent_rejects_a_bundle_missing_a_paragraph(tmp_path):
    ts = tmp_path / "en.ts"
    ts.write_text("export const en = {\n  consent: {\n    infoStudy: 'S',\n  },\n} as const;\n",
                  encoding="utf-8")
    with pytest.raises(SystemExit):
        m.en_consent(str(ts))


def test_extract_consent_drops_the_papers_own_english_tail(tmp_path):
    """The two paper-only sentences after the prefix match must not reach the screen."""
    pdf = paper_pdf(tmp_path / "F2-Tagalog_x_Aug21.pdf",
                    [PAPER_STUDY, FIL_STUDY, PAPER_RIGHTS, FIL_RIGHTS, EN_CONTACT, FIL_CONTACT]
                    + CONTACT_TABLE)
    tr, rep = m.extract_consent(m.pdf_lines(pdf), ANCHORS)
    assert rep == {"infoStudy": "prefix", "infoRights": "prefix", "contactsHeading": "exact"}
    assert tr["infoStudy"].startswith("Ang Asian Social Project Services")
    assert tr["infoStudy"].endswith("Kagawaran ng Kalusugan.")
    assert "The interview may last" not in tr["infoStudy"]      # paper-only variant sentence
    assert "The questions will cover" not in tr["infoStudy"]    # anchor tail printed verbatim
    assert "Universal Health Care (UHC)" in tr["infoStudy"]     # program names kept, not dropped-english
    assert m.norm(tr["infoRights"]) == m.norm(FIL_RIGHTS)
    assert tr["contactsHeading"].endswith("sa:") and "Office" not in tr["contactsHeading"]


def test_extract_consent_rejoins_a_word_the_paper_broke_at_its_own_hyphen(tmp_path):
    """Every paper wraps "pag-aaral" as "pag-" / "aaral"; joining the lines must not
    print "pag- aaral" on the consent screen."""
    pdf = tmp_path / "F2-Tagalog_x_Aug21.pdf"
    make_pdf(pdf, textwrap.wrap(PAPER_RIGHTS, 95)
             + ["Malaya kang tumanggi sa paglahok o huminto anumang oras sa pag-",
                "aaral na ito, at wala kang babayaran para dito.", EN_CONTACT])
    tr, _ = m.extract_consent(m.pdf_lines(str(pdf)), ANCHORS)
    assert "sa pag-aaral na ito" in tr["infoRights"]
    assert "pag- aaral" not in tr["infoRights"]


def test_extract_consent_drops_english_echo_and_reports_missing(tmp_path):
    pdf = paper_pdf(tmp_path / "F2-Bicolano_x_Aug21.pdf",
                    [PAPER_STUDY, PAPER_STUDY, EN_CONTACT])   # echoed English, no rights paragraph
    tr, rep = m.extract_consent(m.pdf_lines(pdf), ANCHORS)
    assert rep["infoStudy"] == "dropped-english" and rep["infoRights"] == "missing"
    assert "infoStudy" not in tr


def test_build_consent_applies_f2_overrides_and_render_ts(tmp_path):
    src = tmp_path / "Translations"
    src.mkdir()
    paper_pdf(src / "F2-Tagalog_x_Aug21.pdf",
              [PAPER_RIGHTS, FIL_RIGHTS, EN_CONTACT, FIL_CONTACT] + CONTACT_TABLE)
    paper_pdf(src / "F2-Waray_x_Aug21.pdf", [PAPER_RIGHTS, PAPER_RIGHTS, EN_CONTACT])
    ov = {"F2": {"fil": {EN_CONTACT: {"keep": None, "reason": "test: never write"}},
                 "war": {EN_RIGHTS: {"keep": "Pinned WAR", "reason": "test: pin"}}}}
    by_loc, rep = m.build_consent(str(src), {"infoRights": EN_RIGHTS, "contactsHeading": EN_CONTACT}, ov)
    assert m.norm(by_loc["fil"]["infoRights"]) == m.norm(FIL_RIGHTS)
    assert "contactsHeading" not in by_loc["fil"]
    assert rep["fil"]["contactsHeading"] == "override"
    assert by_loc["war"] == {"infoRights": "Pinned WAR"} and rep["war"]["infoRights"] == "override"
    assert by_loc["ceb"] == {}                       # no PDF -> empty patch -> English fallback
    ts = m.render_ts(by_loc)
    # Emitted pre-wrapped the way prettier (printWidth 100) would format it.
    assert ("export const consentAug21: Record<\n"
            "  'fil' | 'ceb' | 'bis' | 'ilo' | 'hil' | 'war' | 'bcl',\n"
            "  ConsentAug21Patch\n"
            "> = {") in ts
    assert "    'infoStudy' | 'infoPrivacy' | 'infoBenefits' | 'infoRights' | 'contactsHeading'\n" in ts
    assert "  war: {\n    infoRights: 'Pinned WAR',\n  }," in ts
    assert "  ceb: {\n  }," in ts


def test_ts_str_escapes_quotes_backslashes_and_newlines():
    assert m.ts_str("it's \"x\"\nnext") == "'it\\'s \"x\"\\nnext'"
    assert m.ts_str("a\\b") == "'a\\\\b'"


def test_real_en_ts_anchors_are_all_on_every_aug21_f2_paper():
    """Guards the one assumption the whole extractor rests on, against the real files."""
    root = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
    en_ts = os.path.join(root, "deliverables", "F2", "PWA", "app", "src", "i18n", "locales", "en.ts")
    src = os.path.join(root, "raw", "Survey-Instruments-2026-08-21", "Translations")
    if not (os.path.exists(en_ts) and os.path.isdir(src)):
        pytest.skip("Aug-21 pack / F2 app not available in this checkout")
    anchors = m.en_consent(en_ts)
    by_loc, report = m.build_consent(src, anchors, {})
    assert sorted(report) == sorted(m.LOCALES)
    for loc in m.LOCALES:
        assert set(by_loc[loc]) == set(m.CONSENT_PARAGRAPH_KEYS), f"{loc}: {report[loc]}"
        for key, text in by_loc[loc].items():
            head = m.norm(text)[:40].lower()
            assert head not in m.norm(anchors[key]).lower(), f"{loc}/{key} starts in English: {head!r}"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
