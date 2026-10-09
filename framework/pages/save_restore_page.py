"""App > Activity > Save & Restore State: two text fields, one with a view ID and one without.

Android saves and restores the state of views that have an ID when it recreates an activity, for
example after the process was killed in the background. The field without an ID loses its text.
"""
from __future__ import annotations

from appium.webdriver.common.appiumby import AppiumBy

from framework.pages.base_page import BasePage, resource_id

SAVED_FIELD = resource_id("io.appium.android.apis:id/saved")
TEXT_FIELDS = (AppiumBy.CLASS_NAME, "android.widget.EditText")
INITIAL_TEXT = "Initial text."


class SaveRestorePage(BasePage):
    def is_loaded(self, timeout: float | None = None) -> bool:
        return self.is_present(SAVED_FIELD, self._timeout(timeout))

    def _fields(self):
        """(field with an ID, field without an ID)"""
        self.find(SAVED_FIELD)
        with_id, without_id = self.find_all(TEXT_FIELDS)[:2]
        assert with_id.get_attribute("resource-id").endswith("/saved"), "unexpected field order"
        return with_id, without_id

    def fill(self, with_id: str, without_id: str) -> None:
        for field, value in zip(self._fields(), (with_id, without_id)):
            field.clear()
            field.send_keys(value)

    def texts(self) -> tuple[str, str]:
        with_id, without_id = self._fields()
        return with_id.text, without_id.text
