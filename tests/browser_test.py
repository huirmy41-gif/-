import json,threading,functools,http.server,pathlib,os
from playwright.sync_api import sync_playwright
ROOT=pathlib.Path(__file__).resolve().parents[1];ASSETS=ROOT/'word-pet-mobile/android-native/app/src/main/assets';OUT=ROOT/'evidence';OUT.mkdir(exist_ok=True)
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ASSETS)))
threading.Thread(target=server.serve_forever,daemon=True).start()
results=[];errors=[]
def check(name,value):
 assert value,name
 results.append({'name':name,'status':'passed'})
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,args=['--no-sandbox']);context=browser.new_context(viewport={'width':390,'height':844},device_scale_factor=1)
  page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.goto(f'http://127.0.0.1:{server.server_port}/index.html')
  check('phone first launch',page.title()=='作文小作家 Word Pet');check('phone fits width',page.evaluate('document.documentElement.scrollWidth<=innerWidth'));check('AI and voice off by default',page.evaluate('!config.voice&&!config.ai&&!cloud.url'))
  page.screenshot(path=str(OUT/'home-phone.png'),full_page=True)
  page.get_by_role('button',name='📖 学习',exact=True).click();page.locator('[data-word]').first.click();page.locator('#wordSentence').fill('毛茸茸的小狗跑到了我的身边。');page.locator('#complete0').click();check('first star earned',page.locator('#stars').inner_text()=='1');check('completed task locked',page.locator('#complete0').is_disabled())
  page.locator('#detail1').fill('小狗长着白色的毛');page.locator('#detail2').fill('小狗摇着尾巴');page.locator('#complete1').click();page.locator('#sentence').fill('白色的小狗在草地上欢快地跑。');page.locator('#complete2').click();page.screenshot(path=str(OUT/'lesson-phone.png'),full_page=True)
  page.get_by_role('button',name='✏️ 作文',exact=True).click();page.locator('#essay').fill('我喜欢毛茸茸的小狗。它跑来跑去。我看见它就很开心。');page.locator('#title').fill('我的小狗');page.get_by_role('button',name='保存作品，不覆盖原文',exact=True).click();original=page.evaluate('s.essays[0].original');page.locator('#complete3').click();check('six stars for four tasks',page.locator('#stars').inner_text()=='6')
  page.get_by_role('button',name='保存作品，不覆盖原文',exact=True).click();check('duplicate saves ignored',page.evaluate('s.essays.length===1&&s.essays[0].revisions.length===0'));page.locator('#essay').fill(original+'它用小鼻子轻轻碰了碰我。');page.get_by_role('button',name='保存作品，不覆盖原文',exact=True).click();check('original preserved',page.evaluate('(t)=>s.essays[0].original===t',original));check('revision separate',page.evaluate('s.essays[0].revisions.length===1'))
  page.locator('#essay').fill('一段还没按保存按钮的草稿。');page.reload();page.get_by_role('button',name='✏️ 作文',exact=True).click();check('autosave survives reload',page.locator('#essay').input_value()=='一段还没按保存按钮的草稿。');page.get_by_role('button',name='🦉 给我一个提示',exact=True).click();check('rules not labelled AI','不是AI批改' in page.locator('#feedback').inner_text());page.get_by_role('button',name='联网 AI 老师',exact=True).click();check('AI consent gate','默认关闭' in page.locator('#toast').inner_text())
  page.locator('#title').fill('<img src=x onerror=alert(1)>');page.get_by_role('button',name='保存作品，不覆盖原文',exact=True).click();check('stored text escapes HTML',page.locator('#history img').count()==0);page.screenshot(path=str(OUT/'writing-phone.png'),full_page=True)
  page.get_by_role('button',name='🐾 宠物',exact=True).click();page.locator('#petKind').select_option('rabbit');page.locator('#petNickname').fill('棉花糖');page.get_by_role('button',name='孵化 / 保存名字',exact=True).click();check('pet hatches',page.evaluate("s.pet.hatched&&s.pet.kind==='rabbit'"));page.locator('[data-buy="scarf"]').click();check('fixed price gift',page.locator('#stars').inner_text()=='3');check('gift duplicate blocked',page.locator('[data-buy="scarf"]').is_disabled());page.get_by_role('button',name='孵化 / 保存名字',exact=True).click();check('no pet rename exploit',page.locator('#stars').inner_text()=='3')
  answers=iter(['123456','123456'])
  def setup_dialog(d):d.accept(next(answers))
  page.on('dialog',setup_dialog);page.get_by_role('button',name='🔑 家长',exact=True).click();page.wait_for_selector('#parent:not([hidden])');page.remove_listener('dialog',setup_dialog);check('salted PIN hash stored',page.evaluate("parentPin.hash.length===64&&!!parentPin.salt&&parentPin.hash!=='123456'"))
  page.locator('#grade').select_option('3');page.locator('#unit').fill('观察与表达');page.locator('#customGoal').fill('按先后顺序写清楚');page.get_by_role('button',name='保存教学设置',exact=True).click();check('custom goals retained',page.evaluate("s.profile.grade===3&&s.profile.goal==='按先后顺序写清楚'"))
  with page.expect_download() as download_info:page.get_by_role('button',name='导出学习记录',exact=True).click()
  download_info.value.save_as(str(OUT/'synthetic-backup.json'));backup=json.loads((OUT/'synthetic-backup.json').read_text());check('backup no tokens or PIN',backup['app']=='WordPet' and 'token' not in backup['state'] and 'hash' not in backup['state'])
  page.on('dialog',lambda d:d.accept());page.evaluate('(raw)=>receiveBackup(raw)',json.dumps(backup,ensure_ascii=False));check('restore preserves essay',page.evaluate('s.essays.length===1'))
  page.evaluate('E.day(s,current).seconds=900;render()');page.get_by_role('button',name='📖 学习',exact=True).click();check('15-minute notice',page.locator('#timeNotice').is_visible());check('new tasks blocked at limit',page.locator('#complete0').is_disabled());page.get_by_role('button',name='✏️ 作文',exact=True).click();page.locator('#essay').fill('时间到了仍然可以保存我的作品。');page.get_by_role('button',name='保存作品，不覆盖原文',exact=True).click();check('save works after time limit',page.evaluate("s.essays[0].revisions.at(-1).text==='时间到了仍然可以保存我的作品。'"));check('no page errors',not errors)
  tablet=browser.new_context(viewport={'width':1024,'height':1366},device_scale_factor=1).new_page();tablet.goto(f'http://127.0.0.1:{server.server_port}/index.html');check('tablet fits width',tablet.evaluate('document.documentElement.scrollWidth<=innerWidth'));tablet.screenshot(path=str(OUT/'home-tablet.png'),full_page=True);browser.close()
finally:
 server.shutdown();(OUT/'browser-tests.json').write_text(json.dumps({'mode':'Chromium via localhost HTTP, native APIs not covered','tests':results,'errors':errors},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'passed':len(results),'errors':errors},ensure_ascii=False))
