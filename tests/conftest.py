"""pytest entry point: options, preflight checks, fixtures, case selection, failure evidence.

    pytest                         # --env=local: Android in a container on this machine
    pytest --env=ci                # the Android emulator on a CI runner
    pytest --target_marks=smoke
    pytest --target_case_ids=SMK-001,NAV-001
"""
from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

import pytest

from framework import config
from framework.device import AdbError, Device
from framework.driver import create_driver
from framework.logcat import find_problems
from framework.pages.menu_page import HomePage

ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_DIR = ROOT / "reports" / "evidence"


# ---- options ----------------------------------------------------------------------------

def pytest_addoption(parser):
    g = parser.getgroup("android-appium-lab")
    g.addoption("--env", default="local", choices=config.names(),
                help="where to run: see testdata/environments.yaml")
    g.addoption("--target_case_ids", default="", help="run only these case IDs, comma-separated")
    g.addoption("--target_marks", default="", help="run only tests with any of these marks, comma-separated")


# ---- case selection ---------------------------------------------------------------------

def case_ids_of(item) -> set[str]:
    ids = {m.args[0] for m in item.iter_markers("case_id")}
    if hasattr(item, "callspec"):
        ids.add(item.callspec.id)          # data-driven cases: the parameter ID is the case ID
    return ids


def pytest_collection_modifyitems(config, items):
    want_ids = {s for s in config.getoption("--target_case_ids").split(",") if s}
    want_marks = {s for s in config.getoption("--target_marks").split(",") if s}
    if not want_ids and not want_marks:
        return
    keep, drop = [], []
    for item in items:
        ok = (not want_ids or case_ids_of(item) & want_ids) and \
             (not want_marks or {m.name for m in item.iter_markers()} & want_marks)
        (keep if ok else drop).append(item)
    config.hook.pytest_deselected(items=drop)
    items[:] = keep


# ---- environment, with preflight checks -------------------------------------------------

@pytest.fixture(scope="session")
def env(request) -> config.Environment:
    """The selected environment. Stops the run with a clear message if it is not ready,
    instead of failing every test with the same connection error."""
    env = config.load(request.config.getoption("--env"))
    device = Device(env.udid)
    if not device.is_booted():
        pytest.exit(f"[{env.name}] device {env.udid} is not connected or not booted "
                    f"(local: tools/setup_redroid.sh up)", returncode=2)
    if not device.is_installed(env.app_package):
        pytest.exit(f"[{env.name}] {env.app_package} is not installed on {env.udid} "
                    f"(local: tools/setup_redroid.sh up)", returncode=2)
    try:
        with urllib.request.urlopen(f"{env.appium_url}/status", timeout=5) as r:
            ready = json.load(r)["value"]["ready"]
    except OSError:
        ready = False
    if not ready:
        pytest.exit(f"[{env.name}] Appium server is not ready at {env.appium_url} "
                    f"(local: tools/appium_server.sh start)", returncode=2)
    return env


@pytest.fixture(scope="session")
def device(env) -> Device:
    return Device(env.udid)


@pytest.fixture(scope="session")
def driver(env):
    """One Appium session for the whole run: creating a session takes seconds, so tests share it
    and the `home` fixture resets the app between tests instead."""
    drv = create_driver(env)
    yield drv
    drv.quit()


@pytest.fixture
def home(env, device, driver) -> HomePage:
    """Every test starts from a freshly launched app on its home screen, with an empty logcat,
    and ends with a logcat check (STB-002): if the app crashed or stopped responding (ANR) during
    the test, the test fails, even when its own assertions passed. Checking per test, rather than
    once after the whole run, names the test during which the app crashed."""
    device.clear_logcat()
    device.force_stop(env.app_package)
    driver.activate_app(env.app_package)
    page = HomePage(driver)
    assert page.is_loaded(), "the app did not open on its home screen"
    yield page
    problems = find_problems(device.logcat(), env.app_package)
    if problems:
        pytest.fail("STB-002: the app crashed or stopped responding during this test:\n"
                    + "\n".join(str(p) for p in problems), pytrace=False)


# ---- evidence on failure ----------------------------------------------------------------

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """When a test fails, save what was on screen: screenshot, UI hierarchy and logcat."""
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or not report.failed:
        return
    driver, device = item.funcargs.get("driver"), item.funcargs.get("device")
    if driver is None:
        return
    folder = EVIDENCE_DIR / re.sub(r"[^\w.-]+", "_", item.nodeid)
    folder.mkdir(parents=True, exist_ok=True)
    saved = []
    try:
        driver.save_screenshot(str(folder / "screenshot.png"))
        saved.append("screenshot.png")
        (folder / "page_source.xml").write_text(driver.page_source)
        saved.append("page_source.xml")
    except Exception as e:                   # the session itself may be what broke
        saved.append(f"(screenshot/page source unavailable: {type(e).__name__})")
    if device is not None:
        try:
            (folder / "logcat.txt").write_text(device.logcat())
            saved.append("logcat.txt")
        except AdbError as e:
            saved.append(f"(logcat unavailable: {e})")
    report.sections.append(("evidence", f"{folder.relative_to(ROOT)}: {', '.join(saved)}"))
