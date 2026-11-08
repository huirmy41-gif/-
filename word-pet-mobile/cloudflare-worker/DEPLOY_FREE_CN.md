# 可选家庭云部署

APK不依赖云服务，不用配置就能开始学习。此目录只负责可选的跨设备快照和联网AI。

授权材料只保存到GitHub仓库的Actions Secrets/Variables，不发到聊天、不提交源码：
- Secret CLOUDFLARE_API_TOKEN：仅目标账户的Workers编辑和D1编辑权限。
- Variable CLOUDFLARE_ACCOUNT_ID：目标账户编号。
- Secret WORDPET_PAIR_CODE：至少32位随机家庭访问密钥。
- Variable WORDPET_FREE_PLAN_CONFIRMED：确认使用免费方案后才设为true。
- Variable WORDPET_ENABLE_AI：可选；明确启用联网AI时设为true，默认关闭。

执行Deploy Word Pet Family Server工作流。脚本自动查找或创建D1数据库、应用新增表迁移、设置Worker Secret、部署并验证health。缺少授权时只报告缺项，不上线。不修改计费设置，不购买套餐。
AI使用Cloudflare Workers AI免费方案可用模型，每家庭每日最多10次请求。免费额度和模型可用性由平台决定，不保证永久或无限使用。
旧数据库表保留。新版云同步用版本号比较写入，冲突返回409，不能悄悄覆盖本机作品。
不要向这个公开仓库提交真实儿童作文、学习备份、配对密钥和API令牌。
