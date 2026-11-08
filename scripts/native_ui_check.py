"""Check the actual Android screen and touch controls after a clean install."""
from pathlib import Path
import json,time,subprocess,re,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'evidence'
report={'android_webview_cold_start':False,'checks':[],'surrogate_browser':False,'method':'Android UIAutomator and adb touch'}
def adb(*args,timeout=20):return subprocess.check_output(['adb',*args],timeout=timeout,stderr=subprocess.STDOUT)
def shot(name):
 data=adb('exec-out','screencap','-p')
 if not data.startswith(b'\x89PNG'):raise RuntimeError('Device screenshot is not PNG')
 (OUT/name).write_bytes(data)
def view():
 adb('shell','uiautomator','dump','--compressed','/sdcard/wordpet-screen.xml')
 raw=adb('exec-out','cat','/sdcard/wordpet-screen.xml').decode('utf-8')
 (OUT/'android-view.xml').write_text(raw)
 return ET.fromstring(raw),raw
def node(root,token):
 for n in root.iter('node'):
  if token in (n.get('text','')+' '+n.get('content-desc','')):
   b=[int(x) for x in re.findall(r'\d+',n.get('bounds',''))]
   if len(b)==4 and b[2]>b[0] and b[3]>b[1]:return b
 return None
def wait_for(token,required=()):
 end=time.monotonic()+65;last=''
 while time.monotonic()<end:
  try:
   root,raw=view();b=node(root,token)
   if b and all(v in raw for v in required):return b
   last='Requested screen text was not visible'
  except Exception as e:last=type(e).__name__+': '+str(e)[:200]
  time.sleep(1)
 raise RuntimeError(last)
def tap(b):adb('shell','input','tap',str((b[0]+b[2])//2),str((b[1]+b[3])//2))
start='\u5f00\u59cb\u6211\u7684\u5c0f\u5192\u9669'
try:
 button=wait_for(start)
 report['checks'].append('fresh Android install shows a visible learning start button')
 time.sleep(1);shot('android-emulator-home.png')
 tap(button)
 wait_for('\u6bdb\u8338\u8338',('\u9999\u55b7\u55b7','\u6e05\u6f88\u89c1\u5e95'))
 report['checks'].append('real touch opens the lesson with all three vocabulary options')
 time.sleep(1);shot('android-emulator-lesson.png')
 button=wait_for('\u4fdd\u5b58\u9000\u51fa');tap(button)
 wait_for(start)
 report['checks'].append('save-and-exit touch returns to the learning home')
 time.sleep(1);shot('android-emulator-home.png')
 report['android_webview_cold_start']=True
except Exception as e:
 report['error']=type(e).__name__+': '+str(e)[:500]
 try:shot('android-cold-start-failure.png')
 except Exception:pass
 raise
finally:
 (OUT/'android-ui-smoke.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
