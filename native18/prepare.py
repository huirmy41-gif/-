from pathlib import Path
import tarfile,zipfile,shutil,urllib.request,hashlib,json,re
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'complete-source';IN=ROOT/'input';OUT=ROOT/'evidence';OUT.mkdir(exist_ok=True)
with zipfile.ZipFile(IN/'app-source.zip') as z:
 for name in z.namelist():
  if name.startswith('/') or '..' in Path(name).parts:raise ValueError('Unsafe source path')
 z.extractall(SRC)
app=SRC/'word-pet-mobile/android-native/app';assets=app/'src/main/assets';native=app/'src/main/java/com/wordpet/app'
model=assets/'voice/mandarin';model.mkdir(parents=True,exist_ok=True)
with tarfile.open(IN/'mandarin.tar.bz2') as t:
 for member in t.getmembers():
  if not member.isfile():continue
  p=Path(member.name);parts=p.parts[1:]
  if not parts or '..' in parts:continue
  rel=Path(*parts)
  if rel.suffix=='.py' or 'test' in rel.parts:continue
  target=model/rel;target.parent.mkdir(parents=True,exist_ok=True)
  target.write_bytes(t.extractfile(member).read())
print('VOICE LICENSE', (model/'MODEL_CARD').read_text())
with tarfile.open(IN/'sherpa-android.tar.bz2') as t:
 for member in t.getmembers():
  parts=Path(member.name).parts
  if member.isfile() and member.name.endswith(('/libonnxruntime.so','/libsherpa-onnx-jni.so')):
   abi=parts[-2]
   if abi not in ['arm64-v8a','armeabi-v7a','x86_64']:continue
   target=app/'src/main/jniLibs'/abi/parts[-1];target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(t.extractfile(member).read())
