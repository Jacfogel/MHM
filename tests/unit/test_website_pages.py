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
    home = parse_page("home.html")
    account = parse_page("app.html")
    tasks = parse_page("tasks.html")
    notebook = parse_page("notes.html")
    insights = parse_page("insights.html")
    messages = parse_page("messages.html")

    assert "task-create-form" not in account.ids
    assert "note-create-form" not in account.ids
    assert "task-create-form" in tasks.ids
    assert "note-create-form" not in tasks.ids
    assert "note-create-form" in notebook.ids
    assert "task-create-form" not in notebook.ids
    assert "home-capture-form" not in home.ids
    assert {"talk-form", "talk-input", "talk-send", "today-heading"} <= home.ids
    assert "home-checkin" in home.ids
    assert "home-checkin-answer" in home.ids
    assert "home-task-off" in home.ids
    assert "task-create-form" not in home.ids

    checkin = parse_page("checkin.html")
    assert {"checkin-form", "checkin-answer", "checkin-skip", "checkin-cancel"} <= checkin.ids
    signed_in_hrefs = {"home.html", "app.html", "tasks.html", "notes.html", "messages.html", "insights.html"}
    assert "checkin.html" in home.hrefs
    assert "checkin.html" in insights.hrefs
    assert signed_in_hrefs <= home.hrefs
    assert signed_in_hrefs <= checkin.hrefs
    assert signed_in_hrefs <= account.hrefs
    assert signed_in_hrefs <= tasks.hrefs
    assert signed_in_hrefs <= notebook.hrefs
    assert signed_in_hrefs <= insights.hrefs
    assert signed_in_hrefs <= messages.hrefs
    assert "logout" in home.ids & checkin.ids & account.ids & tasks.ids & notebook.ids & insights.ids & messages.ids
    assert 'aria-current="page">Home</a>' in (WEBSITE / "home.html").read_text(encoding="utf-8")


def test_marketing_page_leads_with_the_assistant_and_keeps_randomized_timing_prominent():
    html = (WEBSITE / "index.html").read_text(encoding="utf-8")

    assert "Your personal assistant for real life" in html
    assert "reminders, tasks, notes, check-ins" in html
    assert "slightly randomized times within windows you choose" in html
    assert "browser, by email, or through Discord" in html


def test_insights_page_exposes_checkin_history():
    insights = parse_page("insights.html")
    assert {
        "insights-days",
        "insights-summary",
        "checkin-history",
    } <= insights.ids
    assert "health-connect" not in insights.ids


def test_integrations_page_exposes_google_health_controls():
    account = parse_page("app.html")
    assert {
        "health-connect",
        "health-enable",
        "health-pause",
        "health-sync",
        "health-delete",
        "settings-account",
        "settings-integrations",
    } <= account.ids
    assert "app.html#integrations" in parse_page("integrations.html").hrefs
    html = (WEBSITE / "app.html").read_text(encoding="utf-8")
    account_panel = html.split('id="settings-account"', 1)[1].split('id="settings-integrations"', 1)[0]
    integrations_panel = html.split('id="settings-integrations"', 1)[1]
    assert "social-connections" not in account_panel
    assert "connected-signins" not in account_panel
    assert "social-connections" in integrations_panel
    assert "Google Health" in integrations_panel
    assert "account-email" in account_panel
    assert "Your account" not in html.split("<main", 1)[1]
    assert "account-timezone" not in html
    assert "account-discord" not in html


def test_message_library_exposes_category_schedule_and_editing_controls():
    messages = parse_page("messages.html")
    assert {
        "message-category",
        "message-form",
        "message-text",
        "message-active",
        "message-days",
        "message-periods",
        "message-list",
        "message-more-options",
        "message-extra-fields",
    } <= messages.ids
    assert "hidden" in messages.controls["message-extra-fields"]
    assert messages.controls["message-more-options"]["aria-expanded"] == "false"


