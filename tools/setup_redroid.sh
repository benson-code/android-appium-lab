#!/usr/bin/env bash
# Local Android device for development: Android 14 in a Docker container (redroid).
#
#   tools/setup_redroid.sh up      # load binder, start the container, connect adb, install the app
#   tools/setup_redroid.sh down    # stop the container (it is started with --rm, so its data is discarded)
#   tools/setup_redroid.sh status
#
# Why redroid: the development machine is an ARM64 cloud VM without KVM, so the Android
# emulator cannot run. redroid runs Android's user space in a container on the host kernel,
# natively on ARM64. Requirements and choices:
#   - binder_linux kernel module (Android IPC); loading it needs sudo and does not survive a reboot
#   - androidboot.use_memfd=true, because recent kernels no longer provide ashmem
#   - --privileged, which the container needs to mount binderfs
#   - adb is published on 127.0.0.1 only; an adb port must never be reachable from the network
#   - lower CPU weight and a memory cap, because the machine is shared with other services
set -euo pipefail
cd "$(dirname "$0")/.."

NAME="${REDROID_NAME:-redroid}"
IMAGE="${REDROID_IMAGE:-redroid/redroid:14.0.0_64only-latest}"
PORT="${ADB_PORT:-5555}"
SERIAL="127.0.0.1:${PORT}"
APP_PACKAGE="io.appium.android.apis"

running() {
  [ "$(docker inspect -f '{{.State.Running}}' "$NAME" 2>/dev/null)" = "true" ]
}

exists() {
  docker inspect "$NAME" > /dev/null 2>&1
}

# With --rm, `docker stop` returns before the container is removed, and the name stays taken
# until removal finishes; starting a new container with the same name in that window fails.
wait_removed() {
  for _ in $(seq 30); do
    exists || return 0
    sleep 1
  done
  echo "Container ${NAME} was not removed in time" >&2
  return 1
}

up() {
  command -v docker > /dev/null || { echo "docker is required" >&2; exit 1; }
  command -v adb > /dev/null || { echo "adb is required (Ubuntu: sudo apt install adb)" >&2; exit 1; }

  if ! grep -qw binder /proc/filesystems; then
    echo "Loading the binder kernel module (sudo)"
    sudo modprobe binder_linux devices="binder,hwbinder,vndbinder"
  fi

  if running; then
    echo "Container ${NAME} is already running"
  else
    if exists; then
      # stopped but not yet removed (still being removed, or left over): clear the name first
      docker rm -f "$NAME" > /dev/null 2>&1 || true
      wait_removed
    fi
    echo "Starting ${NAME} (${IMAGE})"
    docker run -d --rm --privileged --name "$NAME" \
      --cpu-shares 256 --memory 3g \
      -p "127.0.0.1:${PORT}:5555" \
      "$IMAGE" androidboot.use_memfd=true > /dev/null
  fi

  adb connect "$SERIAL" > /dev/null
  echo "Waiting for Android to finish booting"
  for _ in $(seq 60); do
    if [ "$(adb -s "$SERIAL" shell getprop sys.boot_completed 2> /dev/null | tr -d '\r')" = "1" ]; then
      break
    fi
    sleep 2
    adb connect "$SERIAL" > /dev/null 2>&1 || true
  done
  if [ "$(adb -s "$SERIAL" shell getprop sys.boot_completed 2> /dev/null | tr -d '\r')" != "1" ]; then
    echo "Android did not finish booting; check: docker logs ${NAME}" >&2
    exit 1
  fi

  tools/fetch_apk.sh
  echo "Installing the app under test"
  adb -s "$SERIAL" install -r apps/ApiDemos-debug.apk > /dev/null
  status
}

down() {
  if running; then
    adb disconnect "$SERIAL" > /dev/null 2>&1 || true
    docker stop "$NAME" > /dev/null
    wait_removed
    echo "Stopped ${NAME}"
  else
    echo "Container ${NAME} is not running"
  fi
}

status() {
  if ! running; then
    echo "Container ${NAME} is not running"
    return 1
  fi
  local prop="adb -s ${SERIAL} shell getprop"
  echo "Device ${SERIAL}: Android $($prop ro.build.version.release | tr -d '\r')," \
       "API $($prop ro.build.version.sdk | tr -d '\r'), $($prop ro.product.cpu.abi | tr -d '\r')"
  if adb -s "$SERIAL" shell pm list packages | grep -q "package:${APP_PACKAGE}\$"; then
    echo "App installed: ${APP_PACKAGE}"
  else
    echo "App not installed: ${APP_PACKAGE}"
  fi
}

case "${1:-}" in
  up) up ;;
  down) down ;;
  status) status ;;
  *) echo "usage: $0 up|down|status" >&2; exit 2 ;;
esac
