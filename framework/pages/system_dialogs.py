"""System dialogs that belong to Android, not to the app under test."""
from __future__ import annotations

from appium.webdriver.webdriver import WebDriver

from framework.pages.base_page import resource_id

ANR_TITLE = resource_id("android:id/alertTitle")     # "<app> isn't responding"
ANR_WAIT = resource_id("android:id/aerr_wait")


def dismiss_other_app_not_responding(driver: WebDriver, app_label: str) -> str | None:
    """If another app's "isn't responding" dialog covers the screen, tap Wait and return its title.

    Seen on the CI emulator right after boot: "Pixel Launcher isn't responding" covered the screen,
    so the app under test could not be seen. That is the environment, not the app. A dialog about
    the app under test itself is left alone: it is a real defect, and the test's crash check
    (logcat "ANR in <package>") must fail the test.
    """
    if not driver.find_elements(*ANR_WAIT):
        return None
    titles = driver.find_elements(*ANR_TITLE)
    title = titles[0].text if titles else "(untitled)"
    if app_label in title:
        return None
    driver.find_element(*ANR_WAIT).click()
    return title
