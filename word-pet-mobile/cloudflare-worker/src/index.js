const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type,X-Child-Pairing-Code",
  "Content-Type": "application/json; charset=utf-8"
};
const json = (data, status=200) => new Response(JSON.stringify(data), {status,headers:cors});
const auth = (request, env) => {
  const supplied=request.headers.get("X-Child-Pairing-Code") || "";
  return !!env.WORDPET_PAIR_CODE && supplied.length>0 && supplied===env.WORDPET_PAIR_CODE;
};
export default {
 async fetch(request,env) {
  if(request.method==="OPTIONS") return new Response(null,{headers:cors});
  const url=new URL(request.url);
  if(url.pathname==="/health") return json({ok:true,service:"word-pet-family",ai_configured:!!(env.AI_BASE_URL&&env.AI_API_KEY)});
  if(!auth(request,env)) return json({error:"家长配对码不正确或尚未设置"},401);
  if(url.pathname==="/api/child/sync" && request.method==="GET") {
   const id=url.searchParams.get("child_id")||"main";
   const row=await env.DB.prepare("SELECT state_json,updated_at FROM child_state WHERE child_id=?").bind(id).first();
   return json({ok:true,state:row?JSON.parse(row.state_json):null,updated_at:row?.updated_at||null});
  }
  if(url.pathname==="/api/child/sync" && request.method==="POST") {
   const body=await request.json(); const id=String(body.child_id||"main").slice(0,80);
   const state=JSON.stringify(body.state||{}); if(state.length>200000) return json({error:"学习数据过大"},413);
   const now=new Date().toISOString();
   await env.DB.prepare("INSERT INTO child_state(child_id,state_json,updated_at) VALUES(?,?,?) ON CONFLICT(child_id) DO UPDATE SET state_json=excluded.state_json,updated_at=excluded.updated_at").bind(id,state,now).run();
   return json({ok:true,state:body.state,updated_at:now});
  }
  if(url.pathname==="/api/child/essay-feedback" && request.method==="POST") {
   const b=await request.json(); const text=String(b.text||"").slice(0,12000);
   if(text.length<5) return json({error:"作文内容太短"},400);
   let feedback="我读完啦！先补充一个具体细节：事情发生在哪里？主角做了什么动作？最后写一句你的真实感受。试着自己修改一处。";
   let source="guided_fallback";
   if(env.AI_BASE_URL && env.AI_API_KEY) {
    try {
     const resp=await fetch(env.AI_BASE_URL.replace(/\/$/,"")+"/chat/completions",{method:"POST",headers:{"Authorization":"Bearer "+env.AI_API_KEY,"Content-Type":"application/json"},body:JSON.stringify({model:env.AI_MODEL||"gpt-4o-mini",temperature:0.35,messages:[{role:"system",content:"你是耐心的小学语文作文老师。面向二年级孩子。先鼓励，只指出一个最重要的改进点，用一个问题引导孩子自己修改。绝不代写整篇作文，不编造细节。中文短句，温暖具体。"},{"role":"user",content:"题目："+String(b.title||"我的作文")+"\n作文："+text}]})});
     if(resp.ok){const d=await resp.json();feedback=d.choices?.[0]?.message?.content||feedback;source="online_ai"}
    } catch(e) {}
   }
   await env.DB.prepare("INSERT INTO essays(child_id,title,essay_text,created_at) VALUES(?,?,?,?)").bind("main",String(b.title||"我的作文").slice(0,120),text,new Date().toISOString()).run();
   return json({ok:true,feedback,source,ai_configured:!!(env.AI_BASE_URL&&env.AI_API_KEY)});
  }
  return json({error:"接口不存在"},404);
 }
};
