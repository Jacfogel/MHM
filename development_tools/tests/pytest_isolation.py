"""Isolate development-tools pytest from the host project's tests/conftest.py.

Host suites keep their own pytest.ini. Tools tests must be invoked with
``tools_suite_pytest_args()`` so ``confcutdir`` stops at the tools test
directory and MHM autouse fixtures never load.
"""

from __future__ import annotations

from pathlib import Path

DEFAULT_TOOLS_PYTEST_INI = "development_tools/pytest.ini"
DEFAULT_TOOLS_CONFCUTDIR = "tests/development_tools"
DEFAULT_TOOLS_TEST_PATHS = ["tests/development_tools"]


def normalize_rel(path: str) -> str:
    """Return a forward-slash relative path without a trailing slash."""
    return str(path).replace("\\", "/").strip().rstrip("/")


def is_tools_test_path(path: str, tools_roots: list[str] | None = None) -> bool:
    """True when *path* is a tools-test root or a file under one."""
    rel = normalize_rel(path)
    for root in tools_roots or DEFAULT_TOOLS_TEST_PATHS:
        root_n = normalize_rel(root)
        if rel == root_n or rel.startswith(f"{root_n}/"):
            return True
    return False


def path_contains_tools_root(path: str, tools_roots: list[str]) -> bool:
    """True when *path* is an ancestor of (or equal to) a tools-test root."""
    rel = normalize_rel(path)
    for root in tools_roots:
        root_n = normalize_rel(root)
        if root_n == rel or root_n.startswith(f"{rel}/"):
            return True
    return False


def tools_suite_pytest_args(
    *,
    pytest_ini: str = DEFAULT_TOOLS_PYTEST_INI,
    confcutdir: str = DEFAULT_TOOLS_CONFCUTDIR,
    rootdir: str = ".",
) -> list[str]:
    """Return argv that load the tools pytest.ini and stop parent conftest discovery."""
    return [
        "-c",
        pytest_ini,
        f"--rootdir={rootdir}",
        f"--confcutdir={confcutdir}",
    ]


def host_ignore_args(tools_roots: list[str]) -> list[str]:
    """Return ``--ignore`` flags so a host ``tests/`` collection skips tools tests."""
    return [f"--ignore={normalize_rel(root)}" for root in tools_roots]


def existing_tools_roots(tools_roots: list[str], *, cwd: Path | None = None) -> list[str]:
    """Keep configured tools roots that exist on disk."""
    base = cwd or Path.cwd()
    found: list[str] = []
    for root in tools_roots:
        rel = normalize_rel(root)
        if rel and (base / rel).exists():
            found.append(rel)
    return found


def partition_test_paths(
    paths: list[str],
    tools_roots: list[str],
) -> tuple[list[str], list[str]]:
    """Split requested pytest paths into (host_paths, tools_paths).

    A host path that *contains* a tools root (for example ``tests`` containing
    ``tests/development_tools``) stays in the host list; the tools roots are
    also scheduled as a second invocation.
    """
    if not tools_roots:
        return list(paths), []

    host: list[str] = []
    tools: list[str] = []
    need_default_tools = False
    for raw in paths:
        if is_tools_test_path(raw, tools_roots):
            tools.append(raw)
            continue
        host.append(raw)
        if path_contains_tools_root(raw, tools_roots):
            need_default_tools = True
    if need_default_tools:
        for root in tools_roots:
            if root not in tools and not any(
                is_tools_test_path(existing, [root]) for existing in tools
            ):
                tools.append(root)
    return host, tools
