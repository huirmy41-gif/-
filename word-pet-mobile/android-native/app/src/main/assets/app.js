'use strict';
const $=id=>document.getElementById(id),E=WordPet,KEY='wordpet-v14-state';
const fields=['word','wordSentence','detail1','detail2','sentence','title','essay'];
let s,current=E.dateKey(),page='home',parentUntil=0,timerMark=Date.now(),toastTimer;
let config={},cloud={},parentPin={},pendingImportUntil=0;
const native=window.WordPetNative;
function safeJSON(raw,fallback){try{return raw?JSON.parse(raw):fallback}catch(e){return fallback}}
function load(){
 const raw=native?native.loadState():localStorage.getItem(KEY);
 const old=safeJSON(raw,null)||safeJSON(localStorage.getItem('wordpet-v13-state'),null)||safeJSON(localStorage.getItem('wordpet-state'),null);
 try{s=E.migrate(old)}catch(e){s=E.fresh();notify('旧记录读取失败，原始数据未删除。请家长从备份恢复。')}
 config=safeJSON(localStorage.getItem('wordpet-parent-options'),{voice:false,ai:false});
 cloud=safeJSON(localStorage.getItem('wordpet-cloud-v2'),{});parentPin=safeJSON(localStorage.getItem('wordpet-parent-pin'),{});
 E.day(s,current);fill();render();persist();
}
function notify(t){$('toast').textContent=String(t);$('toast').style.display='block';clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('toast').style.display='none',4500)}
function persist(){try{const raw=JSON.stringify(s);if(native&&!native.saveState(raw))throw Error();localStorage.setItem(KEY,raw);$('draftStatus').textContent='已自动保存到本设备'}catch(e){$('draftStatus').textContent='保存失败：请家长立即导出备份';notify('保存遇到问题，请先导出备份。不要卸载应用。')}}
function lesson(){return WORDPET_LESSONS[E.day(s,current).lesson]}
function fill(){const d=E.day(s,current);if(!d.draft.title)d.draft.title=lesson().topic;fields.forEach(f=>$(f).value=d.draft[f]||'');$('grade').value=s.profile.grade;$('unit').value=s.profile.unit;$('customGoal').value=s.profile.goal;$('petKind').value=s.pet.kind;$('petNickname').value=s.pet.name;$('voiceConsent').checked=!!config.voice;$('aiConsent').checked=!!config.ai;$('server').value=cloud.url||'';$('token').value=cloud.token||''}
function escapeHTML(t){return String(t).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function render(){
 const d=E.day(s,current),l=lesson(),count=d.tasks.filter(Boolean).length,st=E.stage(s);
 $('stars').textContent=E.balance(s);$('todayCount').textContent=count+' / 4 关';$('progress').style.width=count*25+'%';
 const sec=Math.floor(d.seconds);$('clock').textContent=String(Math.floor(sec/60)).padStart(2,'0')+':'+String(sec%60).padStart(2,'0')+' / 15:00';
 $('theme').textContent=l.title;$('goal').textContent='今天只练一件事：'+(s.profile.goal||l.goal);
 $('taskOverview').innerHTML=['词语魔法屋','观察侦探社','句子魔法师','迷你小作文'].map((t,i)=>'<p>'+(d.tasks[i]?'✅ ':'○ ')+t+'</p>').join('');
 $('lessonIntro').textContent='第'+(l.id+1)+'个学习主题 · '+l.title;$('observe').textContent=l.observe;$('baseSentence').textContent=l.base;$('writingTopic').textContent=l.topic;
 const level={2:'写3–5句话就好，把事情或样子说清楚。',3:'尝试写一个连贯段落，注意先后顺序。',4:'围绕一个重点，选择有用的细节。',5:'想清楚想表达什么，安排材料的详略。',6:'独立构思、分段，再读一遍修改。'};
 const goal=(s.profile.unit?'当前学校进度：'+s.profile.unit+'。':'')+(s.profile.goal||l.goal)+'。'+level[s.profile.grade];$('writingGoal').textContent=goal;$('writeHint').textContent=goal;
 $('targetWords').innerHTML=l.words.map(w=>'<button class="word" data-word="'+escapeHTML(w)+'">'+escapeHTML(w)+'</button>').join('');$('wordBookToday').textContent=l.words.join(' · ');document.querySelectorAll('[data-word]').forEach(b=>b.onclick=()=>pick(b.dataset.word));
 for(let i=0;i<4;i++){const b=$('complete'+i);b.disabled=d.tasks[i]||d.seconds>=900;b.textContent=d.tasks[i]?'已完成，奖励已记入':i===3?'完成第四关 · 自动结算奖励':'我完成了 · 获得1颗星'}
 $('timeNotice').hidden=d.seconds<900;$('essayTaskStatus').textContent=d.tasks[3]?'今日作品练习已完成。':'完成后可获得1颗星；四关全部完成再加2颗。';$('charCount').textContent=Array.from(d.draft.essay.replace(/\s/g,'')).length+'字';
 const icons={dog:'🐶',rabbit:'🐰',dragon:'🐉'},names=['魔法宠物蛋','初生伙伴','魔法幼崽','少年伙伴','成长伙伴','守护精灵'];
 $('petIcon').textContent=$('petBig').textContent=s.pet.hatched?icons[s.pet.kind]:'🥚';$('petName').textContent=s.pet.hatched?s.pet.name+' · '+names[st]:'等待孵化的魔法蛋';$('petWelcome').textContent=s.pet.hatched?'你写下的每一点进步，都有伙伴陪伴。':'认真完成一个小任务，就能迎接伙伴。';$('stageTitle').textContent=names[st];
 const nDays=Object.values(s.days).filter(x=>x.tasks.every(Boolean)).length,nRev=s.essays.filter(e=>e.revisions.length).length;
 $('petEvidence').textContent='已完成 '+nDays+' 天完整练习，留下 '+s.essays.length+' 篇作品、'+nRev+' 篇修改记录。';
 $('shop').innerHTML=E.catalog.map(x=>{const key=x.id==='snack'?x.id+':'+current:x.id;return '<div class="shop-item"><div>'+x.icon+' '+escapeHTML(x.name)+'</div><small>'+x.type+' · '+x.cost+'颗星</small><button class="secondary" data-buy="'+x.id+'" '+(s.purchases[key]?'disabled':'')+'>'+(s.purchases[key]?'已收到':'送给伙伴')+'</button></div>'}).join('');document.querySelectorAll('[data-buy]').forEach(b=>b.onclick=()=>buy(b.dataset.buy));
 $('wordHistory').innerHTML=s.words.slice(-60).reverse().map(w=>'<div class="saved-work"><b>'+escapeHTML(w.word)+'</b><p>'+escapeHTML(w.sentence)+'</p></div>').join('')||'<p class="muted">今天试着用一个词吧。</p>';
 $('history').innerHTML=s.essays.slice(-30).reverse().map(e=>'<details class="saved-work"><summary>'+escapeHTML(e.title)+' · '+escapeHTML(e.date)+'</summary><b>第一次写下的原文</b><p>'+escapeHTML(e.original)+'</p>'+(e.revisions||[]).map((r,i)=>'<b>第'+(i+1)+'次修改</b><p>'+escapeHTML(r.text)+'</p>').join('')+'</details>').join('')||'<p class="muted">保存的作品会出现在这里。</p>';
 const recent=[];for(let i=0;i<7;i++){const t=new Date();t.setDate(t.getDate()-i);const dd=s.days[E.dateKey(t)];if(dd)recent.push(dd)}
 $('weekly').innerHTML='<p>有练习记录：<b>'+recent.filter(x=>x.tasks.some(Boolean)).length+' 天</b></p><p>练习时间：<b>'+Math.round(recent.reduce((a,x)=>a+x.seconds,0)/60)+' 分钟</b></p><p>累计作品：<b>'+s.essays.length+' 篇</b>；修改过的作品：<b>'+nRev+' 篇</b></p>';
}
const definitions={'毛茸茸':'形容表面长着细软的毛。','圆溜溜':'形容很圆的样子。','欢快':'欢乐、轻快的样子。','清澈见底':'水清得能看见底部。','红彤彤':'形容很红。','金灿灿':'形容金黄色又有光彩。','绿油油':'形容浓绿而有光泽。','小心翼翼':'做事特别小心。','轻轻':'动作不重，用力很小。','蹦蹦跳跳':'一边蹦一边跳。','湿漉漉':'表面有水，潮湿的样子。'};
function pick(w){$('word').value=w;draft('word',w);$('definition').textContent=definitions[w]||'想一想“'+w+'”适合形容什么。先说一句自己的话，用得合适比用得多更重要。'}
function draft(f,v){E.setDraft(s,current,f,v);persist();if(f==='essay')$('charCount').textContent=Array.from(v.replace(/\s/g,'')).length+'字'}
function finish(i){try{fields.forEach(f=>E.setDraft(s,current,f,$(f).value));const n=E.complete(s,current,i);persist();render();notify('完成啦！获得'+n+'颗星星。'+(n===3?'四关全部完成，今天可以休息啦！':''))}catch(e){notify(e.message)}}
function saveWork(){try{fields.forEach(f=>E.setDraft(s,current,f,$(f).value));E.saveEssay(s,current);persist();render();notify('作品已保存。第一次的原文不会被覆盖。')}catch(e){notify(e.message)}}
function hint(){$('feedback').hidden=false;$('feedback').textContent='🦉 本地练习提示（不是AI批改）\n'+E.hint($('essay').value)}
function hatchPet(){try{E.hatch(s,$('petKind').value,$('petNickname').value);persist();render();notify('伙伴在这里陪你啦！')}catch(e){notify(e.message)}}
function buy(id){try{if(E.purchase(s,id,current)){persist();render();notify('礼物已送给伙伴。今天的奖励时间到这里就好。')}}catch(e){notify(e.message)}}
function rollover(){const key=E.dateKey();if(key!==current){persist();current=key;E.day(s,current);fill();render();persist();notify('新的一天，新的小发现。昨天的记录还在。')}}
function show(id){if(id==='parent'&&Date.now()>parentUntil){unlockParent();return}page=id;document.querySelectorAll('main section').forEach(x=>x.hidden=x.id!==id);document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('active',b.dataset.page===id));if(id==='parent')fill();window.scrollTo(0,0)}
function assertParent(){if(Date.now()>parentUntil){notify('请先解锁家长面板。');return false}return true}
async function pinHash(pin,salt){const key=await crypto.subtle.importKey('raw',new TextEncoder().encode(pin),'PBKDF2',false,['deriveBits']);const bytes=await crypto.subtle.deriveBits({name:'PBKDF2',salt:new TextEncoder().encode(salt),iterations:120000,hash:'SHA-256'},key,256);return Array.from(new Uint8Array(bytes),x=>x.toString(16).padStart(2,'0')).join('')}
async function unlockParent(){try{
 if(Date.now()<Number(parentPin.lockUntil||0)){notify('密码尝试过多，请稍后再试。');return}
 const value=prompt(parentPin.hash?'请输入家长密码':'第一次使用：请家长设置6位数字密码。孩子的学习页无需密码。');if(value===null)return;if(!/^\d{6}$/.test(value)){notify('请输入6位数字。');return}
 if(!parentPin.hash){if(prompt('请再次输入6位密码')!==value){notify('两次输入不一致。');return}const salt=Array.from(crypto.getRandomValues(new Uint8Array(16)),x=>x.toString(16).padStart(2,'0')).join('');parentPin={salt,hash:await pinHash(value,salt),failures:0}}
 else if(await pinHash(value,parentPin.salt)!==parentPin.hash){parentPin.failures=(parentPin.failures||0)+1;if(parentPin.failures>=5){parentPin.lockUntil=Date.now()+60000;parentPin.failures=0}localStorage.setItem('wordpet-parent-pin',JSON.stringify(parentPin));notify('密码不正确。');return}
 parentPin.failures=0;parentPin.lockUntil=0;localStorage.setItem('wordpet-parent-pin',JSON.stringify(parentPin));parentUntil=Date.now()+300000;show('parent');
 }catch(e){notify('本设备暂不支持安全密码设置。核心学习仍可使用。')}}
