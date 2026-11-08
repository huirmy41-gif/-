package com.wordpet.app;
import androidx.test.ext.junit.rules.ActivityScenarioRule;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import org.junit.*;
import org.junit.runner.RunWith;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;
import static org.junit.Assert.*;
@RunWith(AndroidJUnit4.class)
public class AppSmokeTest {
 @Rule public ActivityScenarioRule<MainActivity> rule=new ActivityScenarioRule<>(MainActivity.class);
 private String js(String script)throws Exception{CountDownLatch done=new CountDownLatch(1);AtomicReference<String> result=new AtomicReference<>("");rule.getScenario().onActivity(a->a.view().evaluateJavascript(script,v->{result.set(v);done.countDown();}));assertTrue("JS callback timeout",done.await(8,TimeUnit.SECONDS));return result.get();}
 private void ready()throws Exception{for(int i=0;i<60;i++){if("true".equals(js("typeof WordPet!=='undefined' && typeof WPApp!=='undefined'")))return;Thread.sleep(250);}fail("Bundled application did not start");}
 @Before public void reset()throws Exception{ready();js("localStorage.clear();WordPetNative.saveState(JSON.stringify(WordPet.fresh()));location.reload();true");Thread.sleep(500);ready();}
 @Test public void bundledAppStartsWithoutServer()throws Exception{assertEquals("true",js("document.title.includes('Word Pet') && !cloud.url"));assertEquals("30",js("WORDPET_LESSONS.length"));}
 @Test public void secureOriginAndWebCryptoAvailable()throws Exception{assertEquals("true",js("isSecureContext && !!crypto.subtle"));}
 @Test public void parentPinHashRunsOnNativeWebView()throws Exception{js("window.pinTest='';pinHash('123456','sample-salt').then(v=>window.pinTest=v);true");for(int i=0;i<60;i++){if("64".equals(js("window.pinTest.length")))return;Thread.sleep(100);}fail("PIN hashing failed");}
 @Test public void nativeSnapshotSurvivesActivityRestart()throws Exception{assertEquals("true",js("s.profile.nickname='Persistence test';persist();true"));rule.getScenario().recreate();ready();assertEquals("\"Persistence test\"",js("s.profile.nickname"));}
 @Test public void realLearningFlowAndIdempotence()throws Exception{
  String fill="Object.assign(E.day(s,current).draft,{word:'毛茸茸',wordSentence:'毛茸茸的小狗跑了。',detail1:'白色的毛',detail2:'摇着尾巴',sentence:'小狗在草地上跑。',title:'测试作品',essay:'我喜欢毛茸茸的小狗。它摇着尾巴跑过来。'});";
  assertEquals("6",js(fill+"[0,1,2,3].forEach(i=>E.complete(s,current,i));persist();E.balance(s)"));assertEquals("6",js("[0,1,2,3].forEach(i=>E.complete(s,current,i));E.balance(s)"));assertEquals("1",js("s.essays.length"));
 }
 @Test public void nativeBridgeRejectsInvalidSnapshot()throws Exception{assertEquals("false",js("WordPetNative.saveState('{bad-json}')"));assertEquals("false",js("WordPetNative.saveState('{\"schema\":0}')"));}
 @Test public void originalPreservedAndDraftRestored()throws Exception{js("E.setDraft(s,current,'essay','我的第一段原文。');E.saveEssay(s,current);E.setDraft(s,current,'essay','改过的文字。');E.saveEssay(s,current);E.setDraft(s,current,'essay','尚未提交的草稿。');persist();true");rule.getScenario().recreate();ready();assertEquals("\"我的第一段原文。\"",js("s.essays[0].original"));assertEquals("\"尚未提交的草稿。\"",js("document.getElementById('essay').value"));}
}
