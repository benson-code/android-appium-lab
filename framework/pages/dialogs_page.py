"""App > Alert Dialogs: buttons that open different kinds of dialogs.

The dialogs are standard Android AlertDialogs, so their parts have framework IDs (android:id/...).
"""
from __future__ import annotations

from framework.pages.base_page import BasePage, resource_id, text

APP_ID = "io.appium.android.apis:id/"

OK_CANCEL_BUTTON = resource_id(APP_ID + "two_buttons")
LIST_DIALOG_BUTTON = resource_id(APP_ID + "select_button")

DIALOG_TITLE = resource_id("android:id/alertTitle")
DIALOG_MESSAGE = resource_id("android:id/message")
DIALOG_OK = resource_id("android:id/button1")           # positive button
DIALOG_CANCEL = resource_id("android:id/button2")       # negative button
DIALOG_LIST = resource_id("android:id/select_dialog_listview")


class AlertDialogsPage(BasePage):
    def is_loaded(self, timeout: float | None = None) -> bool:
        return self.is_present(OK_CANCEL_BUTTON, self._timeout(timeout))

    def open_ok_cancel_dialog(self) -> None:
        self.tap(OK_CANCEL_BUTTON)
        self.find(DIALOG_TITLE)

    def open_list_dialog(self) -> list[str]:
        """Open the list dialog and return its options."""
        self.tap(LIST_DIALOG_BUTTON)
        listing = self.find(DIALOG_LIST)
        return [o.text for o in listing.find_elements(*resource_id("android:id/text1"))]

    def choose(self, option: str) -> None:
        self.tap(text(option))

    def cancel(self) -> None:
        self.tap(DIALOG_CANCEL)

    def dialog_closed(self) -> bool:
        """Wait for the dialog to disappear."""
        return self.is_gone(DIALOG_TITLE)

    def dialog_message(self) -> str:
        return self.find(DIALOG_MESSAGE).text
