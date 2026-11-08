#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/word-pet-mobile/android-native"
trap 'adb logcat -d > "$ROOT/evidence/android-logcat.txt" || true' EXIT
gradle connectedDebugAndroidTest --no-daemon --stacktrace
# Reinstall the exact tested APK after instrumentation teardown, then verify a real cold start.
adb install -r -t "$ROOT/dist/WordPet-Family-1.4.0.apk"
adb shell pm clear com.wordpet.family
adb shell am start -W -n com.wordpet.family/com.wordpet.app.MainActivity
APP_PID="$(adb shell pidof com.wordpet.family | tr -d '\r')"
test -n "$APP_PID"
adb forward tcp:9222 "localabstract:webview_devtools_remote_${APP_PID}"
python "$ROOT/scripts/native_ui_check.py"
adb shell pidof com.wordpet.family > "$ROOT/evidence/android-process.txt"
