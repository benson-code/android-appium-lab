"""INP. Text input and form controls on Views > Controls > 1. Light Theme."""
import pytest

from framework.pages.controls_page import CHECKBOX, RADIO, TOGGLE
from testdata import cases

pytestmark = pytest.mark.input


@pytest.fixture
def controls(home):
    page = home.open_controls()
    assert page.is_loaded()
    return page


@pytest.mark.parametrize("case", cases.load("text_input.csv"))
def test_text_field_keeps_exactly_what_was_typed(controls, case):
    """Each row of testdata/cases/text_input.csv: type the text, read it back unchanged."""
    value = case["text"] * int(case["repeat"])
    controls.type_text(value)
    assert controls.typed_text() == value, case["title"]


@pytest.mark.case_id("INP-010")
def test_checkbox_checks_and_unchecks(controls):
    assert not controls.is_checked(CHECKBOX[1])
    controls.tap(CHECKBOX[1])
    assert controls.is_checked(CHECKBOX[1])
    assert not controls.is_checked(CHECKBOX[2]), "checking one box must not check another"
    controls.tap(CHECKBOX[1])
    assert not controls.is_checked(CHECKBOX[1])


@pytest.mark.case_id("INP-011")
def test_radio_buttons_are_mutually_exclusive(controls):
    controls.tap(RADIO[1])
    assert controls.is_checked(RADIO[1])
    controls.tap(RADIO[2])
    assert controls.is_checked(RADIO[2])
    assert not controls.is_checked(RADIO[1]), "selecting radio 2 must clear radio 1"


@pytest.mark.case_id("INP-012")
def test_toggle_switches_on_and_off(controls):
    assert (controls.toggle_text(), controls.is_checked(TOGGLE)) == ("OFF", False)
    controls.tap(TOGGLE)
    assert (controls.toggle_text(), controls.is_checked(TOGGLE)) == ("ON", True)
    controls.tap(TOGGLE)
    assert (controls.toggle_text(), controls.is_checked(TOGGLE)) == ("OFF", False)


@pytest.mark.case_id("INP-013")
def test_spinner_shows_the_selected_option(controls):
    assert controls.spinner_value() == "Mercury"
    controls.select_in_spinner("Earth")
    assert controls.spinner_value() == "Earth"
