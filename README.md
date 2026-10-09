# android-appium-lab

> **Self-built practice project, not production work.** The app under test is
> [ApiDemos](https://github.com/appium/android-apidemos), the demo app published by the Appium
> project for automation practice.

UI automation for an Android app with Appium and pytest, organized in the same three layers as
[payment-api-quality-lab](https://github.com/benson-code/payment-api-quality-lab): a driver and
page-object layer, a test data layer, and a test case layer. The same tests run locally against
Android in a container (redroid) and in CI against the Android emulator.

**Status: work in progress.** Built in small steps; this README grows with each one.

## Running locally

The development machine is an ARM64 cloud VM without KVM, so the Android emulator cannot run on it.
Android 14 runs in a Docker container instead ([redroid](https://github.com/remote-android/redroid-doc)).

```bash
tools/fetch_apk.sh            # download ApiDemos at a pinned version and verify its SHA-256
tools/setup_redroid.sh up     # load binder, start Android 14, connect adb, install the app
tools/setup_redroid.sh status
tools/setup_redroid.sh down   # stop the container
```

The container publishes adb on `127.0.0.1` only; an adb port must never be reachable from the network.
