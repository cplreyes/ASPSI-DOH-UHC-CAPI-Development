"""
apply_dcf_translations.py — DEPRECATED (2026-06-04). DO NOT RUN.

The multi-language overlay this script used to perform is now FOLDED INTO each
instrument's generator: F1/F3/F4 `generate_dcf.py` each call
`cspro_helpers.apply_translations(dictionary, <inst>/translations)` in their
`main()` before writing the .dcf. So `python <INST>/generate_dcf.py` alone now
emits the fully multi-language dictionary — there is no separate overlay step,
and regenerating can no longer silently reset a .dcf to English.

Why this script was retired:
  - The old two-step pipeline (generate THEN overlay) was a footgun: re-running
    generate_dcf.py without the overlay produced an English-only .dcf. That is
    exactly what happened when F3/F4 were rebuilt for the 12-digit case key.
  - Running this overlay ON TOP of the new generator output would now CORRUPT
    the .dcf: it emits `{text}` labels without the `language` tag the new code
    writes, and declares a different locale set/order (it hard-codes HIL for
    F3/F4, which ASPSI never translated). It must not be run anymore.

What to do instead:
  - Regenerate any instrument:           python F1/generate_dcf.py
                                          python F3/generate_dcf.py
                                          python F4/generate_dcf.py
  - Add a locale (e.g. Filipino) drop-in: place translations/<loc>.json next to
    the generator and re-run it. Locales are auto-discovered by file existence
    (see cspro_helpers.TRANSLATION_LANGUAGES); no code change needed.

See [[project_aspsi_cspro_translations]] and TRANSLATION-STATUS-2026-06-03.md.
"""
import sys

_MSG = __doc__.strip()

if __name__ == "__main__":
    sys.stderr.write(_MSG + "\n\nRefusing to run (deprecated). Use generate_dcf.py.\n")
    sys.exit(2)
