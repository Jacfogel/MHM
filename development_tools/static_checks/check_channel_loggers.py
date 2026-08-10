"""
Static logging style enforcement for application code.

Rules enforced (fail on violation):
- Application code must not import `logging` directly or call `logging.getLogger(...)`.
  Allowed: excluded dirs (from config) and explicit allowlist files (from config).
- Logger calls must use a single positional argument (favor f-strings instead of printf-style formatting).
- ``get_component_logger("name")`` string names must be canonical or aliased
  (parsed from ``core/logger.py`` ``CANONICAL_COMPONENT_NAMES`` /
  ``COMPONENT_NAME_ALIASES`` without importing ``core``).

Directory exclusion uses shared should_exclude_file; project-specific excluded_dirs and
allowed_logging_import_paths come from config (static_checks.channel_loggers).
"""
from __future__ import annotations

import ast
import sys
import os
import importlib.util
from pathlib import Path
from collections.abc import Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
# Ensure repo root is importable when this script is run as a file (sys.path[0] is static_checks/).
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
LOG_METHODS = {"debug", "info", "warning", "error", "exception", "critical"}
LOGGER_MODULE_PATH = REPO_ROOT / "core" / "logger.py"

# Non-project-specific: dir names to skip during walk (should_exclude_file covers most)
IGNORED_DIR_NAMES = {
    ".git",
    ".venv",
    "venv",
    ".pytest_runtime",
    "tmp_pytest_runtime",
    ".pytest_cache",
    ".pytest_profile_cache",
    ".pytest_profile_tmp",
    ".pytest_tmp_cache",
    ".tmp_pytest_runner",
    ".tmp_pytest",
    ".tmp_devtools_pyfiles",
    "htmlcov",
}


def _get_channel_loggers_config():
    """Load excluded_dirs and allowed_logging_import_paths from canonical dev-tools config.

    Project-specific lists must not be duplicated here; they live in
    ``development_tools_config.json`` (``static_checks.channel_loggers``) with defaults
    and merge behavior in ``development_tools.config.config`` - see
    ``development_tools/LIST_OF_LISTS.md`` sections 6-7.

    Loads ``config.py`` via importlib (same pattern as ``standard_exclusions``) so this
    script does not import the full ``development_tools`` package tree. GitHub Actions
    runs this step without ``pip install``.
    """
    # Prefer live project JSON; when it is missing (gitignored on CI), fall back to
    # the committed .example via load_external_config() with no explicit path.
    module_path = REPO_ROOT / "development_tools" / "config" / "config.py"
    try:
        spec = importlib.util.spec_from_file_location(
            "_devtools_static_check_dt_config", module_path
        )
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Unable to load config module from {module_path}")
        dt_config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dt_config)
        dt_config.load_external_config()
        return dt_config.get_static_check_channel_loggers_config()
    except Exception:
        # Align with STATIC_CHECK_CHANNEL_LOGGERS_DEFAULT in development_tools/config/config.py
        return {
            "excluded_dirs": ["tests", "scripts", "ai_tools", "development_tools"],
            "allowed_logging_import_paths": [],
        }


_channel_loggers_config = None
_allowed_component_names: frozenset[str] | None = None


def _get_excluded_dirs():
    global _channel_loggers_config
    if _channel_loggers_config is None:
        _channel_loggers_config = _get_channel_loggers_config()
    return set(_channel_loggers_config.get("excluded_dirs", []))


def _get_allowed_logging_import_paths():
    global _channel_loggers_config
    if _channel_loggers_config is None:
        _channel_loggers_config = _get_channel_loggers_config()
    return {
        Path(p) for p in _channel_loggers_config.get("allowed_logging_import_paths", [])
    }


