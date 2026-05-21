"""case_id.py — 12-digit RR-PP-MMM-FF-CCC case-ID block for CSPro dictionaries.

Implements the adopted case-ID convention documented in
`wiki/concepts/Questionnaire Numbering Convention.md` (adopted 2026-05-05).

Composite shape (12 digits, zero-padded, no separators in the data file):
    RR PP MMM FF CCC
     |  |   |  |  |
     |  |   |  |  +-- CASE_SEQ              (3) per-instrument-per-facility seq
     |  |   |  +----- FACILITY_NO           (2) ASPSI sample-frame index within mun
     |  |   +-------- CITY_MUNICIPALITY_CODE (3) PSA 1Q 2026 PSGC pos 5-7
     |  +------------ PROVINCE_HUC_CODE     (2) PSA 1Q 2026 PSGC pos 3-4
     +--------------- REGION_CODE           (2) PSA 1Q 2026 PSGC pos 1-2

CASE_SEQ partitioning (per facility, per instrument):
    001-699 = active
    700-899 = replacement (from alternative-respondent list, Annex D)
    900-999 = refused / forfeited (recorded for response-rate accounting)

The five fields are emitted as five separate ID items, matching CSPro's
decomposed-ID convention. Display form for manual / training / dashboards is
the dashed form `RR-PP-MMM-FF-CCC`; the data file uses the concatenated
12-digit form via CSPro's standard zero-fill rendering.
"""

from __future__ import annotations

from typing import List, Dict, Any


# ---- Field widths (12 total digits) -----------------------------------------

REGION_WIDTH            = 2
PROVINCE_HUC_WIDTH      = 2
CITY_MUNICIPALITY_WIDTH = 3
FACILITY_NO_WIDTH       = 2
CASE_SEQ_WIDTH          = 3

ID_BLOCK_TOTAL_WIDTH = (
    REGION_WIDTH
    + PROVINCE_HUC_WIDTH
    + CITY_MUNICIPALITY_WIDTH
    + FACILITY_NO_WIDTH
    + CASE_SEQ_WIDTH
)
assert ID_BLOCK_TOTAL_WIDTH == 12, "RR-PP-MMM-FF-CCC must total 12 digits"


# ---- CASE_SEQ ranges --------------------------------------------------------

CASE_SEQ_ACTIVE_LO       = 1
CASE_SEQ_ACTIVE_HI       = 699
CASE_SEQ_REPLACEMENT_LO  = 700
CASE_SEQ_REPLACEMENT_HI  = 899
CASE_SEQ_REFUSED_LO      = 900
CASE_SEQ_REFUSED_HI      = 999


def build_id_block(instrument_label: str) -> List[Dict[str, Any]]:
    """Return the 5-ID-item block as a list of CSPro DCF item dicts.

    Caller passes the human-readable instrument label (e.g., "Facility Head
    Survey") which is woven into the CASE_SEQ label only — the geographic
    items are instrument-agnostic so they can be joined across F1/F3/F4.

    The returned list is intended for the `ids.items` slot of a dictionary
    level. Positions (`start`) are NOT set here — the caller is responsible
    for assigning record positions (or the writer should renumber on emit).
    """
    return [
        {
            "name":        "REGION_CODE",
            "labels":      [{"text": "Region code (PSA 1Q 2026 PSGC pos 1-2)"}],
            "contentType": "numeric",
            "length":      REGION_WIDTH,
            "zeroFill":    True,
            "valueSets":   [{
                "name":    "REGION_CODE_VS",
                "labels":  [{"text": "Region codes"}],
                # Populated by psgc.load_region_value_set() at generator time.
                "values":  [],
            }],
        },
        {
            "name":        "PROVINCE_HUC_CODE",
            "labels":      [{"text": "Province/HUC code (PSA 1Q 2026 PSGC pos 3-4)"}],
            "contentType": "numeric",
            "length":      PROVINCE_HUC_WIDTH,
            "zeroFill":    True,
            # Province value set cascades from REGION_CODE — wired in the APC
            # via PSGC-Cascade logic, not as a static value set here.
        },
        {
            "name":        "CITY_MUNICIPALITY_CODE",
            "labels":      [{"text": "City/Municipality code (PSA 1Q 2026 PSGC pos 5-7)"}],
            "contentType": "numeric",
            "length":      CITY_MUNICIPALITY_WIDTH,
            "zeroFill":    True,
            # City/mun value set cascades from PROVINCE_HUC_CODE — APC-driven.
        },
        {
            "name":        "FACILITY_NO",
            "labels":      [{"text": "Facility number (ASPSI sample frame, within municipality)"}],
            "contentType": "numeric",
            "length":      FACILITY_NO_WIDTH,
            "zeroFill":    True,
            "range":       {"low": 1, "high": 99},
        },
        {
            "name":        "CASE_SEQ",
            "labels":      [{
                "text": (
                    f"Case sequence (per-facility) — {instrument_label}. "
                    "001-699 active | 700-899 replacement | 900-999 refused/forfeited"
                ),
            }],
            "contentType": "numeric",
            "length":      CASE_SEQ_WIDTH,
            "zeroFill":    True,
            "range":       {"low": 1, "high": 999},
        },
    ]


# ---- Display helpers --------------------------------------------------------

def format_dashed(region: int, province: int, city_mun: int,
                  facility: int, case_seq: int) -> str:
    """Return the human-readable dashed form `RR-PP-MMM-FF-CCC`.

    Use this for training materials, dashboards, and enumerator cards — NOT
    for the CSPro data file (which renders the concatenated 12-digit form
    via the dictionary's zeroFill on each ID item).
    """
    return (
        f"{region:0{REGION_WIDTH}d}-"
        f"{province:0{PROVINCE_HUC_WIDTH}d}-"
        f"{city_mun:0{CITY_MUNICIPALITY_WIDTH}d}-"
        f"{facility:0{FACILITY_NO_WIDTH}d}-"
        f"{case_seq:0{CASE_SEQ_WIDTH}d}"
    )


def format_concatenated(region: int, province: int, city_mun: int,
                        facility: int, case_seq: int) -> str:
    """Return the 12-digit concatenated form `RRPPMMMFFCCC` (data-file shape)."""
    return (
        f"{region:0{REGION_WIDTH}d}"
        f"{province:0{PROVINCE_HUC_WIDTH}d}"
        f"{city_mun:0{CITY_MUNICIPALITY_WIDTH}d}"
        f"{facility:0{FACILITY_NO_WIDTH}d}"
        f"{case_seq:0{CASE_SEQ_WIDTH}d}"
    )


def classify_case_seq(seq: int) -> str:
    """Return one of 'active' | 'replacement' | 'refused' | 'invalid' for the
    given case-sequence number."""
    if CASE_SEQ_ACTIVE_LO <= seq <= CASE_SEQ_ACTIVE_HI:
        return "active"
    if CASE_SEQ_REPLACEMENT_LO <= seq <= CASE_SEQ_REPLACEMENT_HI:
        return "replacement"
    if CASE_SEQ_REFUSED_LO <= seq <= CASE_SEQ_REFUSED_HI:
        return "refused"
    return "invalid"
