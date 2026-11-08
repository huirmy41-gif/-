/* Word Pet state engine: no network, no DOM, deterministic and independently tested. */
(function (root, factory) {
  const api = factory();
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.WordPet = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  const VERSION = 2;
  const catalog = [
    {id:'scarf', name:'星星围巾', type:'衣', cost:3, icon:'🧣'},
    {id:'snack', name:'爱心饼干', type:'食', cost:1, icon:'🍪'},
    {id:'bed', name:'云朵小床', type:'住', cost:5, icon:'🛏️'},
    {id:'balloon', name:'小小热气球', type:'行', cost:8, icon:'🎈'}
  ];
  function dateKey(date=new Date()) {
    return [date.getFullYear(),String(date.getMonth()+1).padStart(2,'0'),String(date.getDate()).padStart(2,'0')].join('-');
  }
  function fresh() {
    return {schema:VERSION, profile:{nickname:'小作家',grade:2,unit:'',goal:''},
      days:{}, essays:[], words:[], ledger:{}, purchases:{},
      pet:{kind:'dog',name:'星星',hatched:false}, legacyStars:0, updatedAt:0};
  }
  function text(v,max=3000) { return String(v==null?'':v).slice(0,max).trim(); }
  function migrate(old) {
    if (!old || typeof old!=='object' || Array.isArray(old)) return fresh();
    if (old.schema===VERSION) {
      if(!old.profile || !old.days || !Array.isArray(old.essays) || !Array.isArray(old.words) || !old.ledger || !old.purchases || !old.pet)
        throw new Error('备份结构不完整');
      if(![2,3,4,5,6].includes(Number(old.profile.grade))) throw new Error('年级不正确');
      if(JSON.stringify(old).length>1800000) throw new Error('备份过大');
      const clean=fresh();
      for(const k of Object.keys(clean)) if(Object.hasOwn(old,k)) clean[k]=old[k];
      return clean;
    }
    const s=fresh();
    s.legacyStars=Math.min(10000,Math.max(0,Number(old.stars)||0));
    s.essays=(old.essays||[]).filter(e=>e&&typeof e==='object').slice(-1000).map((e,i)=>({
      id:'legacy-'+i,date:text(e.at||e.created_at||'旧版作品',40),title:text(e.title||'旧版作文',80),
      original:text(e.text||e.original_text||''),revisions:[],updatedAt:0}));
    s.words=(old.words||[]).filter(e=>e&&typeof e==='object').map(e=>({
      word:text(e.word||e.w,30),sentence:text(e.sentence||e.s,500),date:'旧版练习'}));
    s.pet={kind:old.pet==='🐰'?'rabbit':old.pet==='🐉'?'dragon':'dog',
      name:text(old.petName||'星星',20),hatched:!!old.pet&&old.pet!=='🥚'};
    return s;
  }
  function day(s,key=dateKey()) {
    if(!/^\d{4}-\d{2}-\d{2}$/.test(key)) throw new Error('日期不正确');
    if(!s.days[key]) {
      const used=Object.values(s.days).filter(d=>d.tasks&&d.tasks.some(Boolean)).length;
      s.days[key]={lesson:used%30,tasks:[false,false,false,false],seconds:0,
        draft:{word:'',wordSentence:'',detail1:'',detail2:'',sentence:'',title:'',essay:''}};
    }
    return s.days[key];
  }
  function touch(s) { s.updatedAt=Date.now(); }
  function setDraft(s,key,field,value) {
    const d=day(s,key);
    if(!Object.hasOwn(d.draft,field)) throw new Error('字段不正确');
    d.draft[field]=String(value).slice(0, field==='essay'?3000:500);
    touch(s);
  }
  function complete(s,key,index) {
    const d=day(s,key), v=d.draft;
    if(index<0||index>3||!Number.isInteger(index)) throw new Error('任务不正确');
    if(d.tasks[index]) return 0;
    if(d.seconds>=900) throw new Error('今天的15分钟已经结束，草稿已保存。明天再继续吧。');
    if(index===0 && (!text(v.word)||text(v.wordSentence).length<4||!v.wordSentence.includes(text(v.word))))
      throw new Error('选一个词语，用它写一句自己的话。');
    if(index===1 && (text(v.detail1).length<2||text(v.detail2).length<2))
      throw new Error('写下两个观察到的小细节，也可以先说给家长听。');
    if(index===2 && text(v.sentence).length<5) throw new Error('把句子补充清楚，写下自己的表达。');
    if(index===3 && text(v.essay).length<5) throw new Error('先写几句自己的话，再完成这一关。');
    d.tasks[index]=true;
    let gained=0;
    const k=key+':'+index;
    if(!Object.hasOwn(s.ledger,k)) { s.ledger[k]=1; gained++; }
    if(index===0) {
      const w={word:text(v.word,30),sentence:text(v.wordSentence,500),date:key};
      if(!s.words.some(x=>x.word===w.word&&x.sentence===w.sentence)) s.words.push(w);
    }
    if(index===3) saveEssay(s,key);
    if(d.tasks.every(Boolean)&&!Object.hasOwn(s.ledger,key+':bonus')) {
      s.ledger[key+':bonus']=2; gained+=2;
    }
    touch(s);return gained;
  }
  function saveEssay(s,key) {
    const d=day(s,key), t=text(d.draft.essay);
    if(!t) throw new Error('先写下自己的想法吧。');
    const id=key+':essay', title=text(d.draft.title||'我的小作文',80);
    let e=s.essays.find(x=>x.id===id);
    if(!e) {
      e={id,date:key,title,original:t,revisions:[],updatedAt:Date.now()};
      s.essays.push(e);
    } else {
      const last=e.revisions.length?e.revisions[e.revisions.length-1].text:e.original;
      if(last!==t) e.revisions.push({text:t,at:new Date().toISOString()});
      e.title=title; e.updatedAt=Date.now();
    }
    touch(s);return e;
  }
  function balance(s) {
    return Math.max(0,s.legacyStars+Object.values(s.ledger).reduce((a,b)=>a+(Number(b)||0),0)-
      Object.values(s.purchases).reduce((a,b)=>a+(Number(b.cost)||0),0));
  }
  function purchase(s,id,key=dateKey()) {
    const item=catalog.find(x=>x.id===id);
    if(!item) throw new Error('没有找到这件礼物');
    if(!s.pet.hatched) throw new Error('先完成第一关，孵化伙伴吧。');
    const purchaseKey=id==='snack'?id+':'+key:id;
    if(s.purchases[purchaseKey]) return false;
    if(balance(s)<item.cost) throw new Error('星星还不够。慢慢来，伙伴会一直等你。');
    s.purchases[purchaseKey]={id,cost:item.cost,date:key};
    touch(s);return true;
  }
  function hatch(s,kind,name) {
    if(!['dog','rabbit','dragon'].includes(kind)) throw new Error('请选择一位伙伴');
    if(!Object.values(s.days).some(d=>d.tasks.some(Boolean))) throw new Error('先完成一个学习小任务，就能孵化啦。');
    s.pet={kind,name:text(name||'星星',20),hatched:true};touch(s);
  }
  function stage(s) {
    const days=Object.values(s.days).filter(d=>d.tasks.every(Boolean)).length;
    const originals=s.essays.filter(e=>e.original.length>=5).length;
    const revisions=s.essays.filter(e=>e.revisions.length>0).length;
    if(!s.pet.hatched) return 0;
    if(days>=25&&originals>=20&&revisions>=8)return 5;
    if(days>=15&&originals>=10&&revisions>=4)return 4;
    if(days>=7&&originals>=5&&revisions>=1)return 3;
    if(days>=3&&originals>=3)return 2;
    return 1;
  }
  function tick(s,key,seconds) {
    const d=day(s,key); d.seconds=Math.min(900,Math.max(0,d.seconds)+Math.max(0,Math.min(30,Number(seconds)||0)));
    touch(s);
  }
  function hint(t) {
    t=text(t);
    if(!t)return '先写一点自己的想法，再来看看提示吧。';
    if(t.length<25)return '你已经把想法写下来了。主角在哪里，正在做什么？选一处补充清楚。';
    if(!/开心|喜欢|难过|害怕|惊讶|感到|觉得|高兴|期待/.test(t))return '你写出了事情的样子。那一刻，你心里有什么真实的感受？';
    return '你写下了自己的感受。读一遍，挑一句加上一个真正观察过的动作细节；不需要句句加修饰词。';
  }
  function backup(s) { return JSON.stringify({app:'WordPet',version:'1.4.0',exportedAt:new Date().toISOString(),state:s}); }
  function restore(raw) {
    if(typeof raw!=='string'||raw.length>2000000) throw new Error('备份文件太大或格式错误');
    const data=JSON.parse(raw);
    return migrate(data.app==='WordPet'?data.state:data);
  }
  return {fresh,migrate,day,dateKey,setDraft,complete,saveEssay,balance,purchase,hatch,stage,tick,hint,backup,restore,catalog,touch,text};
});