def _constant_str_keys_and_values(node: ast.AST) -> tuple[set[str], set[str]]:
    """Extract string keys/values from a dict/set AST node used for component names."""
    keys: set[str] = set()
    values: set[str] = set()
    if isinstance(node, ast.Dict):
        for key_node, value_node in zip(node.keys, node.values, strict=False):
            if isinstance(key_node, ast.Constant) and isinstance(key_node.value, str):
                keys.add(key_node.value.strip().lower())
            if isinstance(value_node, ast.Constant) and isinstance(
                value_node.value, str
            ):
                values.add(value_node.value.strip().lower())
    elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        # frozenset({...}) / set({...})
        if node.func.id in {"frozenset", "set"} and node.args:
            inner = node.args[0]
            if isinstance(inner, (ast.Set, ast.Tuple, ast.List)):
                for elt in inner.elts:
                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                        values.add(elt.value.strip().lower())
    elif isinstance(node, (ast.Set, ast.Tuple, ast.List)):
        for elt in node.elts:
            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                values.add(elt.value.strip().lower())
    return keys, values


def load_allowed_component_logger_names(
    logger_path: Path | None = None,
) -> frozenset[str]:
    """Parse allowed component logger names from core/logger.py without importing core.

    Allowed = CANONICAL_COMPONENT_NAMES ∪ COMPONENT_NAME_ALIASES keys.
    Alias targets are validated against the canonical set.
    """
    path = logger_path or LOGGER_MODULE_PATH
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return frozenset()

    canonical: set[str] = set()
    alias_keys: set[str] = set()
    alias_targets: set[str] = set()

    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Name):
                continue
            keys, values = _constant_str_keys_and_values(node.value)
            if target.id == "CANONICAL_COMPONENT_NAMES":
                canonical |= values or keys
            elif target.id == "COMPONENT_NAME_ALIASES":
                alias_keys |= keys
                alias_targets |= values

    if not canonical:
        return frozenset()

    unknown_targets = sorted(alias_targets - canonical)
    if unknown_targets:
        raise RuntimeError(
            "COMPONENT_NAME_ALIASES targets not in CANONICAL_COMPONENT_NAMES: "
            + ", ".join(unknown_targets)
        )

    return frozenset(canonical | alias_keys)


def get_allowed_component_logger_names() -> frozenset[str]:
    """Cached allowed component logger names for static checks."""
    global _allowed_component_names
    if _allowed_component_names is None:
        _allowed_component_names = load_allowed_component_logger_names()
    return _allowed_component_names


def _is_get_component_logger_call(node: ast.Call) -> bool:
    func = node.func
    if isinstance(func, ast.Name) and func.id == "get_component_logger":
        return True
    return isinstance(func, ast.Attribute) and func.attr == "get_component_logger"


