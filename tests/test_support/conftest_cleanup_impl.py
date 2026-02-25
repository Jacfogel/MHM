"""
Cleanup implementation for test conftest.

Cleanup helpers (_cleanup_*, _prune_*, _apply_*, _clear_*, _get_active_pytest_basetemp,
_cleanup_session_test_data_artifacts, _snapshot_worker_logs_with_retention, _is_transient_test_data_dir_name)
live here. Conftest keeps fixture definitions (e.g. prune_test_artifacts_before_and_after_session)
that call into this module.
"""

import os
import re
import stat
import sys
import time
import shutil
from pathlib import Path

from core.time_utilities import now_datetime_full


def _get_test_logger():
    """Lazy import to avoid circular import (conftest imports this module)."""
    from tests.conftest import test_logger
    return test_logger


def _remove_path_best_effort(path: Path) -> None:
    """Best-effort removal for transient test artifacts."""
    try:
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        else:
            path.unlink(missing_ok=True)
    except Exception:
        pass


def _clear_directory_contents(
    path: Path, keep_dir_names: set[str] | None = None
) -> None:
    """Remove directory contents while optionally preserving specific child directories."""
    if not path.exists() or not path.is_dir():
        return
    keep = keep_dir_names or set()
    for child in path.iterdir():
        if child.is_dir() and child.name in keep:
            continue
        _remove_path_best_effort(child)


def _get_active_pytest_basetemp() -> Path | None:
    """Best-effort parse of active --basetemp path from current pytest invocation."""
    try:
        argv = list(sys.argv)
    except Exception:
        return None

    for idx, arg in enumerate(argv):
        if arg.startswith("--basetemp="):
            raw = arg.split("=", 1)[1].strip()
            if raw:
                return Path(raw).resolve()
        if arg == "--basetemp" and idx + 1 < len(argv):
            raw = argv[idx + 1].strip()
            if raw:
                return Path(raw).resolve()
    return None


def _clear_pytest_runner_directory_contents(
    runner_dir: Path, active_basetemp: Path | None = None
) -> None:
    """Clean pytest runner roots without deleting active concurrent basetemp dirs."""
    if not runner_dir.exists() or not runner_dir.is_dir():
        return

    keep: set[str] = set()
    if active_basetemp is not None:
        try:
            if active_basetemp.parent.resolve() == runner_dir.resolve():
                keep.add(active_basetemp.name)
        except Exception:
            pass

    grace_seconds = 30 * 60
    now_ts = time.time()
    for child in runner_dir.iterdir():
        if not child.is_dir():
            continue
        name = child.name
        if not (
            name.startswith("mhm_pytest_tmp_")
            or name.startswith("repro_")
            or name.startswith("pytest-")
        ):
            continue
        try:
            age_seconds = now_ts - child.stat().st_mtime
            if age_seconds <= grace_seconds:
                keep.add(name)
        except Exception:
            keep.add(name)

    _clear_directory_contents(runner_dir, keep_dir_names=keep)


def _cleanup_session_test_data_artifacts(data_dir: Path) -> None:
    """Clean known transient test-data directories before/after a test session."""
    for name in ("devtools_pyfiles", "devtools_unit", "error_handling_tmp"):
        _remove_path_best_effort(data_dir / name)

    _clear_directory_contents(data_dir / "backups")
    _clear_directory_contents(data_dir / "users")

    active_basetemp = _get_active_pytest_basetemp()

    tmp_dir = data_dir / "tmp"
    _clear_directory_contents(tmp_dir, keep_dir_names={"pytest_runner"})
    tmp_runner_dir = tmp_dir / "pytest_runner"
    _clear_pytest_runner_directory_contents(tmp_runner_dir, active_basetemp)

    runtime_tmp_dir = data_dir / "tmp_pytest_runtime"
    _clear_directory_contents(
        runtime_tmp_dir, keep_dir_names={"pytest_runner", "pytest_cache"}
    )
    runtime_runner_dir = runtime_tmp_dir / "pytest_runner"
    _clear_pytest_runner_directory_contents(runtime_runner_dir, active_basetemp)


def _is_transient_test_data_dir_name(name: str) -> bool:
    """True for per-run transient test-data directories safe to purge."""
    if name == "tmp_pytest_runtime":
        return False
    return (
        name.startswith("pytest-of-")
        or name.startswith("tmp_")
        or (name.startswith("tmp") and name != "tmp")
    )


def _cleanup_test_log_files(project_root: str | Path) -> None:
    """Clean up excessive test log files to prevent accumulation."""
    try:
        logs_dir = Path(project_root) / "tests" / "logs"
        if not logs_dir.exists():
            return

        for log_file in logs_dir.glob("*.log"):
            if log_file.name in ["test_consolidated.log", "test_run.log"]:
                continue

            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if (
                        content.startswith("# Log rotated at")
                        and len(content.split("\n")) <= 2
                    ) or len(content) == 0:
                        log_file.unlink()
            except Exception:
                continue

        backups_dir = logs_dir / "backups"
        if backups_dir.exists():
            for backup_file in backups_dir.glob("*.bak"):
                try:
                    if backup_file.stat().st_mtime < time.time() - 86400:
                        backup_file.unlink()
                except Exception:
                    continue

    except Exception as e:
        _get_test_logger().warning(f"Error during test log cleanup: {e}")


