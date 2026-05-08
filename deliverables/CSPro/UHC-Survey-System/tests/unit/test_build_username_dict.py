import json
import openpyxl
from shared.build_username_dict import build_user_roster


def make_fixture_xlsx(tmp_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["RA_ID", "RA_NAME", "PASSWORD_PLAINTEXT", "ROLE", "SUPERVISOR_ID", "REGION_CODE"])
    ws.append([1001, "Sup A",    "p-sup", 1, 1001, 13])
    ws.append([2001, "RA Alpha", "p-ra",  2, 1001, 13])
    p = tmp_path / "user_roster.xlsx"
    wb.save(p)
    return p


def test_build_user_roster_emits_dcf_and_dat(tmp_path):
    src = make_fixture_xlsx(tmp_path)
    dcf_path = tmp_path / "user_roster.dcf"
    dat_path = tmp_path / "user_roster.dat"

    build_user_roster(src, dcf_path, dat_path)

    assert dcf_path.exists()
    assert dat_path.exists()

    dcf = json.loads(dcf_path.read_text(encoding="utf-8"))
    assert dcf["name"] == "USER_ROSTER_DICT"
    assert dcf["levels"][0]["ids"][0]["name"] == "RA_ID"

    dat = dat_path.read_text(encoding="utf-8").splitlines()
    assert len(dat) == 2          # 2 users in fixture
    assert dat[0].startswith("1001")


def test_build_user_roster_passwords_hashed_not_plaintext(tmp_path):
    src = make_fixture_xlsx(tmp_path)
    dcf_path = tmp_path / "user_roster.dcf"
    dat_path = tmp_path / "user_roster.dat"
    build_user_roster(src, dcf_path, dat_path)

    dat_text = dat_path.read_text(encoding="utf-8")
    assert "p-sup" not in dat_text
    assert "p-ra"  not in dat_text
