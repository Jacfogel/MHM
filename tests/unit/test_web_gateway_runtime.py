"""The service-owned gateway binds, shuts down, and leaves other servers alone."""

import socket
from unittest.mock import Mock
from urllib.request import urlopen

from aiohttp import web
import pytest

from core.web_gateway_runtime import WebGatewayRuntime

pytestmark = [pytest.mark.unit, pytest.mark.core]


def app_factory():
    app = web.Application()

    async def health(request):
        return web.Response(text="owned gateway")

    app.router.add_get("/", health)
    return app


def test_owned_gateway_lifecycle_and_port_release():
    runtime = WebGatewayRuntime(host="127.0.0.1", port=0, app_factory=app_factory)
    try:
        assert runtime.start()
        assert runtime.start()
        with urlopen(f"http://127.0.0.1:{runtime.bound_port}/", timeout=3) as response:
            assert response.read() == b"owned gateway"
    finally:
        runtime.stop()
    assert runtime._thread is not None
    assert not runtime._thread.is_alive()
    runtime.stop()
    with socket.socket() as released:
        released.bind(("127.0.0.1", runtime.bound_port))


def test_port_collision_does_not_interrupt_existing_server():
    with socket.socket() as existing:
        existing.bind(("127.0.0.1", 0))
        existing.listen()
        runtime = WebGatewayRuntime(
            host="127.0.0.1", port=existing.getsockname()[1], app_factory=app_factory
        )
        assert not runtime.start()
        assert runtime.error == "OSError"
        assert runtime._thread is not None
        assert not runtime._thread.is_alive()
        assert existing.fileno() != -1


def test_service_owns_shutdown_and_disabled_gateway_stays_off(monkeypatch):
    from core import web_gateway_runtime as module
    from core.service import MHMService

    factory = Mock()
    factory.return_value.start.return_value = True
    monkeypatch.setattr(module, "WebGatewayRuntime", factory)
    monkeypatch.setattr(module.config, "WEB_GATEWAY_ENABLED", True)
    service = MHMService()
    service.start_web_gateway()
    assert service.web_gateway is factory.return_value
    service.start_web_gateway()
    factory.assert_called_once()
    service.shutdown()
    factory.return_value.stop.assert_called_once()
    assert service.web_gateway is None
    factory.return_value.start.return_value = False
    service.start_web_gateway()
    assert service.web_gateway is None
    monkeypatch.setattr(module.config, "WEB_GATEWAY_ENABLED", False)
    factory.reset_mock()
    service.start_web_gateway()
    factory.assert_not_called()


@pytest.mark.parametrize("scheduler_fails", [False, True])
def test_service_start_includes_gateway_and_cleans_up_on_later_failure(
    monkeypatch, scheduler_fails
):
    import core.service as service_module
    import core.auto_cleanup as cleanup
    import core.web_gateway_runtime as gateway_module

    monkeypatch.setattr(service_module, "init_service_runtime", Mock())
    monkeypatch.setattr(service_module, "logger", Mock())
    monkeypatch.setattr(service_module.signal, "signal", Mock())
    monkeypatch.setattr(service_module, "verify_file_access", Mock())
    for name in (
        "auto_cleanup_if_needed",
        "cleanup_data_directory",
        "cleanup_tests_data_directory",
    ):
        monkeypatch.setattr(cleanup, name, Mock(return_value=False))
    communication, scheduler, gateway = Mock(), Mock(), Mock()
    gateway.start.return_value = True
    if scheduler_fails:
        scheduler.run_daily_scheduler.side_effect = RuntimeError(
            "isolated startup failure"
        )
    monkeypatch.setattr(
        service_module, "CommunicationManager", Mock(return_value=communication)
    )
    monkeypatch.setattr(
        service_module, "SchedulerManager", Mock(return_value=scheduler)
    )
    monkeypatch.setattr(gateway_module, "WebGatewayRuntime", Mock(return_value=gateway))
    monkeypatch.setattr(service_module.core.config, "WEB_GATEWAY_ENABLED", True)
    service = service_module.MHMService()
    for name in ("validate_configuration", "check_and_fix_logging", "run_service_loop"):
        monkeypatch.setattr(service, name, Mock())
    monkeypatch.setattr(service, "initialize_paths", Mock(return_value={}))
    service.start()
    gateway.start.assert_called_once()
    gateway.stop.assert_called_once()
    communication.start_all.assert_called_once()
    communication.stop_all.assert_called_once()
    scheduler.run_daily_scheduler.assert_called_once()
    scheduler.stop_scheduler.assert_called_once()
    assert service.web_gateway is None
