# TOOL_TIER: core

"""Versioned on-disk shard cache for static-check analyzers (§3.19.2).

Each tool stores a JSON manifest under ``development_tools/<domain>/jsons/scopes/<scope>/``:

- ``.{tool_name}_shard_cache.v1.json`` with ``version``, ``config_digest``, and per-shard
  entries holding ``source_signature`` (Python-only scope) and cached ``fragment`` payload.

Config-only changes bust all shards via ``config_digest`` (from
:func:`development_tools.shared.cache_dependency_paths.static_check_config_digest`).
"""

from __future__ import annotations

import contextlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any


SHARD_CACHE_VERSION = 1


def shard_cache_path(jsons_dir: Path, tool_name: str) -> Path:
    """Return manifest path for *tool_name* (e.g. ``analyze_ruff``)."""
    return Path(jsons_dir) / f".{tool_name}_shard_cache.v{SHARD_CACHE_VERSION}.json"


def stable_shard_id(rels: list[str]) -> str:
    """Stable id from repo-relative path strings (sorted, ``|``-joined)."""
    norm = sorted({str(r).strip().replace("\\", "/") for r in rels if str(r).strip()})
    return "|".join(norm) if norm else "__empty__"


def load_shard_manifest(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return None
        if int(data.get("version", -1)) != SHARD_CACHE_VERSION:
            return None
        return data
    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        return None


def save_shard_manifest_atomic(path: Path, data: dict[str, Any]) -> None:
    """Write JSON atomically (best-effort) next to *path*."""
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(data, indent=2, sort_keys=True)
    fd, tmp = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(raw)
        os.replace(tmp, path)
    except OSError:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


def shard_entry_hit(
    manifest: dict[str, Any] | None,
    *,
    config_digest: str | None,
    shard_id: str,
    source_signature: str | None,
) -> Any | None:
    """Return cached *fragment* if manifest matches *config_digest* and *source_signature*."""
    if not manifest or config_digest is None or source_signature is None:
        return None
    if manifest.get("config_digest") != config_digest:
        return None
    shards = manifest.get("shards")
    if not isinstance(shards, dict):
        return None
    entry = shards.get(shard_id)
    if not isinstance(entry, dict):
        return None
    if entry.get("source_signature") != source_signature:
        return None
    if "fragment" not in entry:
        return None
    return entry.get("fragment")


def upsert_shard_manifest(
    manifest: dict[str, Any] | None,
    *,
    tool_name: str,
    config_digest: str | None,
    shard_id: str,
    source_signature: str | None,
    fragment: Any,
) -> dict[str, Any]:
    """Return updated manifest dict (copy-on-write friendly)."""
    base: dict[str, Any] = (
        dict(manifest)
        if isinstance(manifest, dict)
        else {"version": SHARD_CACHE_VERSION, "tool": tool_name, "shards": {}}
    )
    base["version"] = SHARD_CACHE_VERSION
    base["tool"] = tool_name
    if config_digest is not None:
        base["config_digest"] = config_digest
    shards = base.get("shards")
    if not isinstance(shards, dict):
        shards = {}
    entry: dict[str, Any] = {}
    if source_signature is not None:
        entry["source_signature"] = source_signature
    entry["fragment"] = fragment
    shards = dict(shards)
    shards[shard_id] = entry
    base["shards"] = shards
    return base
