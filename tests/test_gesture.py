"""GES. Touch gestures, built from W3C Actions (the WebDriver standard for pointer input)."""
import pytest

pytestmark = pytest.mark.gesture


@pytest.mark.case_id("GES-001")
def test_dragging_the_seek_bar_changes_its_value(home):
    seek = home.open_seek_bar()
    assert seek.is_loaded()
    assert seek.value() == 50

    seek.drag_thumb_to(0.75)
    # The thumb cannot be placed to the pixel: the bar has padding at both ends. Measured: 77.
    value = seek.value()
    assert 70 <= value <= 80, value
    assert seek.progress_label() == f"{value:.0f} from touch=true", "the change must come from touch"


@pytest.mark.case_id("GES-002")
def test_drag_a_dot_onto_another(home):
    page = home.open_drag_and_drop()
    assert page.is_loaded()
    assert page.result() == "", "precondition: nothing dropped yet"

    page.drag_dot_onto(1, 2)
    assert page.result() == "Dropped!"
