"""STB. Crashes and ANRs. Every test that starts from `home` also ends with a crash check (STB-002,
in tests/conftest.py); these tests add random input, and prove that the check can fail."""
import os
from pathlib import Path

import pytest

from framework.logcat import find_problems

pytestmark = pytest.mark.stability

ROOT = Path(__file__).resolve().parent.parent
MONKEY_SEED = int(os.environ.get("MONKEY_SEED", "20261009"))
MONKEY_EVENTS = int(os.environ.get("MONKEY_EVENTS", "500"))


@pytest.mark.case_id("STB-001")
def test_monkey_random_input_causes_no_crash(home, device, env):
    """The Android monkey sends random taps, swipes and key presses to the app. Reproduce a failure
    with the same seed: MONKEY_SEED=<seed> pytest --target_case_ids=STB-001"""
    status, output = device.run_monkey(env.app_package, MONKEY_EVENTS, MONKEY_SEED)
    report = ROOT / "reports" / "monkey" / f"seed-{MONKEY_SEED}.txt"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(output)

    assert "// CRASH" not in output and "NOT RESPONDING" not in output, \
        f"monkey reported a crash or ANR (seed {MONKEY_SEED}); output in {report.relative_to(ROOT)}"
    assert status == 0 and "// Monkey finished" in output, \
        f"monkey did not finish (exit {status}, seed {MONKEY_SEED}); output in {report.relative_to(ROOT)}"
    assert f"Events injected: {MONKEY_EVENTS}" in output
    assert find_problems(device.logcat(), env.app_package) == []


@pytest.mark.case_id("STB-003")
def test_crash_check_fires_on_a_crash_written_to_logcat(device, env):
    """A check that has never failed proves nothing. Write crash and ANR lines to the device's
    logcat, in the format Android uses, and require the check to find them; a crash of another
    app must not count. (Does not use `home`, whose own check would flag the injected crash.)"""
    package = env.app_package
    device.clear_logcat()
    try:
        device.write_log("E", "AndroidRuntime", "FATAL EXCEPTION: main")
        device.write_log("E", "AndroidRuntime", "Process: com.example.other, PID: 4242")
        assert find_problems(device.logcat(), package) == [], "another app's crash was attributed to this app"

        device.write_log("E", "AndroidRuntime", "FATAL EXCEPTION: main")
        device.write_log("E", "AndroidRuntime", f"Process: {package}, PID: 99999")
        device.write_log("E", "AndroidRuntime", "java.lang.IllegalStateException: written by STB-003")
        device.write_log("E", "ActivityManager", f"ANR in {package} ({package}/.ApiDemos)")

        problems = find_problems(device.logcat(), package)
        assert [p.kind for p in problems] == ["crash", "ANR"], problems
        assert "written by STB-003" in str(problems[0]), "the stack trace was not captured"
    finally:
        device.clear_logcat()
