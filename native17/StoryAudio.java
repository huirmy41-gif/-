package com.wordpet.app;

import android.app.Activity;
import android.content.res.AssetFileDescriptor;
import android.media.AudioAttributes;
import android.media.MediaPlayer;
import android.os.Bundle;
import android.speech.tts.TextToSpeech;
import android.speech.tts.Voice;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;
import org.json.JSONObject;
import java.util.Locale;
import java.util.Set;

/** Local playback only. No recording, network voice or background playback. */
public final class StoryAudio {
 private final Activity activity;
 private final WebView web;
 private TextToSpeech tts;
 private MediaPlayer player;
 private volatile boolean ready=false,closed=false;
 private int generation=0;
 public StoryAudio(Activity a,WebView w){activity=a;web=w;tts=new TextToSpeech(a,status->{
  if(closed||status!=TextToSpeech.SUCCESS||tts==null)return;
  Set<Voice> voices=tts.getVoices();
  if(voices!=null)for(Voice voice:voices){if("zh".equals(voice.getLocale().getLanguage())&&!voice.isNetworkConnectionRequired()){
   if(tts.setVoice(voice)==TextToSpeech.SUCCESS){ready=true;break;}
  }}
 });}
 private void emit(String type,String id){if(closed)return;web.evaluateJavascript("window.wordPetSoundEvent&&window.wordPetSoundEvent("+JSONObject.quote(type)+","+JSONObject.quote(id)+")",null);}
 private static float clamp(double value,double lo,double hi){return (float)Math.max(lo,Math.min(hi,Double.isFinite(value)?value:lo));}
 private void stopPlayer(){generation++;if(player!=null){try{player.stop();}catch(Exception ignored){}player.release();player=null;}}
 @JavascriptInterface public String status(){return "{\"nativePlayback\":true,\"offlineChinese\":"+ready+"}";}
 @JavascriptInterface public void stop(){activity.runOnUiThread(()->{stopPlayer();if(tts!=null)tts.stop();});}
 @JavascriptInterface public void play(String id,double volume){
  if(id==null||!id.matches("[a-z][a-z0-9-]{0,40}")||volume<=0||closed)return;
  activity.runOnUiThread(()->{if(closed||activity.isFinishing())return;stopPlayer();if(tts!=null)tts.stop();final int g=generation;
   try(AssetFileDescriptor fd=activity.getAssets().openFd("soundbook/audio/"+id+".wav")){
    final MediaPlayer p=new MediaPlayer();player=p;
    p.setAudioAttributes(new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_ASSISTANCE_SONIFICATION).setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build());
    p.setDataSource(fd.getFileDescriptor(),fd.getStartOffset(),fd.getLength());
    float vol=clamp(volume,0,.55);p.setVolume(vol,vol);p.setLooping(false);
    p.setOnPreparedListener(mp->{if(g!=generation||closed)return;mp.start();emit("playing",id);});
    p.setOnCompletionListener(mp->{if(player==mp){player=null;mp.release();}emit("ended",id);});
    p.setOnErrorListener((mp,what,extra)->{if(player==mp){player=null;mp.release();}emit("error",id);return true;});
    p.prepareAsync();
   }catch(Exception e){stopPlayer();emit("error",id);}
  });
 }
 @JavascriptInterface public void speak(String raw){if(raw==null||raw.length()>12000||closed)return;
  try{JSONObject o=new JSONObject(raw);final String text=o.optString("text","");if(text.trim().isEmpty()||text.length()>3000)return;
   final float volume=clamp(o.optDouble("volume",.3),0,.55),pitch=clamp(o.optDouble("pitch",1),.85,1.2),rate=clamp(o.optDouble("rate",.85),.7,1.1);
   activity.runOnUiThread(()->{if(closed||volume==0)return;stopPlayer();if(!ready){emit("no-offline-voice","");return;}
    tts.stop();tts.setPitch(pitch);tts.setSpeechRate(rate);Bundle opts=new Bundle();opts.putFloat(TextToSpeech.Engine.KEY_PARAM_VOLUME,volume);
    if(tts.speak(text,TextToSpeech.QUEUE_FLUSH,opts,"wordpet-story-speech")==TextToSpeech.ERROR)emit("speech-error","");else emit("speaking","");
   });
  }catch(Exception e){activity.runOnUiThread(()->emit("speech-error",""));}
 }
 public void pause(){stopPlayer();if(tts!=null)tts.stop();web.evaluateJavascript("window.WPSound&&window.WPSound.stop()",null);}
 public void close(){closed=true;stopPlayer();if(tts!=null){tts.stop();tts.shutdown();}web.removeJavascriptInterface("WordPetAudioNative");}
}
