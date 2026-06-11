"""Status label rendering helpers for the admin UI."""

from importlib import import_module


_lazy_dependencies = import_module("ui.lazy_dependencies")
handle_errors = _lazy_dependencies.handle_errors

RUNNING_STYLE = "color: green; font-weight: bold;"
STOPPED_STYLE = "color: red; font-weight: bold;"


@handle_errors("setting status label", default_return=None)
def _set_status_label(label, text: str, *, running: bool) -> None:
    """Set text and visual state for a status label."""
    label.setText(text)
    label.setStyleSheet(RUNNING_STYLE if running else STOPPED_STYLE)


@handle_errors("updating service status labels", default_return=None)
def update_status_labels(ui, status_provider) -> None:
    """Render service, channel, and tunnel status labels from a provider."""
    is_running, pid = status_provider.check_service_status()
    service_text = (
        f"Service Status: Running (PID: {pid})"
        if is_running
        else "Service Status: Stopped"
    )
    _set_status_label(ui.label_service_status, service_text, running=is_running)

    discord_running = status_provider.check_discord_status()
    _set_status_label(
        ui.label_discord_status,
        "Discord Channel: Running" if discord_running else "Discord Channel: Stopped",
        running=discord_running,
    )

    email_running = status_provider.check_email_status()
    _set_status_label(
        ui.label_email_status,
        "Email Channel: Running" if email_running else "Email Channel: Stopped",
        running=email_running,
    )

    ngrok_status = status_provider.check_ngrok_status()
    ngrok_running = bool(ngrok_status["running"])
    if ngrok_running:
        pid_text = f" (PID: {ngrok_status['pid']})" if ngrok_status["pid"] else ""
        ngrok_text = f"ngrok tunnel: Running{pid_text}"
    else:
        ngrok_text = "ngrok tunnel: Stopped"
    _set_status_label(ui.label_ngrok_status, ngrok_text, running=ngrok_running)
