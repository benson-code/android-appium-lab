"""What every page object needs: locators, explicit waits, scrolling."""
from __future__ import annotations

import re

from appium.webdriver.common.appiumby import AppiumBy
from appium.webdriver.webdriver import WebDriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.actions import interaction
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

Locator = tuple[str, str]

DEFAULT_TIMEOUT = 15


# Locator strategies, in order of preference: accessibility ID, then resource ID, then visible text.
# XPath is avoided: it is slow on Android and breaks when the layout changes.
def accessibility_id(value: str) -> Locator:
    return (AppiumBy.ACCESSIBILITY_ID, value)


def resource_id(value: str) -> Locator:
    return (AppiumBy.ID, value)


def text(value: str) -> Locator:
    return (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{value}")')


class BasePage:
    def __init__(self, driver: WebDriver, timeout: float = DEFAULT_TIMEOUT) -> None:
        self.driver = driver
        self.timeout = timeout

    def find(self, locator: Locator, timeout: float | None = None) -> WebElement:
        """Wait until the element is on screen, then return it."""
        return WebDriverWait(self.driver, self._timeout(timeout)).until(
            EC.visibility_of_element_located(locator), message=f"not visible: {locator}")

    def find_all(self, locator: Locator) -> list[WebElement]:
        return self.driver.find_elements(*locator)

    def tap(self, locator: Locator, timeout: float | None = None) -> None:
        WebDriverWait(self.driver, self._timeout(timeout)).until(
            EC.element_to_be_clickable(locator), message=f"not clickable: {locator}").click()

    def is_present(self, locator: Locator, timeout: float = 0) -> bool:
        if timeout == 0:
            return bool(self.driver.find_elements(*locator))
        try:
            self.find(locator, timeout)
            return True
        except TimeoutException:
            return False

    def is_gone(self, locator: Locator, timeout: float | None = None) -> bool:
        """Wait until the element is no longer on screen (for example a dialog after it is dismissed)."""
        try:
            WebDriverWait(self.driver, self._timeout(timeout)).until(
                EC.invisibility_of_element_located(locator))
            return True
        except TimeoutException:
            return False

    def scroll_down(self) -> bool:
        """Scroll the first scrollable container down by most of its height.

        Returns whether it can scroll further: False means the end of the list has been reached.
        """
        area = self.driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().scrollable(true)")
        return bool(self.driver.execute_script(
            "mobile: scrollGesture", {"elementId": area.id, "direction": "down", "percent": 0.75}))

    def scroll_to_text(self, value: str, max_swipes: int = 15) -> WebElement:
        """Scroll down until an element with this text is on screen, and return it.

        UiAutomator only sees what is on screen: an element further down a list cannot be found
        until it has been scrolled into view. UiScrollable.scrollIntoView does this too, but it
        first scrolls back to the top and then moves in small steps, waiting for the UI to settle
        after each one: about 8 s to reach an entry one screen down, against about 1.5 s here.
        """
        locator = text(value)
        for _ in range(max_swipes):
            found = self.driver.find_elements(*locator)
            if found:
                return found[0]
            if not self.scroll_down():
                break
        found = self.driver.find_elements(*locator)
        if found:
            return found[0]
        raise NoSuchElementException(f'no element with text "{value}" after scrolling to the end')

    def drag(self, start: tuple[int, int], end: tuple[int, int], hold: float = 0) -> None:
        """Touch at start, optionally hold (a long press), move to end, release.

        Built from W3C Actions, the WebDriver standard for pointer input, so the same code works
        with any Appium driver; `mobile:` gesture commands are specific to UiAutomator2.
        """
        actions = ActionBuilder(self.driver, mouse=PointerInput(interaction.POINTER_TOUCH, "finger"))
        finger = actions.pointer_action
        finger.move_to_location(*start)
        finger.pointer_down()
        if hold:
            finger.pause(hold)
        finger.move_to_location(*end)
        finger.release()
        actions.perform()

    @staticmethod
    def center(element: WebElement) -> tuple[int, int]:
        x1, y1, x2, y2 = BasePage.bounds(element)
        return (x1 + x2) // 2, (y1 + y2) // 2

    @staticmethod
    def bounds(element: WebElement) -> tuple[int, int, int, int]:
        """The on-screen rectangle (left, top, right, bottom) of an element.

        Only the visible part counts: an element scrolled almost off screen can be 1 px tall and
        still be found. Use this to check that an element is fully visible, not merely present.
        """
        x1, y1, x2, y2 = (int(n) for n in re.findall(r"-?\d+", element.get_attribute("bounds")))
        return x1, y1, x2, y2

    def back(self) -> None:
        """The system back button."""
        self.driver.back()

    def _timeout(self, timeout: float | None) -> float:
        return self.timeout if timeout is None else timeout
