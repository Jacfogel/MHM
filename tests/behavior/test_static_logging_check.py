import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.behavior
@pytest.mark.slow
def test_repo_static_logging_check_passes():
    """Ensure the repository logging static check passes in CI/test runs."""
    # Run the static check script; it should exit 0
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / 'scripts' / 'static_checks' / 'check_channel_loggers.py'
    assert script.exists(), "static check script missing"

    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
    if result.returncode != 0:
        import logging
        _logger = logging.getLogger("mhm_tests")
        _logger.error(result.stdout)
        _logger.error(result.stderr)
    assert result.returncode == 0, "Static logging check failed"


