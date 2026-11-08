package com.wordpet.app

import android.app.Activity
import android.media.*
import android.webkit.JavascriptInterface
import android.webkit.WebView
import com.k2fsa.sherpa.onnx.*
import org.json.JSONObject
import java.io.File
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import kotlin.math.abs
import kotlin.math.sqrt

/** All models and sound files are shipped in this APK. No TTS service or network. */
class StoryAudio(private val activity: Activity, private val web: WebView) {
 private val worker = Executors.newSingleThreadExecutor()
 private val sequence = AtomicInteger(0)
 @Volatile private var closed = false
 @Volatile private var ready = false
 @Volatile private var initError = ""
 @Volatile private var lastEvent = "idle"
 @Volatile private var generatedSamples = 0
 @Volatile private var engine: OfflineTts? = null
 @Volatile private var track: AudioTrack? = null
 private var player: MediaPlayer? = null
 private val modelRoot = "voice/mandarin"
 init { worker.execute { initialize() } }
 private fun emit(type: String, id: String = "", token: Int? = null) {
  if (closed || (token != null && token != sequence.get())) return
  lastEvent = type
  activity.runOnUiThread {
   if (!closed && (token == null || token == sequence.get())) web.evaluateJavascript("window.wordPetSoundEvent&&window.wordPetSoundEvent("+JSONObject.quote(type)+","+JSONObject.quote(id)+")",null)
  }
 }
 private fun copyTree(asset: String, dest: File) {
  val children = activity.assets.list(asset) ?: emptyArray()
  if (children.isNotEmpty()) { dest.mkdirs(); for (name in children) copyTree("$asset/$name", File(dest,name)) }
  else {
   dest.parentFile?.mkdirs()
   val temp=File(dest.path+".part")
   activity.assets.open(asset).use { source -> temp.outputStream().use { source.copyTo(it) } }
   check(temp.renameTo(dest)) { "Embedded voice file could not be prepared" }
  }
 }
 private fun initialize() {
  try {
   val data=File(activity.filesDir,"embedded-voice-180/espeak-ng-data")
   val marker=File(data.parentFile,"complete")
   if (!marker.exists()) { copyTree("$modelRoot/espeak-ng-data",data);marker.writeText("180") }
   if(closed) return
   val config=OfflineTtsConfig(model=OfflineTtsModelConfig(
    vits=OfflineTtsVitsModelConfig(model="$modelRoot/zh_CN-huayan-medium.onnx",tokens="$modelRoot/tokens.txt",dataDir=data.absolutePath),
    numThreads=2,debug=false,provider="cpu"),maxNumSentences=1)
   engine=OfflineTts(assetManager=activity.assets,config=config)
   check(engine!!.sampleRate()>0)
   ready=true
  } catch(e: Throwable) { initError=e.javaClass.simpleName; ready=false }
 }
 @JavascriptInterface fun status(): String = JSONObject().put("nativePlayback",true).put("offlineChinese",ready).put("embedded",true).put("requiresInstall",false).put("initializing",!ready&&initError.isEmpty()).put("error",initError).put("lastEvent",lastEvent).put("generatedSamples",generatedSamples).toString()
 private fun stopPlayer() { player?.let { try { it.stop() } catch(_:Exception){}; it.release() };player=null }
 @JavascriptInterface fun stop() {
  sequence.incrementAndGet()
  track?.let { try { it.pause();it.flush() } catch(_:Exception){} }
  activity.runOnUiThread { stopPlayer() }
  lastEvent="idle"
 }
 @JavascriptInterface fun play(id: String?, volume: Double) {
  if(closed||id==null||!id.matches(Regex("[a-z][a-z0-9-]{0,40}"))||!volume.isFinite()||volume<=0) return
  stop();val token=sequence.get()
  activity.runOnUiThread {
   if(closed||token!=sequence.get()) return@runOnUiThread
   try {
    val p=MediaPlayer();player=p
    p.setAudioAttributes(AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_MEDIA).setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build())
    activity.assets.openFd("soundbook/audio/$id.wav").use { p.setDataSource(it.fileDescriptor,it.startOffset,it.length) }
    val v=volume.coerceIn(0.0,.55).toFloat();p.setVolume(v,v);p.isLooping=false
    p.setOnPreparedListener { if(!closed&&token==sequence.get()) {it.start();emit("playing",id,token)} }
    p.setOnCompletionListener { if(player===it){player=null;it.release()};emit("ended",id,token) }
    p.setOnErrorListener { mp,_,_ -> if(player===mp){player=null;mp.release()};emit("error",id,token);true }
    p.prepareAsync()
   } catch(_:Exception) { stopPlayer();emit("error",id,token) }
  }
 }
 private fun chunks(text: String): List<String> = text.split(Regex("(?<=[。！？!?；;\n])")).filter { it.isNotBlank() }.flatMap { it.chunked(65) }
 @JavascriptInterface fun speak(raw: String?) {
  if(closed||raw==null||raw.length>16000) return
  try {
   val spec=JSONObject(raw);val text=spec.optString("text").trim().take(3000)
   val rawVolume=spec.optDouble("volume",.32)
   if(text.isEmpty()||!rawVolume.isFinite()||rawVolume<=0) return
   val volume=rawVolume.coerceIn(0.0,.55).toFloat()
   val rate=spec.optDouble("rate",.88).let { if(it.isFinite())it.coerceIn(.7,1.1).toFloat() else .88f }
   val pitch=spec.optDouble("pitch",1.0).let { if(it.isFinite())it.coerceIn(.9,1.12).toFloat() else 1f }
   stop();val token=sequence.get();emit("preparing","",token)
   worker.execute {
    if(closed||token!=sequence.get()) return@execute
    if(!ready||engine==null) {emit("speech-error","",token);return@execute}
    var owned:AudioTrack?=null
    try {
     val sampleRate=engine!!.sampleRate()
     val size=maxOf(AudioTrack.getMinBufferSize(sampleRate,AudioFormat.CHANNEL_OUT_MONO,AudioFormat.ENCODING_PCM_FLOAT),sampleRate/2*4)
     owned=AudioTrack(AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_MEDIA).setContentType(AudioAttributes.CONTENT_TYPE_SPEECH).build(),AudioFormat.Builder().setEncoding(AudioFormat.ENCODING_PCM_FLOAT).setSampleRate(sampleRate).setChannelMask(AudioFormat.CHANNEL_OUT_MONO).build(),size,AudioTrack.MODE_STREAM,AudioManager.AUDIO_SESSION_ID_GENERATE)
     check(owned.state==AudioTrack.STATE_INITIALIZED)
     track=owned;owned.setVolume(volume)
     try {owned.playbackParams=PlaybackParams().setSpeed(1f).setPitch(pitch)}catch(_:Exception){}
     if(closed||token!=sequence.get()) return@execute
     owned.play();var total=0
     for(part in chunks(text)) {
      if(closed||token!=sequence.get()) break
      val audio=engine!!.generate(part,0,rate)
      if(closed||token!=sequence.get()) break
      check(audio.samples.isNotEmpty() && audio.samples.all {it.isFinite()})
      generatedSamples+=audio.samples.size
      emit("speaking","",token)
      var offset=0
      while(offset<audio.samples.size&&!closed&&token==sequence.get()) {
       val n=owned.write(audio.samples,offset,minOf(4096,audio.samples.size-offset),AudioTrack.WRITE_BLOCKING)
       check(n>0);offset+=n;total+=n
      }
     }
     val end=System.currentTimeMillis()+4000
     while(!closed&&token==sequence.get()&&owned.playbackHeadPosition.toLong()<total.toLong()&&System.currentTimeMillis()<end) Thread.sleep(20)
     if(!closed&&token==sequence.get())emit("ended","",token)
    } catch(_:Throwable) {emit("speech-error","",token)}
    finally {if(track===owned)track=null;try {owned?.stop()}catch(_:Exception){};owned?.release()}
   }
  } catch(_:Exception) {emit("speech-error")}
 }
 /** Internal instrumentation-only synthesis check; not exposed to JavaScript. */
 fun synthesizeForTest(text:String):String {
  check(BuildConfig.DEBUG)
  return worker.submit<String> {
   check(ready&&engine!=null) {"Embedded Mandarin engine failed: $initError"}
   val audio=engine!!.generate(text,0,.9f)
   val peak=audio.samples.maxOfOrNull {abs(it)}?:0f
   val rms=sqrt(audio.samples.fold(0.0){s,x->s+x*x}/maxOf(1,audio.samples.size))
   val file=File(activity.filesDir,"test-embedded-mandarin.wav");check(audio.save(file.absolutePath))
   JSONObject().put("samples",audio.samples.size).put("sampleRate",audio.sampleRate).put("peak",peak.toDouble()).put("rms",rms).put("engine","embedded-huayan").put("requiresNetwork",false).put("requiresSystemTts",false).toString()
  }.get(120,TimeUnit.SECONDS)
 }
 fun pause() {stop();web.evaluateJavascript("window.WPSound&&window.WPSound.stop()",null)}
 fun close() {if(closed)return;stop();closed=true;worker.execute {engine?.release();engine=null};worker.shutdown();web.removeJavascriptInterface("WordPetAudioNative")}
}
