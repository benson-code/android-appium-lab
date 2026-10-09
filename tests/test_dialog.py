"""DLG. Standard Android dialogs on App > Alert Dialogs."""
import pytest

pytestmark = pytest.mark.dialog


@pytest.fixture
def dialogs(home):
    page = home.open_alert_dialogs()
    assert page.is_loaded()
    return page


@pytest.mark.case_id("DLG-001")
def test_cancel_closes_the_dialog(dialogs):
    dialogs.open_ok_cancel_dialog()
    dialogs.cancel()
    assert dialogs.dialog_closed(), "the dialog is still open after Cancel"
    assert dialogs.is_loaded(), "Cancel must return to the Alert Dialogs screen"


@pytest.mark.case_id("DLG-002")
def test_list_dialog_reports_the_chosen_option(dialogs):
    options = dialogs.open_list_dialog()
    assert options == ["Command one", "Command two", "Command three", "Command four"]
    dialogs.choose("Command two")
    assert dialogs.dialog_message() == "You selected: 1 , Command two"
