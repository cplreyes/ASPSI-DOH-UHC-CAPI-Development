"""generate_apc.py — emit FacilityHeadSurvey.ent.apc.

Phase 1 strategy:
  1. Read the existing F1 .apc from the main checkout (Carl's working logic).
  2. Prepend #include directives for Sync-Helpers.apc + Expiration-Guard.apc.
  3. Write into 107_F1/.

Phase 2 will refactor to fully spec-driven generation (skip-logic from
F1-Skip-Logic-and-Validations.md emitted as PROC blocks).
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEGACY_APC = Path(
    r"C:\Users\analy\Documents\analytiflow\1_Projects\ASPSI-DOH-CAPI-CSPro-Development"
    r"\deliverables\CSPro\F1\FacilityHeadSurvey.ent.apc"
)

PREAMBLE = r'''{ FacilityHeadSurvey.ent.apc — generated; do NOT hand-edit on the device.    }
{ Source of truth: 107_F1/generate_apc.py + the legacy F1 .apc body below.       }

#include "..\shared\Expiration-Guard.apc"
#include "..\shared\Sync-Helpers.apc"

'''


def main():
    if LEGACY_APC.exists():
        legacy_body = LEGACY_APC.read_text(encoding="utf-8")
    else:
        legacy_body = "{ legacy F1 APC not found at " + str(LEGACY_APC) + " — placeholder }\n"
        print(f"  WARN: legacy APC missing at {LEGACY_APC}")

    out = PREAMBLE + legacy_body
    (HERE / "FacilityHeadSurvey.ent.apc").write_text(out, encoding="utf-8")
    print(f"wrote FacilityHeadSurvey.ent.apc ({len(out)} chars; legacy body {len(legacy_body)} chars)")


if __name__ == "__main__":
    main()