def _load_should_exclude_file():
    """Load standard exclusions helper without importing development_tools package."""
    module_path = REPO_ROOT / "development_tools" / "shared" / "standard_exclusions.py"
    try:
        spec = importlib.util.spec_from_file_location(
            "_devtools_standard_exclusions", module_path
        )
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Unable to load exclusions helper from {module_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.should_exclude_file
    except Exception:
        # Keep logging enforcement runnable in isolated CI environments where
        # optional runtime dependencies for full dev-tools config are unavailable.
        def _fallback_should_exclude_file(
            file_path: str, tool_type: str | None = None, context: str = "development"
        ) -> bool:
            normalized = str(file_path).replace("\\", "/")
            fallback_fragments = (
                "__pycache__",
                ".git/",
                ".venv/",
                "venv/",
                ".pytest_cache/",
                ".pytest_runtime/",
                ".tmp_pytest",
                ".tmp_devtools_pyfiles",
                "htmlcov/",
                ".egg-info/",
            )
            return any(fragment in normalized for fragment in fallback_fragments)

        return _fallback_should_exclude_file


should_exclude_file = _load_should_exclude_file()


def is_excluded(path: Path) -> bool:
    """Check if path should be excluded (project-specific dirs from config)."""
    return any(part in _get_excluded_dirs() for part in path.parts)


def has_logger_name(node: ast.AST) -> bool:
    current = node
    while isinstance(current, ast.Attribute):
        if current.attr.lower().endswith("logger"):
            return True
        current = current.value
    return isinstance(current, ast.Name) and current.id.lower().endswith("logger")


def format_issue(rel_path: Path, lineno: int, message: str) -> str:
    return f"{rel_path}:{lineno}: {message}"


def check_file(path: Path) -> Iterable[str]:
    rel_path = path.relative_to(REPO_ROOT)
    if is_excluded(rel_path):
        return []

    allow_logging_imports = rel_path in _get_allowed_logging_import_paths()
    allowed_names = get_allowed_component_logger_names()

    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:  # pragma: no cover - script should fail loudly
        return [format_issue(rel_path, exc.lineno or 0, f"Failed to parse file: {exc}")]

    issues = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "logging" and not allow_logging_imports:
                    issues.append(
                        format_issue(
                            rel_path,
                            node.lineno,
                            "Direct logging import is forbidden; use core.logger.get_component_logger in product code "
                            "or development_tools.shared.logging.get_dev_tools_logger under development_tools/",
                        )
                    )
        elif isinstance(node, ast.ImportFrom):
            if node.module == "logging" and not allow_logging_imports:
                issues.append(
                    format_issue(
                        rel_path,
                        node.lineno,
                        "Direct logging import is forbidden; use core.logger.get_component_logger in product code "
                        "or development_tools.shared.logging.get_dev_tools_logger under development_tools/",
                    )
                )
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute):
                # logging.getLogger(...)
                if (
                    isinstance(func.value, ast.Name)
                    and func.value.id == "logging"
                    and func.attr == "getLogger"
                    and not allow_logging_imports
                ):
                    issues.append(
                        format_issue(
                            rel_path,
                            node.lineno,
                            "Use core.logger.get_component_logger (product) or development_tools.shared.logging.get_dev_tools_logger "
                            "(development_tools) instead of logging.getLogger",
                        )
                    )
                # logger.info/debug/etc positional arg enforcement
                elif (
                    func.attr in LOG_METHODS
                    and has_logger_name(func.value)
                    and len(node.args) > 1
                ):
                    issues.append(
                        format_issue(
                            rel_path,
                            node.lineno,
                            "Logger calls should use a single positional argument (prefer f-strings over printf formatting)",
                        )
                    )

            if _is_get_component_logger_call(node) and node.args and allowed_names:
                first = node.args[0]
                if isinstance(first, ast.Constant) and isinstance(first.value, str):
                    name = first.value.strip().lower()
                    if name and name not in allowed_names:
                        issues.append(
                            format_issue(
                                rel_path,
                                node.lineno,
                                f'Unknown get_component_logger name "{first.value}"; '
                                "add it to CANONICAL_COMPONENT_NAMES or COMPONENT_NAME_ALIASES "
                                "in core/logger.py (do not invent ad-hoc component log files)",
                            )
                        )
    return issues


def iter_python_files(root: Path) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = Path(dirpath).relative_to(root)
        dirnames[:] = [
            name
            for name in dirnames
            if name not in IGNORED_DIR_NAMES
            and not is_excluded(rel_dir / name)
            and not should_exclude_file(
                str((rel_dir / name).as_posix()),
                tool_type="analysis",
                context="development",
            )
        ]
        for filename in filenames:
            if filename.endswith(".py"):
                rel_file = (rel_dir / filename).as_posix()
                if should_exclude_file(
                    rel_file, tool_type="analysis", context="development"
                ):
                    continue
                yield Path(dirpath) / filename


def main() -> int:
    python_files = [p for p in iter_python_files(REPO_ROOT) if p.is_file()]
    violations = []

    try:
        # Fail fast if logger.py aliases/canonical sets are inconsistent
        get_allowed_component_logger_names()
    except RuntimeError as exc:
        print(f"Static logging check failed. Resolve the issues below:\n\n- {exc}")
        return 1

    for file_path in sorted(python_files):
        violations.extend(check_file(file_path))

    if violations:
        print("Static logging check failed. Resolve the issues below:\n")
        for violation in violations:
            print(f"- {violation}")
        return 1

    print(
        "Static check passed: no forbidden logger usage or unknown "
        "get_component_logger names detected"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
