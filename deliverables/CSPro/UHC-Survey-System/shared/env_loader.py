"""env_loader.py — read urls.yaml and return the env-specific config block.

Used by build_all.py to splice the correct csweb_url + expiration_days into
each instrument's .ent before CSDeploy packages it.
"""
from pathlib import Path
from typing import Any
import yaml


def load_env(env: str, yaml_path: Path) -> dict[str, Any]:
    """Load urls.yaml and return the dict for the named environment.

    Raises:
        FileNotFoundError: if yaml_path doesn't exist.
        KeyError: if env is not present in the yaml.
    """
    if not yaml_path.exists():
        raise FileNotFoundError(f"urls.yaml not found at {yaml_path}")
    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    if env not in data:
        raise KeyError(f"environment {env!r} not in {yaml_path} (have: {list(data)})")
    return data[env]