function lockParent(){parentUntil=0;show('home');notify('家长面板已锁定')}
async function changePin(){if(!assertParent())return;const pin=prompt('设置新的6位数字密码');if(pin===null)return;if(!/^\d{6}$/.test(pin)||prompt('再输入一次新密码')!==pin){notify('两次密码不一致或格式错误');return}parentPin.hash=await pinHash(pin,parentPin.salt);localStorage.setItem('wordpet-parent-pin',JSON.stringify(parentPin));notify('已修改')}
function saveProfile(){if(!assertParent())return;s.profile.grade=Number($('grade').value);s.profile.unit=$('unit').value.slice(0,120);s.profile.goal=$('customGoal').value.slice(0,200);E.touch(s);persist();render();notify('教学设置已保存，下次练习会沿用。')}
function saveConsent(){if(!assertParent())return;config={voice:$('voiceConsent').checked,ai:$('aiConsent').checked};localStorage.setItem('wordpet-parent-options',JSON.stringify(config));notify('授权已保存。')}
function exportBackup(){if(!assertParent())return;const data=E.backup(s);if(native){native.exportBackup(data);return}const url=URL.createObjectURL(new Blob([data],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='WordPet-backup-'+current+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}
function importBackup(){if(!assertParent())return;pendingImportUntil=Date.now()+300000;if(native)native.importBackup();else $('backupFile').click()}
window.receiveBackup=function(raw){if(Date.now()>pendingImportUntil&&!assertParent())return;pendingImportUntil=0;try{const incoming=E.restore(raw);if(!confirm('恢复会替换本机学习记录，应用会保留恢复前的本机快照。确认恢复吗？'))return;localStorage.setItem('wordpet-before-restore',E.backup(s));s=incoming;E.day(s,current);persist();fill();render();notify('已恢复学习记录。')}catch(e){notify('备份没有导入：'+e.message)}};
function speak(text){if(!text.trim()){notify('先写一些内容吧。');return}if(native){native.speak(text.slice(0,3000));return}if(!window.speechSynthesis){notify('设备没有可用的朗读功能。');return}const voice=speechSynthesis.getVoices().find(v=>v.localService&&v.lang.startsWith('zh'));if(!voice){notify('请家长先在设备上安装离线中文语音。');return}speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(text);u.lang='zh-CN';u.voice=voice;u.rate=.85;speechSynthesis.speak(u)}
function speakEssay(){speak($('essay').value)}function readPrompt(){const l=lesson();speak(l.title+'。'+l.observe+'。'+l.goal)}
function dictate(){if(!config.voice){notify('语音输入默认关闭，请家长到面板授权。');return}if(!native){notify('请使用安卓安装版的系统语音输入，或键盘上的语音按钮。');return}native.recognize()}
window.receiveSpeech=function(text){if(confirm('系统识别到：\n'+text+'\n\n请检查文字，确认后加入作文？')){$('essay').value=($('essay').value?$('essay').value+'\n':'')+String(text).slice(0,1000);draft('essay',$('essay').value)}};
window.nativeMessage=notify;
function validatedUrl(value){const u=new URL(value);if(u.protocol!=='https:'||u.username||u.password||u.search||u.hash||!['','/'].includes(u.pathname))throw Error('请输入不带路径的HTTPS根地址');return u.origin}
async function api(path,options={}){if(!cloud.url||!cloud.token)throw Error('尚未配置家庭服务');const c=new AbortController(),t=setTimeout(()=>c.abort(),20000);try{const r=await fetch(cloud.url+path,{...options,signal:c.signal,headers:{'Content-Type':'application/json','X-Child-Pairing-Code':cloud.token,...options.headers}});const data=await r.json();if(!r.ok)throw Error(data.error||('服务返回 '+r.status));return data}finally{clearTimeout(t)}}
async function saveConnection(){if(!assertParent())return;try{const url=validatedUrl($('server').value.trim()),token=$('token').value.trim();if(token.length<16||token.length>200)throw Error('访问密钥应为16至200位');if(!confirm('将连接你指定的家庭服务。只有手动上传或请求AI时才会发送学习内容。继续吗？'))return;cloud={url,token,version:null};localStorage.setItem('wordpet-cloud-v2',JSON.stringify(cloud));const d=await api('/health');if(d.protocol!==2)throw Error('服务版本不兼容，请部署新版家庭服务');$('cloudStatus').textContent='连接可达；尚未同步作品。'+(d.ai_enabled?'服务器启用了AI。':'服务器未启用AI，仍可同步。')}catch(e){$('cloudStatus').textContent='没有完成连接：'+e.message}}
async function uploadCloud(){if(!assertParent())return;try{if(cloud.version===null||cloud.version===undefined){const r=await api('/api/child/sync');if(r.state)throw Error('云端已有记录。本机不会覆盖它，请先备份本机，再选择“从云端恢复”。');cloud.version=0}const result=await api('/api/child/sync',{method:'POST',body:JSON.stringify({state:s,expectedVersion:cloud.version})});cloud.version=result.version;localStorage.setItem('wordpet-cloud-v2',JSON.stringify(cloud));$('cloudStatus').textContent='上传成功，云版本 '+cloud.version+'。本机记录未删除。'}catch(e){$('cloudStatus').textContent='上传未完成，本机记录安全保留：'+e.message}}
async function downloadCloud(){if(!assertParent())return;try{const r=await api('/api/child/sync');if(!r.state)throw Error('云端还没有记录');const incoming=E.migrate(r.state);if(!confirm('云端恢复将替换本机记录。请先导出备份。确认吗？'))return;localStorage.setItem('wordpet-before-restore',E.backup(s));s=incoming;cloud.version=r.version;localStorage.setItem('wordpet-cloud-v2',JSON.stringify(cloud));E.day(s,current);persist();fill();render();$('cloudStatus').textContent='已恢复云版本 '+r.version}catch(e){$('cloudStatus').textContent='未恢复任何数据：'+e.message}}
function disconnect(){if(!assertParent())return;cloud={};localStorage.removeItem('wordpet-cloud-v2');fill();$('cloudStatus').textContent='已断开。本机作品仍在。'}
async function aiFeedback(){const text=$('essay').value.trim();if(!config.ai){notify('联网AI默认关闭，请家长先授权。');return}if(!text){notify('先写一点自己的想法。');return}$('feedback').hidden=false;$('feedback').textContent='正在请求老师。草稿已保存在本机。';try{const r=await api('/api/child/essay-feedback',{method:'POST',body:JSON.stringify({title:$('title').value,text:text.slice(0,1600),grade:s.profile.grade,consent:true})});$('feedback').textContent=(r.source==='online_ai'?'联网AI老师：':'本地规则提示（不是AI批改）：')+'\n'+r.feedback}catch(e){$('feedback').textContent='联网AI未完成，不会把它说成已批改。\n'+e.message+'\n可使用左边的本地提示。'}}
fields.forEach(f=>$(f).addEventListener('input',()=>draft(f,$(f).value)));document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>show(b.dataset.page));
$('backupFile').onchange=async()=>{const f=$('backupFile').files[0];if(!f)return;if(f.size>2000000){notify('文件过大');return}receiveBackup(await f.text());$('backupFile').value=''};
setInterval(()=>{const now=Date.now(),delta=(now-timerMark)/1000;timerMark=now;rollover();if(!document.hidden&&['learn','write','words','pet'].includes(page)&&delta<30){const before=E.day(s,current).seconds;E.tick(s,current,delta);if(before<900&&E.day(s,current).seconds>=900){persist();render();notify('15分钟到啦。草稿已保存，今天就到这里吧。')}const sec=Math.floor(E.day(s,current).seconds);$('clock').textContent=String(Math.floor(sec/60)).padStart(2,'0')+':'+String(sec%60).padStart(2,'0')+' / 15:00';if(sec%15===0)persist()}if(page==='parent'&&Date.now()>parentUntil)lockParent()},1000);
document.addEventListener('visibilitychange',()=>{timerMark=Date.now();persist();if(document.hidden&&page==='parent')lockParent()});window.addEventListener('pagehide',persist);window.onAppBack=()=>{if(page!=='home'){parentUntil=0;show('home');return true}persist();return false};window.WPApp={getState:()=>s};load();
