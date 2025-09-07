import os


def test_no_direct_os_environ_mutations_in_tests():
    """Policy: tests must use monkeypatch.setenv; no direct os.environ mutations.

    Scans test files for forbidden patterns. Allows exceptions in tests/conftest.py.
    """
    root = os.path.join(os.path.dirname(__file__), '..')
    root = os.path.abspath(root)

    forbidden_patterns = [
        'os.environ[',  # direct assignment or deletion
        'os.environ.update(',  # bulk update
    ]

    violations = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            if not name.endswith('.py'):
                continue
            # Skip conftest.py which sets env intentionally before imports
            if name == 'conftest.py' and os.path.basename(dirpath) == 'tests':
                continue
            path = os.path.join(dirpath, name)
            try:
                with open(path, 'r', encoding='utf-8') as f:
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


