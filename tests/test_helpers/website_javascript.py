"""Helpers for running the standalone website JavaScript test suite."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess


DEFAULT_TIMEOUT_SECONDS = 120
MAX_FAILURE_OUTPUT_CHARS = 12_000


class WebsiteJavaScriptTestError(RuntimeError):
    """Raised when the website JavaScript suite cannot complete successfully."""


def _failure_output(result: subprocess.CompletedProcess[str]) -> str:
    output = "\n".join(
        part.strip() for part in (result.stdout, result.stderr) if part and part.strip()
    )
    if len(output) > MAX_FAILURE_OUTPUT_CHARS:
        output = f"... output truncated ...\n{output[-MAX_FAILURE_OUTPUT_CHARS:]}"
    return output


def run_website_javascript_tests(
    project_root: Path,
    *,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> subprocess.CompletedProcess[str]:
    """Run every ``website/*.test.mjs`` file and raise on infrastructure/test failure."""

    node = shutil.which("node")
    if node is None:
        raise WebsiteJavaScriptTestError(
            "Node.js 20 or newer is required to run the website JavaScript tests."
        )

    test_files = sorted((project_root / "website").glob("*.test.mjs"))
    if not test_files:
        raise WebsiteJavaScriptTestError(
            "No website JavaScript tests were found under website/*.test.mjs."
        )

    command = [
        node,
        "--test",
        *(path.relative_to(project_root).as_posix() for path in test_files),
    ]
    try:
        result = subprocess.run(
            command,
            cwd=project_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise WebsiteJavaScriptTestError(
            f"Website JavaScript tests exceeded the {timeout_seconds}-second timeout."
        ) from error

    if result.returncode != 0:
        details = _failure_output(result)
        message = f"Website JavaScript tests failed with exit code {result.returncode}."
        if details:
            message = f"{message}\n\n{details}"
        raise WebsiteJavaScriptTestError(message)

    return result
