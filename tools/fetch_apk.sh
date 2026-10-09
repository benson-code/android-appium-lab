#!/usr/bin/env bash
# Download the app under test (Appium's ApiDemos) at a pinned version and verify its SHA-256.
#
#   tools/fetch_apk.sh            # -> apps/ApiDemos-debug.apk
#
# The APK is not committed to the repository. A pinned version keeps every run on the same
# app, and the checksum ensures the file is exactly the one that was reviewed: a mismatch
# (corrupted download, replaced release asset) deletes the file and fails.
set -euo pipefail
cd "$(dirname "$0")/.."

VERSION="v6.0.18"
SHA256="a9eecf37b26cd084855c530db81c2bb1b91f4c1b095a04f47aa7c20e2791f686"
URL="https://github.com/appium/android-apidemos/releases/download/${VERSION}/ApiDemos-debug.apk"
APK="apps/ApiDemos-debug.apk"

verify() {
  echo "${SHA256}  ${APK}" | sha256sum --check --status
}

if [ -f "$APK" ] && verify; then
  echo "ApiDemos ${VERSION} already present and verified: ${APK}"
  exit 0
fi

mkdir -p apps
echo "Downloading ApiDemos ${VERSION}"
curl -fsSL --retry 3 -o "${APK}.part" "$URL"
mv "${APK}.part" "$APK"

if ! verify; then
  echo "SHA-256 mismatch for ${APK}; expected ${SHA256}, got $(sha256sum "$APK" | cut -d' ' -f1)" >&2
  rm -f "$APK"
  exit 1
fi
echo "Verified: ${APK} (${VERSION}, sha256 ${SHA256})"