api=app/'src/main/java/com/k2fsa/sherpa/onnx/Tts.kt';api.parent.mkdir(parents=True,exist_ok=True)
url='https://raw.githubusercontent.com/k2-fsa/sherpa-onnx/v1.13.2/sherpa-onnx/kotlin-api/Tts.kt'
urllib.request.urlretrieve(url,api)
licenses=assets/'licenses';licenses.mkdir(exist_ok=True)
for filename,url in {
 'sherpa-onnx-Apache-2.0.txt':'https://raw.githubusercontent.com/k2-fsa/sherpa-onnx/v1.13.2/LICENSE',
 'onnxruntime-MIT.txt':'https://raw.githubusercontent.com/microsoft/onnxruntime/v1.23.2/LICENSE',
 'espeak-ng-GPL-3.0.txt':'https://raw.githubusercontent.com/espeak-ng/espeak-ng/master/COPYING'
}.items():urllib.request.urlretrieve(url,licenses/filename)
shutil.copyfile(model/'MODEL_CARD',licenses/'Mandarin-model-card.txt')
(licenses/'SOURCES.txt').write_text('Sherpa-onnx v1.13.2: https://github.com/k2-fsa/sherpa-onnx/tree/v1.13.2\nAndroid native binaries: https://github.com/k2-fsa/sherpa-onnx/releases/download/v1.13.2/sherpa-onnx-v1.13.2-android.tar.bz2\nMandarin Huayan model: https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-zh_CN-huayan-medium.tar.bz2\nHuayan upstream: https://huggingface.co/rhasspy/piper-voices/tree/main/zh/zh_CN/huayan/medium\neSpeak-ng source: https://github.com/espeak-ng/espeak-ng\nONNX Runtime source: https://github.com/microsoft/onnxruntime\nThis distribution preserves third-party license notices. Application source accompanies the release. No proprietary account data or voice service credentials are included.\n')
shutil.copyfile(ROOT/'native18/StoryAudio.kt',native/'StoryAudio.kt');(native/'StoryAudio.java').unlink()
main=native/'MainActivity.java';text=main.read_text()
text=re.sub(r'^import android\.speech\.tts\..*;\n','',text,flags=re.M)
text=text.replace(' private TextToSpeech tts;\n','').replace(' private boolean ttsReady=false;\n','')
text=re.sub(r'^  tts=new TextToSpeech\(.*\n','',text,flags=re.M)
text=re.sub(r'  @JavascriptInterface public void speak\(String text\)\{[^\n]+', '  @JavascriptInterface public void speak(String text){if(text==null||text.length()>3000)return;try{storyAudio.speak(new JSONObject().put("text",text).put("volume",0.32).put("rate",0.88).toString());}catch(Exception ignored){}}',text)
text=text.replace('if(tts!=null)tts.stop();','').replace('if(tts!=null)tts.shutdown();','')
text=text.replace(' public WebView view(){return web;}',' public WebView view(){return web;}\n public StoryAudio audio(){return storyAudio;}')
assert 'TextToSpeech' not in text and 'ttsReady' not in text
main.write_text(text)
gradle=SRC/'word-pet-mobile/android-native/build.gradle';gradle.write_text("plugins {\n id 'com.android.application' version '8.6.1' apply false\n id 'org.jetbrains.kotlin.android' version '2.0.21' apply false\n}\n")
p=app/'build.gradle';text=p.read_text().replace("plugins { id 'com.android.application' }","plugins { id 'com.android.application'; id 'org.jetbrains.kotlin.android' }")
text=text.replace("applicationId 'com.wordpet.soundbook'","applicationId 'com.wordpet.complete'").replace('versionCode 170','versionCode 180').replace("versionName '1.7.0'","versionName '1.8.0'")
text=text.replace("noCompress += ['wav']","noCompress += ['wav','onnx']")
text=text.replace(' buildFeatures'," packaging { jniLibs { useLegacyPackaging true } }\n kotlinOptions { jvmTarget = '17' }\n buildFeatures")
p.write_text(text)
p=app/'src/main/AndroidManifest.xml';text=p.read_text().replace(' <uses-permission android:name="android.permission.INTERNET"/>\n','').replace('  <intent><action android:name="android.intent.action.TTS_SERVICE"/></intent>\n','').replace('android:label="作文小作家·有声绘本"','android:label="作文小作家"');p.write_text(text)
# Override only the system-speech fallback; preserve all existing sound controls and gameplay.
p=assets/'soundbook/audio.js';text=p.read_text()
a=text.index('  if(!window.speechSynthesis)');b=text.index('\n }\n function save',a)
text=text[:a]+"  notify('请在完整安卓应用内使用中文朗读；语音引擎已随APK内置。');return false;"+text[b:]
a=text.index(' window.wordPetSoundEvent=');b=text.index('\n document.addEventListener',a)
text=text[:a]+" window.wordPetSoundEvent=(type,id)=>{if(type==='preparing')updateStatus('正在准备内置中文语音…');else if(type==='speech-error'){notify('内置朗读暂时未完成，请重试。无需安装其他软件。');updateStatus('朗读暂时不可用')}else updateStatus(type)};"+text[b:]
# Prior source stores Chinese UI in escaped strings; decode those for targeted copy replacement.
text=re.sub(r'\\u([0-9a-fA-F]{4})',lambda m:chr(int(m[1],16)),text)
text=text.replace('音效已内置，不联网。中文朗读使用设备的离线中文语音；缺少时会提示安装。角色音效是原创合成声，不是真实动物录音。','音效、中文朗读引擎和语音模型全部内置，无需安装语音包。首次朗读会自动准备内置资源。角色音效是原创合成声，不是真实动物录音。')
assert 'speechSynthesis.getVoices' not in text
p.write_text(text)
p=assets/'soundbook/soundbook.js';text=p.read_text().replace("version:'1.7.0'","version:'1.8.0'")
text=re.sub(r'\\u([0-9a-fA-F]{4})',lambda m:chr(int(m[1],16)),text)
text=text.replace('Word Pet 1.7 · 有声绘本测试版','Word Pet 1.8 · 离线有声完整版').replace('图片与音效已内置，朗读使用设备离线中文语音。','图片、音效和中文朗读全部内置，无需安装额外语音包。')
p.write_text(text)
# This distribution is explicitly offline; hide nonfunctional cloud controls, not the parent PIN.
p=assets/'index.html';text=p.read_text();text=re.sub(r'<div class="card"><h3>可选：家庭云连接</h3>.*?</div><button class="secondary" onclick="lockParent', '<div class="card" hidden><h3>可选：家庭云连接</h3>'+text.split('<div class="card"><h3>可选：家庭云连接</h3>')[1].split('</div><button class="secondary" onclick="lockParent')[0]+'</div><button class="secondary" onclick="lockParent',text) if '可选：家庭云连接' in text else text
p.write_text(text)
# Replace native-probe with a real shipped cue, then add end-to-end embedded speech tests.
test=app/'src/androidTest/java/com/wordpet/app/AppSmokeTest.java';text=test.read_text().replace("'native-probe'","'sfx-correct'");test.write_text(text)
shutil.copyfile(ROOT/'native18/EmbeddedSpeechTest.java',test.parent/'EmbeddedSpeechTest.java')
p=SRC/'tests/soundbook_ui_test.py';text=p.read_text().replace("executable_path='/usr/bin/chromium',",'').replace("=='1.7.0'","=='1.8.0'");p.write_text(text)
# Keep source overlays consistent with the actual assets.
for name in ['audio.js','soundbook.js']:shutil.copyfile(assets/'soundbook'/name,SRC/'soundbook'/name)
(SRC/'LICENSE').write_text('Application modifications in Word Pet 1.8 are provided under GNU GPL version 3 or later. Third-party components remain under their respective licenses; see assets/licenses. AI-generated illustration assets are included for use in this application.\n')
records={str(p.relative_to(assets)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in assets.rglob('*') if p.is_file()}
(OUT/'asset-manifest.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
print('Prepared full self-contained application:',len(records),'assets')
