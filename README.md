# android-appium-lab

> **Self-built practice project, not production work.** The app under test is
> [ApiDemos](https://github.com/appium/android-apidemos), the demo app published by the Appium
> project for automation practice.

UI automation for an Android app with Appium and pytest, organized in the same three layers as
[payment-api-quality-lab](https://github.com/benson-code/payment-api-quality-lab): a driver and
page-object layer, a test data layer, and a test case layer. The same tests run locally against
Android in a container (redroid) and in CI against the Android emulator.

**Status: work in progress.** Built in small steps; this README grows with each one.

## Architecture

```
android-appium-lab/
├── framework/                 (1) Driver and page-object layer
│   ├── config.py              Environments from testdata/environments.yaml
│   ├── driver.py              Appium session (UiAutomator2)
│   ├── device.py              adb: preflight checks, app state, logcat
│   └── pages/
│       ├── base_page.py       Locator strategies, explicit waits, scrolling
│       └── menu_page.py       ApiDemos list screens: home and sub-menus
├── testdata/                  (2) Test data layer
│   └── environments.yaml      local (redroid) and ci (emulator)
├── tests/                     (3) Test case layer
│   ├── conftest.py            Options, preflight, fixtures, case selection, failure evidence
│   └── test_smoke.py
└── tools/
    ├── fetch_apk.sh           Pinned ApiDemos release, SHA-256 verified
    ├── setup_redroid.sh       Local Android 14 container: up / down / status
    ├── appium_server.sh       Local Appium server on 127.0.0.1: start / stop / status
    └── make_minimal_sdk.sh    Minimal ANDROID_HOME for ARM64 Linux
```

**Page objects:** tests describe what a user does (`home.open_views()`, `views.back()`); how each
element is located lives in `framework/pages/`. When a screen changes, only its page object changes.

**Locator strategies,** in order of preference: accessibility ID, resource ID, visible text. XPath is
avoided because it is slow on Android and breaks when the layout changes.

**Every test starts from a known state:** the `home` fixture force-stops the app, launches it again,
clears logcat and waits for the home screen. One Appium session is shared by the whole run, because
creating a session takes several seconds.

**Every failed test leaves evidence** in `reports/evidence/<test>/`: a screenshot, the UI hierarchy
(`page_source.xml`) and logcat since the test started.

## Running locally

The development machine is an ARM64 cloud VM without KVM, so the Android emulator cannot run on it.
Android 14 runs in a Docker container instead ([redroid](https://github.com/remote-android/redroid-doc)).

One-time setup:

```bash
sudo apt install adb apksigner
npm install -g appium && appium driver install uiautomator2
tools/make_minimal_sdk.sh                       # ARM64 only; on x86_64 use the Android SDK
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

Each session:

```bash
tools/setup_redroid.sh up                       # Android 14 with the app installed
tools/appium_server.sh start
.venv/bin/pytest                                # --env=local by default
.venv/bin/pytest --target_marks=smoke
.venv/bin/pytest --target_case_ids=SMK-002

tools/appium_server.sh stop
tools/setup_redroid.sh down
```

If the device, the app or the Appium server is not ready, the run stops before any test with a
message naming the command to fix it.

The container publishes adb, and the Appium server listens, on `127.0.0.1` only; neither may be
reachable from the network.

## Test cases

| ID | Mark | Case |
|---|---|---|
| SMK-001 | smoke | The app starts on the home menu, with its first entries in order |
| SMK-002 | smoke | Open Views, press the system back button, return to the home menu |

## Issues found during development

| Issue | How it was found | Fix |
|---|---|---|
| `tools/setup_redroid.sh down` followed immediately by `up` failed: the container name was still in use | Testing the script from a cold start | With `--rm`, `docker stop` returns before the container is removed. `down` now waits for removal, and `up` clears a stopped leftover first |
| SMK-002 failed although the app behaved correctly | The failure evidence: the screenshot showed the home menu, scrolled down | Android restores a list's scroll position on back, so the top entry used to recognize the home screen was out of view. Screens are now recognized by any of several entries unique to them |
| The `app` capability failed with "Could not find 'aapt2'" | First Appium session on the ARM64 machine | aapt2 has no ARM64 Linux build. The app is installed with adb, and the session names its package and activity |
