"""Keep tools invocations independent of the product conftest in every phase."""

import copy

import pytest

import run_tests as rt


pytestmark = [pytest.mark.unit, pytest.mark.user]


@pytest.mark.parametrize("mode,full", [("development_tools", False), ("all", True)])
def test_tools_serial_and_parallel_commands_use_tools_configuration(
    monkeypatch, tmp_path, mode, full
):
    calls = []
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        rt.sys,
        "argv",
        ["run_tests.py", "--mode", mode, "--workers", "1", "--quick"]
        + (["--full"] if full else []),
    )
    for name in (
        "cleanup_stale_test_artifacts",
        "cleanup_post_run_test_artifacts",
        "print_combined_summary",
    ):
        monkeypatch.setattr(rt, name, lambda *a, **kw: None)
    monkeypatch.setattr(rt, "set_process_priority_for_pid", lambda *a: True)

    def capture_command(command, description, **kwargs):
        calls.append((command, description))
        return copy.deepcopy(
            {"success": True, "results": {"passed": 1}, "duration": 0, "output": ""}
        )

    monkeypatch.setattr(rt, "run_command", capture_command)
    assert rt.main() == 0
    tools_calls = [
        (cmd, label)
        for cmd, label in calls
        if any("tests/development_tools" in arg for arg in cmd)
    ]
    assert len(tools_calls) == 2
    for command, _ in tools_calls:
        assert command[command.index("-c") + 1] == "development_tools/pytest.ini"
        assert "--confcutdir=tests/development_tools" in command
        assert "--rootdir=." in command
    serial_command = next(
        cmd for cmd, label in tools_calls if label.startswith("Serial")
    )
    assert "no_parallel" in serial_command[serial_command.index("-m", 3) + 1]
    assert "-n" not in serial_command
    for command, _ in calls:
        if not any("tests/development_tools" in arg for arg in command):
            assert "-c" not in command
            assert not any(arg.startswith("--confcutdir") for arg in command)
