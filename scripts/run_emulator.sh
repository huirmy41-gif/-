#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/word-pet-mobile/android-native"
trap 'adb logcat -d > "$ROOT/evidence/android-logcat.txt" || true' EXIT
gradle connectedDebugAndroidTest --no-daemon --stacktrace
adb shell pm clear com.wordpet.family
adb shell am start -n com.wordpet.family/com.wordpet.app.MainActivity
sleep 5
adb exec-out screencap -p > "$ROOT/evidence/android-emulator-home.png"
adb shell pidof com.wordpet.family > "$ROOT/evidence/android-process.txt"
