"""What every page object needs: locators, explicit waits, scrolling."""
from __future__ import annotations

from appium.webdriver.common.appiumby import AppiumBy
from appium.webdriver.webdriver import WebDriver
from selenium.common.exceptions import TimeoutException
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

    def scroll_to_text(self, value: str) -> WebElement:
        """Scroll the first scrollable container until an element with this text is on screen.

        UiAutomator only sees what is on screen: an element further down a list cannot be found
        until it has been scrolled into view.
        """
        return self.driver.find_element(
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiScrollable(new UiSelector().scrollable(true))'
            f'.scrollIntoView(new UiSelector().text("{value}"))')

    def back(self) -> None:
        """The system back button."""
        self.driver.back()

    def _timeout(self, timeout: float | None) -> float:
        return self.timeout if timeout is None else timeout
