"""Run first: the app starts and the main navigation works. If these fail, nothing else will pass."""
import pytest

from framework.pages.menu_page import HomePage

pytestmark = pytest.mark.smoke


@pytest.mark.case_id("SMK-001")
def test_app_starts_on_the_home_menu(home):
    entries = home.visible_entries()
    assert entries[:4] == ["Access'ibility", "Accessibility", "Animation", "App"], entries


@pytest.mark.case_id("SMK-002")
def test_back_button_returns_to_the_home_menu(home):
    views = home.open_views()
    assert views.is_loaded(), "Views did not open"

    views.back()
    assert HomePage(views.driver).is_loaded(), "the back button did not return to the home menu"
