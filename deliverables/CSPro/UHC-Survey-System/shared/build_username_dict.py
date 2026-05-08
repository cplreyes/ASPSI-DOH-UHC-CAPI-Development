"""build_username_dict.py — generate user_roster.dcf + user_roster.dat from XLSX.

Khurshid pattern: external single-level dict (Tutorial 1: Create Login Application
in CSPro @ 01:57 — "An external file dictionary can contain only one level").
The login app loads this via loadcase(USER_ROSTER_DICT, RA_ID).

Passwords are stored as hex-SHA256 hashes — plaintext NEVER lands in the .dat.
"""
import hashlib
import json
import openpyxl
from pathlib import Path


# Field widths — sized for the largest expected value
FIELD_RA_ID         = 4    # numeric, supports up to 9999 RAs
FIELD_RA_NAME       = 40   # alpha
FIELD_PASSWORD_HASH = 64   # alpha — hex SHA-256 is 64 chars
FIELD_ROLE          = 1    # 1=sup, 2=enum, 3=ops
FIELD_SUPERVISOR_ID = 4
FIELD_REGION_CODE   = 2


def _pad_num(value: int, width: int) -> str:
    return str(value).zfill(width)


def _pad_alpha(value: str, width: int) -> str:
    s = (value or "")[:width]
    return s.ljust(width)


def _hash_password(plaintext: str) -> str:
    return hashlib.sha256(plaintext.encode("utf-8")).hexdigest()


def build_user_roster(src_xlsx: Path, dcf_path: Path, dat_path: Path) -> None:
    """Read user_roster.xlsx, emit user_roster.dcf + user_roster.dat."""
    wb = openpyxl.load_workbook(src_xlsx, data_only=True)
    ws = wb.active

    rows = list(ws.iter_rows(values_only=True))
    header = [str(c).strip() for c in rows[0]]
    expected = ["RA_ID", "RA_NAME", "PASSWORD_PLAINTEXT", "ROLE", "SUPERVISOR_ID", "REGION_CODE"]
    if header != expected:
        raise ValueError(f"unexpected header {header!r}; want {expected!r}")

    # Emit .dat — fixed-width records
    dat_lines = []
    for row in rows[1:]:
        if row[0] is None:
            continue
        ra_id, name, pw, role, sup_id, region = row
        dat_lines.append(
            _pad_num(int(ra_id), FIELD_RA_ID)
            + _pad_alpha(str(name), FIELD_RA_NAME)
            + _hash_password(str(pw))
            + _pad_num(int(role), FIELD_ROLE)
            + _pad_num(int(sup_id), FIELD_SUPERVISOR_ID)
            + _pad_num(int(region), FIELD_REGION_CODE)
        )
    dat_path.write_text("\n".join(dat_lines), encoding="utf-8")

    # Emit .dcf
    dcf = {
        "software": "CSPro",
        "version": 8.0,
        "fileType": "dictionary",
        "name": "USER_ROSTER_DICT",
        "label": "User Roster",
        "levels": [{
            "name": "USER_LEVEL",
            "label": "User Level",
            "ids": [{
                "name": "RA_ID", "label": "RA ID",
                "type": "numeric", "length": FIELD_RA_ID, "zeroFill": True,
            }],
            "records": [{
                "name": "USER_REC",
                "label": "User Record",
                "recordType": "",
                "required": True,
                "items": [
                    {"name": "RA_NAME",       "label": "RA Name",        "type": "alpha",   "length": FIELD_RA_NAME},
                    {"name": "PASSWORD_HASH", "label": "Password Hash",  "type": "alpha",   "length": FIELD_PASSWORD_HASH},
                    {"name": "ROLE",          "label": "Role",           "type": "numeric", "length": FIELD_ROLE},
                    {"name": "SUPERVISOR_ID", "label": "Supervisor ID",  "type": "numeric", "length": FIELD_SUPERVISOR_ID, "zeroFill": True},
                    {"name": "REGION_CODE",   "label": "Region Code",    "type": "numeric", "length": FIELD_REGION_CODE,   "zeroFill": True},
                ],
            }],
        }],
    }
    dcf_path.write_text(json.dumps(dcf, indent=2), encoding="utf-8")


if __name__ == "__main__":
    HERE = Path(__file__).resolve().parent.parent
    build_user_roster(
        HERE / "104_excel" / "user_roster.xlsx",
        HERE / "102_EXT_DIC" / "user_roster.dcf",
        HERE / "103_EXT_DATA" / "user_roster.dat",
    )
    print("built user_roster.dcf + user_roster.dat")
