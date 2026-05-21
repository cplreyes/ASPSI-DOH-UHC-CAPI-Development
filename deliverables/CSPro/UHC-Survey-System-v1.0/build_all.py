"""build_all.py — UHC Survey System v1.0 build orchestrator.

Runs each instrument's ``generate_dcf.py`` (and, in later phases,
``generate_fmf.py`` and the APC writers) in order. See README.md "Build
phases". Steps for phases not yet built are commented out — uncomment as each
phase lands its generator.

Run:
    python deliverables/CSPro/UHC-Survey-System-v1.0/build_all.py
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# (instrument folder, script, build phase)
STEPS = [
    ("F1", "generate_dcf.py", 1),
    ("F3", "generate_dcf.py", 2),
    ("F4", "generate_dcf.py", 3),
    ("F1", "generate_fmf.py", 4),
    ("F1", "generate_apc.py", 4),
    ("F3", "generate_fmf.py", 4),
    ("F3", "generate_apc.py", 4),
    ("F4", "generate_fmf.py", 4),
    ("F4", "generate_apc.py", 4),
]


def main():
    failures = []
    for folder, script, phase in STEPS:
        path = ROOT / folder / script
        if not path.exists():
            print(f"[phase {phase}] SKIP {folder}/{script} — not present")
            continue
        print(f"[phase {phase}] running {folder}/{script}")
        result = subprocess.run([sys.executable, str(path)], cwd=str(path.parent))
        if result.returncode != 0:
            failures.append(f"{folder}/{script}")
        print()

    if failures:
        print(f"BUILD FAILED: {', '.join(failures)}")
        sys.exit(1)
    print("BUILD OK")


if __name__ == "__main__":
    main()
