"""Appium session for an environment."""
from __future__ import annotations

from appium import webdriver
from appium.options.android import UiAutomator2Options

from framework.config import Environment


def create_driver(env: Environment) -> webdriver.Remote:
    options = UiAutomator2Options()
    options.udid = env.udid
    # The app is installed beforehand with adb (tools/setup_redroid.sh locally, the CI workflow in CI).
    # Passing the APK through options.app would make the driver parse it with aapt2, which has no
    # ARM64 Linux build; naming the package and activity works the same way everywhere.
    options.app_package = env.app_package
    options.app_activity = env.app_activity
    options.no_reset = True                  # the suite resets app state itself, per test
    options.new_command_timeout = 120
    options.set_capability("appium:disableWindowAnimation", True)   # animations make waits flaky
    return webdriver.Remote(env.appium_url, options=options)
