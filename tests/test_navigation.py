"""NAV. Moving between screens. UiAutomator only sees what is on screen, so scrolling is part of navigation."""
import pytest

from framework.pages.base_page import accessibility_id, resource_id
from framework.pages.controls_page import ControlsPage

pytestmark = pytest.mark.navigation


@pytest.mark.case_id("NAV-001")
def test_open_an_entry_below_the_visible_list(home):
    """Visibility is near the end of the Views menu (about 40 entries), below the first screenful on
    any phone-sized screen: it can only be opened after scrolling. (Views on the home menu was used
    first, but the CI emulator's taller screen shows the whole home menu; the precondition caught it.)"""
    views = home.open_views()
    assert "Visibility" not in views.visible_entries(), "precondition: Visibility starts out of view"
    views.open("Visibility")
    assert views.is_present(resource_id("io.appium.android.apis:id/victim"), timeout=10), \
        "the Visibility screen did not open"


@pytest.mark.case_id("NAV-002")
def test_three_levels_deep(home, driver):
    """Views > Controls > 1. Light Theme opens the Controls screen, a separate activity."""
    controls = home.open_controls()
    assert isinstance(controls, ControlsPage) and controls.is_loaded()
    assert driver.current_activity == ".view.Controls1"


@pytest.mark.case_id("NAV-003")
def test_scroll_a_long_list_to_its_end(home):
    """The Views menu ends with WebView3, which must be fully visible once the list is at its end."""
    views = home.open_views()
    views.scroll_to_end()
    rows = views.entries()
    last = rows[-1]
    assert last.text == "WebView3", [r.text for r in rows]

    # Being found is not enough: an entry 1 px on screen is found too. Fully visible means as tall
    # as a row in the middle of the list.
    end_position = views.bounds(last)
    _, top, _, bottom = end_position
    _, row_top, _, row_bottom = views.bounds(rows[len(rows) // 2])
    assert bottom - top == row_bottom - row_top, f"WebView3 is only {bottom - top} px tall on screen"

    # end_position was read before this scroll; reading it again from the element afterwards would
    # always match, because bounds are read live
    assert views.scroll_down() is False, "the list still scrolls after reaching its end"
    assert views.bounds(views.entries()[-1]) == end_position, "the list moved after reaching its end"


@pytest.mark.case_id("NAV-004")
def test_open_an_entry_above_the_visible_list(home):
    """After scrolling a long list to its end, its first entry is above the screen: opening it
    requires scrolling back up. (Scrolling only searched downwards at first; a list that Android
    restores in a scrolled position would have hidden its first entries.)"""
    views = home.open_views()
    views.scroll_to_end()
    assert "Animation" not in views.visible_entries(), "precondition: Animation is out of view above"
    views.open("Animation")
    assert views.is_present(accessibility_id("Interpolators"), timeout=10), "Views > Animation did not open"

