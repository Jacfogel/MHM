#!/usr/bin/env python3
# TOOL_TIER: supporting

"""
Analyze possible duplicate/similar functions and methods across the codebase.

This tool looks for functions with similar names, arguments, local variables,
and imports. It reports possible duplicates using a weighted similarity score.

- Records are deduplicated by (file, line, full_name) so the same function is
  never compared with itself (avoids false-positive "self-pair" groups).
- Groups containing only one unique function are filtered out.
- Use --max-groups N to report more or fewer groups (default from config).
- When the report is capped at max_groups, the human-readable output and
  details.groups_capped in JSON indicate it.

Exclusion: Functions can be excluded from duplicate detection by adding a
comment inside the function (or in the few lines before it): 
  # duplicate_functions_exclude
  or
  # duplicate functions exclude
(optionally with a reason after a colon). Use this for intentional thin
wrappers (e.g. same method name across classes that delegate to a shared
helper) or other cases that are not actionable duplicates.

Not duplication: To suppress reporting of a specific intentional group
(e.g. polymorphism, same API pattern), add the same comment to every
function in that group, including a group id after a colon so the tool
knows which pairs to suppress. Only pairs where both functions have the
same group id are omitted; future duplicates without the comment still
appear. Example (all three methods get the same id):
  # not_duplicate: format_message
  # duplicate_functions_intentional: get_color_for_type
Supported: duplicate_functions_intentional, not_duplicate, duplicate functions intentional.

Optional body/structural similarity: Use --consider-body-similarity (or config
consider_body_similarity) to also compare functions by AST body structure,
surfacing pairs with different names but similar logic. Cost is capped via
max_body_candidate_pairs and body_similarity_scope (e.g. same_file).
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypedDict
from collections.abc import Iterable

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.logger import get_component_logger

try:
    from .. import config
    from ..shared.standard_exclusions import should_exclude_file
except ImportError:
    from development_tools import config
    from development_tools.shared.standard_exclusions import should_exclude_file

config.load_external_config()

logger = get_component_logger("development_tools")


FunctionSummary = TypedDict(
    "FunctionSummary",
    {
        "name": str,
        "full_name": str,
        "class": str | None,
        "file": str,
        "line": int,
        "args": list[str],
    },
)


class _PairResultRequired(TypedDict):
    overall_similarity: float
    name_similarity: float
    args_similarity: float
    locals_similarity: float
    imports_similarity: float
    a: FunctionSummary
    b: FunctionSummary


class PairResult(_PairResultRequired, total=False):
    body_similarity: float


class GroupSummary(TypedDict):
    similarity_range: dict[str, float]
    functions: list[FunctionSummary]
    pair_examples: list[PairResult]


class ClusterData(TypedDict):
    functions: dict[str, FunctionSummary]
    similarities: list[float]
    pair_examples: list[PairResult]


FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef


@dataclass(frozen=True)
class FunctionRecord:
    name: str
    full_name: str
    class_name: str | None
    file_path: str
    line: int
    args: tuple[str, ...]
    locals_used: tuple[str, ...]
    imports_used: tuple[str, ...]
    name_tokens: tuple[str, ...]
    excluded: bool = False  # True if # duplicate_functions_exclude (or variant) in function
    intentional_group_id: str | None = None  # If set, pair is omitted only when both sides have same id
    body_node_sequence: tuple[str, ...] | None = None  # AST node-type sequence when body similarity enabled


def _get_analysis_config() -> dict:
    return config.get_analyze_duplicate_functions_config()


def _tokenize_name(name: str) -> list[str]:
    tokens: list[str] = []
    for part in re.split(r"_+", name):
        if not part:
            continue
        for token in re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+", part):
            if token:
                tokens.append(token.lower())
    return tokens


def _jaccard(a: Iterable[str], b: Iterable[str]) -> float:
    set_a = set(a)
    set_b = set(b)
    if not set_a or not set_b:
        return 0.0
    intersection = set_a.intersection(set_b)
    union = set_a.union(set_b)
    return len(intersection) / len(union)


def _collect_imports(tree: ast.AST) -> set[str]:
    imports: set[str] = set()
    for node in tree.body if isinstance(tree, ast.Module) else []:
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name:
                    imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                if module:
                    imports.add(module)
                    if alias.name:
                        imports.add(f"{module}.{alias.name}")
                elif alias.name:
                    imports.add(alias.name)
    return imports


class _LocalNameCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.names: set[str] = set()
        self.self_attrs: set[str] = set()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        # Do not traverse nested functions
        return

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        # Do not traverse nested async functions
        return

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        # Do not traverse nested classes
        return

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Store) and node.id:
            self.names.add(node.id)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if isinstance(node.value, ast.Name) and node.value.id in ("self", "cls"):
            if node.attr:
                self.self_attrs.add(node.attr)
        self.generic_visit(node)


def _function_has_exclude_comment(content: str, node: FunctionNode) -> bool:
    """Return True if the function (or a few lines before it) contains duplicate_functions_exclude."""
    if not content:
        return False
    lines = content.split("\n")
    start_lineno = getattr(node, "lineno", 1) or 1
    end_lineno = getattr(node, "end_lineno", start_lineno) or start_lineno
    context_start = max(0, start_lineno - 4)
    snippet = "\n".join(lines[context_start:end_lineno]).lower()
    return (
        "# duplicate_functions_exclude" in snippet
        or "# duplicate functions exclude" in snippet
    )


def _get_intentional_group_id(content: str, node: FunctionNode) -> str | None:
    """If the function (or a few lines before it) has an intentional/not_duplicate marker with a group id after a colon, return that id (normalized). Otherwise None."""
    if not content:
        return None
    lines = content.split("\n")
    start_lineno = getattr(node, "lineno", 1) or 1
    end_lineno = getattr(node, "end_lineno", start_lineno) or start_lineno
    # Include enough lines before def so comment above decorator(s) is found
    context_start = max(0, start_lineno - 8)
    snippet_lower = "\n".join(lines[context_start:end_lineno]).lower()
    markers = (
        "# duplicate_functions_intentional:",
        "# not_duplicate:",
        "# duplicate functions intentional:",
    )
    for marker in markers:
        idx = snippet_lower.find(marker)
        if idx >= 0:
            rest = snippet_lower[idx + len(marker) :].split("\n")[0].strip()
            group_id = rest.split("#")[0].strip()
            return group_id if group_id else ""
    if (
        "# duplicate_functions_intentional" in snippet_lower
        or "# not_duplicate" in snippet_lower
        or "# duplicate functions intentional" in snippet_lower
    ):
        return ""
    return None


def _deserialize_intentional_group_id(raw: Any) -> str | None:
    """Return normalized intentional_group_id from cache/item; None if missing or invalid."""
    if raw is None:
        return None
    if isinstance(raw, bool):
        return "" if raw else None
    return str(raw).strip() or None


def _body_node_sequence(node: FunctionNode) -> tuple[str, ...]:
    """Return a normalized sequence of AST node-type names for the function body (top-level statements only)."""
    return tuple(type(stmt).__name__ for stmt in node.body)


class _FunctionCollector(ast.NodeVisitor):
    def __init__(
        self,
        file_path: str,
        imports_used: set[str],
        content: str = "",
        consider_body_similarity: bool = False,
    ) -> None:
        self.file_path = file_path
        self.imports_used = tuple(sorted(imports_used))
        self.content = content
        self.class_stack: list[str] = []
        self.records: list[FunctionRecord] = []
        self.consider_body_similarity = consider_body_similarity

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()

    def _handle_function(self, node: FunctionNode) -> None:
        class_name = self.class_stack[-1] if self.class_stack else None
        full_name = f"{class_name}.{node.name}" if class_name else node.name

        args = [
            arg.arg
            for arg in node.args.args
            if arg.arg and arg.arg not in ("self", "cls")
        ]
        locals_collector = _LocalNameCollector()
        for stmt in node.body:
            locals_collector.visit(stmt)
        locals_used = sorted(
            {
                name.lower()
                for name in locals_collector.names.union(locals_collector.self_attrs)
                if name
            }
        )
        name_tokens = _tokenize_name(node.name)
        excluded = _function_has_exclude_comment(self.content, node)
        intentional_group_id = _get_intentional_group_id(self.content, node)
        body_seq: tuple[str, ...] | None = (
            _body_node_sequence(node) if self.consider_body_similarity else None
        )

        record = FunctionRecord(
            name=node.name,
            full_name=full_name,
            class_name=class_name,
            file_path=self.file_path,
            line=getattr(node, "lineno", 0),
            args=tuple(arg.lower() for arg in args),
            locals_used=tuple(locals_used),
            imports_used=self.imports_used,
            name_tokens=tuple(name_tokens),
            excluded=excluded,
            intentional_group_id=intentional_group_id,
            body_node_sequence=body_seq,
        )
        self.records.append(record)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._handle_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._handle_function(node)


def _scan_file(
    file_path: Path, consider_body_similarity: bool = False
) -> list[FunctionRecord]:
    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content)
    except Exception as exc:
        logger.warning(f"Failed to parse {file_path}: {exc}")
        return []

    imports_used = _collect_imports(tree)
    collector = _FunctionCollector(
        str(file_path),
        imports_used,
        content=content,
        consider_body_similarity=consider_body_similarity,
    )
    collector.visit(tree)
    return collector.records


def _serialize_records(
    records: list[FunctionRecord], include_body: bool = False
) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for record in records:
        item: dict[str, object] = {
            "name": record.name,
            "full_name": record.full_name,
            "class_name": record.class_name,
            "file_path": record.file_path,
            "line": record.line,
            "args": list(record.args),
            "locals_used": list(record.locals_used),
            "imports_used": list(record.imports_used),
            "name_tokens": list(record.name_tokens),
            "excluded": getattr(record, "excluded", False),
            "intentional_group_id": getattr(record, "intentional_group_id", None),
        }
        body_seq = getattr(record, "body_node_sequence", None)
        if include_body and body_seq is not None:
            item["body_node_sequence"] = list(body_seq)
        out.append(item)
    return out


def _deserialize_records(data: list[dict[str, Any]]) -> list[FunctionRecord]:
    records: list[FunctionRecord] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        class_name_raw = item.get("class_name")
        class_name = class_name_raw if isinstance(class_name_raw, str) else None
        line_raw = item.get("line", 0)
        line = int(line_raw) if isinstance(line_raw, (int, float)) else 0
        args_raw = item.get("args", [])
        args_seq = args_raw if isinstance(args_raw, (list, tuple)) else []
        locals_raw = item.get("locals_used", [])
        locals_seq = locals_raw if isinstance(locals_raw, (list, tuple)) else []
        imports_raw = item.get("imports_used", [])
        imports_seq = imports_raw if isinstance(imports_raw, (list, tuple)) else []
        tokens_raw = item.get("name_tokens", [])
        tokens_seq = tokens_raw if isinstance(tokens_raw, (list, tuple)) else []
        body_raw = item.get("body_node_sequence")
        body_seq: tuple[str, ...] | None = None
        if isinstance(body_raw, (list, tuple)):
            body_seq = tuple(str(x) for x in body_raw)
        records.append(
            FunctionRecord(
                name=str(item.get("name", "")),
                full_name=str(item.get("full_name", "")),
                class_name=class_name,
                file_path=str(item.get("file_path", "")),
                line=line,
                args=tuple(str(arg).lower() for arg in args_seq),
                locals_used=tuple(str(name).lower() for name in locals_seq),
                imports_used=tuple(str(name) for name in imports_seq),
                name_tokens=tuple(str(token) for token in tokens_seq),
                excluded=bool(item.get("excluded", False)),
                intentional_group_id=_deserialize_intentional_group_id(item.get("intentional_group_id")),
                body_node_sequence=body_seq,
            )
        )
    return records


def _gather_function_records(
    include_tests: bool,
    include_dev_tools: bool,
    consider_body_similarity: bool = False,
) -> tuple[list[FunctionRecord], dict[str, int]]:
    project_root = Path(config.get_project_root())
    scan_dirs = list(config.get_scan_directories())
    analysis_config = _get_analysis_config()
    use_cache = bool(analysis_config.get("use_mtime_cache", True))

    from development_tools.shared.mtime_cache import MtimeFileCache

    cache_tool_name = (
        "analyze_duplicate_functions_body"
        if consider_body_similarity
        else "analyze_duplicate_functions"
    )
    cache = MtimeFileCache(
        project_root=project_root,
        use_cache=use_cache,
        tool_name=cache_tool_name,
        domain="functions",
        tool_paths=[Path(__file__)],
    )

    if include_tests and "tests" not in scan_dirs:
        scan_dirs.append("tests")
    if include_dev_tools and "development_tools" not in scan_dirs:
        scan_dirs.append("development_tools")

    context = "development" if include_tests or include_dev_tools else "production"
    include_body = consider_body_similarity

    records: list[FunctionRecord] = []
    total_files = 0
    cached_files = 0
    scanned_files = 0

    for scan_dir in scan_dirs:
        dir_path = project_root / scan_dir
        if not dir_path.exists():
            continue
        for py_file in dir_path.rglob("*.py"):
            if should_exclude_file(str(py_file), "analysis", context):
                continue
            total_files += 1
            cached_records = cache.get_cached(py_file)
            if isinstance(cached_records, list):
                cached_files += 1
                records.extend(_deserialize_records(cached_records))
                continue
            file_records = _scan_file(py_file, consider_body_similarity=consider_body_similarity)
            cache.cache_results(py_file, _serialize_records(file_records, include_body=include_body))
            scanned_files += 1
            records.extend(file_records)

    for py_file in project_root.glob("*.py"):
        if should_exclude_file(str(py_file), "analysis", context):
            continue
        total_files += 1
        cached_records = cache.get_cached(py_file)
        if isinstance(cached_records, list):
            cached_files += 1
            records.extend(_deserialize_records(cached_records))
            continue
        file_records = _scan_file(py_file, consider_body_similarity=consider_body_similarity)
        cache.cache_results(py_file, _serialize_records(file_records, include_body=include_body))
        scanned_files += 1
        records.extend(file_records)

    cache.save_cache()
    return records, {
        "total_files": total_files,
        "cached_files": cached_files,
        "scanned_files": scanned_files,
    }


def _build_candidate_pairs(
    records: list[FunctionRecord],
    stop_tokens: set[str],
    max_token_group_size: int,
    max_candidate_pairs: int,
) -> tuple[set[tuple[int, int]], dict[str, int], bool]:
    token_to_ids: dict[str, list[int]] = {}
    for idx, record in enumerate(records):
        if getattr(record, "excluded", False):
            continue
        for token in record.name_tokens:
            if token in stop_tokens:
                continue
            token_to_ids.setdefault(token, []).append(idx)

    skipped_tokens: dict[str, int] = {}
    candidate_pairs: set[tuple[int, int]] = set()
    max_reached = False

    for token, ids in token_to_ids.items():
        if len(ids) > max_token_group_size:
            skipped_tokens[token] = len(ids)
            continue
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                pair = (ids[i], ids[j])
                if pair not in candidate_pairs:
                    candidate_pairs.add(pair)
                    if len(candidate_pairs) >= max_candidate_pairs:
                        max_reached = True
                        return candidate_pairs, skipped_tokens, max_reached

    return candidate_pairs, skipped_tokens, max_reached


def _build_body_candidate_pairs(
    records: list[FunctionRecord],
    scope: str,
    max_pairs: int,
) -> set[tuple[int, int]]:
    """Build candidate pairs for body similarity (e.g. same file or same module). Capped at max_pairs."""
    pairs: set[tuple[int, int]] = set()
    n = len(records)

    # Only consider records that have body data and are not excluded
    eligible = [
        i
        for i in range(n)
        if not getattr(records[i], "excluded", False)
        and getattr(records[i], "body_node_sequence", None)
    ]

    if scope == "same_file":
        by_file: dict[str, list[int]] = {}
        for i in eligible:
            path = records[i].file_path or ""
            by_file.setdefault(path, []).append(i)
        for indices in by_file.values():
            for ii in range(len(indices)):
                for jj in range(ii + 1, len(indices)):
                    a_id, b_id = indices[ii], indices[jj]
                    pairs.add((min(a_id, b_id), max(a_id, b_id)))
                    if len(pairs) >= max_pairs:
                        return pairs
    elif scope == "same_module":
        def _module_key(idx: int) -> str:
            p = (records[idx].file_path or "").replace("\\", "/")
            if "/" in p:
                return p.rsplit("/", 1)[0]
            return ""

        by_module: dict[str, list[int]] = {}
        for i in eligible:
            by_module.setdefault(_module_key(i), []).append(i)
        for indices in by_module.values():
            for ii in range(len(indices)):
                for jj in range(ii + 1, len(indices)):
                    a_id, b_id = indices[ii], indices[jj]
                    pairs.add((min(a_id, b_id), max(a_id, b_id)))
                    if len(pairs) >= max_pairs:
                        return pairs
    else:
        # hash_bucket: group by hash of body sequence, compare within bucket
        from hashlib import md5

        buckets: dict[str, list[int]] = {}
        for i in eligible:
            seq = getattr(records[i], "body_node_sequence", None) or ()
            key = (
                md5(" ".join(seq).encode(), usedforsecurity=False).hexdigest()
                if seq
                else ""
            )
            buckets.setdefault(key, []).append(i)
        for indices in buckets.values():
            for ii in range(len(indices)):
                for jj in range(ii + 1, len(indices)):
                    a_id, b_id = indices[ii], indices[jj]
                    pairs.add((min(a_id, b_id), max(a_id, b_id)))
                    if len(pairs) >= max_pairs:
                        return pairs
    return pairs


def _record_identity(
    record: FunctionRecord, project_root: Path | None = None
) -> tuple[str, int, str]:
    """Return (file_path, line, full_name) for deduplication. Path normalized for cross-platform and project-relative consistency."""
    raw = (record.file_path or "").strip()
    if project_root is not None and raw:
        try:
            resolved = Path(raw).resolve()
            root_resolved = Path(project_root).resolve()
            path_key = resolved.relative_to(root_resolved).as_posix()
        except (ValueError, OSError):
            path_key = raw.replace("\\", "/")
    else:
        path_key = raw.replace("\\", "/")
    return (path_key, record.line, record.full_name)


def _deduplicate_records(
    records: list[FunctionRecord], project_root: Path | None = None
) -> list[FunctionRecord]:
    """Remove duplicate records (same file, line, full_name). Keeps first occurrence. Uses project-relative path when project_root given."""
    seen: set[tuple[str, int, str]] = set()
    result: list[FunctionRecord] = []
    for r in records:
        key = _record_identity(r, project_root)
        if key in seen:
            continue
        seen.add(key)
        result.append(r)
    return result


def _compute_similarity(
    a: FunctionRecord, b: FunctionRecord, weights: dict[str, float]
) -> tuple[float, dict[str, float]]:
    name_score = _jaccard(a.name_tokens, b.name_tokens)
    args_score = _jaccard(a.args, b.args)
    locals_score = _jaccard(a.locals_used, b.locals_used)
    imports_score = _jaccard(a.imports_used, b.imports_used)
    scores: dict[str, float] = {
        "name": name_score,
        "args": args_score,
        "locals": locals_score,
        "imports": imports_score,
    }
    body_score: float | None = None
    a_body = getattr(a, "body_node_sequence", None)
    b_body = getattr(b, "body_node_sequence", None)
    if a_body is not None and b_body is not None:
        body_score = _jaccard(a_body, b_body)
        scores["body"] = body_score
    weight_sum = sum(weights.values()) or 1.0
    overall = (
        name_score * weights.get("name", 0.0)
        + args_score * weights.get("args", 0.0)
        + locals_score * weights.get("locals", 0.0)
        + imports_score * weights.get("imports", 0.0)
    )
    if body_score is not None and weight_sum > 0:
        overall += body_score * weights.get("body", 0.0)
    if weight_sum > 0:
        overall /= weight_sum
    return overall, scores


def _analyze_duplicates(
    records: list[FunctionRecord],
    config_values: dict,
    cache_stats: dict[str, int] | None = None,
) -> dict[str, Any]:
    weights = config_values.get("weights", {})
    min_name_similarity = float(config_values.get("min_name_similarity", 0.6))
    min_overall_similarity = float(config_values.get("min_overall_similarity", 0.7))
    max_pairs = int(config_values.get("max_pairs", 50))
    max_groups = int(config_values.get("max_groups", 25))
    max_candidate_pairs = int(config_values.get("max_candidate_pairs", 20000))
    max_token_group_size = int(config_values.get("max_token_group_size", 200))
    stop_tokens = set(config_values.get("stop_name_tokens", []))
    consider_body_similarity = bool(config_values.get("consider_body_similarity", False))
    body_for_near_miss_only = bool(config_values.get("body_for_near_miss_only", False))
    body_similarity_min_name_threshold = float(
        config_values.get("body_similarity_min_name_threshold", 0.35)
    )
    max_body_candidate_pairs = int(config_values.get("max_body_candidate_pairs", 5000))
    body_similarity_scope = str(config_values.get("body_similarity_scope", "same_file"))
    weights = dict(weights or {})
    body_weight = float(weights.get("body", 0.0))
    if (consider_body_similarity or body_for_near_miss_only) and body_weight == 0.0:
        weights = {**weights, "body": 0.25}
        body_weight = 0.25
    weights_no_body = {k: v for k, v in weights.items() if k != "body"} if weights else {}
    if not weights_no_body:
        weights_no_body = dict(weights or {})

    # Deduplicate so the same function (file, line, full_name) is not compared with itself.
    # Use project-relative path so the same file from different scan paths is deduplicated.
    project_root = Path(config.get_project_root()).resolve()
    original_count = len(records)
    records = _deduplicate_records(records, project_root=project_root)
    records_deduplicated = original_count - len(records)

    candidate_pairs, skipped_tokens, max_reached = _build_candidate_pairs(
        records,
        stop_tokens=stop_tokens,
        max_token_group_size=max_token_group_size,
        max_candidate_pairs=max_candidate_pairs,
    )
    body_pairs_count = 0
    if consider_body_similarity and not body_for_near_miss_only:
        body_pairs = _build_body_candidate_pairs(
            records, scope=body_similarity_scope, max_pairs=max_body_candidate_pairs
        )
        body_pairs_count = len(body_pairs)
        candidate_pairs = candidate_pairs.union(body_pairs)

    record_by_id = {idx: record for idx, record in enumerate(records)}

    pair_results: list[PairResult] = []
    pairs_filtered_intentional = 0
    for a_id, b_id in candidate_pairs:
        a = record_by_id[a_id]
        b = record_by_id[b_id]
        a_gid = getattr(a, "intentional_group_id", None)
        b_gid = getattr(b, "intentional_group_id", None)
        if a_gid is not None and b_gid is not None and a_gid == b_gid:
            pairs_filtered_intentional += 1
            continue
        if body_for_near_miss_only:
            overall_base, scores_base = _compute_similarity(a, b, weights_no_body)
            passes_normal = (
                scores_base["name"] >= min_name_similarity
                and overall_base >= min_overall_similarity
            )
            if passes_normal:
                overall, scores = _compute_similarity(a, b, weights)
                item = _make_pair_result_item(a, b, overall, scores)
                pair_results.append(item)
                continue
            if scores_base["name"] < body_similarity_min_name_threshold:
                continue
            overall, scores = _compute_similarity(a, b, weights)
            if overall < min_overall_similarity:
                continue
            item = _make_pair_result_item(a, b, overall, scores)
            pair_results.append(item)
        else:
            overall, scores = _compute_similarity(a, b, weights)
            use_body_score = "body" in scores and body_weight > 0
            if not use_body_score and scores["name"] < min_name_similarity:
                continue
            if overall < min_overall_similarity:
                continue
            item = _make_pair_result_item(a, b, overall, scores)
            pair_results.append(item)

    pair_results.sort(
        key=lambda item: float(item["overall_similarity"]), reverse=True
    )

    # Build all groups (no cap yet), then keep only multi-function groups, then apply max_groups
    # so we report the top max_groups *real* duplicate groups, not "top N then drop singles"
    all_groups = _group_pairs(pair_results, max_groups=None)
    groups_before_filter = len(all_groups)
    multi_function_groups = [g for g in all_groups if len(g.get("functions", [])) >= 2]
    groups_filtered_single_function = groups_before_filter - len(multi_function_groups)
    groups = multi_function_groups[:max_groups]

    files_affected = {
        entry["file"]
        for group in groups
        for entry in group.get("functions", [])
        if entry.get("file")
    }
    functions_excluded = sum(1 for r in records if getattr(r, "excluded", False))

    details: dict[str, Any] = {
        "total_functions": len(records),
        "functions_excluded": functions_excluded,
        "records_deduplicated": records_deduplicated,
        "groups_filtered_single_function": groups_filtered_single_function,
        "cache": cache_stats or {},
        "pairs_considered": len(candidate_pairs),
        "pairs_reported": len(pair_results),
        "groups_reported": len(groups),
        "min_name_similarity": min_name_similarity,
        "min_overall_similarity": min_overall_similarity,
        "weights": weights,
        "max_candidate_pairs": max_candidate_pairs,
        "max_token_group_size": max_token_group_size,
        "max_pairs": max_pairs,
        "max_groups": max_groups,
        "skipped_token_groups": skipped_tokens,
        "candidate_pair_cap_reached": max_reached,
        "groups_capped": len(multi_function_groups) > max_groups and max_groups > 0,
        "top_pairs": pair_results[:max_pairs],
        "duplicate_groups": groups,
    }
    if pairs_filtered_intentional > 0:
        details["pairs_filtered_intentional"] = pairs_filtered_intentional
    if consider_body_similarity or body_for_near_miss_only:
        details["consider_body_similarity_used"] = consider_body_similarity
        if body_for_near_miss_only:
            details["body_for_near_miss_only"] = True
            details["body_similarity_min_name_threshold"] = body_similarity_min_name_threshold
        if consider_body_similarity and not body_for_near_miss_only:
            details["body_candidate_pairs_considered"] = body_pairs_count
    return {
        "summary": {
            "total_issues": len(groups),
            "files_affected": len(files_affected),
        },
        "details": details,
    }


def _record_summary(record: FunctionRecord) -> FunctionSummary:
    return {
        "name": record.name,
        "full_name": record.full_name,
        "class": record.class_name,
        "file": _normalize_path(record.file_path),
        "line": record.line,
        "args": list(record.args),
    }


def _make_pair_result_item(
    a: FunctionRecord, b: FunctionRecord, overall: float, scores: dict[str, float]
) -> PairResult:
    item: PairResult = {
        "overall_similarity": round(overall, 3),
        "name_similarity": round(scores["name"], 3),
        "args_similarity": round(scores["args"], 3),
        "locals_similarity": round(scores["locals"], 3),
        "imports_similarity": round(scores["imports"], 3),
        "a": _record_summary(a),
        "b": _record_summary(b),
    }
    if "body" in scores:
        item["body_similarity"] = round(scores["body"], 3)
    return item


def _normalize_path(path: str) -> str:
    try:
        resolved = Path(path).resolve()
        project_root = Path(config.get_project_root()).resolve()
        try:
            return resolved.relative_to(project_root).as_posix()
        except ValueError:
            return resolved.as_posix()
    except Exception:
        return path.replace("\\", "/")


def _group_pairs(
    pair_results: list[PairResult], max_groups: int | None = None
) -> list[GroupSummary]:
    if not pair_results:
        return []

    # Union-Find for grouping pairs into clusters
    parent: dict[str, str] = {}

    def find(node: str) -> str:
        root = node
        while parent.get(root, root) != root:
            root = parent[root]
        while node != root:
            next_node = parent.get(node, node)
            parent[node] = root
            node = next_node
        return root

    def union(a: str, b: str) -> None:
        root_a = find(a)
        root_b = find(b)
        if root_a != root_b:
            parent[root_b] = root_a

    for item in pair_results:
        a_key = _pair_key(item["a"])
        b_key = _pair_key(item["b"])
        parent.setdefault(a_key, a_key)
        parent.setdefault(b_key, b_key)
        union(a_key, b_key)

    clusters: dict[str, ClusterData] = {}
    for item in pair_results:
        a_key = _pair_key(item["a"])
        b_key = _pair_key(item["b"])
        cluster_key = find(a_key)
        cluster = clusters.setdefault(
            cluster_key,
            {
                "functions": {},
                "similarities": [],
                "pair_examples": [],
            },
        )
        cluster["functions"][a_key] = item["a"]
        cluster["functions"][b_key] = item["b"]
        cluster["similarities"].append(item["overall_similarity"])
        if len(cluster["pair_examples"]) < 5:
            cluster["pair_examples"].append(item)

    grouped: list[GroupSummary] = []
    for cluster in clusters.values():
        similarities = cluster["similarities"]
        if not similarities:
            continue
        functions_list = list(cluster["functions"].values())
        pair_examples = cluster["pair_examples"]
        grouped.append(
            {
                "similarity_range": {
                    "min": round(min(similarities), 3),
                    "max": round(max(similarities), 3),
                },
                "functions": functions_list,
                "pair_examples": pair_examples,
            }
        )

    grouped.sort(
        key=lambda item: item["similarity_range"]["max"], reverse=True
    )
    if max_groups is not None and max_groups > 0:
        return grouped[:max_groups]
    return grouped


def _pair_key(summary: FunctionSummary) -> str:
    return f"{summary.get('file')}:{summary.get('line')}:{summary.get('full_name')}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analyze possible duplicate or similar functions and methods."
    )
    parser.add_argument(
        "--include-tests", action="store_true", help="Include test files in analysis."
    )
    parser.add_argument(
        "--include-dev-tools",
        action="store_true",
        help="Include development_tools in analysis.",
    )
    parser.add_argument(
        "--json", action="store_true", help="Output results as JSON."
    )
    parser.add_argument(
        "--consider-body-similarity",
        action="store_true",
        help="Include body/structural similarity (AST node-type sequence); increases runtime.",
    )
    parser.add_argument(
        "--body-for-near-miss",
        action="store_true",
        help="Run body similarity only on name-token pairs that exceed a lower name threshold (for full-audit near-miss rescue).",
    )
    parser.add_argument(
        "--min-overall",
        type=float,
        default=None,
        help="Override minimum overall similarity threshold.",
    )
    parser.add_argument(
        "--min-name",
        type=float,
        default=None,
        help="Override minimum name similarity threshold.",
    )
    parser.add_argument(
        "--max-groups",
        type=int,
        default=None,
        metavar="N",
        help="Maximum number of duplicate groups to report (default from config, often 25).",
    )

    args = parser.parse_args()

    analysis_config = _get_analysis_config()
    if args.consider_body_similarity:
        analysis_config["consider_body_similarity"] = True
    if args.body_for_near_miss:
        analysis_config["body_for_near_miss_only"] = True
        analysis_config["consider_body_similarity"] = True
    if args.min_overall is not None:
        analysis_config["min_overall_similarity"] = args.min_overall
    if args.min_name is not None:
        analysis_config["min_name_similarity"] = args.min_name
    if args.max_groups is not None:
        analysis_config["max_groups"] = args.max_groups

    use_body = (
        analysis_config.get("consider_body_similarity", False)
        or analysis_config.get("body_for_near_miss_only", False)
    )
    records, cache_stats = _gather_function_records(
        include_tests=args.include_tests,
        include_dev_tools=args.include_dev_tools,
        consider_body_similarity=use_body,
    )
    result = _analyze_duplicates(records, analysis_config, cache_stats=cache_stats)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        summary: dict[str, Any] = result.get("summary") or {}
        details: dict[str, Any] = result.get("details") or {}
        print("Possible Duplicate Functions")
        print("=" * 30)
        print(f"Total functions analyzed: {details.get('total_functions', 0)}")
        if details.get("records_deduplicated", 0) > 0:
            print(f"Duplicate records removed: {details.get('records_deduplicated', 0)}")
        if details.get("groups_filtered_single_function", 0) > 0:
            print(f"Single-function groups filtered out: {details.get('groups_filtered_single_function', 0)}")
        print(f"Duplicate groups found: {summary.get('total_issues', 0)}")
        if details.get("groups_capped", False):
            print(f"(Report capped at max_groups={details.get('max_groups', 0)}; use --max-groups N for more.)")
        if summary.get("total_issues", 0) > 0:
            top_pairs = details.get("top_pairs", [])[:5]
            if top_pairs:
                print("\nTop Similarity Pairs:")
                for pair in top_pairs:
                    a = pair.get("a", {})
                    b = pair.get("b", {})
                    overall = pair.get("overall_similarity")
                    print(
                        f"- {a.get('full_name')} ({Path(a.get('file', '')).name}) "
                        f"<-> {b.get('full_name')} ({Path(b.get('file', '')).name}) "
                        f"score={overall}"
                    )
            else:
                print("No high-confidence pairs found.")
        else:
            print("No duplicate groups detected.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
