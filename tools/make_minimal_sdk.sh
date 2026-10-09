#!/usr/bin/env bash
# A minimal ANDROID_HOME for ARM64 Linux, where Google publishes no platform-tools or build-tools.
#
#   sudo apt install adb apksigner
#   tools/make_minimal_sdk.sh            # -> $HOME/android-sdk (or $ANDROID_HOME)
#
# The UiAutomator2 driver expects the standard SDK layout. It needs adb, and apksigner to check
# the signature of its own server APKs. It does not need aapt2 as long as the app under test is
# installed with adb rather than passed through the `app` capability (see framework/driver.py).
# On x86_64, install the real Android SDK instead.
set -euo pipefail

SDK="${ANDROID_HOME:-$HOME/android-sdk}"
BUILD_TOOLS_VERSION="34.0.0"

for tool in adb apksigner; do
  command -v "$tool" > /dev/null || { echo "$tool not found (Ubuntu: sudo apt install adb apksigner)" >&2; exit 1; }
done

mkdir -p "$SDK/platform-tools" "$SDK/build-tools/$BUILD_TOOLS_VERSION"
ln -sfn "$(command -v adb)" "$SDK/platform-tools/adb"
ln -sfn "$(command -v apksigner)" "$SDK/build-tools/$BUILD_TOOLS_VERSION/apksigner"
echo "ANDROID_HOME=$SDK"
ls -l "$SDK/platform-tools/adb" "$SDK/build-tools/$BUILD_TOOLS_VERSION/apksigner"
