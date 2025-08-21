"""
Global pytest configuration to enforce logging isolation for ALL tests,
including those outside the `tests/` directory (e.g., `scripts/`).

This ensures no test writes to real log files under `logs/`; all logs go to
`tests/logs` instead.
"""

import os
import logging
from pathlib import Path


def _isolate_logging_globally():
    # Force test mode and verbose component logs by default
    os.environ['MHM_TESTING'] = '1'
    os.environ['TEST_VERBOSE_LOGS'] = os.environ.get('TEST_VERBOSE_LOGS', '1')

    # Point all logging paths to tests/logs
    project_root = Path(__file__).parent.resolve()
    tests_logs_dir = (project_root / 'tests' / 'logs')
    tests_logs_dir.mkdir(parents=True, exist_ok=True)
    (tests_logs_dir / 'backups').mkdir(parents=True, exist_ok=True)
    (tests_logs_dir / 'archive').mkdir(parents=True, exist_ok=True)

    os.environ['LOGS_DIR'] = str(tests_logs_dir)
    os.environ['LOG_BACKUP_DIR'] = str(tests_logs_dir / 'backups')
    os.environ['LOG_ARCHIVE_DIR'] = str(tests_logs_dir / 'archive')

    # Explicit per-file env bindings so any early import that snapshots env uses tests/logs
    os.environ['LOG_MAIN_FILE'] = str(tests_logs_dir / 'app.log')
    os.environ['LOG_DISCORD_FILE'] = str(tests_logs_dir / 'discord.log')
    os.environ['LOG_AI_FILE'] = str(tests_logs_dir / 'ai.log')
    os.environ['LOG_USER_ACTIVITY_FILE'] = str(tests_logs_dir / 'user_activity.log')
    os.environ['LOG_ERRORS_FILE'] = str(tests_logs_dir / 'errors.log')
    os.environ['LOG_COMMUNICATION_MANAGER_FILE'] = str(tests_logs_dir / 'communication_manager.log')
    os.environ['LOG_EMAIL_FILE'] = str(tests_logs_dir / 'email.log')
    os.environ['LOG_TELEGRAM_FILE'] = str(tests_logs_dir / 'telegram.log')
    os.environ['LOG_UI_FILE'] = str(tests_logs_dir / 'ui.log')
    os.environ['LOG_FILE_OPS_FILE'] = str(tests_logs_dir / 'file_ops.log')
    os.environ['LOG_SCHEDULER_FILE'] = str(tests_logs_dir / 'scheduler.log')

    # Disable log rotation during tests to prevent Windows file locking issues
    os.environ['DISABLE_LOG_ROTATION'] = '1'
    
    # Set default categories for tests
    os.environ['CATEGORIES'] = 'motivational,health,fun_facts,quotes_to_ponder,word_of_the_day'

    # Remove any existing handlers from root and the "mhm" namespace to prevent leakage
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        try:
            handler.close()
        except Exception:
            pass
        root_logger.removeHandler(handler)
    root_logger.propagate = False

    mhm_logger = logging.getLogger('mhm')
    for handler in mhm_logger.handlers[:]:
        try:
            handler.close()
        except Exception:
            pass
        mhm_logger.removeHandler(handler)
    mhm_logger.propagate = False


_isolate_logging_globally()


