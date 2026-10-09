"""LCY. What happens to the app when it leaves the screen: background, process death, cold start."""
import pytest

from framework.pages.menu_page import HomePage, ViewsPage
from framework.pages.save_restore_page import INITIAL_TEXT

pytestmark = pytest.mark.lifecycle

KEYCODE_HOME = 3
COLD_START_LIMIT_MS = 5000      # generous: redroid measured 762 ms; CI emulators are slower


@pytest.mark.case_id("LCY-001")
def test_background_and_return_keeps_the_screen(home, driver, device, env):
    """5 s in the background: the same process comes back on the same screen, not restarted."""
    views = home.open_views()
    assert views.is_loaded()
    pid = device.pid(env.app_package)

    driver.background_app(5)

    assert ViewsPage(driver).is_loaded(), "the app did not come back on the Views screen"
    assert device.pid(env.app_package) == pid, "the process was restarted"


@pytest.mark.case_id("LCY-002")
def test_state_survives_process_death_only_for_views_with_an_id(home, driver, device, env):
    """The system kills the app's process while it is in the background (as under memory pressure).
    Returning to it recreates the activity: the field with a view ID gets its text back, the field
    without an ID does not. A form that loses user input this way is a real, common defect."""
    page = home.open_save_restore_state()
    assert page.is_loaded()
    page.fill(with_id="typed into the field with an ID", without_id="typed into the field without one")
    pid = device.pid(env.app_package)

    driver.press_keycode(KEYCODE_HOME)
    device.kill_background_process(env.app_package)
    assert device.pid(env.app_package) is None, "precondition: the process must be gone"
    driver.activate_app(env.app_package)

    assert page.is_loaded(), "returning did not reopen the Save & Restore State screen"
    assert device.pid(env.app_package) not in (None, pid), "expected a new process"
    assert page.texts() == ("typed into the field with an ID", INITIAL_TEXT)


@pytest.mark.case_id("LCY-003")
def test_cold_start_opens_the_home_menu_in_time(driver, device, env):
    """No running process: am start -W reports a COLD launch and the time to the first frame."""
    device.force_stop(env.app_package)
    report = device.launch_and_measure(f"{env.app_package}/{env.app_activity}")

    assert report.get("Status") == "ok", report
    assert report.get("LaunchState") == "COLD", report
    total = int(report["TotalTime"])
    print(f"cold start: {total} ms")
    assert total < COLD_START_LIMIT_MS, f"cold start took {total} ms"
    assert HomePage(driver).is_loaded()
