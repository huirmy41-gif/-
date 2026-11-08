"""Apply original 1.5 experience to the 1.4 core without replacing existing records."""
from pathlib import Path
import shutil
root=Path(__file__).resolve().parents[1]
a=root/'word-pet-mobile/android-native/app/src/main/assets'
for name in ['quests.js','journey-engine.js','journey-art.js','journey.js','journey.css']:
 shutil.copyfile(root/'redesign'/name,a/name)
index=(a/'index.html').read_text()
if 'journey.css' not in index:
 index=index.replace('</head>','<link rel="stylesheet" href="journey.css"></head>')
 index=index.replace('</body>','<script src="quests.js"></script><script src="journey-engine.js"></script><script src="journey-art.js"></script><script src="journey.js"></script></body>')
(a/'index.html').write_text(index)
engine=(a/'engine.js').read_text()
engine=engine.replace('legacyStars:0, updatedAt:0','legacyStars:0, adventure:null, updatedAt:0')
engine=engine.replace('d.tasks&&d.tasks.some(Boolean)).length','d.tasks&&d.tasks.every(Boolean)).length')
engine=engine.replace("version:'1.4.0'","version:'1.5.0'")
(a/'engine.js').write_text(engine)
app=(a/'app.js').read_text().replace("['learn','write','words','pet'].includes(page)","['home','learn','write','words','pet'].includes(page)")
(a/'app.js').write_text(app)
j=(a/'journey.js').read_text()
j=j.replace("return r.reviewId?Q.cards.find", "return r.reviewId&&!r.reviewDone?Q.cards.find")
j=j.replace("if(questionReady){questionReady=false;nextQuiz();return}","if(questionReady){questionReady=false;if(r.step===0&&r.reviewId&&!r.reviewDone){r.reviewDone=true;lastQuizKey='';persist();drawQuiz();return}nextQuiz();return}")
j=j.replace("if(r.step===1&&!r.reviewId)J.answer(s,current,d.lesson,'new:'+q.id,true,q.id);",'')
j=j.replace("selected=-1;chosenTiles=[];questionReady=false;lastQuizKey=current+':'+step", "selected=-1;chosenTiles=step===3?[...(r.selected||[])]:[];questionReady=false;lastQuizKey=current+':'+step")
j=j.replace("chosenTiles.push(Number(b.dataset.tile));drawQuiz()", "chosenTiles.push(Number(b.dataset.tile));run().selected=[...chosenTiles];persist();drawQuiz()")
j=j.replace("chosenTiles=chosenTiles.filter(v=>v!==Number(b.dataset.remove));drawQuiz()", "chosenTiles=chosenTiles.filter(v=>v!==Number(b.dataset.remove));run().selected=[...chosenTiles];persist();drawQuiz()")
j=j.replace("<small>'+Math.floor(c.seconds)+' / 90 秒</small>","<small id=\"careClock\">'+Math.floor(c.seconds)+' / 90 秒</small>")
j=j.replace("const c=astate().care[current];if(c.seconds===90", "const c=astate().care[current];if($('careClock'))$('careClock').textContent=Math.floor(c.seconds)+' / 90 秒';if(c.seconds===90")
j=j.replace("if(!s.purchases[key])E.purchase(s,id,current);else J.equip(s,id);", "if(!s.purchases[key]){E.purchase(s,id,current);if(id!=='snack')J.equip(s,id)}else J.equip(s,id);")
(a/'journey.js').write_text(j)
gradle=root/'word-pet-mobile/android-native/app/build.gradle'
t=gradle.read_text().replace("applicationId 'com.wordpet.family'","applicationId 'com.wordpet.adventure'").replace('versionCode 140','versionCode 150').replace("versionName '1.4.0'","versionName '1.5.0'")
gradle.write_text(t)
manifest=root/'word-pet-mobile/android-native/app/src/main/AndroidManifest.xml'
manifest.write_text(manifest.read_text().replace('作文小作家·家庭版','作文小作家·星语岛'))
script=root/'scripts/run_emulator.sh'
script.write_text(script.read_text().replace('com.wordpet.family','com.wordpet.adventure').replace('WordPet-Family-1.4.0.apk','WordPet-Adventure-1.5.0.apk'))
report=root/'scripts/build_report.py'
report.write_text(report.read_text().replace('WordPet-Family-1.4.0.apk','WordPet-Adventure-1.5.0.apk').replace('1.4.0','1.5.0').replace('com.wordpet.family','com.wordpet.adventure').replace('四关练习','闯关式练习、学习路径、错题回顾与间隔复习、可见的宠物换装与房间装饰、90秒互动上限、四项原创任务'))
test=root/'word-pet-mobile/android-native/app/src/androidTest/java/com/wordpet/app/AppSmokeTest.java'
t=test.read_text();extra='''
 @Test public void adventureAssetsAndMapReady()throws Exception{ready();assertEquals("true",js("typeof WPAdventure==='object' && typeof WPJourney==='object' && document.getElementById('islandApp').children.length>0"));}
 @Test public void quizOpensAndRecordsWrongAnswerWithoutPenalty()throws Exception{ready();js("WPAdventure.open();true");assertEquals("false",js("document.getElementById('journeyScreen').hidden"));assertEquals("0",js("WPJourney.answer(s,current,0,'test-wrong',false,'q0');E.balance(s)"));}
 @Test public void adventureStateSurvivesNativeRestart()throws Exception{ready();js("WPJourney.ensure(s).outfit='scarf';persist();true");rule.getScenario().recreate();ready();assertEquals("\\\"scarf\\\"",js("WPJourney.ensure(s).outfit"));}
'''
if 'adventureAssetsAndMapReady' not in t:t=t.rstrip()[:-1]+extra+'}\n'
test.write_text(t)
print('Prepared Word Pet 1.5 assets, compatibility state and test target.')
