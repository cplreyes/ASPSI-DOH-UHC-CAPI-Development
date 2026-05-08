"""build_all.py — orchestrate generators + CSDeploy across all UHC instruments.

Usage:
    python build_all.py --env=dev               # all .pen for dev
    python build_all.py --env=dev --only=F1     # iterate on F1 alone
    python build_all.py --env=uat               # for tablet upload
    python build_all.py --env=prod              # post-VPS, when ready

Outputs to dist/<env>/<NN>_<name>.pen.
"""
import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

from shared.env_loader import load_env, splice_user_settings


WORKSPACE = Path(__file__).resolve().parent
CSDEPLOY = Path(r"C:\Program Files (x86)\CSPro 8.0\CSDeploy.exe")

# (numeric_prefix, short_name, dir_name, ent_filename)
# Phase 1 builds 3 instruments. Phase 2 will append PLF, F3, F4_listing, F4.
INSTRUMENTS = [
    ("101", "login", "101_login", "login_app"),
    ("106", "menu",  "106_menu",  "menu_app"),
    ("107", "F1",    "107_F1",    "FacilityHeadSurvey"),
]


def run_generators(inst_dir: Path) -> None:
    """Run every generate_*.py in the instrument's folder, in alphabetical order
    (dcf → ent → fmf → apc puts the dictionary first, which the others depend on)."""
    for gen in sorted(inst_dir.glob("generate_*.py")):
        print(f"  -> {gen.name}")
        result = subprocess.run(
            [sys.executable, str(gen)], cwd=inst_dir, capture_output=True, text=True
        )
        if result.returncode != 0:
            print(result.stdout)
            print(result.stderr, file=sys.stderr)
            raise RuntimeError(f"{gen.name} failed (exit {result.returncode})")


def deploy(ent_path: Path, out_pen: Path) -> None:
    """Invoke CSDeploy.exe to compile ent -> pen."""
    out_pen.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [str(CSDEPLOY), str(ent_path), "-out", str(out_pen)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise RuntimeError(f"CSDeploy failed for {ent_path.name} (exit {result.returncode})")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def build_one(inst, env_config, dist_dir):
    prefix, short, dir_name, ent_name = inst
    inst_dir = WORKSPACE / dir_name
    ent_path = inst_dir / f"{ent_name}.ent"
    out_pen = dist_dir / f"{prefix}_{short}.pen"

    print(f"[{prefix}_{short}] generating sources ...")
    run_generators(inst_dir)

    if ent_path.exists():
        print(f"[{prefix}_{short}] splicing env config into {ent_path.name}")
        splice_user_settings(ent_path, {
            "csweb_url": env_config["csweb_url"],
            "expiration_days": env_config["expiration_days"],
        })
    else:
        raise RuntimeError(f"{ent_path} not produced by generators")

    print(f"[{prefix}_{short}] compiling -> {out_pen.relative_to(WORKSPACE)}")
    deploy(ent_path, out_pen)

    print(f"[{prefix}_{short}] OK ({sha256(out_pen)})")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--env", required=True, choices=["dev", "uat", "prod"])
    p.add_argument("--only", help="short name to build only (e.g. F1, login, menu)")
    args = p.parse_args()

    env_config = load_env(args.env, WORKSPACE / "urls.yaml")
    dist_dir = WORKSPACE / "dist" / args.env

    targets = INSTRUMENTS
    if args.only:
        targets = [i for i in INSTRUMENTS if i[1] == args.only]
        if not targets:
            sys.exit(f"--only={args.only} matched no instrument; have {[i[1] for i in INSTRUMENTS]}")

    for inst in targets:
        build_one(inst, env_config, dist_dir)

    print(f"\nBuilt {len(targets)} instrument(s) for env={args.env} -> {dist_dir}")


if __name__ == "__main__":
    main()
