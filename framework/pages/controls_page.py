"""Views > Controls > 1. Light Theme: a text field and the standard form controls."""
from __future__ import annotations

from framework.pages.base_page import BasePage, resource_id, text

APP_ID = "io.appium.android.apis:id/"

TEXT_FIELD = resource_id(APP_ID + "edit")
CHECKBOX = {1: resource_id(APP_ID + "check1"), 2: resource_id(APP_ID + "check2")}
RADIO = {1: resource_id(APP_ID + "radio1"), 2: resource_id(APP_ID + "radio2")}
TOGGLE = resource_id(APP_ID + "toggle1")
SPINNER = resource_id(APP_ID + "spinner1")
SPINNER_VALUE = resource_id("android:id/text1")          # the selected value, inside the spinner
SPINNER_OPTIONS = resource_id("android:id/select_dialog_listview")


class ControlsPage(BasePage):
    def is_loaded(self, timeout: float | None = None) -> bool:
        return self.is_present(TEXT_FIELD, self._timeout(timeout))

    # ---- text field ---------------------------------------------------------------------

    def type_text(self, value: str) -> None:
        field = self.find(TEXT_FIELD)
        field.clear()
        if value:
            field.send_keys(value)

    def typed_text(self) -> str:
        """What the field contains.

        An empty EditText reports its hint ("hint text") as its text, so reading .text alone would
        report the hint for an empty field. When text and hint are equal, the field is empty.
        """
        field = self.find(TEXT_FIELD)
        value = field.text
        return "" if value == field.get_attribute("hint") else value

    # ---- checkboxes, radio buttons, toggle ----------------------------------------------

    def is_checked(self, locator) -> bool:
        return self.find(locator).get_attribute("checked") == "true"

    def toggle_text(self) -> str:
        return self.find(TOGGLE).text

    # ---- spinner (drop-down) ------------------------------------------------------------

    def select_in_spinner(self, option: str) -> None:
        self.tap(SPINNER)
        self.find(SPINNER_OPTIONS)                     # wait for the option list to open
        self.tap(text(option))

    def spinner_value(self) -> str:
        return self.find(SPINNER).find_element(*SPINNER_VALUE).text
