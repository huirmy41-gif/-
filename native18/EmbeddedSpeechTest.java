package com.wordpet.app;
import androidx.test.ext.junit.rules.ActivityScenarioRule;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import org.junit.*;
import org.junit.runner.RunWith;
import org.json.JSONObject;
import java.io.File;
import java.util.Arrays;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;
import static org.junit.Assert.*;
@RunWith(AndroidJUnit4.class)
public class EmbeddedSpeechTest {
 @Rule public ActivityScenarioRule<MainActivity> rule=new ActivityScenarioRule<>(MainActivity.class);
 private String js(String script)throws Exception{CountDownLatch done=new CountDownLatch(1);AtomicReference<String> value=new AtomicReference<>("");rule.getScenario().onActivity(a->a.view().evaluateJavascript(script,v->{value.set(v);done.countDown();}));assertTrue(done.await(15,TimeUnit.SECONDS));return value.get();}
 private void ready()throws Exception{for(int i=0;i<240;i++){if("true".equals(js("typeof WPSound==='object' && JSON.parse(WordPetAudioNative.status()).offlineChinese")))return;Thread.sleep(500);}fail("Embedded Mandarin model did not become ready");}
 @Test public void wholeAppHasNoNetworkPermission()throws Exception{
  PackageInfo p=InstrumentationRegistry.getInstrumentation().getTargetContext().getPackageManager().getPackageInfo("com.wordpet.complete",PackageManager.GET_PERMISSIONS);
  assertFalse(p.requestedPermissions!=null&&Arrays.asList(p.requestedPermissions).contains("android.permission.INTERNET"));
 }
 @Test public void generatesUnseenChineseLocallyWithoutSystemTts()throws Exception{
  ready();AtomicReference<StoryAudio> audio=new AtomicReference<>();rule.getScenario().onActivity(a->audio.set(a.audio()));
  String text="今天，我在窗边发现两片金黄色的叶子。小兔子开心地跳了三下。";
  JSONObject r=new JSONObject(audio.get().synthesizeForTest(text));
  assertEquals("embedded-huayan",r.getString("engine"));assertTrue(r.getInt("sampleRate")>=16000);assertTrue(r.getInt("samples")>r.getInt("sampleRate"));assertTrue(r.getDouble("rms")>0.001);assertTrue(r.getDouble("peak")>0.01);assertFalse(r.getBoolean("requiresSystemTts"));
  File out=new File(InstrumentationRegistry.getInstrumentation().getTargetContext().getFilesDir(),"embedded-voice-verification.json");try(java.io.FileOutputStream f=new java.io.FileOutputStream(out)){f.write(r.toString(2).getBytes("UTF-8"));}
 }
 @Test public void actualVoiceButtonPlaysAndCompletes()throws Exception{
  ready();js("window.embeddedEvents=[];const old=window.wordPetSoundEvent;window.wordPetSoundEvent=(t,id)=>{embeddedEvents.push(t);old(t,id)};WPSound.set('muted',false);WPSound.set('narration',true);WPSound.speak('小作家，你好。');true");
  for(int i=0;i<240;i++){if("true".equals(js("embeddedEvents.includes('ended')"))){assertEquals("true",js("embeddedEvents.includes('speaking') && JSON.parse(WordPetAudioNative.status()).generatedSamples>0"));return;}Thread.sleep(500);}fail("Embedded voice did not complete playback");
 }
 @Test public void muteStopsAllSpeechWithoutUninstallingAnything()throws Exception{
  ready();js("WPSound.set('muted',true);true");assertEquals("false",js("WPSound.speak('这句话不应播放。')"));assertEquals("false",js("WPSound.play('pet-rabbit')"));assertEquals("false",js("JSON.parse(WordPetAudioNative.status()).requiresInstall"));
 }
 @Test public void finalArtworkAndAudioFilesExist()throws Exception{
  ready();assertEquals("21",js("WPSound.allowed.length"));assertEquals("14",js("WPSoundbook.images.length"));assertEquals("\"1.8.0\"",js("WPSoundbook.version"));
  for(String name:new String[]{"soundbook/images/cotton-rabbit.webp","soundbook/images/star-dragon.webp","soundbook/images/magic-egg.webp","soundbook/audio/sfx-hatch.wav","voice/mandarin/zh_CN-huayan-medium.onnx"})try(java.io.InputStream in=InstrumentationRegistry.getInstrumentation().getTargetContext().getAssets().open(name)){assertTrue(in.read()>=0);}
 }
}
