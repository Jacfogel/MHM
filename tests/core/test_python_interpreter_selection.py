import os
import sys

import pytest

from run_mhm import resolve_python_interpreter, prepare_launch_environment


@pytest.mark.unit
def test_resolve_python_interpreter_prefers_windows(tmp_path):
    script_dir = tmp_path
    scripts_dir = script_dir / '.venv' / 'Scripts'
    scripts_dir.mkdir(parents=True)
    windows_python = scripts_dir / 'python.exe'
    windows_python.write_text('')

    bin_dir = script_dir / '.venv' / 'bin'
    bin_dir.mkdir(parents=True)
    (bin_dir / 'python').write_text('')

    resolved = resolve_python_interpreter(str(script_dir))
    assert resolved == str(windows_python)


@pytest.mark.unit
def test_resolve_python_interpreter_posix(tmp_path):
    script_dir = tmp_path
    bin_dir = script_dir / '.venv' / 'bin'
    bin_dir.mkdir(parents=True)
    posix_python = bin_dir / 'python'
    posix_python.write_text('')

    resolved = resolve_python_interpreter(str(script_dir))
    assert resolved == str(posix_python)


@pytest.mark.unit
def test_resolve_python_interpreter_falls_back_to_sys_executable(tmp_path):
    script_dir = tmp_path
    # Ensure neither interpreter path exists
    resolved = resolve_python_interpreter(str(script_dir))
    assert resolved == sys.executable


@pytest.mark.skipif(os.name == 'nt', reason="PATH expectations differ on Windows")
@pytest.mark.unit
def test_prepare_launch_environment_includes_posix_bin(tmp_path):
    script_dir = tmp_path
    bin_dir = script_dir / '.venv' / 'bin'
    bin_dir.mkdir(parents=True)
    (bin_dir / 'python').write_text('')

    env = prepare_launch_environment(str(script_dir))
    path_value = env.get('PATH', '')
    assert str(bin_dir) in path_value.split(os.pathsep)
