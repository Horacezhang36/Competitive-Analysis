# 🦜 飞书 AI 助手机器人

手机飞书扫码激活，随时随地跟 AI 对话、执行任务。

---

## ⚡ 快速激活（3 步，5 分钟）

### 第 1 步：创建飞书应用

1. 打开 [飞书开放平台](https://open.feishu.cn/app) 登录
2. 点击 **「创建企业自建应用」**，名称随意（如"AI助手"）
3. 进入应用页面 → 左侧 **「添加应用能力」** → 开启 **「机器人」**

### 第 2 步：获取凭据

在应用页面左侧：

| 凭据 | 位置 |
|------|------|
| **App ID** | 首页 → 「凭证与基础信息」 |
| **App Secret** | 首页 → 「凭证与基础信息」（点击显示） |
| **Verify Token** | 左侧「事件订阅」→ Verification Token |

### 第 3 步：配置 & 启动

```bash
cd feishu-bot
./setup.sh
```

按提示填入上面获取的 3 个凭据 + OpenAI API Key。

---

## 🔗 配置回调地址

服务启动后，你需要一个**公网 HTTPS 地址**让飞书能回调。

**最简单方式 — ngrok（免费）：**

```bash
# 新开一个终端
ngrok http 8080
```

复制 ngrok 输出的 `https://xxxx.ngrok-free.app` 地址。

然后回到飞书开放平台：

1. 左侧 **「事件订阅」**
2. **请求地址** 填入：`https://xxxx.ngrok-free.app/feishu/event`
3. 点击保存 → 飞书会验证地址 → 验证通过 ✅
4. 下方 **「添加事件」** → 搜索 `接收消息` → 勾选 **「im.message.receive_v1」**
5. 保存后点击右上角 **「发布」** → 选择「仅企业内成员可用」

---

## 📱 扫码使用

1. 飞书开放平台 → 左侧 **「应用发布」** → 点击 **「查看」**
2. 用手机飞书扫描二维码
3. 在飞书中搜索你的机器人名称，开始对话！

---

## 🛠️ 部署到服务器（长期运行）

```bash
# 使用 gunicorn 生产模式
pip install gunicorn
gunicorn -w 2 -b 0.0.0.0:8080 bot:app

# 或使用 systemd / supervisor 守护进程
```

---

## 🔧 环境变量

| 变量 | 说明 | 必填 |
|------|------|------|
| `FEISHU_APP_ID` | 飞书应用 ID | ✅ |
| `FEISHU_APP_SECRET` | 飞书应用密钥 | ✅ |
| `FEISHU_VERIFY_TOKEN` | 事件验证 Token | ✅ |
| `OPENAI_API_KEY` | OpenAI API Key | ✅ |
| `OPENAI_BASE_URL` | API 地址（默认 OpenAI 官方） | ❌ |
| `OPENAI_MODEL` | 模型名（默认 gpt-4o） | ❌ |
| `SYSTEM_PROMPT` | 系统提示词 | ❌ |
| `PORT` | 服务端口（默认 8080） | ❌ |

---

## 📁 文件结构

```
feishu-bot/
├── bot.py           # 主程序
├── setup.sh         # 一键配置启动脚本
├── requirements.txt # Python 依赖
├── .env.example     # 配置模板
└── README.md        # 本文件
```
