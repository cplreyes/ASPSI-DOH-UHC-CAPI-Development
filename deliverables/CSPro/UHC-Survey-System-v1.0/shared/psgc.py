"""psgc.py — PSGC value-set loaders (PSA 1Q 2026).

Loads the geographic code CSVs extracted from the PSA 1Q 2026 PSGC
publication. Per the v1.0 README, the CSVs are reused as-is from the existing
F1 inputs folder and are NOT regenerated here:

    deliverables/CSPro/F1/inputs/psgc_region.csv
    deliverables/CSPro/F1/inputs/psgc_province_huc.csv
    deliverables/CSPro/F1/inputs/psgc_city_municipality.csv
    deliverables/CSPro/F1/inputs/psgc_barangay.csv

The v1.0 case-ID convention slices the full 10-digit PSGC code into positional
sub-codes:

    REGION_CODE            = PSGC digits 1-2
    PROVINCE_HUC_CODE      = PSGC digits 3-4
    CITY_MUNICIPALITY_CODE = PSGC digits 5-7
    BARANGAY_CODE          = PSGC digits 8-10

Only the REGION value set is emitted statically into the DCF. PROVINCE / CITY /
BARANGAY value sets are populated at runtime by the PSGC cascade logic in the
.apc (phase 4) — see ``case_id.py`` and ``wiki/concepts/PSGC Value Sets``.
"""

from __future__ import annotations

import csv
from pathlib import Path

# CSVs live alongside the legacy F1 inputs (v1.0 README: "do not regenerate").
# shared/psgc.py -> UHC-Survey-System-v1.0/ -> CSPro/ ; then F1/inputs.
_INPUTS_DIR = Path(__file__).resolve().parents[2] / "F1" / "inputs"


def _load(filename):
    path = _INPUTS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"PSGC source CSV not found: {path}\n"
            f"Expected the PSA 1Q 2026 extracts under "
            f"deliverables/CSPro/F1/inputs/."
        )
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load_region_value_set(whitelist=None):
    """Return ``[(label, code), ...]`` for the REGION_CODE id item.

    ``code`` is the 2-digit slice (PSGC positions 1-2) of the full 10-digit
    region code, zero-padded. Sorted by code.

    ``whitelist``, if given, is an iterable of 2-digit region codes to keep —
    used by F4 (phase 3) to restrict to its 6 household-survey regions. F1 and
    F3 pass no whitelist (all 18 regions).
    """
    rows = _load("psgc_region.csv")
    by_code = {}
    for r in rows:
        code2 = r["code"][:2]
        by_code[code2] = r["name"]
    codes = sorted(by_code)
    if whitelist is not None:
        wl = {str(c).zfill(2) for c in whitelist}
        missing = wl - set(codes)
        if missing:
            raise ValueError(f"whitelist region codes not in PSGC: {sorted(missing)}")
        codes = [c for c in codes if c in wl]
    return [(by_code[c], c) for c in codes]
