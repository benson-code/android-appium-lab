"""ApiDemos screens that are a scrollable list of entries: the home screen and its sub-menus.

All of them run in the same activity (.ApiDemos) and the title is always "API Demos", so a screen
is recognized by its entries. A single entry is not enough: Android keeps a list's scroll position
when the user comes back to it, so any one entry may be scrolled out of view. Each screen lists
several entries that appear on no other menu, spread over the list; at least one is always on screen.
"""
from __future__ import annotations

from appium.webdriver.common.appiumby import AppiumBy

from framework.pages.base_page import BasePage, Locator, resource_id

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
        """Scroll to an entry (it may be below the visible part of the list) and tap it."""
        self.scroll_to_text(entry).click()


class HomePage(MenuPage):
    MARKERS = ("Content", "Graphics", "Media", "NFC", "OS", "Preference", "Text", "Views")

    def open_views(self) -> ViewsPage:
        self.open("Views")
        return ViewsPage(self.driver, self.timeout)


class ViewsPage(MenuPage):
    MARKERS = ("Auto Complete", "Buttons", "Chronometer", "Controls", "Expandable Lists",
               "Seek Bar", "Spinner", "Switches", "WebView")
