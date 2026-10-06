"""Regression tests for the pytest-to-Node website test bridge."""

from pathlib import Path
import subprocess

import pytest

from tests.test_helpers import website_javascript


pytestmark = [pytest.mark.unit, pytest.mark.website, pytest.mark.suite]


def _add_test_file(project_root: Path, name: str) -> None:
    website = project_root / "website"
    website.mkdir(exist_ok=True)
    (website / name).write_text("// test fixture\n", encoding="utf-8")


def test_runner_invokes_every_website_test_file_in_stable_order(
    monkeypatch, tmp_path
):
    _add_test_file(tmp_path, "z-last.test.mjs")
    _add_test_file(tmp_path, "a-first.test.mjs")
    observed = {}

    monkeypatch.setattr(website_javascript.shutil, "which", lambda _name: "node")

    def fake_run(command, **kwargs):
        observed["command"] = command
        observed["kwargs"] = kwargs
        return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

    monkeypatch.setattr(website_javascript.subprocess, "run", fake_run)

    result = website_javascript.run_website_javascript_tests(tmp_path)

    assert result.returncode == 0
    assert observed["command"] == [
        "node",
        "--test",
        "website/a-first.test.mjs",
        "website/z-last.test.mjs",
    ]
    assert observed["kwargs"]["cwd"] == tmp_path
    assert observed["kwargs"]["check"] is False


def test_runner_fails_clearly_when_node_is_unavailable(monkeypatch, tmp_path):
    _add_test_file(tmp_path, "page.test.mjs")
    monkeypatch.setattr(website_javascript.shutil, "which", lambda _name: None)

    with pytest.raises(
        website_javascript.WebsiteJavaScriptTestError,
        match="Node.js 20 or newer is required",
    ):
        website_javascript.run_website_javascript_tests(tmp_path)


def test_runner_propagates_node_test_failures(monkeypatch, tmp_path):
    _add_test_file(tmp_path, "page.test.mjs")
    monkeypatch.setattr(website_javascript.shutil, "which", lambda _name: "node")
    monkeypatch.setattr(
        website_javascript.subprocess,
        "run",
        lambda command, **_kwargs: subprocess.CompletedProcess(
            command,
            1,
            stdout="not ok 1 - browser behavior",
            stderr="assertion failed",
        ),
    )

    with pytest.raises(website_javascript.WebsiteJavaScriptTestError) as captured:
        website_javascript.run_website_javascript_tests(tmp_path)

    message = str(captured.value)
    assert "exit code 1" in message
    assert "not ok 1 - browser behavior" in message
    assert "assertion failed" in message
