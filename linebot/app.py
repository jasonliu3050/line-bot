from flask import Flask, request, abort
from linebot.v3.messaging import MessagingApi, Configuration
from linebot.v3.webhook import WebhookHandler, MessageEvent
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging.models import TextMessage  # ✅ 正確的 import
from linebot.v3.messaging.models import TextMessageContent  # ✅ 修正錯誤
import os



# 讀取環境變數（確保這些變數已設定）
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "你的Token")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "你的Secret")

# 檢查環境變數是否存在
if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_CHANNEL_SECRET:
    raise ValueError("請確保 LINE_CHANNEL_ACCESS_TOKEN 和 LINE_CHANNEL_SECRET 已正確設定！")

# 初始化 Flask 應用
app = Flask(__name__)

# 設定 LINE Messaging API
config = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
line_bot_api = MessagingApi(configuration=config)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    """處理 LINE Webhook 事件"""
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    """處理收到的訊息"""
    user_message = event.message.text  # 使用者發送的文字
    reply_message = f"你說了：{user_message}"

    # 回覆訊息
    line_bot_api.reply_message(
        event.reply_token,
        [TextMessage(text=reply_message)]
    )

# 啟動 Flask 伺服器
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
