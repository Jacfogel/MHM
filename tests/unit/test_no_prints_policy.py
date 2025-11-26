import os

import pytest


@pytest.mark.unit
def test_no_print_calls_in_tests():
    """Policy: tests should not use print(); prefer logging or assertions."""
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
                # Ignore conftest informational prints for now
                if name == 'conftest.py' and os.path.basename(dirpath) == 'tests':
                    continue
                # Skip standalone test runners (AI functionality tests, scripts, etc.)
                if name in ['run_ai_functionality_tests.py', 'test_ai_functionality_manual.py']:
                    continue
                # Skip scripts directory
                if 'scripts' in dirpath:
                    continue
                # Skip this test file itself (it contains 'print(' in the check logic)
                if name == 'test_no_prints_policy.py':
                    continue
                # Skip AI functionality test module files (they're not pytest tests)
                # Normalize path separators for cross-platform compatibility
                normalized_path = dirpath.replace('\\', '/')
                normalized_root = root.replace('\\', '/')
                normalized_file_path = path.replace('\\', '/')
                if '/tests/ai/' in normalized_path or normalized_path.endswith('tests/ai') or normalized_file_path.startswith(f'{normalized_root}/tests/ai/'):
                    continue
                # Skip fixture files (they're test data, not test code)
                if '/tests/fixtures/' in normalized_path or normalized_path.endswith('tests/fixtures') or normalized_file_path.startswith(f'{normalized_root}/tests/fixtures/'):
                    continue
                # Heuristic: flag print( usages
                if 'print(' in text:
                    violations.append(path)
            except Exception:
                continue

    assert not violations, "print() found in test files (use logging or assertions).\n" + "\n".join(sorted(violations))


