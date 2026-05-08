import pytest
from pathlib import Path
from shared.env_loader import load_env

FIXTURE_YAML = """
dev:
  csweb_url: "http://localhost/cswebtest/api"
  expiration_days: 30
uat:
  csweb_url: "http://192.168.1.42/cswebtest/api"
  expiration_days: 7
"""


def test_load_env_dev_returns_localhost(tmp_path):
    yaml_path = tmp_path / "urls.yaml"
    yaml_path.write_text(FIXTURE_YAML, encoding="utf-8")
    env = load_env("dev", yaml_path)
    assert env["csweb_url"] == "http://localhost/cswebtest/api"
    assert env["expiration_days"] == 30


def test_load_env_uat_returns_lan_ip(tmp_path):
    yaml_path = tmp_path / "urls.yaml"
    yaml_path.write_text(FIXTURE_YAML, encoding="utf-8")
    env = load_env("uat", yaml_path)
    assert env["csweb_url"].startswith("http://192.168.")
    assert env["expiration_days"] == 7


def test_load_env_unknown_env_raises(tmp_path):
    yaml_path = tmp_path / "urls.yaml"
    yaml_path.write_text(FIXTURE_YAML, encoding="utf-8")
    with pytest.raises(KeyError, match="prod"):
        load_env("prod", yaml_path)


def test_load_env_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_env("dev", tmp_path / "does-not-exist.yaml")
