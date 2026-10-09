"""adb access to the device, for what Appium does not cover: preflight checks, app state, logcat."""
from __future__ import annotations

import subprocess


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

    # ---- logcat -------------------------------------------------------------------------

    def clear_logcat(self) -> None:
        self.adb("logcat", "-c")

    def logcat(self) -> str:
        """Everything logged since the last clear_logcat(), with timestamps, process and thread IDs."""
        return self.adb("logcat", "-d", "-v", "threadtime")
