"""build_username_dict.py — generate user_roster.dcf + user_roster.dat from XLSX.

Uses cspro_helpers for the canonical CSPro 8.0 DCF schema.

Khurshid pattern: external single-level dict (Tutorial 1: Create Login Application
in CSPro @ 01:57 — "An external file dictionary can contain only one level").
The login app loads this via loadcase(USER_ROSTER_DICT, RA_ID).

Default: passwords stored as hex-SHA256 hashes (plaintext NEVER lands in the .dat).
Phase 1 workaround: pass --plaintext to store passwords plaintext-padded so the
login_app.ent.apc plaintext compare works end-to-end before CSPro 8.0 Action
Invoker Hash.createHash gets wired up in Phase 2.
"""
import argparse
import hashlib
import sys
from pathlib import Path

import openpyxl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from cspro_helpers import alpha, numeric, record, build_dictionary, write_dcf


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


def build_user_roster(src_xlsx: Path, dcf_path: Path, dat_path: Path,
                      password_mode: str = "sha256") -> None:
    """Read user_roster.xlsx, emit user_roster.dcf + user_roster.dat.

    password_mode:
        "sha256"    — hex SHA-256 (production default; plaintext never on disk)
        "plaintext" — plaintext padded to 64 chars (Phase 1 workaround)
    """
    if password_mode not in ("sha256", "plaintext"):
        raise ValueError(f"unknown password_mode {password_mode!r}")

    wb = openpyxl.load_workbook(src_xlsx, data_only=True)
    ws = wb.active

    rows = list(ws.iter_rows(values_only=True))
    header = [str(c).strip() for c in rows[0]]
    expected = ["RA_ID", "RA_NAME", "PASSWORD_PLAINTEXT", "ROLE", "SUPERVISOR_ID", "REGION_CODE"]
    if header != expected:
        raise ValueError(f"unexpected header {header!r}; want {expected!r}")

    # Emit .dat — fixed-width records, prefixed with the "U" record-type marker
    # at position 1 (DCF schema: recordType.start=1, length=1; USER_REC.recordType="U")
    dat_lines = []
    for row in rows[1:]:
        if row[0] is None:
            continue
        ra_id, name, pw, role, sup_id, region = row
        if password_mode == "sha256":
            pw_field = _hash_password(str(pw))
        else:
            pw_field = _pad_alpha(str(pw), FIELD_PASSWORD_HASH)
        dat_lines.append(
            "U"                                                  # record type marker
            + _pad_num(int(ra_id), FIELD_RA_ID)
            + _pad_alpha(str(name), FIELD_RA_NAME)
            + pw_field
            + _pad_num(int(role), FIELD_ROLE)
            + _pad_num(int(sup_id), FIELD_SUPERVISOR_ID)
            + _pad_num(int(region), FIELD_REGION_CODE)
        )
    # LF line endings (not CRLF) — CSPro Android external-dict parser is sensitive
    dat_path.write_bytes("\n".join(dat_lines).encode("utf-8") + b"\n")

    # Emit .dcf via cspro_helpers
    user_rec = record(
        name="USER_REC", label="User Record", record_type="U",
        items=[
            alpha  ("RA_NAME",       "RA Name",        length=FIELD_RA_NAME),
            alpha  ("PASSWORD_HASH", "Password Hash",  length=FIELD_PASSWORD_HASH),
            numeric("ROLE",          "Role",           length=FIELD_ROLE),
            numeric("SUPERVISOR_ID", "Supervisor ID",  length=FIELD_SUPERVISOR_ID, zero_fill=True),
            numeric("REGION_CODE",   "Region Code",    length=FIELD_REGION_CODE,   zero_fill=True),
        ],
    )

    dictionary = build_dictionary(
        dict_name="USER_ROSTER_DICT",
        dict_label="UserRoster",
        id_item_name="RA_ID",
        id_item_label="RA ID",
        id_length=FIELD_RA_ID,
        records=[user_rec],
    )
    write_dcf(dictionary, dcf_path)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument(
        "--plaintext", action="store_true",
        help="store plaintext-padded passwords (Phase 1 workaround; NOT for prod)",
    )
    args = p.parse_args()

    HERE = Path(__file__).resolve().parent.parent
    build_user_roster(
        HERE / "104_excel" / "user_roster.xlsx",
        HERE / "102_EXT_DIC" / "user_roster.dcf",
        HERE / "103_EXT_DATA" / "user_roster.dat",
        password_mode="plaintext" if args.plaintext else "sha256",
    )
    mode = "PLAINTEXT (Phase 1)" if args.plaintext else "SHA-256"
    print(f"built user_roster.dcf + user_roster.dat ({mode})")
