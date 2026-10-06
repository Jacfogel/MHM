"""Process-lifecycle tests for the managed Discord webhook tunnel."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import psutil
import pytest

import communication.communication_channels.discord.webhooks.tunnel as tunnel


pytestmark = [pytest.mark.unit, pytest.mark.communication]


class _Host(tunnel.DiscordWebhookTunnelMixin):
    def __init__(self):
        self._ngrok_process = None
        self._ngrok_pid = None
        self._webhook_server = None


def _process(*, pid=42, name="ngrok.exe", cmdline=None, running=True):
    return SimpleNamespace(
        info={"pid": pid, "name": name, "cmdline": cmdline or ["ngrok", "http", "8080"]},
        is_running=lambda: running,
    )


def test_external_ngrok_detection_requires_running_http_tunnel(monkeypatch):
    host = _Host()
    monkeypatch.setattr(
        tunnel.psutil,
        "process_iter",
        lambda _attrs: [
            _process(name="python.exe"),
            _process(cmdline=["ngrok", "tcp", "22"]),
            _process(pid=99),
        ],
    )

    assert host._has_external_ngrok_tunnel() is True


def test_start_ngrok_returns_cleanly_when_binary_is_missing(monkeypatch):
    host = _Host()
    monkeypatch.setattr(tunnel.shutil, "which", lambda _name: None)

    host._start_ngrok_tunnel(8080)

    assert host._ngrok_process is None
    assert host._ngrok_pid is None


def test_start_ngrok_skips_external_running_tunnel(monkeypatch):
    host = _Host()
    popen = MagicMock()
    monkeypatch.setattr(tunnel.shutil, "which", lambda _name: "C:/tools/ngrok.exe")
    monkeypatch.setattr(tunnel.psutil, "process_iter", lambda _attrs: [_process()])
    monkeypatch.setattr(tunnel.subprocess, "Popen", popen)

    host._start_ngrok_tunnel(8080)

    popen.assert_not_called()


def test_start_and_stop_managed_ngrok_process(monkeypatch):
    host = _Host()
    proc = MagicMock()
    proc.pid = 321
    proc.poll.return_value = None
    proc.stderr = None
    monkeypatch.setattr(tunnel.shutil, "which", lambda _name: "C:/tools/ngrok.exe")
    monkeypatch.setattr(tunnel.psutil, "process_iter", lambda _attrs: [])
    monkeypatch.setattr(tunnel.subprocess, "Popen", lambda *_args, **_kwargs: proc)
    monkeypatch.setattr(tunnel.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(tunnel.threading.Thread, "start", lambda _self: None)

    host._start_ngrok_tunnel(8080)

    assert host._ngrok_pid == 321
    assert host._ngrok_process is proc

    host._stop_ngrok_tunnel()

    proc.terminate.assert_called_once()
    proc.wait.assert_called_once_with(timeout=5)
    assert host._ngrok_process is None
    assert host._ngrok_pid is None


def test_stop_ngrok_force_kills_after_graceful_timeout():
    host = _Host()
    proc = MagicMock()
    proc.pid = 654
    proc.poll.return_value = None
    proc.wait.side_effect = [tunnel.subprocess.TimeoutExpired("ngrok", 5), None]
    host._ngrok_process = proc
    host._ngrok_pid = proc.pid

    host._stop_ngrok_tunnel()

    proc.kill.assert_called_once()
    assert proc.wait.call_count == 2
    assert host._ngrok_pid is None


def test_stop_ngrok_uses_pid_when_process_reference_is_missing(monkeypatch):
    host = _Host()
    host._ngrok_pid = 777
    proc = MagicMock()
    proc.is_running.return_value = True
    monkeypatch.setattr(tunnel.psutil, "Process", lambda _pid: proc)

    host._stop_ngrok_tunnel()

    proc.terminate.assert_called_once()
    proc.wait.assert_called_once_with(timeout=5)
    assert host._ngrok_pid is None


def test_stop_ngrok_tolerates_already_exited_pid(monkeypatch):
    host = _Host()
    host._ngrok_pid = 888

    def missing(_pid):
        raise psutil.NoSuchProcess(_pid)

    monkeypatch.setattr(tunnel.psutil, "Process", missing)

    host._stop_ngrok_tunnel()

    assert host._ngrok_pid is None
