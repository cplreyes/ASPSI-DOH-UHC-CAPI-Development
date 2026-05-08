"""env_loader.py — read urls.yaml and return the env-specific config block.

Used by build_all.py to splice the correct csweb_url + expiration_days into
each instrument's .ent before CSDeploy packages it.
"""
import json
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


def splice_user_settings(ent_path: Path, settings: dict[str, Any]) -> None:
    """Mutate a CSPro .ent file's userSettings block to set/overwrite the given keys.

    CSPro stores all userSetting values as strings; we stringify here.
    Existing keys not in the settings dict are preserved.
    """
    ent_data = json.loads(ent_path.read_text(encoding="utf-8"))
    existing = ent_data.setdefault("userSettings", [])

    by_name = {s["name"]: s for s in existing}
    for name, value in settings.items():
        if name in by_name:
            by_name[name]["value"] = str(value)
        else:
            existing.append({"name": name, "value": str(value)})

    ent_path.write_text(json.dumps(ent_data, indent=2), encoding="utf-8")
