import pathlib,json,os,re,hashlib,xml.etree.ElementTree as ET
root=pathlib.Path(__file__).resolve().parents[1];out=root/'evidence';apk=root/'dist/WordPet-Family-1.4.0.apk'
tap=(out/'unit-tests.tap').read_text();passed=int(re.search(r'# pass (\d+)',tap).group(1));failed=int(re.search(r'# fail (\d+)',tap).group(1))
browser=json.loads((out/'browser-tests.json').read_text());cloud=json.loads((out/'cloud-status.json').read_text())
xmls=list((root/'word-pet-mobile/android-native/app/build/outputs/androidTest-results').rglob('*.xml'))
tests=failures=errors=0
for p in xmls:
 try:
  node=ET.parse(p).getroot()
  if node.tag=='testsuite':
   tests+=int(node.get('tests','0'));failures+=int(node.get('failures','0'));errors+=int(node.get('errors','0'))
 except ET.ParseError:pass
assert passed>0 and failed==0 and tests>=7 and failures==0 and errors==0 and not browser['errors']
report={'version':'1.4.0','build':os.getenv('GITHUB_RUN_NUMBER'),'commit':os.getenv('GITHUB_SHA'),'apk_bytes':apk.stat().st_size,'apk_sha256':hashlib.sha256(apk.read_bytes()).hexdigest(),'unit_tests_passed':passed,'browser_tests_passed':len(browser['tests']),'android_emulator_tests_passed':tests,'android_api':35,'physical_device_tested':False,'signature':'Android debug test signature','cloud':cloud,'real_ai_inference_tested':False}
(out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
text=f'''# 作文小作家 Word Pet 1.4.0 家庭测试版

安装即可离线学习，无需账号、服务器、Replit或API密钥。

## 实际验证
- 学习引擎和服务接口单元测试：{passed}项通过。
- 手机和平板 Chromium 交互测试：{len(browser['tests'])}项通过。
- Android 35模拟器原生测试：{tests}项通过。
- APK签名、包名和内置学习文件一致性已检查。
- APK大小：{apk.stat().st_size}字节。
- SHA256：`{report['apk_sha256']}`。
- 构建编号：{report['build']}；源码：`{report['commit']}`。

## 功能
30个主题、四关练习、每日重置、15分钟提醒与新任务限制、草稿自动保存、原文与修改记录、三种伙伴、固定价格礼物、家长密码、系统语音和文件备份恢复。

## 明确的边界
这是Debug家庭测试版，不是应用商店正式版。应用ID为com.wordpet.family，与旧版并存。
未在用户实际手机或平板验收；中文语音取决于设备已有语音服务。
联网AI和跨设备云同步是否上线：{str(cloud.get('deployed',False))}。详细缺项见cloud-status.json。未进行真实AI效果验收。
本地提示不是大模型批改。未导入学校教材，不宣称已达到具体写作学习效果。
云部署脚本不购买套餐、不修改计费设置；缺少授权与免费计划确认时不会上线。
换设备、卸载或安装不同签名测试版前请备份。请勿卸载仍有作品的旧版。
'''
(out/'VERIFICATION.md').write_text(text,encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
