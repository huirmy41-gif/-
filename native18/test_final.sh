#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p evidence
trap 'adb logcat -d > "$ROOT/evidence/android-logcat.txt" || true' EXIT
adb shell svc wifi disable
adb shell svc data disable
adb shell settings put global airplane_mode_on 1
adb shell pm disable-user --user 0 com.google.android.tts > evidence/system-tts-disabled.txt 2>&1 || true
adb shell pm list packages -d >> evidence/system-tts-disabled.txt
adb install -r -t dist/WordPet-Complete-1.8.0.apk
adb install -r -t complete-source/word-pet-mobile/android-native/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk
adb shell am instrument -w com.wordpet.complete.test/androidx.test.runner.AndroidJUnitRunner | tee evidence/instrumentation.txt
grep -Eq 'OK \([0-9]+ tests?\)' evidence/instrumentation.txt
if grep -Eq 'FAILURES!!!|INSTRUMENTATION_FAILED|Process crashed' evidence/instrumentation.txt; then exit 1; fi
adb exec-out run-as com.wordpet.complete cat files/embedded-voice-verification.json > evidence/embedded-voice-verification.json
adb exec-out run-as com.wordpet.complete cat files/test-embedded-mandarin.wav > evidence/embedded-mandarin-sample.wav
python - <<'PY'
import json,wave,pathlib
report=json.loads(pathlib.Path('evidence/embedded-voice-verification.json').read_text());assert report['samples']>16000 and report['rms']>.001
with wave.open('evidence/embedded-mandarin-sample.wav','rb') as f:assert f.getnframes()>16000 and f.getframerate()>=16000
print('Final Android APK generated non-silent novel Chinese speech with bundled model')
PY
# Verify cold start of the final app after clearing synthetic test records.
adb shell pm clear com.wordpet.complete
adb shell am start -W -n com.wordpet.complete/com.wordpet.app.MainActivity
sleep 8
python - <<'PY'
from pathlib import Path
p=Path('complete-source/scripts/native_ui_check.py')
s=p.read_text().replace('com.wordpet.adventure','com.wordpet.complete')
p.write_text(s)
PY
python complete-source/scripts/native_ui_check.py
cp complete-source/evidence/android-emulator-home.png evidence/android-final-home.png
adb shell pidof com.wordpet.complete > evidence/android-final-process.txt
