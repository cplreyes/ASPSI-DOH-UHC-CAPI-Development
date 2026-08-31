"""Guard tests for auto_deploy.deploy_one().

Regression driver (2026-08-27, Task 42 Step 0): add_files() has five early-return
paths (no 'Add files...' button, no picker, no file-name field, picker did not
close, and a per-file `continue` when the source .dat/.dcf is absent). deploy_one()
used to IGNORE the returned list, so a run that added 0 of 8 PSGC files still
clicked Deploy and shipped a PSGC-less package -- exactly the silent defect of
2026-06-17. deploy_one() must now abort before the Deploy click and exit non-zero,
naming the files that never made it in.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import auto_deploy  # noqa: E402


class FakeButton:
    def __init__(self, text):
        self.text = text
        self.clicks = 0

    def click(self):
        self.clicks += 1


class FakeDialog:
    handle = 4242


@pytest.fixture
def rig(monkeypatch, tmp_path):
    """deploy_one() with every Windows touch-point stubbed out.

    Returns a dict holding the Deploy button (so a test can assert it was never
    clicked) and the list add_files() will pretend it added.
    """
    dd = FakeDialog()
    deploy_btn = FakeButton("Deploy")
    state = {"deploy_btn": deploy_btn, "added": [], "shots": []}

    monkeypatch.setattr(auto_deploy, "find_for", lambda inst: (dd, "PatientSurvey"))
    monkeypatch.setattr(auto_deploy, "restore", lambda d: None)
    monkeypatch.setattr(auto_deploy, "ensure_csweb_target", lambda d: (True, "already ok"))
    monkeypatch.setattr(auto_deploy, "shot", lambda d, n: state["shots"].append(n))
    monkeypatch.setattr(auto_deploy, "add_files", lambda d, base: list(state["added"]))
    monkeypatch.setattr(auto_deploy, "btn", lambda d, text: deploy_btn if text == "Deploy" else None)
    monkeypatch.setattr(auto_deploy, "answer_login_prompt", lambda: False)
    # terminal on the first poll, so a test never waits out DEPLOY_WAIT_S
    monkeypatch.setattr(auto_deploy, "_deploy_result", lambda dd_, inst: "success")
    monkeypatch.setattr(auto_deploy, "cleanup_after_deploy", lambda d: None)
    monkeypatch.setattr(auto_deploy.time, "sleep", lambda s: None)
    monkeypatch.setattr(auto_deploy, "ROOT", tmp_path)
    return state


def test_partial_add_aborts_before_deploy_click(rig, capsys):
    """0 of 8 files added -> no Deploy click, deploy_one() reports failure."""
    rig["added"] = []
    ok = auto_deploy.deploy_one("F3", do_deploy=True)
    out = capsys.readouterr().out
    assert ok is False
    assert rig["deploy_btn"].clicks == 0, "Deploy was clicked despite an incomplete package"
    assert "psgc_region.dcf" in out and "psgc_barangay.dat" in out, out


def test_one_missing_file_aborts_and_names_it(rig, capsys):
    """7 of 8 files added -> still an abort, and the message names the one gap."""
    rig["added"] = [f for f in auto_deploy.expected_files(Path("F3")) if f != "psgc_city.dat"]
    ok = auto_deploy.deploy_one("F3", do_deploy=True)
    out = capsys.readouterr().out
    assert ok is False
    assert rig["deploy_btn"].clicks == 0
    assert "psgc_city.dat" in out
    assert "psgc_region.dcf" not in out, "only the MISSING file should be named"


def test_complete_add_still_deploys(rig):
    """All expected files added -> the Deploy click still happens (no regression)."""
    rig["added"] = auto_deploy.expected_files(Path("F3"))
    assert auto_deploy.deploy_one("F3", do_deploy=True) is True
    assert rig["deploy_btn"].clicks == 1


def test_guard_runs_even_without_deploy(rig, capsys):
    """The no---deploy 'prepare' run must also report the incomplete package, so the
    operator never proceeds to --deploy-only on a half-filled dialog."""
    rig["added"] = []
    ok = auto_deploy.deploy_one("F3", do_deploy=False)
    assert ok is False
    assert "psgc_region.dat" in capsys.readouterr().out


def test_f4_expects_review_html():
    """F4 ships review.html alongside the 8 PSGC files; the other instruments do not."""
    assert auto_deploy.expected_files(Path("F4")) == auto_deploy.PSGC + ["review.html"]
    assert auto_deploy.expected_files(Path("F3")) == auto_deploy.PSGC
    assert auto_deploy.expected_files(Path("F1")) == auto_deploy.PSGC


def test_sv_and_hub_expect_no_extra_files():
    """SV (SupervisorApp) and HUB (LoginApp/MenuApp bundle) ship no PSGC dicts at all --
    deliverables/CSPro/SV/ holds none and the HUB spec lives in supervisor-hub/, not HUB/.
    A blanket PSGC expectation made the completeness guard abort their deploys."""
    assert auto_deploy.expected_files(Path("SV")) == []
    assert auto_deploy.expected_files(Path("HUB")) == []
    # anything unlisted defaults to "no extra files", never to the PSGC set
    assert auto_deploy.expected_files(Path("NOPE")) == []


def test_hub_still_clicks_deploy_with_zero_files(rig, capsys):
    """The guard must not fire for an instrument that legitimately adds nothing:
    HUB deploys with 0 extra files and the Deploy click must still happen."""
    rig["added"] = []
    assert auto_deploy.deploy_one("HUB", do_deploy=True) is True
    assert rig["deploy_btn"].clicks == 1
    assert "ABORT" not in capsys.readouterr().out


def test_sv_still_clicks_deploy_with_zero_files(rig):
    """Same for the Supervisor App."""
    rig["added"] = []
    assert auto_deploy.deploy_one("SV", do_deploy=True) is True
    assert rig["deploy_btn"].clicks == 1


def test_deploy_only_skips_the_guard(rig):
    """--deploy-only clicks Deploy on an already-prepared dialog: add_files never runs,
    so the completeness guard must not fire on its empty list."""
    rig["added"] = []
    assert auto_deploy.deploy_one("F3", do_deploy=True, skip_add=True) is True
    assert rig["deploy_btn"].clicks == 1
