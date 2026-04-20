"""
MHM test package marker.

This file exists to ensure pytest imports under `tests.*` paths instead of
accidentally resolving test subpackages (e.g. `tests/development_tools`) as
top-level packages that can conflict with project packages of the same name.
It is intentionally lightweight and should avoid side effects on import.
"""
