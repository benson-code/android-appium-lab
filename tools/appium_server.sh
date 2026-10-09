#!/usr/bin/env bash
# Appium server for local runs, listening on 127.0.0.1 only.
#
#   tools/appium_server.sh start     # log: reports/appium.log
#   tools/appium_server.sh stop
#   tools/appium_server.sh status
#
# Needs appium on PATH with the uiautomator2 driver (appium driver install uiautomator2),
# ANDROID_HOME and JAVA_HOME. On ARM64 Linux, create ANDROID_HOME with tools/make_minimal_sdk.sh.
# If the inspector plugin is installed (appium plugin install inspector), it is enabled.
set -euo pipefail
cd "$(dirname "$0")/.."

PORT="${APPIUM_PORT:-4723}"
URL="http://127.0.0.1:${PORT}"
LOG="reports/appium.log"

[ -d "$HOME/.local/node20/bin" ] && export PATH="$HOME/.local/node20/bin:$PATH"
export ANDROID_HOME="${ANDROID_HOME:-$HOME/android-sdk}"
if [ -z "${JAVA_HOME:-}" ] && command -v java > /dev/null; then
  JAVA_HOME="$(dirname "$(dirname "$(readlink -f "$(command -v java)")")")"
  export JAVA_HOME
fi

ready() {
  curl -s -m 2 "${URL}/status" | grep -q '"ready":true'
}

start() {
  if ready; then
    echo "Appium is already running at ${URL}"
    return 0
  fi
  command -v appium > /dev/null || { echo "appium not found (npm install -g appium)" >&2; exit 1; }
  [ -x "${ANDROID_HOME}/platform-tools/adb" ] || {
    echo "ANDROID_HOME=${ANDROID_HOME} has no platform-tools/adb (ARM64: tools/make_minimal_sdk.sh)" >&2; exit 1; }
  local plugins=()
  if appium plugin list --installed 2>&1 | grep -q 'inspector'; then
    plugins=(--use-plugins=inspector)
  fi
  mkdir -p reports
  nohup nice -n 15 appium --address 127.0.0.1 --port "$PORT" "${plugins[@]}" > "$LOG" 2>&1 &
  for _ in $(seq 30); do
    if ready; then
      echo "Appium is ready at ${URL}${plugins[*]:+ (inspector: ${URL}/inspector)}"
      return 0
    fi
    sleep 1
  done
  echo "Appium did not start; see ${LOG}" >&2
  tail -20 "$LOG" >&2
  exit 1
}

stop() {
  # [a]ppium keeps this pattern from matching the shell that runs pkill
  if pkill -f "node.*[a]ppium --address 127.0.0.1 --port ${PORT}"; then
    echo "Stopped Appium"
  else
    echo "Appium is not running"
  fi
}

status() {
  if ready; then
    echo "Appium is ready at ${URL}"
  else
    echo "Appium is not running at ${URL}"
    return 1
  fi
}

case "${1:-}" in
  start) start ;;
  stop) stop ;;
  status) status ;;
  *) echo "usage: $0 start|stop|status" >&2; exit 2 ;;
esac
