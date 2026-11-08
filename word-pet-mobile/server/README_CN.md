# Word Pet 家庭服务器

## 环境变量
- `WORDPET_PAIR_CODE`：家长自行设置的长随机配对码（必填）。
- `WORDPET_DB`：数据库文件路径，默认 `/data/wordpet.sqlite3`。
- `AI_BASE_URL`：兼容 OpenAI Chat Completions 的服务地址（可选）。
- `AI_API_KEY`：AI服务密钥（可选，只放服务器环境变量，绝不放进APK）。
- `AI_MODEL`：模型名称，默认 `gpt-4o-mini`。

## 启动
Docker运行时将持久磁盘挂载到 `/data`，映射端口8080。配置HTTPS反向代理后，家长在App的“连接”页面填写服务器HTTPS地址和配对码。

## 接口
- `GET /health`
- `POST /api/child/sync`：请求头 `X-Child-Pairing-Code`，正文 `{child_id,state,updated_at}`。
- `GET /api/child/sync?child_id=main`
- `POST /api/child/essay-feedback`：正文 `{title,text,grade}`。

注意：必须使用HTTPS；不要公开配对码。SQLite需使用持久磁盘。若未配置AI地址和密钥，作文点评会明确返回引导式备用提示，不会冒充真实AI批改。
