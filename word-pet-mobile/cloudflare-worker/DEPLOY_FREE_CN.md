# Word Pet 免费联网服务器部署（Cloudflare）

## 免费部分
Cloudflare Workers 免费额度可运行接口，D1 免费额度可保存家庭学习数据。具体免费额度以 Cloudflare 当前政策为准。此项目不需要 Replit 付费部署。

## 需要家长亲自完成的授权
1. 注册/登录 Cloudflare 免费账户。
2. 创建一个 D1 数据库，名称填 word-pet-family。
3. 在 D1 Console 执行 schema.sql。
4. 把 wrangler.toml 中 REPLACE_WITH_D1_DATABASE_ID 换成数据库 ID。
5. 创建 Worker 并部署 src/index.js。
6. 在 Worker Settings → Variables and Secrets 添加：
   - WORDPET_PAIR_CODE：家长自设的高强度随机配对码（必填）。
   - AI_BASE_URL：兼容 OpenAI Chat Completions 的服务地址（可选）。
   - AI_API_KEY：家长自己的AI服务密钥（可选，设为 Secret）。
   - AI_MODEL：模型名称（可选）。
7. 将 Worker 的 HTTPS 地址填入 Android App 的“连接”页面。

## 安全
- 不要把 AI_API_KEY 写入 App、GitHub 仓库或聊天。
- 配对码不要使用生日、手机号等容易猜到的内容。
- 目前是单家庭共享配对码模式；正式多家庭产品上线前需升级独立家长账号、孩子令牌、速率限制和审计。
- 数据存储在 D1；家长应定期导出备份。
- 没有 AI 密钥时，作文老师明确使用引导式备用反馈，不冒充AI批改。
