import os, json, sqlite3, secrets
from datetime import datetime, timezone
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx

DB=os.getenv("WORDPET_DB","/data/wordpet.sqlite3")
PAIR=os.getenv("WORDPET_PAIR_CODE","")
AI_URL=os.getenv("AI_BASE_URL","")
AI_KEY=os.getenv("AI_API_KEY","")
AI_MODEL=os.getenv("AI_MODEL","gpt-4o-mini")
app=FastAPI(title="Word Pet Family API",version="1.0.0")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_methods=["GET","POST"],allow_headers=["*"])

def db():
    os.makedirs(os.path.dirname(DB) or ".",exist_ok=True)
    c=sqlite3.connect(DB); c.execute("CREATE TABLE IF NOT EXISTS child_state (child_id TEXT PRIMARY KEY, state TEXT NOT NULL, updated_at TEXT NOT NULL)")
    c.execute("CREATE TABLE IF NOT EXISTS essays (id INTEGER PRIMARY KEY AUTOINCREMENT, child_id TEXT, title TEXT, text TEXT, created_at TEXT)")
    return c

def auth(code):
    if not PAIR: raise HTTPException(503,"家长尚未设置配对码")
    if not code or not secrets.compare_digest(code,PAIR): raise HTTPException(401,"配对码不正确")

class SyncBody(BaseModel):
    child_id: str = Field(default="main",max_length=80)
    state: dict
    updated_at: str|None=None

class EssayBody(BaseModel):
    title: str="我的作文"
    text: str=Field(min_length=5,max_length=12000)
    grade: int=Field(default=2,ge=2,le=6)

@app.get("/health")
def health():
    return {"ok":True,"service":"word-pet","ai_configured":bool(AI_URL and AI_KEY),"sync":"ready"}

@app.post("/api/child/sync")
def sync(body:SyncBody,x_child_pairing_code:str|None=Header(default=None)):
    auth(x_child_pairing_code)
    c=db(); now=datetime.now(timezone.utc).isoformat()
    c.execute("INSERT INTO child_state(child_id,state,updated_at) VALUES(?,?,?) ON CONFLICT(child_id) DO UPDATE SET state=excluded.state,updated_at=excluded.updated_at",(body.child_id,json.dumps(body.state,ensure_ascii=False),now))
    c.commit(); c.close()
    return {"ok":True,"state":body.state,"updated_at":now}

@app.get("/api/child/sync")
def get_sync(child_id:str="main",x_child_pairing_code:str|None=Header(default=None)):
    auth(x_child_pairing_code)
    c=db(); row=c.execute("SELECT state,updated_at FROM child_state WHERE child_id=?",(child_id,)).fetchone(); c.close()
    return {"ok":True,"state":json.loads(row[0]) if row else None,"updated_at":row[1] if row else None}

@app.post("/api/child/essay-feedback")
async def essay_feedback(body:EssayBody,x_child_pairing_code:str|None=Header(default=None)):
    auth(x_child_pairing_code)
    if AI_URL and AI_KEY:
        prompt=("你是一位耐心的小学语文老师，面向"+str(body.grade)+"年级孩子。只鼓励并指出一个最重要的修改方向，通过一个问题引导孩子自己修改。绝不代写整篇作文，不编造孩子没写的事实。请用简短、温暖、儿童能懂的中文回复。\n题目："+body.title+"\n作文："+body.text)
        async with httpx.AsyncClient(timeout=45) as client:
            try:
                r=await client.post(AI_URL.rstrip("/")+"/chat/completions",headers={"Authorization":"Bearer "+AI_KEY,"Content-Type":"application/json"},json={"model":AI_MODEL,"messages":[{"role":"system","content":"你是儿童作文启蒙老师。"},{"role":"user","content":prompt}],"temperature":0.4})
                r.raise_for_status(); data=r.json(); feedback=data["choices"][0]["message"]["content"]
                source="online_ai"
            except Exception:
                feedback="老师暂时没有连上，请稍后再试。你的作文已经安全保存在设备上。"; source="service_error"
    else:
        feedback="我读完啦！先找一个最值得补充的细节：这件事发生在哪里？主角做了什么动作？最后再写一句你当时的真实感受。试着自己修改一处，老师相信你可以！"
        source="guided_fallback"
    c=db(); c.execute("INSERT INTO essays(child_id,title,text,created_at) VALUES(?,?,?,?)",("main",body.title,body.text,datetime.now(timezone.utc).isoformat())); c.commit(); c.close()
    return {"ok":True,"feedback":feedback,"source":source,"ai_configured":bool(AI_URL and AI_KEY)}

@app.get("/")
def root(): return {"service":"Word Pet Family API","health":"/health"}
