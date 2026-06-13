"""
飞书 AI 助手机器人
扫码激活，手机飞书直接对话 Codex/OpenAI
"""
import os
import json
import time
import hashlib
import logging
from threading import Lock

import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# ── 日志 ──────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("feishu-bot")

# ── 配置 ──────────────────────────────────────────────
APP_ID = os.getenv("FEISHU_APP_ID", "")
APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")
VERIFY_TOKEN = os.getenv("FEISHU_VERIFY_TOKEN", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", "你是一个有用的AI助手，用中文简洁回答。")

app = Flask(__name__)

# ── Token 缓存 ─────────────────────────────────────────
_tenant_token: str | None = None
_token_expire: float = 0
_token_lock = Lock()


def get_tenant_token() -> str:
    """获取 tenant_access_token，自动缓存和刷新"""
    global _tenant_token, _token_expire
    with _token_lock:
        if _tenant_token and time.time() < _token_expire - 60:
            return _tenant_token

        resp = requests.post(
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            json={"app_id": APP_ID, "app_secret": APP_SECRET},
            timeout=10,
        )
        data = resp.json()
        if data.get("code") != 0:
            raise RuntimeError(f"获取 token 失败: {data}")

        _tenant_token = data["tenant_access_token"]
        _token_expire = time.time() + data.get("expire", 7200)
        logger.info("✅ tenant_access_token 已刷新")
        return _tenant_token


# ── 消息存储（简单内存存储，生产环境建议用 Redis）─────
# 存储每个会话的对话历史
conversations: dict[str, list[dict]] = {}
MAX_HISTORY = 20  # 每个会话最多保留 20 轮对话


def chat_with_ai(chat_id: str, user_message: str) -> str:
    """调用 OpenAI API 并维护对话上下文"""
    if chat_id not in conversations:
        conversations[chat_id] = [{"role": "system", "content": SYSTEM_PROMPT}]

    conversations[chat_id].append({"role": "user", "content": user_message})

    # 裁剪历史
    if len(conversations[chat_id]) > MAX_HISTORY * 2 + 1:
        conversations[chat_id] = (
            conversations[chat_id][:1] + conversations[chat_id][-(MAX_HISTORY * 2):]
        )

    try:
        client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=conversations[chat_id],
            temperature=0.7,
            max_tokens=2000,
        )
        reply = resp.choices[0].message.content.strip()
        conversations[chat_id].append({"role": "assistant", "content": reply})
        return reply
    except Exception as e:
        logger.error(f"OpenAI 调用失败: {e}")
        return f"抱歉，AI 服务暂时不可用：{str(e)[:100]}"


def send_feishu_message(chat_id: str, content: str, msg_type: str = "text"):
    """通过飞书 API 发送消息"""
    token = get_tenant_token()
    url = "https://open.feishu.cn/open-apis/im/v1/messages"
    params = {"receive_id_type": "chat_id"}

    body = {
        "receive_id": chat_id,
        "msg_type": msg_type,
        "content": json.dumps({"text": content}, ensure_ascii=False),
    }

    resp = requests.post(
        url, params=params, json=body,
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    data = resp.json()
    if data.get("code") != 0:
        logger.error(f"发送消息失败: {data}")
    return data


# ── 飞书事件回调 ────────────────────────────────────────

@app.route("/feishu/event", methods=["POST"])
def feishu_event():
    """接收飞书事件回调"""
    body = request.get_json(force=True, silent=True) or {}

    # ── URL 验证（首次配置时飞书会发 challenge）─────────
    challenge = body.get("challenge")
    if challenge:
        token = body.get("token", "")
        challenge_type = body.get("type", "")
        logger.info(f"收到 URL 验证请求: type={challenge_type}")
        return jsonify({"challenge": challenge})

    # ── 消息事件处理 ────────────────────────────────────
    header = body.get("header", {})
    event_type = header.get("event_type", "")

    if event_type == "im.message.receive_v1":
        event = body.get("event", {})
        message = event.get("message", {})
        msg_type = message.get("message_type", "")
        chat_id = message.get("chat_id", "")
        content_str = message.get("content", "{}")

        try:
            content = json.loads(content_str)
            text = content.get("text", "").strip()
        except json.JSONDecodeError:
            text = ""

        # 过滤机器人自己的消息
        if text and chat_id:
            logger.info(f"📩 收到消息: chat_id={chat_id[:20]}... text={text[:80]}")
            reply = chat_with_ai(chat_id, text)
            send_feishu_message(chat_id, reply)

    return jsonify({"code": 0})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "timestamp": time.time()})


# ── 启动 ────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    logger.info(f"🚀 飞书机器人启动在端口 {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
