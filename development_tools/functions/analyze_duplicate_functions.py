#!/usr/bin/env python3
# TOOL_TIER: supporting

"""
Analyze possible duplicate/similar functions and methods across the codebase.

This tool looks for functions with similar names, arguments, local variables,
and imports. It reports possible duplicates using a weighted similarity score.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple, TypedDict, Union

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
        "class": Optional[str],
        "file": str,
        "line": int,
        "args": List[str],
    },
)

PairResult = TypedDict(
    "PairResult",
    {
        "overall_similarity": float,
        "name_similarity": float,
        "args_similarity": float,
        "locals_similarity": float,
        "imports_similarity": float,
        "a": FunctionSummary,
        "b": FunctionSummary,
    },
)

GroupSummary = TypedDict(
    "GroupSummary",
    {
        "similarity_range": Dict[str, float],
        "functions": List[FunctionSummary],
        "pair_examples": List[PairResult],
    },
)

ClusterData = TypedDict(
    "ClusterData",
    {
        "functions": Dict[str, FunctionSummary],
        "similarities": List[float],
        "pair_examples": List[PairResult],
    },
)

FunctionNode = Union[ast.FunctionDef, ast.AsyncFunctionDef]


@dataclass(frozen=True)
class FunctionRecord:
    name: str
    full_name: str
    class_name: Optional[str]
    file_path: str
    line: int
    args: Tuple[str, ...]
    locals_used: Tuple[str, ...]
    imports_used: Tuple[str, ...]
    name_tokens: Tuple[str, ...]


def _get_analysis_config() -> Dict:
    return config.get_analyze_duplicate_functions_config()


def _tokenize_name(name: str) -> List[str]:
    tokens: List[str] = []
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


def _collect_imports(tree: ast.AST) -> Set[str]:
    imports: Set[str] = set()
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
        self.names: Set[str] = set()
        self.self_attrs: Set[str] = set()

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


class _FunctionCollector(ast.NodeVisitor):
    def __init__(self, file_path: str, imports_used: Set[str]) -> None:
        self.file_path = file_path
        self.imports_used = tuple(sorted(imports_used))
        self.class_stack: List[str] = []
        self.records: List[FunctionRecord] = []

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
        )
        self.records.append(record)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._handle_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._handle_function(node)


def _scan_file(file_path: Path) -> List[FunctionRecord]:
    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content)
    except Exception as exc:
        logger.warning(f"Failed to parse {file_path}: {exc}")
        return []

    imports_used = _collect_imports(tree)
    collector = _FunctionCollector(str(file_path), imports_used)
    collector.visit(tree)
    return collector.records


def _serialize_records(records: List[FunctionRecord]) -> List[Dict[str, object]]:
    return [
        {
            "name": record.name,
            "full_name": record.full_name,
            "class_name": record.class_name,
            "file_path": record.file_path,
            "line": record.line,
            "args": list(record.args),
            "locals_used": list(record.locals_used),
            "imports_used": list(record.imports_used),
            "name_tokens": list(record.name_tokens),
        }
        for record in records
    ]


def _deserialize_records(data: List[Dict[str, object]]) -> List[FunctionRecord]:
    records: List[FunctionRecord] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        records.append(
            FunctionRecord(
                name=str(item.get("name", "")),
                full_name=str(item.get("full_name", "")),
                class_name=item.get("class_name"),
                file_path=str(item.get("file_path", "")),
                line=int(item.get("line", 0) or 0),
                args=tuple(str(arg).lower() for arg in item.get("args", []) or []),
                locals_used=tuple(
                    str(name).lower() for name in item.get("locals_used", []) or []
                ),
                imports_used=tuple(
                    str(name) for name in item.get("imports_used", []) or []
                ),
                name_tokens=tuple(
                    str(token) for token in item.get("name_tokens", []) or []
                ),
            )
        )
    return records


def _gather_function_records(
    include_tests: bool, include_dev_tools: bool
) -> Tuple[List[FunctionRecord], Dict[str, int]]:
    project_root = Path(config.get_project_root())
    scan_dirs = list(config.get_scan_directories())
    analysis_config = _get_analysis_config()
    use_cache = bool(analysis_config.get("use_mtime_cache", True))

    from development_tools.shared.mtime_cache import MtimeFileCache

    cache = MtimeFileCache(
        project_root=project_root,
        use_cache=use_cache,
        tool_name="analyze_duplicate_functions",
        domain="functions",
    )

    if include_tests and "tests" not in scan_dirs:
        scan_dirs.append("tests")
    if include_dev_tools and "development_tools" not in scan_dirs:
        scan_dirs.append("development_tools")

    if include_tests or include_dev_tools:
        context = "development"
    else:
        context = "production"

    records: List[FunctionRecord] = []
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
            file_records = _scan_file(py_file)
            cache.cache_results(py_file, _serialize_records(file_records))
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
        file_records = _scan_file(py_file)
        cache.cache_results(py_file, _serialize_records(file_records))
        scanned_files += 1
        records.extend(file_records)

    cache.save_cache()
    return records, {
        "total_files": total_files,
        "cached_files": cached_files,
        "scanned_files": scanned_files,
    }


def _build_candidate_pairs(
    records: List[FunctionRecord],
    stop_tokens: Set[str],
    max_token_group_size: int,
    max_candidate_pairs: int,
) -> Tuple[Set[Tuple[int, int]], Dict[str, int], bool]:
    token_to_ids: Dict[str, List[int]] = {}
    for idx, record in enumerate(records):
        for token in record.name_tokens:
            if token in stop_tokens:
                continue
            token_to_ids.setdefault(token, []).append(idx)

    skipped_tokens: Dict[str, int] = {}
    candidate_pairs: Set[Tuple[int, int]] = set()
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


def _compute_similarity(
    a: FunctionRecord, b: FunctionRecord, weights: Dict[str, float]
) -> Tuple[float, Dict[str, float]]:
    name_score = _jaccard(a.name_tokens, b.name_tokens)
    args_score = _jaccard(a.args, b.args)
    locals_score = _jaccard(a.locals_used, b.locals_used)
    imports_score = _jaccard(a.imports_used, b.imports_used)

    weight_sum = sum(weights.values()) or 1.0
    overall = (
        name_score * weights.get("name", 0.0)
        + args_score * weights.get("args", 0.0)
        + locals_score * weights.get("locals", 0.0)
        + imports_score * weights.get("imports", 0.0)
    ) / weight_sum

    return overall, {
        "name": name_score,
        "args": args_score,
        "locals": locals_score,
        "imports": imports_score,
    }


def _analyze_duplicates(
    records: List[FunctionRecord],
    config_values: Dict,
    cache_stats: Optional[Dict[str, int]] = None,
) -> Dict[str, object]:
    weights = config_values.get("weights", {})
    min_name_similarity = float(config_values.get("min_name_similarity", 0.6))
    min_overall_similarity = float(config_values.get("min_overall_similarity", 0.7))
    max_pairs = int(config_values.get("max_pairs", 50))
    max_groups = int(config_values.get("max_groups", 25))
    max_candidate_pairs = int(config_values.get("max_candidate_pairs", 20000))
    max_token_group_size = int(config_values.get("max_token_group_size", 200))
    stop_tokens = set(config_values.get("stop_name_tokens", []))

    candidate_pairs, skipped_tokens, max_reached = _build_candidate_pairs(
        records,
        stop_tokens=stop_tokens,
        max_token_group_size=max_token_group_size,
        max_candidate_pairs=max_candidate_pairs,
    )

    record_by_id = {idx: record for idx, record in enumerate(records)}

    pair_results: List[PairResult] = []
    for a_id, b_id in candidate_pairs:
        a = record_by_id[a_id]
        b = record_by_id[b_id]
        overall, scores = _compute_similarity(a, b, weights)
        if scores["name"] < min_name_similarity:
            continue
        if overall < min_overall_similarity:
            continue
        pair_results.append(
            {
                "overall_similarity": round(overall, 3),
                "name_similarity": round(scores["name"], 3),
                "args_similarity": round(scores["args"], 3),
                "locals_similarity": round(scores["locals"], 3),
                "imports_similarity": round(scores["imports"], 3),
                "a": _record_summary(a),
                "b": _record_summary(b),
            }
        )

    pair_results.sort(
        key=lambda item: float(item["overall_similarity"]), reverse=True
    )

    groups = _group_pairs(pair_results, max_groups=max_groups)

    files_affected = {
        entry["file"]
        for group in groups
        for entry in group.get("functions", [])
        if entry.get("file")
    }

    return {
        "summary": {
            "total_issues": len(groups),
            "files_affected": len(files_affected),
        },
        "details": {
            "total_functions": len(records),
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
            "top_pairs": pair_results[:max_pairs],
            "duplicate_groups": groups,
        },
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


def _group_pairs(pair_results: List[PairResult], max_groups: int) -> List[GroupSummary]:
    if not pair_results:
        return []

    # Union-Find for grouping pairs into clusters
    parent: Dict[str, str] = {}

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

    clusters: Dict[str, ClusterData] = {}
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

    grouped: List[GroupSummary] = []
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
    return grouped[:max_groups]


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

    args = parser.parse_args()

    analysis_config = _get_analysis_config()
    if args.min_overall is not None:
        analysis_config["min_overall_similarity"] = args.min_overall
    if args.min_name is not None:
        analysis_config["min_name_similarity"] = args.min_name

    records, cache_stats = _gather_function_records(
        include_tests=args.include_tests,
        include_dev_tools=args.include_dev_tools,
    )
    result = _analyze_duplicates(records, analysis_config, cache_stats=cache_stats)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        summary = result.get("summary", {})
        details = result.get("details", {})
        print("Possible Duplicate Functions")
        print("=" * 30)
        print(f"Total functions analyzed: {details.get('total_functions', 0)}")
        print(f"Duplicate groups found: {summary.get('total_issues', 0)}")
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
