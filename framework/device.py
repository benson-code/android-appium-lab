"""adb access to the device, for what Appium does not cover: preflight checks, app state, logcat."""
from __future__ import annotations

import subprocess
import time


class AdbError(RuntimeError):
    pass


class Device:
    def __init__(self, serial: str) -> None:
        self.serial = serial

    def adb(self, *args: str, timeout: float = 60) -> str:
        result = subprocess.run(["adb", "-s", self.serial, *args], capture_output=True, text=True,
                                timeout=timeout)
        if result.returncode != 0:
            raise AdbError(f"adb {' '.join(args)} failed: {result.stderr.strip() or result.stdout.strip()}")
        return result.stdout

    def shell(self, *args: str, timeout: float = 60) -> str:
        return self.adb("shell", *args, timeout=timeout).replace("\r\n", "\n")

    # ---- state ----------------------------------------------------------------------

    def is_booted(self) -> bool:
        try:
            return self.shell("getprop", "sys.boot_completed").strip() == "1"
        except (AdbError, subprocess.TimeoutExpired):
            return False

    def android_version(self) -> str:
        return self.shell("getprop", "ro.build.version.release").strip()

    def is_installed(self, package: str) -> bool:
        return f"package:{package}" in self.shell("pm", "list", "packages", package).split()

    def force_stop(self, package: str) -> None:
        self.shell("am", "force-stop", package)

    def pid(self, package: str) -> str | None:
        """Process ID of the app, or None when it is not running (pidof exits 1 then)."""
        try:
            return self.shell("pidof", package).strip() or None
        except AdbError:
            return None

    def kill_background_process(self, package: str, timeout: float = 10) -> None:
        """Kill the app's process the way the system does under memory pressure.

        `am kill` only kills a process that is in the background; the task stays in Recents,
        so returning to the app recreates its activities from their saved state. This is what
        a user sees after switching to other apps for a while. (Setting the developer option
        "Don't keep activities" with `settings put global always_finish_activities 1` alone does
        not take effect: the activity record stayed alive in `dumpsys activity`.)

        Right after the app leaves the screen it is not yet a background process, and `am kill`
        silently does nothing. So retry until the process is gone instead of sleeping a fixed time.
        """
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.shell("am", "kill", package)
            if self.pid(package) is None:
                return
            time.sleep(0.5)
        raise AdbError(f"{package} was still running {timeout:.0f} s after am kill")

    def launch_and_measure(self, component: str) -> dict[str, str]:
        """Start an activity with `am start -W` and return its report: LaunchState (COLD, WARM,
        HOT), TotalTime in ms (until the first frame is drawn), and Status."""
        out = self.shell("am", "start", "-W", "-n", component)
        return dict(line.split(": ", 1) for line in out.splitlines() if ": " in line)

    # ---- logcat -------------------------------------------------------------------------

    def clear_logcat(self) -> None:
        self.adb("logcat", "-c")

    def logcat(self) -> str:
        """Everything logged since the last clear_logcat(), with timestamps, process and thread IDs."""
        return self.adb("logcat", "-d", "-v", "threadtime")
