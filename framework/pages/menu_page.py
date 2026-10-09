"""ApiDemos screens that are a scrollable list of entries: the home screen and its sub-menus.

All of them run in the same activity (.ApiDemos) and the title is always "API Demos", so a screen
is recognized by its entries. A single entry is not enough: Android keeps a list's scroll position
when the user comes back to it, so any one entry may be scrolled out of view. Each screen lists
several entries that appear on no other menu, spread over the list; at least one is always on screen.
"""
from __future__ import annotations

from appium.webdriver.common.appiumby import AppiumBy

from framework.pages.base_page import BasePage, Locator, resource_id, text
from framework.pages.controls_page import ControlsPage
from framework.pages.dialogs_page import AlertDialogsPage
from framework.pages.gesture_pages import DragAndDropPage, SeekBarPage
from framework.pages.save_restore_page import SaveRestorePage

ENTRY = resource_id("android:id/text1")


def any_entry(names: tuple[str, ...]) -> Locator:
    """One query that matches an entry with any of these names (exact match)."""
    pattern = "^(" + "|".join(names) + ")$"
    return (AppiumBy.ANDROID_UIAUTOMATOR,
            f'new UiSelector().resourceId("android:id/text1").descriptionMatches("{pattern}")')


class MenuPage(BasePage):
    MARKERS: tuple[str, ...] = ()        # entries that only this screen shows

    def is_loaded(self, timeout: float | None = None) -> bool:
        return self.is_present(any_entry(self.MARKERS), self._timeout(timeout))

    def visible_entries(self) -> list[str]:
        return [e.text for e in self.find_all(ENTRY)]

    def open(self, entry: str) -> None:
        """Scroll to an entry (it may be out of view) and tap it, then wait for the next screen.

        Found on the CI emulator, which is slower than the local device: a tap returns before the
        next screen is drawn. Looking for the next entry at once searched the old screen, and
        scrolling then acted on the new list as it appeared, moving the target out of view. So:
        wait for this menu's list before searching it, and after the tap wait until the tapped
        entry is gone, which means this screen has been replaced. (Waiting for the tapped element
        to go stale took over 11 s; checking that its text is gone takes a fraction of a second.)
        """
        self.find(ENTRY)
        self.scroll_to_text(entry).click()
        if not self.is_gone(text(entry)):
            raise AssertionError(f'the screen did not change after tapping "{entry}"')

    def open_path(self, *entries: str) -> None:
        """Open nested entries in turn, e.g. open_path("Views", "Controls")."""
        for entry in entries:
            self.open(entry)

    def entries(self) -> list:
        return self.find_all(ENTRY)

    def scroll_to_end(self, max_swipes: int = 50) -> None:
        """Scroll down until the list is at its end.

        The scroll gesture can report that it cannot scroll further one swipe early, with the last
        entry still almost entirely off screen (measured: 1 px visible). The end is reached only
        when the gesture reports it AND the last entry stops moving.
        """
        previous = None
        for _ in range(max_swipes):
            can_scroll = self.scroll_down()
            last = self.entries()[-1]
            position = (last.text, self.bounds(last))
            if not can_scroll and position == previous:
                return
            previous = position
        raise AssertionError(f"the list did not end after {max_swipes} swipes")


class HomePage(MenuPage):
    MARKERS = ("Content", "Graphics", "Media", "NFC", "OS", "Preference", "Text", "Views")

    def open_views(self) -> ViewsPage:
        self.open("Views")
        return ViewsPage(self.driver, self.timeout)

    def open_controls(self) -> ControlsPage:
        self.open_path("Views", "Controls", "1. Light Theme")
        return ControlsPage(self.driver, self.timeout)

    def open_alert_dialogs(self) -> AlertDialogsPage:
        self.open_path("App", "Alert Dialogs")
        return AlertDialogsPage(self.driver, self.timeout)

    def open_seek_bar(self) -> SeekBarPage:
        self.open_path("Views", "Seek Bar")
        return SeekBarPage(self.driver, self.timeout)

    def open_drag_and_drop(self) -> DragAndDropPage:
        self.open_path("Views", "Drag and Drop")
        return DragAndDropPage(self.driver, self.timeout)

    def open_save_restore_state(self) -> SaveRestorePage:
        self.open_path("App", "Activity", "Save & Restore State")
        return SaveRestorePage(self.driver, self.timeout)


class ViewsPage(MenuPage):
    MARKERS = ("Auto Complete", "Buttons", "Chronometer", "Controls", "Expandable Lists",
               "Seek Bar", "Spinner", "Switches", "WebView")
