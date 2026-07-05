import os

import pytest


@pytest.mark.unit
def test_no_direct_os_environ_mutations_in_tests():
    """Policy: tests must use monkeypatch.setenv; no direct os.environ mutations.

    Scans test files for forbidden patterns. Allows exceptions in tests/conftest.py
    and tests/conftest_*.py plugins (they set env intentionally for session setup).
    """
    root = os.path.join(os.path.dirname(__file__), '..')
    root = os.path.abspath(root)

    forbidden_patterns = [
        'os.environ[',  # direct assignment or deletion
        'os.environ.update(',  # bulk update
    ]

    violations = []
    ignored_runtime_dirs = {
        'tmp_pytest_runtime',
        'pytest-of-Julie',
        'pytest_runner',
        '.pytest_cache',
        '__pycache__',
    }

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in ignored_runtime_dirs]
        normalized_dir = dirpath.replace('\\', '/')
        if '/tests/data/tmp/' in normalized_dir or normalized_dir.endswith('/tests/data/tmp'):
            continue
        for name in filenames:
            if not name.endswith('.py'):
                continue
            # Skip root conftest and conftest_* plugins (set env for session setup)
            if os.path.basename(dirpath) == 'tests':
                if name == 'conftest.py' or (name.startswith('conftest_') and name.endswith('.py')):
                    continue
            # Skip test_support (conftest plugins and impl set env intentionally)
            normalized = dirpath.replace('\\', '/')
            if 'test_support' in normalized or 'test_helpers/test_support' in normalized:
                continue
            # Skip standalone test runners (AI functionality tests, etc.)
            if name == 'run_ai_functionality_tests.py' or name == 'test_ai_functionality_manual.py':
                continue
            path = os.path.join(dirpath, name)
            try:
                with open(path, encoding='utf-8') as f:
                    text = f.read()
                # Exclude this policy file itself from matches
                if os.path.basename(path) != os.path.basename(__file__):
                    for pat in forbidden_patterns:
                        if pat in text:
                            violations.append(f"{path}: contains '{pat}'")
            except Exception:
                # Ignore unreadable files
                continue

    assert not violations, "Direct os.environ mutations found in tests. Use monkeypatch.setenv() instead.\n" + "\n".join(violations)

