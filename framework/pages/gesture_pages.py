"""Screens driven by gestures: Views > Seek Bar and Views > Drag and Drop."""
from __future__ import annotations

from framework.pages.base_page import BasePage, resource_id

APP_ID = "io.appium.android.apis:id/"

SEEK_BAR = resource_id(APP_ID + "seek")
SEEK_PROGRESS = resource_id(APP_ID + "progress")     # "<value> from touch=<bool>" after a change
DRAG_DOT = {n: resource_id(APP_ID + f"drag_dot_{n}") for n in (1, 2, 3)}
DRAG_RESULT = resource_id(APP_ID + "drag_result_text")


class SeekBarPage(BasePage):
    def is_loaded(self, timeout: float | None = None) -> bool:
        return self.is_present(SEEK_BAR, self._timeout(timeout))

    def value(self) -> float:
        """The seek bar reports its progress (0-100) as its text."""
        return float(self.find(SEEK_BAR).text)

    def progress_label(self) -> str:
        return self.find(SEEK_PROGRESS).text

    def drag_thumb_to(self, fraction: float) -> None:
        """Drag the thumb from its current position to a fraction of the bar's width."""
        bar = self.find(SEEK_BAR)
        left, top, right, bottom = self.bounds(bar)
        y = (top + bottom) // 2
        start_x = left + round((right - left) * self.value() / 100)
        self.drag((start_x, y), (left + round((right - left) * fraction), y))


class DragAndDropPage(BasePage):
    def is_loaded(self, timeout: float | None = None) -> bool:
        return self.is_present(DRAG_DOT[1], self._timeout(timeout))

    def result(self) -> str:
        return self.find(DRAG_RESULT).text

    def drag_dot_onto(self, source: int, target: int) -> None:
        """Long-press a dot (that starts a drag in this demo), move it onto another dot, release."""
        start = self.center(self.find(DRAG_DOT[source]))
        end = self.center(self.find(DRAG_DOT[target]))
        self.drag(start, end, hold=1.0)
