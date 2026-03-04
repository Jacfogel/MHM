import os
from pathlib import Path
from unittest.mock import patch

import pytest

import core.config as config


@pytest.mark.unit
class TestConfigBranchCoverage:
    def test_validate_ai_configuration_threshold_branches(self):
        with (
            patch.object(config, "LM_STUDIO_BASE_URL", "http://localhost:1234/v1"),
            patch.object(config, "LM_STUDIO_API_KEY", ""),
            patch.object(config, "LM_STUDIO_MODEL", ""),
            patch.object(config, "AI_TIMEOUT_SECONDS", 4),
            patch.object(config, "AI_BATCH_SIZE", 0),
            patch.object(config, "CONTEXT_CACHE_TTL", 30),
            patch.object(config, "CONTEXT_CACHE_MAX_SIZE", 5),
        ):
            valid, errors, warnings = config.validate_ai_configuration()

        assert valid is False
        assert "AI_BATCH_SIZE must be at least 1" in errors
        assert any("LM_STUDIO_API_KEY is explicitly set to empty" in w for w in warnings)
        assert any("LM_STUDIO_MODEL is explicitly set to empty" in w for w in warnings)
        assert any("AI_TIMEOUT_SECONDS is very low" in w for w in warnings)
        assert any("CONTEXT_CACHE_TTL is very low" in w for w in warnings)
        assert any("CONTEXT_CACHE_MAX_SIZE is very low" in w for w in warnings)

    def test_validate_ai_configuration_upper_bounds(self):
        with (
            patch.object(config, "LM_STUDIO_BASE_URL", "http://localhost:1234/v1"),
            patch.object(config, "LM_STUDIO_API_KEY", "lm-studio"),
            patch.object(config, "LM_STUDIO_MODEL", "phi-2"),
            patch.object(config, "AI_TIMEOUT_SECONDS", 301),
            patch.object(config, "AI_BATCH_SIZE", 25),
            patch.object(config, "CONTEXT_CACHE_TTL", 3601),
            patch.object(config, "CONTEXT_CACHE_MAX_SIZE", 1001),
        ):
            valid, errors, warnings = config.validate_ai_configuration()

        assert valid is True
        assert errors == []
        assert any("AI_TIMEOUT_SECONDS is very high" in w for w in warnings)
        assert any("AI_BATCH_SIZE is very high" in w for w in warnings)
        assert any("CONTEXT_CACHE_TTL is very high" in w for w in warnings)
        assert any("CONTEXT_CACHE_MAX_SIZE is very high" in w for w in warnings)

    def test_validate_communication_channels_email_format_warning(self):
        env = {
            "EMAIL_SMTP_SERVER": "smtp.example.com",
            "EMAIL_IMAP_SERVER": "imap.example.com",
            "EMAIL_SMTP_USERNAME": "not-an-email",
            "EMAIL_SMTP_PASSWORD": "secret",
            "DISCORD_BOT_TOKEN": "bad-token-format",
        }
        with patch.dict(os.environ, env, clear=True):
            valid, errors, warnings = config.validate_communication_channels()

        assert valid is True
        assert errors == []
        assert any("EMAIL_SMTP_USERNAME doesn't appear" in w for w in warnings)
        assert any("DISCORD_BOT_TOKEN doesn't match expected" in w for w in warnings)

    def test_validate_logging_configuration_all_warning_and_error_paths(self, tmp_path):
        log_file = tmp_path / "logs" / "app.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        log_file.write_text("x" * (11 * 1024 * 1024), encoding="utf-8")

        with (
            patch.object(config, "LOG_LEVEL", "NOPE"),
            patch.object(config, "LOG_MAIN_FILE", str(log_file)),
            patch.object(config, "LOG_MAX_BYTES", 512),
            patch.object(config, "LOG_BACKUP_COUNT", 21),
        ):
            valid, errors, warnings = config.validate_logging_configuration()

        assert valid is False
        assert any("Invalid LOG_LEVEL" in e for e in errors)
        assert any("LOG_MAX_BYTES" in w for w in warnings)
        assert any("LOG_BACKUP_COUNT (21) is very high" in w for w in warnings)
        assert any("Current log file is" in w for w in warnings)

    def test_validate_logging_configuration_backup_count_minimum_error(self, tmp_path):
        log_file = tmp_path / "app.log"
        with (
            patch.object(config, "LOG_MAIN_FILE", str(log_file)),
            patch.object(config, "LOG_LEVEL", "INFO"),
            patch.object(config, "LOG_MAX_BYTES", 2 * 1024 * 1024),
            patch.object(config, "LOG_BACKUP_COUNT", 0),
        ):
            valid, errors, _warnings = config.validate_logging_configuration()

        assert valid is False
        assert "LOG_BACKUP_COUNT must be at least 1" in errors

    def test_validate_scheduler_configuration_edge_branches(self):
        with patch.object(config, "SCHEDULER_INTERVAL", 9):
            valid_low, errors_low, warnings_low = config.validate_scheduler_configuration()
        assert valid_low is False
        assert "SCHEDULER_INTERVAL must be at least 10 seconds" in errors_low
        assert warnings_low == []

        with patch.object(config, "SCHEDULER_INTERVAL", 20):
            valid_mid, errors_mid, warnings_mid = config.validate_scheduler_configuration()
        assert valid_mid is True
        assert errors_mid == []
        assert any("very low" in w for w in warnings_mid)

        with patch.object(config, "SCHEDULER_INTERVAL", 3601):
            valid_high, errors_high, warnings_high = config.validate_scheduler_configuration()
        assert valid_high is True
        assert errors_high == []
        assert any("very high" in w for w in warnings_high)

    def test_validate_file_organization_settings_invalid_type(self):
        with patch.object(config, "AUTO_CREATE_USER_DIRS", "yes"):
            valid, errors, warnings = config.validate_file_organization_settings()

        assert valid is False
        assert "AUTO_CREATE_USER_DIRS must be a boolean value" in errors
        assert any("AUTO_CREATE_USER_DIRS is enabled" in w for w in warnings)

    def test_validate_environment_variables_warning_paths(self):
        fake_env = {"MHM_EMPTY_VAR": "", "MHM_SET_VAR": "ok"}
        with (
            patch("core.config.Path.exists", return_value=False),
            patch.dict(os.environ, fake_env, clear=True),
        ):
            valid, errors, warnings = config.validate_environment_variables()

        assert valid is True
        assert errors == []
        assert any("No .env file found" in w for w in warnings)
        assert any("Empty environment variables found: MHM_EMPTY_VAR" in w for w in warnings)

    def test_validate_all_configuration_validator_exception_path(self):
        validators = [
            (True, [], []),
            RuntimeError("boom"),
            (True, [], ["warn"]) ,
            (True, [], []),
            (True, [], []),
            (True, [], []),
            (True, [], []),
        ]

        def _side_effect():
            current = validators.pop(0)
            if isinstance(current, Exception):
                raise current
            return current

        with (
            patch("core.config.validate_core_paths", side_effect=_side_effect),
            patch("core.config.validate_ai_configuration", side_effect=_side_effect),
            patch("core.config.validate_communication_channels", side_effect=_side_effect),
            patch("core.config.validate_logging_configuration", side_effect=_side_effect),
            patch("core.config.validate_scheduler_configuration", side_effect=_side_effect),
            patch("core.config.validate_file_organization_settings", side_effect=_side_effect),
            patch("core.config.validate_environment_variables", side_effect=_side_effect),
            patch("core.config.get_available_channels", return_value=[]),
        ):
            result = config.validate_all_configuration()

        assert result["valid"] is False
        assert any("Validation failed with exception: boom" in e for e in result["errors"])
        assert result["summary"].endswith("No communication channels available")

    def test_validate_all_configuration_success_summary_with_channels(self):
        with patch("core.config.get_available_channels", return_value=["email"]):
            result = config.validate_all_configuration()

        assert "Available channels: email" in result["summary"]

    def test_validate_and_raise_if_invalid_wraps_unexpected_exception(self):
        with patch("core.config.validate_all_configuration", side_effect=RuntimeError("kaboom")):
            with pytest.raises(config.ConfigValidationError) as exc:
                config.validate_and_raise_if_invalid()

        assert "kaboom" in str(exc.value)
        assert exc.value.missing_configs == ["kaboom"]

    def test_print_configuration_report_exception_path(self, capsys):
        with patch("core.config.validate_all_configuration", side_effect=RuntimeError("broken")):
            result = config.print_configuration_report()

        output = capsys.readouterr().out
        assert result is False
        assert "Error generating configuration report: broken" in output

    def test_get_user_data_dir_invalid_and_exception_paths(self):
        assert config.get_user_data_dir("") == ""

        with patch("core.config.Path", side_effect=RuntimeError("path failed")):
            assert config.get_user_data_dir("u1") == ""

    def test_get_user_file_path_invalid_user_dir(self):
        with patch("core.config.get_user_data_dir", return_value=""):
            assert config.get_user_file_path("u1", "account") == ""

    def test_ensure_user_directory_auto_create_disabled(self):
        with patch.object(config, "AUTO_CREATE_USER_DIRS", False):
            assert config.ensure_user_directory("u1") is True

    def test_ensure_user_directory_exception_path(self):
        with (
            patch.object(config, "AUTO_CREATE_USER_DIRS", True),
            patch("core.config.get_user_data_dir", return_value="/tmp/u1"),
            patch("core.config.os.makedirs", side_effect=OSError("nope")),
        ):
            assert config.ensure_user_directory("u1") is False
