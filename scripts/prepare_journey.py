"""Prepare the adventure build and avoid redundant hidden scene work during startup."""
from pathlib import Path
import runpy
root=Path(__file__).resolve().parents[1]
runpy.run_path(str(root/'scripts/prepare_journey_base.py'))
assets=root/'word-pet-mobile/android-native/app/src/main/assets'
p=assets/'journey.js';j=p.read_text()
j=j.replace("if($('islandApp'))mapView();if($('roomApp'))roomView();", "if($('islandApp')&&page==='home'&&!wizardOpen)mapView();if($('roomApp')&&page==='pet')roomView();")
j=j.replace('title=r.reviewId?', 'title=r.reviewId&&!r.reviewDone?').replace('sub=r.reviewId?', 'sub=r.reviewId&&!r.reviewDone?')
p.write_text(j)
test=root/'word-pet-mobile/android-native/app/src/androidTest/java/com/wordpet/app/AppSmokeTest.java'
t=test.read_text()
t=t.replace("typeof WordPet!=='undefined' && typeof WPApp!=='undefined'", "document.readyState==='complete' && typeof WordPet!=='undefined' && typeof WPApp!=='undefined' && typeof WPAdventure==='object'")
# Never reload a WebView while awaiting evaluateJavascript's callback: navigation can discard it.
# Actual Activity restart persistence remains covered by separate tests and their assertions.
t=t.replace('persist();location.reload();true', "config={voice:false,ai:false};cloud={};parentPin={};parentUntil=0;timerMark=Date.now();WPJourney.ensure(s);selectedIsland=null;lastQuizKey='';fill();persist();WPAdventure.close();true")
t=t.replace('Thread.sleep(500);ready();','ready();')
test.write_text(t)
print('Visible-scene rendering and deterministic test setup prepared; restart assertions retained.')
