"""Structural checks for the standalone website pages."""

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

import pytest


pytestmark = [pytest.mark.unit, pytest.mark.ui]
WEBSITE = Path(__file__).resolve().parents[2] / "website"


class PageStructure(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids: set[str] = set()
        self.hrefs: set[str] = set()
        self.scripts: set[str] = set()
        self.controls: dict[str, dict[str, str | None]] = {}
        self.option_values: set[str] = set()

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if element_id := values.get("id"):
            self.ids.add(element_id)
            self.controls[element_id] = values
        if href := values.get("href"):
            self.hrefs.add(href)
        if tag == "script" and (src := values.get("src")):
            self.scripts.add(src)
        if tag == "option" and (value := values.get("value")):
            self.option_values.add(value)


def parse_page(name: str) -> PageStructure:
    parser = PageStructure()
    parser.feed((WEBSITE / name).read_text(encoding="utf-8"))
    return parser


def test_signed_in_pages_keep_workspaces_separate_and_linked():
    account = parse_page("app.html")
    tasks = parse_page("tasks.html")
    notebook = parse_page("notes.html")

    assert "task-create-form" not in account.ids
    assert "note-create-form" not in account.ids
    assert "task-create-form" in tasks.ids
    assert "note-create-form" not in tasks.ids
    assert "note-create-form" in notebook.ids
    assert "task-create-form" not in notebook.ids

    assert {"tasks.html", "notes.html"} <= account.hrefs
    assert {"app.html", "notes.html"} <= tasks.hrefs
    assert {"app.html", "tasks.html"} <= notebook.hrefs
    assert "logout" in account.ids & tasks.ids & notebook.ids


def test_notebook_page_exposes_all_entry_types_and_bounded_fields():
    notebook = parse_page("notes.html")

    assert {"note", "journal_entry", "list"} <= notebook.option_values
    assert {"entry-kind", "note-title", "note-description", "entry-list-field", "entry-add-item"} <= notebook.ids
    assert notebook.controls["note-title"]["maxlength"] == "200"
    assert notebook.controls["note-description"]["maxlength"] == "10000"
    assert notebook.controls["note-group"]["maxlength"] == "50"


@pytest.mark.parametrize("page_name", ["index.html", "login.html", "app.html", "tasks.html", "notes.html"])
def test_page_local_scripts_and_assets_exist(page_name):
    page = parse_page(page_name)
    for source in page.scripts:
        local_path = urlsplit(source).path
        if "://" not in source:
            assert (WEBSITE / local_path).is_file(), f"{page_name} references missing {local_path}"
    assert (WEBSITE / "mhm-logo.png").is_file()
