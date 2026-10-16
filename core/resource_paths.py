"""Stable paths to files shipped with an editable install or wheel."""

from pathlib import Path

from core.error_handling import handle_errors


_PROJECT_PACKAGE_ROOT = Path(__file__).resolve().parent.parent


@handle_errors(
    "resolving shipped resource path",
    user_friendly=False,
    re_raise=True,
)
def shipped_resource_path(*parts: str) -> Path:
    """Return a path below the installed ``resources`` package."""
    return _PROJECT_PACKAGE_ROOT.joinpath("resources", *parts)


@handle_errors(
    "resolving shipped website path",
    user_friendly=False,
    re_raise=True,
)
def shipped_website_path() -> Path:
    """Return the root containing the installed browser assets."""
    return _PROJECT_PACKAGE_ROOT / "website"


@handle_errors(
    "resolving shipped style path",
    user_friendly=False,
    re_raise=True,
)
def shipped_style_path(filename: str) -> Path:
    """Return one installed Qt style file."""
    return _PROJECT_PACKAGE_ROOT / "styles" / filename
