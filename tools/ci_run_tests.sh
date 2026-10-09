#!/usr/bin/env bash
# The CI test run, called by .github/workflows/ci.yml once the Android emulator has booted.
#
# Kept as a script in the repository rather than inline in the workflow, so it can be read,
# reviewed and run like any other tool. Expects: the emulator as emulator-5554, ANDROID_HOME and
# JAVA_HOME (set on GitHub-hosted runners), appium with the uiautomator2 driver, the Python
# requirements, and apps/ApiDemos-debug.apk (tools/fetch_apk.sh).
set -euo pipefail
cd "$(dirname "$0")/.."

SERIAL="emulator-5554"
mkdir -p reports

adb -s "$SERIAL" wait-for-device
adb -s "$SERIAL" install -r apps/ApiDemos-debug.apk
echo "Device: Android $(adb -s "$SERIAL" shell getprop ro.build.version.release | tr -d '\r')," \
     "$(adb -s "$SERIAL" shell getprop ro.product.cpu.abi | tr -d '\r'), $(adb -s "$SERIAL" shell wm size | tr -d '\r')"

# Right after boot the emulator is still busy, and system apps can stop responding; close any
# system dialog left over from boot (CI run 37958235196: "Pixel Launcher isn't responding").
adb -s "$SERIAL" shell am broadcast -a android.intent.action.CLOSE_SYSTEM_DIALOGS > /dev/null

tools/appium_server.sh start

status=0
# Smoke first: if the app does not start or navigate, the full run would only repeat that failure.
python -m pytest --env=ci --target_marks=smoke --junitxml=reports/junit-smoke.xml || status=$?
if [ "$status" -eq 0 ]; then
  python -m pytest --env=ci --html=reports/report.html --self-contained-html \
    --junitxml=reports/junit.xml || status=$?
fi

# Whole-device logcat for the record (each test also checks its own logcat for crashes)
adb -s "$SERIAL" logcat -d -v threadtime > reports/logcat-device.txt 2>&1 || true
tools/appium_server.sh stop || true
exit "$status"
