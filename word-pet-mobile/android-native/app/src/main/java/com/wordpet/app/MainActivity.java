package com.wordpet.app;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.content.ActivityNotFoundException;
import android.os.Bundle;
import android.speech.RecognizerIntent;
import android.speech.tts.TextToSpeech;
import android.speech.tts.Voice;
import android.util.AtomicFile;
import android.view.WindowInsets;
import android.webkit.*;
import android.widget.FrameLayout;
import androidx.webkit.WebViewAssetLoader;
import org.json.JSONObject;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

public final class MainActivity extends Activity {
 private static final String ORIGIN="https://appassets.androidplatform.net";
 private static final int EXPORT=41,IMPORT=42,SPEECH=43;
 private WebView web;
 private TextToSpeech tts;
 private boolean ttsReady=false;
 private String pendingBackup;
 private AtomicFile stateFile;
 @Override public void onCreate(Bundle saved){
  super.onCreate(saved);
  stateFile=new AtomicFile(new File(getFilesDir(),"learning-state-v2.json"));
  final WebViewAssetLoader loader=new WebViewAssetLoader.Builder().addPathHandler("/assets/",new WebViewAssetLoader.AssetsPathHandler(this)).build();
  FrameLayout root=new FrameLayout(this);root.setBackgroundColor(0xFF352B54);
  web=new WebView(this);web.setBackgroundColor(0xFFFCF9F5);
  WebSettings settings=web.getSettings();settings.setJavaScriptEnabled(true);settings.setDomStorageEnabled(true);
  settings.setAllowFileAccess(false);settings.setAllowContentAccess(false);settings.setAllowFileAccessFromFileURLs(false);settings.setAllowUniversalAccessFromFileURLs(false);
  settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);settings.setMediaPlaybackRequiresUserGesture(true);
  WebView.setWebContentsDebuggingEnabled(BuildConfig.DEBUG);
  web.setWebViewClient(new WebViewClient(){
   @Override public WebResourceResponse shouldInterceptRequest(WebView v,WebResourceRequest r){return loader.shouldInterceptRequest(r.getUrl());}
   @Override public boolean shouldOverrideUrlLoading(WebView v,WebResourceRequest r){return !r.getUrl().toString().startsWith(ORIGIN+"/assets/");}
   @Override public boolean shouldOverrideUrlLoading(WebView v,String url){return !url.startsWith(ORIGIN+"/assets/");}
  });
  web.setWebChromeClient(new WebChromeClient(){@Override public void onPermissionRequest(PermissionRequest r){r.deny();}});
  web.addJavascriptInterface(new Bridge(),"WordPetNative");root.addView(web,new FrameLayout.LayoutParams(-1,-1));
  if(android.os.Build.VERSION.SDK_INT>=30){root.setOnApplyWindowInsetsListener((v,insets)->{android.graphics.Insets bars=insets.getInsets(WindowInsets.Type.systemBars()|WindowInsets.Type.ime());v.setPadding(bars.left,bars.top,bars.right,bars.bottom);return insets;});}else root.setFitsSystemWindows(true);
  setContentView(root);web.loadUrl(ORIGIN+"/assets/index.html");
  tts=new TextToSpeech(this,status->{if(status!=TextToSpeech.SUCCESS)return;int language=tts.setLanguage(Locale.SIMPLIFIED_CHINESE);if(language<0)return;Set<Voice> voices=tts.getVoices();if(voices!=null)for(Voice v:voices){if("zh".equals(v.getLocale().getLanguage())&&!v.isNetworkConnectionRequired()){tts.setVoice(v);tts.setSpeechRate(.85f);ttsReady=true;break;}}});
 }
 public WebView view(){return web;}
 private void call(String fn,String value){runOnUiThread(()->{if(web!=null)web.evaluateJavascript("window."+fn+"("+JSONObject.quote(value)+")",null);});}
 private void notice(String value){call("nativeMessage",value);}
 private static String readLimited(InputStream in)throws IOException{
  ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] buf=new byte[8192];int n,total=0;
  while((n=in.read(buf))!=-1){total+=n;if(total>2000000)throw new IOException("File too large");out.write(buf,0,n);}return out.toString(StandardCharsets.UTF_8.name());
 }
 private final class Bridge{
  @JavascriptInterface public synchronized String loadState(){try(InputStream in=stateFile.openRead()){return readLimited(in);}catch(Exception e){return "";}}
  @JavascriptInterface public synchronized boolean saveState(String data){
   FileOutputStream out=null;try{if(data==null||data.length()>1800000||new JSONObject(data).optInt("schema")!=2)return false;out=stateFile.startWrite();out.write(data.getBytes(StandardCharsets.UTF_8));stateFile.finishWrite(out);return true;}catch(Exception e){if(out!=null)stateFile.failWrite(out);return false;}
  }
  @JavascriptInterface public void exportBackup(String data){if(data==null||data.length()>2000000)return;runOnUiThread(()->{pendingBackup=data;Intent i=new Intent(Intent.ACTION_CREATE_DOCUMENT);i.addCategory(Intent.CATEGORY_OPENABLE);i.setType("application/json");i.putExtra(Intent.EXTRA_TITLE,"WordPet-backup.json");try{startActivityForResult(i,EXPORT);}catch(ActivityNotFoundException e){notice("设备没有可用的文件保存工具。");}});}
  @JavascriptInterface public void importBackup(){runOnUiThread(()->{Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT);i.addCategory(Intent.CATEGORY_OPENABLE);i.setType("application/json");try{startActivityForResult(i,IMPORT);}catch(ActivityNotFoundException e){notice("设备没有可用的文件选择工具。");}});}
  @JavascriptInterface public void recognize(){runOnUiThread(()->new AlertDialog.Builder(MainActivity.this).setTitle("使用系统语音输入").setMessage("设备的语音识别服务可能把语音发送给其供应商。应用不保存原始录音；识别文字会先请你确认。是否继续？").setNegativeButton("取消",null).setPositiveButton("继续",(dialog,which)->{Intent i=new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);i.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);i.putExtra(RecognizerIntent.EXTRA_LANGUAGE,"zh-CN");i.putExtra(RecognizerIntent.EXTRA_PREFER_OFFLINE,true);i.putExtra(RecognizerIntent.EXTRA_MAX_RESULTS,1);i.putExtra(RecognizerIntent.EXTRA_PROMPT,"说一句自己的话");try{startActivityForResult(i,SPEECH);}catch(ActivityNotFoundException e){notice("本设备没有系统语音识别服务。可使用键盘输入。");}}).show());}
  @JavascriptInterface public void speak(String text){if(text==null||text.length()>3000)return;runOnUiThread(()->{if(!ttsReady){notice("请家长在设备设置中安装离线中文语音。当前仍可文字学习。");return;}tts.speak(text,TextToSpeech.QUEUE_FLUSH,null,"wordpet");});}
 }
 @Override protected void onActivityResult(int request,int result,Intent data){
  super.onActivityResult(request,result,data);if(result!=RESULT_OK||data==null){pendingBackup=null;return;}
  try{if(request==EXPORT&&data.getData()!=null&&pendingBackup!=null){try(OutputStream out=getContentResolver().openOutputStream(data.getData(),"wt")){if(out==null)throw new IOException();out.write(pendingBackup.getBytes(StandardCharsets.UTF_8));}pendingBackup=null;notice("备份已保存到你选择的位置。");}
  else if(request==IMPORT&&data.getData()!=null){try(InputStream in=getContentResolver().openInputStream(data.getData())){if(in==null)throw new IOException();call("receiveBackup",readLimited(in));}}
  else if(request==SPEECH){ArrayList<String> matches=data.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS);if(matches!=null&&!matches.isEmpty())call("receiveSpeech",matches.get(0).substring(0,Math.min(1000,matches.get(0).length())));}}
  catch(Exception e){notice("文件操作没有完成，原学习记录没有删除。");}
 }
 @Override public void onBackPressed(){web.evaluateJavascript("window.onAppBack ? window.onAppBack() : false",result->{if(!"true".equals(result))MainActivity.super.onBackPressed();});}
 @Override protected void onPause(){super.onPause();if(tts!=null)tts.stop();}
 @Override protected void onDestroy(){if(tts!=null)tts.shutdown();if(web!=null){web.removeJavascriptInterface("WordPetNative");web.destroy();web=null;}super.onDestroy();}
}
