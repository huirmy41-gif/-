"""Deploy only with account authorization and confirmed free plan; never print secrets."""
import os,json,pathlib,urllib.request,subprocess,re
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'evidence';OUT.mkdir(exist_ok=True)
token=os.getenv('CLOUDFLARE_API_TOKEN','');account=os.getenv('CLOUDFLARE_ACCOUNT_ID','');pair=os.getenv('WORDPET_PAIR_CODE','')
free=os.getenv('WORDPET_FREE_PLAN_CONFIRMED','').lower()=='true'
missing=[]
if not token:missing.append('CLOUDFLARE_API_TOKEN')
if not account:missing.append('CLOUDFLARE_ACCOUNT_ID')
if len(pair)<32:missing.append('WORDPET_PAIR_CODE (at least 32 characters)')
if not free:missing.append('WORDPET_FREE_PLAN_CONFIRMED')
report={'deployed':False,'missing_authorization':missing,'paid_plan_enabled_by_this_script':False}
if missing:
 (OUT/'cloud-status.json').write_text(json.dumps(report,indent=2))
 print('Cloud deployment not performed: account authorization/free-plan confirmation is missing.')
 raise SystemExit(0)
def api(method,path,data=None):
 raw=json.dumps(data).encode() if data is not None else None
 req=urllib.request.Request('https://api.cloudflare.com/client/v4'+path,data=raw,method=method,headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=30) as r:result=json.load(r)
 if not result.get('success'):raise RuntimeError('Cloudflare rejected an authorized deployment operation.')
 return result['result']
try:
 rows=api('GET','/accounts/'+account+'/d1/database?name=word-pet-family')
 database=next((r for r in rows if r.get('name')=='word-pet-family'),None)
 if database is None:database=api('POST','/accounts/'+account+'/d1/database',{'name':'word-pet-family'})
 work=ROOT/'word-pet-mobile/cloudflare-worker';database_id=database['uuid']
 cfg=(work/'wrangler.toml').read_text().replace('REPLACE_WITH_D1_DATABASE_ID',database_id)
 enable_ai=os.getenv('WORDPET_ENABLE_AI','').lower()=='true';cfg=cfg.replace('AI_ENABLED = "false"','AI_ENABLED = "'+str(enable_ai).lower()+'"')
 (work/'wrangler.runtime.toml').write_text(cfg)
 def wrangler(args,stdin=None):
  p=subprocess.run(['npx','--yes','wrangler@4',*args,'--config','wrangler.runtime.toml'],input=stdin,text=True,cwd=work,capture_output=True,env=os.environ,timeout=180)
  if p.returncode:raise RuntimeError('Wrangler operation failed. Review account permissions in Cloudflare.')
  return p.stdout
 wrangler(['d1','execute','word-pet-family','--remote','--file=schema.sql'])
 wrangler(['secret','put','WORDPET_PAIR_CODE'],pair)
 output=wrangler(['deploy']);urls=re.findall(r'https://[a-z0-9.-]+\.workers\.dev',output)
 if not urls:raise RuntimeError('No verified deployment URL returned')
 url=urls[-1]
 with urllib.request.urlopen(url+'/health',timeout=20) as r:health=json.load(r)
 if health.get('protocol')!=2:raise RuntimeError('Health verification failed')
 report.update(deployed=True,url=url,protocol=2,ai_enabled=enable_ai)
 print('Cloud deployment health check passed.')
except Exception as e:
 report['error']=str(e)[:250];print('Cloud deployment did not complete; the APK remains usable offline.')
finally:
 (OUT/'cloud-status.json').write_text(json.dumps(report,indent=2))
 p=ROOT/'word-pet-mobile/cloudflare-worker/wrangler.runtime.toml'
 if p.exists():p.unlink()
