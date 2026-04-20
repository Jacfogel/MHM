# TOOL_TIER: core

"""Helpers for §3.19.1 sharded static analysis (merge contract, future orchestration).

Ruff ``check --output-format json`` emits a JSON **array** of diagnostic objects.
Bandit ``-f json`` emits a JSON **object** with a ``results`` array.

**Merge contract (Ruff):** concatenate shard lists, drop duplicates using a stable key
``(normalized_filename, code, location.row, location.column)``, then sort by that key
for deterministic output.

**Merge contract (Bandit):** union ``results`` from each payload; dedupe by
``(filename, line_number, test_id, issue_severity)``; sort by filename, line, test_id.

**Pyright:** whole-project analysis remains the default. Path-scoped or sharded runs
can omit cross-package diagnostics. Any future subset mode must be paired with a
documented **full pass** policy (for example ``audit --full`` with ``--clear-cache``,
or CI) so strict whole-repo parity is periodically restored.

**Wiring (§3.19.1 Phase 2):** :func:`development_tools.static_checks.analyze_ruff.run_ruff`
calls :func:`merge_ruff_check_json_lists` when ``static_analysis.ruff_shard_scan`` is true
and ``ruff_path_shards`` is non-empty. :func:`development_tools.static_checks.analyze_bandit.run_bandit`
calls :func:`merge_bandit_raw_payloads` when ``static_analysis.bandit_shard_scan`` is true
and there are multiple scan targets. :func:`development_tools.static_checks.analyze_pyright.run_pyright`
calls :func:`merge_pyright_json_payloads` when ``static_analysis.pyright_shard_scan`` is true
and ``pyright_path_shards`` is non-empty. Defaults in ``STATIC_ANALYSIS`` enable sharding; set
flags to false or clear shard lists for a single subprocess (Ruff falls back to
``check .`` if no shard paths exist).
"""

from __future__ import annotations

from typing import Any


def _norm_path_sep(path: str) -> str:
    return str(path).replace("\\", "/")


def ruff_diagnostic_sort_key(item: dict[str, Any]) -> tuple[str, str, int, int]:
    """Stable sort key aligned with :func:`ruff_diagnostic_identity`."""
    fn, code, row, col = ruff_diagnostic_identity(item)
    return (fn, code, row, col)


def ruff_diagnostic_identity(item: dict[str, Any]) -> tuple[str, str, int, int]:
    """Return (filename, code, row, col) for deduplication of Ruff JSON diagnostics."""
    fn = _norm_path_sep(str(item.get("filename", "")).strip())
    code = str(item.get("code", "")).strip()
    loc = item.get("location")
    row, col = 0, 0
    if isinstance(loc, dict):
        try:
            row = int(loc.get("row", 0))
        except (TypeError, ValueError):
            row = 0
        try:
            col = int(loc.get("column", 0))
        except (TypeError, ValueError):
            col = 0
    return (fn, code, row, col)


def merge_ruff_check_json_lists(shard_lists: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """Merge Ruff ``check`` JSON arrays from disjoint path shards with deduplication."""
    seen: dict[tuple[str, str, int, int], dict[str, Any]] = {}
    for shard in shard_lists:
        if not isinstance(shard, list):
            continue
        for item in shard:
            if not isinstance(item, dict):
                continue
            key = ruff_diagnostic_identity(item)
            seen.setdefault(key, item)
    merged = list(seen.values())
    merged.sort(key=ruff_diagnostic_sort_key)
    return merged


def bandit_result_sort_key(item: dict[str, Any]) -> tuple[str, int, str, str]:
    fn = _norm_path_sep(str(item.get("filename", "")).strip())
    try:
        line = int(item.get("line_number", 0))
    except (TypeError, ValueError):
        line = 0
    tid = str(item.get("test_id", "")).strip()
    sev = str(item.get("issue_severity", "")).strip().upper()
    return (fn, line, tid, sev)


def bandit_result_identity(item: dict[str, Any]) -> tuple[str, int, str, str]:
    """Return identity tuple for Bandit ``results`` item deduplication."""
    return bandit_result_sort_key(item)


def merge_bandit_raw_payloads(payloads: list[dict[str, Any]]) -> dict[str, Any]:
    """Merge Bandit CLI JSON dicts by unioning ``results`` (other keys ignored)."""
    seen: dict[tuple[str, int, str, str], dict[str, Any]] = {}
    for payload in payloads:
        if not isinstance(payload, dict):
            continue
        results = payload.get("results")
        if not isinstance(results, list):
            continue
        for item in results:
            if not isinstance(item, dict):
                continue
            key = bandit_result_identity(item)
            seen.setdefault(key, item)
    merged_list = sorted(seen.values(), key=bandit_result_sort_key)
    return {"results": merged_list}


def pyright_diagnostic_identity(item: dict[str, Any]) -> tuple[str, int, int, str, str, str]:
    """Stable key for Pyright ``generalDiagnostics`` deduplication."""
    fn = _norm_path_sep(str(item.get("file", "")).strip())
    sev = str(item.get("severity", "")).lower().strip()
    msg = str(item.get("message", "")).strip()
    rule = str(item.get("rule", "") or "").strip()
    rng = item.get("range")
    line, char = 0, 0
    if isinstance(rng, dict):
        start = rng.get("start")
        if isinstance(start, dict):
            try:
                line = int(start.get("line", 0))
            except (TypeError, ValueError):
                line = 0
            try:
                char = int(start.get("character", 0))
            except (TypeError, ValueError):
                char = 0
    return (fn, line, char, sev, rule, msg)


def pyright_diagnostic_sort_key(item: dict[str, Any]) -> tuple[str, int, int, str, str, str]:
    return pyright_diagnostic_identity(item)


def merge_pyright_json_payloads(payloads: list[dict[str, Any]]) -> dict[str, Any]:
    """Merge Pyright ``--outputjson`` objects: union ``generalDiagnostics``, dedupe, fix ``summary``."""
    if not payloads:
        return {"version": "", "summary": {}, "generalDiagnostics": []}
    seen: dict[tuple[str, int, int, str, str, str], dict[str, Any]] = {}
    for payload in payloads:
        if not isinstance(payload, dict):
            continue
        diags = payload.get("generalDiagnostics")
        if not isinstance(diags, list):
            continue
        for d in diags:
            if not isinstance(d, dict):
                continue
            key = pyright_diagnostic_identity(d)
            seen.setdefault(key, d)
    merged_diags = sorted(seen.values(), key=pyright_diagnostic_sort_key)
    err = sum(1 for d in merged_diags if str(d.get("severity", "")).lower() == "error")
    warn = sum(1 for d in merged_diags if str(d.get("severity", "")).lower() == "warning")
    info = sum(
        1 for d in merged_diags if str(d.get("severity", "")).lower() == "information"
    )
    files_with_diag: set[str] = set()
    for d in merged_diags:
        fn = str(d.get("file", "")).strip()
        if fn:
            files_with_diag.add(_norm_path_sep(fn))
    base: dict[str, Any] = dict(payloads[0])
    base["generalDiagnostics"] = merged_diags
    summ: dict[str, Any] = dict(base.get("summary") or {}) if isinstance(base.get("summary"), dict) else {}
    summ["errorCount"] = err
    summ["warningCount"] = warn
    summ["informationCount"] = info
    prev_fa = 0
    try:
        prev_fa = int(summ.get("filesAnalyzed", 0) or 0)
    except (TypeError, ValueError):
        prev_fa = 0
    summ["filesAnalyzed"] = max(prev_fa, len(files_with_diag))
    base["summary"] = summ
    return base
