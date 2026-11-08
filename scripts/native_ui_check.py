"""Validate the actual Android WebView after a clean install, not a desktop surrogate."""
from pathlib import Path
import json,time,subprocess
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'evidence'
report={'android_webview_cold_start':False,'checks':[],'surrogate_browser':False}
def shot(name):
 data=subprocess.check_output(['adb','exec-out','screencap','-p'],timeout=15)
 if not data.startswith(b'\x89PNG'):raise RuntimeError('Device screenshot is not PNG')
 (OUT/name).write_bytes(data)
try:
 with sync_playwright() as p:
  deadline=time.monotonic()+60;browser=None
  while time.monotonic()<deadline:
   try:
    browser=p.chromium.connect_over_cdp('http://127.0.0.1:9222',timeout=4000)
    break
   except Exception:
    time.sleep(1)
  if browser is None:raise RuntimeError('Android WebView debug transport did not become ready')
  pages=[page for ctx in browser.contexts for page in ctx.pages]
  if not pages:raise RuntimeError('Android WebView did not expose a page')
  page=next((v for v in pages if 'appassets.androidplatform.net' in v.url),pages[0])
  page.wait_for_function("document.readyState==='complete' && typeof WPAdventure==='object'",timeout=45000)
  page.locator('#startJourney').wait_for(state='visible',timeout=20000)
  assert page.locator('.path-node').count()==5
  assert page.evaluate("document.querySelector('#startJourney').getBoundingClientRect().width>0")
  report['checks'].append('cold start renders five learning path nodes and a visible start button')
  page.wait_for_timeout(1500)
  shot('android-emulator-home.png')
  page.locator('#startJourney').click()
  page.locator('#journeyScreen .answer-choice').first.wait_for(state='visible',timeout=15000)
  assert page.locator('#journeyScreen .answer-choice').count()==3
  report['checks'].append('real Android WebView click opens the three-option lesson')
  page.wait_for_timeout(500)
  shot('android-emulator-lesson.png')
  page.locator('#exitJourney').click()
  page.locator('#startJourney').wait_for(state='visible',timeout=15000)
  report['checks'].append('exit saves and returns to the map')
  page.evaluate('window.scrollTo(0,0)')
  page.wait_for_timeout(1000)
  shot('android-emulator-home.png')
  report['android_webview_cold_start']=True
finally:
 (OUT/'android-ui-smoke.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