def _cleanup_individual_log_files(project_root: str | Path) -> None:
    """Clean up individual log files created before consolidated mode was enabled."""
    try:
        logs_dir = Path(project_root) / "tests" / "logs"
        if not logs_dir.exists():
            return

        individual_log_files = [
            "app.log",
            "errors.log",
            "ai.log",
            "discord.log",
            "user_activity.log",
            "communication_manager.log",
            "email.log",
            "ui.log",
            "file_ops.log",
            "scheduler.log",
            "schedule_utilities.log",
            "analytics.log",
            "message.log",
            "backup.log",
            "checkin_dynamic.log",
        ]

        for log_file_name in individual_log_files:
            log_file = logs_dir / log_file_name
            if log_file.exists():
                try:
                    log_file.unlink()
                    _get_test_logger().debug(
                        f"Cleaned up individual log file: {log_file_name}"
                    )
                except Exception as e:
                    _get_test_logger().warning(
                        f"Error cleaning up {log_file_name}: {e}"
                    )

    except Exception as e:
        _get_test_logger().warning(
            f"Error during individual log file cleanup: {e}"
        )


def _prune_old_files(
    target_dir: Path, patterns: list[str], older_than_days: int
) -> int:
    """Remove files in target_dir matching any pattern older than N days."""
    removed_count = 0
    try:
        if older_than_days <= 0:
            return 0
        cutoff = now_datetime_full().timestamp() - (older_than_days * 24 * 3600)
        for pattern in patterns:
            for file_path in target_dir.rglob(pattern):
                try:
                    if file_path.is_file() and file_path.stat().st_mtime < cutoff:
                        file_path.unlink(missing_ok=True)
                        removed_count += 1
                except Exception:
                    pass
    except Exception:
        pass
    return removed_count


def _apply_versioned_retention_protocol(
    logs_dir: Path,
    backups_dir: Path,
    archive_dir: Path,
    pattern: str,
    keep_backups: int = 7,
    archive_retention_days: int = 30,
    current_file_name: str | None = None,
) -> int:
    """Apply the standard protocol to versioned test artifacts."""
    moved_count = 0
    try:
        backups_dir.mkdir(parents=True, exist_ok=True)
        archive_dir.mkdir(parents=True, exist_ok=True)

        candidates = []
        for base in (logs_dir, backups_dir):
            candidates.extend(list(base.glob(pattern)))

        unique: dict[str, Path] = {}
        for path in candidates:
            unique[str(path.resolve())] = path
        files = sorted(unique.values(), key=lambda p: p.stat().st_mtime, reverse=True)
        if not files:
            return 0

        current_is_fixed = (
            current_file_name is not None and (logs_dir / current_file_name).exists()
        )

        if current_is_fixed:
            current_file = None
            backup_slice = files[:keep_backups]
            archive_slice = files[keep_backups:]
        else:
            current_file = files[0]
            backup_slice = files[1 : 1 + keep_backups]
            archive_slice = files[1 + keep_backups :]

        if current_file is not None and current_file.parent != logs_dir:
            target = logs_dir / current_file.name
            if target.exists():
                target.unlink(missing_ok=True)
            shutil.move(str(current_file), str(target))
            moved_count += 1

        for item in backup_slice:
            if item.parent == backups_dir:
                continue
            target = backups_dir / item.name
            if target.exists():
                target.unlink(missing_ok=True)
            shutil.move(str(item), str(target))
            moved_count += 1

        for item in archive_slice:
            if item.parent == archive_dir:
                continue
            target = archive_dir / item.name
            if target.exists():
                target.unlink(missing_ok=True)
            shutil.move(str(item), str(target))
            moved_count += 1

        cutoff = now_datetime_full().timestamp() - (
            archive_retention_days * 24 * 60 * 60
        )
        for archived in archive_dir.glob(pattern):
            try:
                if archived.stat().st_mtime < cutoff:
                    archived.unlink(missing_ok=True)
            except Exception:
                pass
    except Exception:
        pass
    return moved_count