def test_notebook_page_exposes_all_entry_types_and_bounded_fields():
    notebook = parse_page("notes.html")

    assert {"note", "journal_entry", "list"} <= notebook.option_values
    assert {
        "entry-kind",
        "note-title",
        "note-description",
        "entry-list-field",
        "entry-add-item",
        "note-existing-tag",
    } <= notebook.ids
    assert notebook.controls["note-title"]["maxlength"] == "200"
    assert notebook.controls["note-description"]["maxlength"] == "10000"
    assert notebook.controls["note-tags"]["maxlength"] == "1000"
    assert "list" not in notebook.controls["note-tags"]
    assert "note-tabs" in notebook.ids


def test_task_page_hides_conditional_recurrence_and_suggests_existing_tags():
    tasks = parse_page("tasks.html")
    html = (WEBSITE / "tasks.html").read_text(encoding="utf-8")

    assert html.index('id="task-create-form"') < html.index('id="task-list"')
    assert "task-more-options" in tasks.ids
    assert "hidden" in tasks.controls["task-extra-fields"]
    assert tasks.controls["task-more-options"]["aria-expanded"] == "false"
    assert tasks.controls["task-more-options"]["aria-controls"] == "task-extra-fields"
    assert "hidden" in tasks.controls["task-recurrence-options"]
    assert "hidden" in tasks.controls["task-custom-recurrence"]
    assert tasks.controls["task-recurrence-interval"]["min"] == "1"
    assert tasks.controls["task-recurrence-unit"]["name"] == "recurrence_unit"
    assert "list" not in tasks.controls["task-tags"]
    assert "task-existing-tag" in tasks.ids
    assert "task-reminder-list" in tasks.ids
    assert "task-links" not in tasks.ids
    assert "custom" in tasks.option_values


def test_compact_menu_is_available_on_marketing_and_signed_in_pages():
    marketing = parse_page("index.html")
    assert marketing.controls["nav-toggle"]["aria-controls"] == "site-menu"
    assert marketing.controls["nav-toggle"]["aria-expanded"] == "false"
    assert "site-menu" in marketing.ids
    assert "login.html?mode=create" in marketing.hrefs

    for page_name in ("home.html", "setup.html", "app.html", "tasks.html", "notes.html", "messages.html", "insights.html", "checkin.html"):
        page = parse_page(page_name)
        assert page.controls["nav-toggle"]["aria-controls"] == "site-menu"
        assert "site-menu" in page.ids
        assert "logout" in page.ids
        assert any(source.startswith("script.js") for source in page.scripts)


def test_website_css_hides_sr_only_labels_and_does_not_treat_disabled_as_loading():
    css = (WEBSITE / "styles.css").read_text(encoding="utf-8")
    assert ".sr-only" in css
    assert "clip: rect(0, 0, 0, 0)" in css
    assert "button:disabled { cursor: not-allowed;" in css
    assert "button[aria-busy=\"true\"] { cursor: wait; }" in css
    assert "button:disabled { cursor: wait;" not in css
    assert ".site-header .nav-actions .button-small { display: none; }" not in css
    assert ".nav { display: none; }" not in css


def test_website_scripts_use_only_current_task_and_insights_shapes():
    tasks_source = (WEBSITE / "tasks.js").read_text(encoding="utf-8")
    insights_source = (WEBSITE / "insights.js").read_text(encoding="utf-8")

    assert "custom_when" in tasks_source
    assert "option: 'custom'" in tasks_source
    assert "task.links" not in tasks_source
    assert "Remind now" not in tasks_source
    assert "requestTaskReminder" not in tasks_source
    assert "habit_stats" not in insights_source
    assert "wellness_score" not in insights_source
    assert "value.rate" not in insights_source
    assert "value.total_days" not in insights_source


def test_login_and_account_pages_expose_password_and_provider_controls():
    login = parse_page("login.html")

    assert {
        "password",
        "confirm-password",
        "preferred-name",
        "send-code",
        "forgot-password",
        "primary-action",
    } <= login.ids
    assert "username" not in login.ids
    assert login.controls["preferred-name"].get("required") is None
    assert login.controls["preferred-name"]["maxlength"] == "100"
    assert login.controls["password"]["minlength"] == "12"
    assert login.controls["password"]["maxlength"] == "128"
    settings = parse_page("app.html")
    assert {
        "password-form",
        "current-password",
        "new-password",
        "new-password-confirm",
        "social-connections",
    } <= settings.ids


