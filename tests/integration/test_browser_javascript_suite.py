"""Bridge the website's Node tests into the standard pytest suite."""

from pathlib import Path

import pytest

from tests.test_helpers.website_javascript import (
    WebsiteJavaScriptTestError,
    run_website_javascript_tests,
)


pytestmark = [
    pytest.mark.integration,
    pytest.mark.website,
    pytest.mark.suite,
    pytest.mark.no_parallel,
    pytest.mark.critical,
]

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_website_javascript_suite() -> None:
    """Require all browser-side behavioral tests to pass."""

    try:
        run_website_javascript_tests(PROJECT_ROOT)
    except WebsiteJavaScriptTestError as error:
        pytest.fail(str(error), pytrace=False)