def _cleanup_pytest_cache_temp_dirs(
    project_root_path: Path, data_dir: Path
) -> int:
    """Remove stray pytest-cache-files-* temp directories."""
    removed = 0
    failed_paths: list[tuple[Path, str]] = []

    def _rmtree_with_retries(path: Path, attempts: int = 20) -> bool:
        def _on_rm_error(func, target, exc_info):
            try:
                os.chmod(target, stat.S_IWRITE)
                func(target)
            except Exception:
                pass

        for attempt in range(attempts):
            try:
                shutil.rmtree(path, ignore_errors=False, onerror=_on_rm_error)
                return True
            except Exception:
                time.sleep(min(0.5, 0.05 * (attempt + 1)))
        try:
            shutil.rmtree(path, ignore_errors=True, onerror=_on_rm_error)
        except Exception:
            pass
        return not path.exists()

    try:
        for root in (project_root_path, data_dir, data_dir / "tmp"):
            if not root.exists():
                continue
            for entry in root.glob("pytest-cache-files-*"):
                if entry.is_dir():
                    try:
                        if _rmtree_with_retries(entry):
                            removed += 1
                        else:
                            failed_paths.append(
                                (entry, "directory still exists after retries")
                            )
                    except Exception:
                        failed_paths.append((entry, "exception during cleanup"))
    except Exception:
        pass

    test_logger = _get_test_logger()
    root_leftovers = [
        p
        for p in project_root_path.glob("pytest-cache-files-*")
        if p.is_dir()
    ]
    if root_leftovers:
        details = ", ".join(str(p) for p in root_leftovers[:8])
        if len(root_leftovers) > 8:
            details += f", ... (+{len(root_leftovers) - 8} more)"
        if failed_paths:
            failed_details = "; ".join(
                f"{path}: {reason}" for path, reason in failed_paths[:8]
            )
            test_logger.error(
                "pytest cache temp cleanup failures encountered: %s", failed_details
            )
        raise RuntimeError(
            "Stale root pytest cache temp directories detected after cleanup: "
            f"{details}. Fix filesystem permissions or remove these directories before running tests."
        )
    return removed


def _apply_flaky_run_group_retention(
    runs_dir: Path,
    backups_dir: Path,
    archive_dir: Path,
    keep_backups: int = 7,
    archive_retention_days: int = 30,
) -> int:
    """Apply current/7/archive/30d protocol to flaky detector run files."""
    moved_count = 0
    try:
        if not runs_dir.exists():
            return 0

        backups_dir.mkdir(parents=True, exist_ok=True)
        archive_dir.mkdir(parents=True, exist_ok=True)

        run_groups: dict[int, list[Path]] = {}
        for path in runs_dir.glob("run_*_*"):
            if not path.is_file():
                continue
            match = re.match(r"run_(\d+)_", path.name)
            if not match:
                continue
            run_id = int(match.group(1))
            run_groups.setdefault(run_id, []).append(path)

        if not run_groups:
            return 0

        def _group_mtime(paths: list[Path]) -> float:
            return max(p.stat().st_mtime for p in paths)

        ordered_run_ids = sorted(
            run_groups.keys(),
            key=lambda run_id: _group_mtime(run_groups[run_id]),
            reverse=True,
        )

        backup_run_ids = set(ordered_run_ids[1 : 1 + keep_backups])
        archive_run_ids = set(ordered_run_ids[1 + keep_backups :])

        for run_id in backup_run_ids:
            for path in run_groups[run_id]:
                target = backups_dir / path.name
                if target.exists():
                    target.unlink(missing_ok=True)
                shutil.move(str(path), str(target))
                moved_count += 1

        for run_id in archive_run_ids:
            for path in run_groups[run_id]:
                target = archive_dir / path.name
                if target.exists():
                    target.unlink(missing_ok=True)
                shutil.move(str(path), str(target))
                moved_count += 1

        cutoff = now_datetime_full().timestamp() - (
            archive_retention_days * 24 * 60 * 60
        )
        for archived in archive_dir.glob("run_*_*"):
            try:
                if archived.is_file() and archived.stat().st_mtime < cutoff:
                    archived.unlink(missing_ok=True)
            except Exception:
                pass
    except Exception:
        pass
    return moved_count


def _snapshot_worker_logs_with_retention(
    worker_logs_dir: Path,
    backups_root: Path,
    archive_root: Path,
    keep_backups: int = 7,
    archive_retention_days: int = 30,
) -> int:
    """Snapshot worker log set and retain 7 backups plus 30-day archive."""
    snapshot_count = 0
    try:
        if not worker_logs_dir.exists():
            return 0

        source_files = sorted(p for p in worker_logs_dir.iterdir() if p.is_file())
        if not source_files:
            return 0

        backups_root.mkdir(parents=True, exist_ok=True)
        archive_root.mkdir(parents=True, exist_ok=True)

        snapshot_name = (
            f"worker_logs_backup_{now_datetime_full().strftime('%Y-%m-%d_%H-%M-%S')}"
        )
        snapshot_dir = backups_root / snapshot_name
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        for file_path in source_files:
            shutil.copy2(file_path, snapshot_dir / file_path.name)
            snapshot_count += 1

        snapshots = sorted(
            [p for p in backups_root.glob("worker_logs_backup_*") if p.is_dir()],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for old_snapshot in snapshots[keep_backups:]:
            target = archive_root / old_snapshot.name
            if target.exists():
                shutil.rmtree(target, ignore_errors=True)
            shutil.move(str(old_snapshot), str(target))

        cutoff = now_datetime_full().timestamp() - (
            archive_retention_days * 24 * 60 * 60
        )
        for archived in archive_root.glob("worker_logs_backup_*"):
            try:
                if archived.is_dir() and archived.stat().st_mtime < cutoff:
                    shutil.rmtree(archived, ignore_errors=True)
            except Exception:
                pass
    except Exception:
        pass
    return snapshot_count