def test_first_run_exposes_a_setup_path_for_each_feature():
    setup = parse_page("setup.html")
    assert {
        "step-1",
        "step-discord",
        "step-2",
        "step-message-categories",
        "step-message-windows",
        "step-task-create",
        "step-task-windows",
        "step-checkin-questions",
        "step-checkin-windows",
        "message-categories",
        "message-windows",
        "task-windows",
        "checkin-questions",
        "checkin-windows",
        "preferred-name",
        "timezone",
        "enable-messages",
        "enable-tasks",
        "enable-checkins",
        "first-task",
        "setup-back",
        "setup-connect-discord",
        "setup-progress",
    } <= setup.ids
    for step_id in (
        "step-discord",
        "step-2",
        "step-message-categories",
        "step-message-windows",
        "step-task-create",
        "step-task-windows",
        "step-checkin-questions",
        "step-checkin-windows",
    ):
        assert "hidden" in setup.controls[step_id]
    assert setup.controls["first-task"]["maxlength"] == "500"
    html = (WEBSITE / "setup.html").read_text(encoding="utf-8")
    assert "If you do not connect Discord, MHM uses email." in html
    assert "Custom questions can be added in Account after this setup." in html
    assert "Categories personalized from check-ins or Google Health can be turned on in Account after this setup." in html


def test_setup_requires_one_feature_without_forcing_tasks():
    source = (WEBSITE / "setup.js").read_text(encoding="utf-8")
    assert "tasks = true" not in source
    assert "Pick at least one: supportive messages, task reminders, or check-ins." not in source
    assert "message-categories" in source
    assert "checkin-questions" in source
    assert "Keep these windows" in source
    assert "Use email instead" in source
    assert "/api/auth/discord/start?next=/setup.html" in source


def test_home_and_setup_scripts_stay_scoped_so_they_can_load_with_app_js():
    for name in ("home.js", "setup.js"):
        source = (WEBSITE / name).read_text(encoding="utf-8").lstrip()
        assert source.startswith("(() =>"), f"{name} must keep page variables off the shared global scope"


def test_public_pages_link_privacy_terms_and_data():
    for page_name in ("index.html", "login.html", "app.html"):
        assert {"privacy.html", "terms.html", "data.html"} <= parse_page(page_name).hrefs


@pytest.mark.parametrize("page_name", ["privacy.html", "terms.html", "data.html"])
def test_policy_pages_are_readable_and_cross_linked(page_name):
    page = parse_page(page_name)
    html = (WEBSITE / page_name).read_text(encoding="utf-8")
    assert {"index.html", "privacy.html", "terms.html", "data.html"} <= page.hrefs
    assert "<h1>" in html
    assert "Last updated September 22, 2026." in html
    assert any(source.startswith("script.js") for source in page.scripts)
    if page_name == "privacy.html":
        assert "mhm_session" in html
        assert "Google Health" in html
        assert "does not sell" in html
    if page_name == "terms.html":
        assert "does not provide medical care" in html
        assert "988" in html
    if page_name == "data.html":
        assert "Download my data" in html
        assert "delete-account button" in html


@pytest.mark.parametrize("page_name", ["index.html", "login.html", "home.html", "setup.html", "app.html", "tasks.html", "notes.html", "insights.html", "messages.html", "checkin.html", "privacy.html", "terms.html", "data.html"])
def test_page_local_scripts_and_assets_exist(page_name):
    page = parse_page(page_name)
    for source in page.scripts:
        local_path = urlsplit(source).path
        if "://" not in source:
            assert (WEBSITE / local_path).is_file(), f"{page_name} references missing {local_path}"
    assert (WEBSITE / "mhm-logo.png").is_file()
