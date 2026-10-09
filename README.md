# android-appium-lab

[![CI](https://github.com/benson-code/android-appium-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/benson-code/android-appium-lab/actions/workflows/ci.yml)

> **Self-built practice project, not production work.** The app under test is
> [ApiDemos](https://github.com/appium/android-apidemos), the demo app published by the Appium
> project for automation practice.

UI automation for an Android app with Appium and pytest. The same 25 tests run in two different
Android environments: Android 14 in a container on an ARM64 development machine, and the Android
emulator (x86_64) in GitHub Actions on every push.

**Stack:** Python 3.12 · pytest · Appium 3 (UiAutomator2) · adb · redroid · Android Emulator · GitHub Actions

**What it demonstrates**

- **Page objects in three layers**, the same structure as the sister project
  [payment-api-quality-lab](https://github.com/benson-code/payment-api-quality-lab): tests describe
  what a user does, page objects know how to find each element, test data lives in CSV.
- **Every test is checked for crashes.** A test fails if the app crashed or stopped responding
  (ANR) while it ran, even when its own assertions passed; a dedicated test proves the check fires.
- **Mobile-specific behavior,** not only taps: process death in the background, cold-start time,
  W3C touch gestures, scroll position restored on back, random input with the Android monkey.
- **Checks that are proven to fail.** Several assertions were found to pass when they should not
  (an element 1 px on screen, a process that was never killed); each fix was verified both ways.
- **Every speed-up was measured.** The suite went from 4 minutes to about 2 minutes for the same
  18 tests, with each change justified by timings, and one rejected because it made tests flaky.

---

## Contents

1. [Architecture](#1-architecture)
2. [Test cases](#2-test-cases)
3. [Running locally](#3-running-locally)
4. [CI](#4-ci)
5. [AI-assisted development](#5-ai-assisted-development)
6. [Issues found during development](#6-issues-found-during-development)

---

## 1. Architecture

```
android-appium-lab/
├── framework/                 (1) Driver and page-object layer
│   ├── config.py              Environments from testdata/environments.yaml
│   ├── driver.py              Appium session (UiAutomator2)
│   ├── device.py              adb: preflight, process control, launch timing, logcat, monkey
│   ├── logcat.py              Finds the app's crashes, native crashes and ANRs in logcat
│   └── pages/
│       ├── base_page.py       Locator strategies, explicit waits, scrolling, gestures, bounds
│       ├── menu_page.py       ApiDemos list screens: home and sub-menus
│       ├── controls_page.py   Text field, checkbox, radio, toggle, spinner
│       ├── dialogs_page.py    Standard Android dialogs
│       ├── gesture_pages.py   Seek bar, drag and drop
│       └── save_restore_page.py  Activity state across process death
├── testdata/                  (2) Test data layer
│   ├── environments.yaml      local (redroid) and ci (emulator)
│   ├── cases.py               CSV loader; case_id, marks and is_run live in the data
│   └── cases/text_input.csv   Text-input cases, one per row
├── tests/                     (3) Test case layer
│   ├── conftest.py            Options, preflight, fixtures, case selection, crash check, failure evidence
│   └── test_*.py              smoke, navigation, input, dialog, gesture, lifecycle, stability
├── tools/
│   ├── fetch_apk.sh           Pinned ApiDemos release, SHA-256 verified
│   ├── setup_redroid.sh       Local Android 14 container: up / down / status
│   ├── appium_server.sh       Appium server on 127.0.0.1: start / stop / status
│   ├── ci_run_tests.sh        The CI test run, once the emulator has booted
│   ├── logcat_check.py        Crash/ANR check for a saved logcat file (exit 1 if found)
│   └── make_minimal_sdk.sh    Minimal ANDROID_HOME for ARM64 Linux
└── .github/workflows/ci.yml   Emulator, Appium and the full suite on every push
```

**Page objects:** tests describe what a user does (`home.open_views()`, `views.back()`); how each
element is located lives in `framework/pages/`. When a screen changes, only its page object changes.

**Locator strategies,** in order of preference: accessibility ID, resource ID, visible text. XPath is
avoided because it is slow on Android and breaks when the layout changes.

**Scrolling:** UiAutomator only sees what is on screen, so an entry further down a list must be
scrolled into view before it can be found. The page objects scroll with the `mobile: scrollGesture`
command, a large swipe at a time, instead of `UiScrollable.scrollIntoView`, which first scrolls back
to the top and then moves in small steps (about 8 s against 1.5 s to reach an entry one screen down).

**Gestures** are built from W3C Actions, the WebDriver standard for pointer input (touch down, pause,
move, release), so they work with any Appium driver; `mobile:` gesture commands are specific to
UiAutomator2.

**Lifecycle** tests control the app's process with adb: `am kill` to simulate the system reclaiming
a background app, and `am start -W` to measure a cold start.

**Every test starts from a known state:** the `home` fixture force-stops the app, launches it again,
clears logcat and waits for the home screen. One Appium session is shared by the whole run, because
creating a session takes several seconds.

**Every test is checked for crashes:** a test that starts from the home screen ends with a check of
its own logcat. If the app crashed (Java or native) or stopped responding (ANR) during the test, the
test fails even when its own assertions passed, and the failure names the test during which it
happened. Only the app under test counts: a crash of another app on the device is ignored.

**Every failed test leaves evidence** in `reports/evidence/<test>/`: a screenshot, the UI hierarchy
(`page_source.xml`) and logcat since the test started.

## 2. Test cases

25 tests. Each must pass in both environments.

| ID | Mark | Case |
|---|---|---|
| SMK-001 | smoke | The app starts on the home menu, with its first entries in order |
| SMK-002 | smoke | Open Views, press the system back button, return to the home menu |
| NAV-001 | navigation | Open an entry that starts below the visible part of the list |
| NAV-002 | navigation | Three levels deep: Views > Controls > 1. Light Theme opens its own activity |
| NAV-003 | navigation | Scroll a long list to its end: the last entry is fully visible and the list scrolls no further |
| INP-001–007 | input | Text field, from `testdata/cases/text_input.csv`: English, Traditional Chinese, emoji, markup and quote characters, empty, 200 characters, leading and trailing spaces; each must read back unchanged |
| INP-010 | input | A checkbox checks and unchecks, without affecting the other one |
| INP-011 | input | Radio buttons are mutually exclusive |
| INP-012 | input | A toggle switches ON and OFF, in its label and its checked state |
| INP-013 | input | A spinner (drop-down) shows the option selected |
| DLG-001 | dialog | Cancel closes an OK/Cancel dialog and returns to the screen behind it |
| DLG-002 | dialog | A list dialog offers its four options and reports the one chosen |
| GES-001 | gesture | Dragging the seek bar thumb from 50% to 75% sets a value between 70 and 80, reported as coming from touch |
| GES-002 | gesture | Long-press a dot and drop it onto another: the screen reports "Dropped!" |
| LCY-001 | lifecycle | 5 s in the background: the same process returns on the same screen |
| LCY-002 | lifecycle | The process is killed in the background: the activity is recreated, the field with a view ID gets its text back, the field without an ID does not |
| LCY-003 | lifecycle | Cold start: `am start -W` reports a COLD launch under 5 s (measured about 700 ms locally) and the home menu opens |
| STB-001 | stability | The Android monkey sends 500 random events (fixed seed, system keys excluded): no crash or ANR. `MONKEY_SEED=<n>` reproduces a run |
| STB-002 | stability | Applied to every test that starts from the home screen: no crash or ANR of the app in the test's logcat |
| STB-003 | stability | The crash check can fail: crash and ANR lines written to the device's logcat in Android's format are found, with the stack trace; another app's crash is not attributed to this app |

Select cases by mark or ID, as in [payment-api-quality-lab](https://github.com/benson-code/payment-api-quality-lab):

```bash
pytest --target_marks=smoke
pytest --target_marks=gesture,lifecycle
pytest --target_case_ids=NAV-003,LCY-002
```

## 3. Running locally

The development machine is an ARM64 cloud VM without KVM, so the Android emulator cannot run on it.
Android 14 runs in a Docker container instead ([redroid](https://github.com/remote-android/redroid-doc)),
natively on ARM64. A full local run takes about 3 minutes 15 seconds.

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

tools/appium_server.sh stop
tools/setup_redroid.sh down
```

If the device, the app or the Appium server is not ready, the run stops before any test with a
message naming the command to fix it.

The container publishes adb, and the Appium server listens, on `127.0.0.1` only; neither may be
reachable from the network.

## 4. CI

`.github/workflows/ci.yml` runs on every push to `main` and on every pull request:

1. Installs the Python requirements, Appium 3.8.0 and the UiAutomator2 driver 8.7.0 (pinned).
2. Downloads ApiDemos and verifies its SHA-256 (`tools/fetch_apk.sh`).
3. Gives the runner access to KVM and starts the Android emulator: API 34, x86_64, Pixel 6 profile,
   animations off.
4. Runs `tools/ci_run_tests.sh`: installs the app, starts Appium, runs the smoke tests and stops if
   they fail, then runs the full suite with `--env=ci`.
5. Uploads `reports/` whether the run passed or failed: the pytest-html report, JUnit XML, the
   evidence of any failed test, the monkey log and the device logcat.

The workflow runs on an x64 runner because the emulator needs KVM, which GitHub's x64 Linux runners
provide. Actions are pinned to a commit SHA rather than a version tag, and the workflow's token is
read-only.

Running the same tests in two environments is part of the test: a container on ARM64 and an emulator
on x86_64 differ in screen size, speed and Android build, so a test that depends on any of them by
accident fails in one of the two.

## 5. AI-assisted development

I built this project with **Claude Code**, an AI coding agent running on my development server. My
background is ten years of manual testing on payment and e-commerce systems, including Web, iOS and
Android apps; this repository is part of my move into test automation (SDET). The work was divided as
follows:

| My part | Claude Code's part |
|---|---|
| Set the goal (mobile automation for a test-engineer role) and the constraints: Android only, Python and pytest, the same structure as payment-api-quality-lab, English throughout | Researched what can run on an ARM64 machine without KVM and proposed the redroid + CI emulator split |
| Approved the plan, the folder structure and the 25-case list before any code was written | Wrote the framework, page objects, tests, tools and workflow |
| Explored the app with Appium Inspector to see how elements are located | Probed each screen with Appium before writing its page object, instead of guessing element IDs |
| Reviewed each step's results and decided when to move on and when to publish | Ran every step, three full runs before each commit, and diagnosed every failure |

**How the AI-written tests are verified:** a passing test is not taken as proof that it checks
anything. Checks are shown to fail: STB-003 writes a crash into logcat and requires the crash check
to fire; NAV-003's visibility check fails against the old scrolling (1 px against 96 px); LCY-002
asserts its own precondition, that the process is really gone. Several of the issues below were
found exactly this way.

## 6. Issues found during development

The most instructive is the last one: NAV-003 passed while the element it checked was 1 pixel on
screen, because an element is "found" as soon as any part of it is visible.

| Issue | How it was found | Fix |
|---|---|---|
| `tools/setup_redroid.sh down` followed immediately by `up` failed: the container name was still in use | Testing the script from a cold start | With `--rm`, `docker stop` returns before the container is removed. `down` now waits for removal, and `up` clears a stopped leftover first |
| SMK-002 failed although the app behaved correctly | The failure evidence: the screenshot showed the home menu, scrolled down | Android restores a list's scroll position on back, so the top entry used to recognize the home screen was out of view. Screens are now recognized by any of several entries unique to them |
| The `app` capability failed with "Could not find 'aapt2'" | First Appium session on the ARM64 machine | aapt2 has no ARM64 Linux build. The app is installed with adb, and the session names its package and activity |
| An empty text field read back as "hint text" | Exploring the Controls screen before writing INP-005 | An empty EditText reports its hint as its text. The page object treats the field as empty when its text equals its `hint` attribute |
| The suite took 4 minutes for 18 tests | `pytest --durations`: opening an entry one screen down took 8 s | `UiScrollable.scrollIntoView` scrolls back to the top first and then moves in small steps. Replaced with `mobile: scrollGesture`: 1.5 s. The 18 tests then took about 2 minutes 15 seconds |
| A tap took 1.2 s | Timing UiAutomator's `waitForIdleTimeout` at 10 000, 1 000, 300 and 0 ms | 300 ms halves the time of a tap. 0 ms made element lookups fail, so it is not used: speed bought with flakiness is not a gain |
| The crash detector attached another app's crash to the app's stack trace | Running `tools/logcat_check.py` on a sample log with two crashes in a row | Stack-trace lines are now collected only up to the next crash report |
| "Don't keep activities" did not take effect | LCY-002 draft: the field without a view ID kept its text, which is only possible if the activity was never destroyed; `dumpsys activity` confirmed the activity record was still alive | `settings put global always_finish_activities 1` alone does not apply the developer option. LCY-002 kills the background process with `am kill` instead, which is also closer to what users experience |
| LCY-002 failed its own precondition: the process was still alive after `am kill` | The precondition assertion, which exists so the test cannot pass without the process actually dying | Right after the app leaves the screen it is not yet a background process, and `am kill` silently does nothing. The kill is retried until the process is gone, instead of sleeping a fixed time |
| NAV-003 passed while the last entry was 1 px on screen | A second assertion (the list must not move after its end) failed consistently; the element bounds showed `[0,1183][720,1184]` | The scroll gesture can report the end one swipe early, and an element 1 px on screen is still found. The end is now reached only when the gesture reports it and the last entry stops moving, and NAV-003 requires the last entry to be as tall as a full row. Checked both ways: the old scrolling fails the new assertion (1 px against 96 px) |
