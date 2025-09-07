import os


def test_no_print_calls_in_tests_except_debug_marked():
    """Policy: tests should not use print(); prefer logging or assertions.

    Allowed: files containing '@pytest.mark.debug' marker.
    """
    root = os.path.join(os.path.dirname(__file__), '..')
    root = os.path.abspath(root)

    violations = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            if not name.endswith('.py'):
                continue
            path = os.path.join(dirpath, name)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    text = f.read()
                if ('@pytest.mark.debug' in text) or ('pytestmark = pytest.mark.debug' in text) or ('pytest.mark.debug' in text):
                    continue
                # Ignore conftest informational prints for now
                if name == 'conftest.py' and os.path.basename(dirpath) == 'tests':
                    continue
                # Heuristic: flag print( usages
                if 'print(' in text:
                    violations.append(path)
            except Exception:
                continue

    assert not violations, "print() found in test files (use logging or assertions).\n" + "\n".join(sorted(violations))


