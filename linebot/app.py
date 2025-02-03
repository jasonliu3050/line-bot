from flask import Flask, request, abort
from linebot.v3.messaging import MessagingApi, Configuration
from linebot.v3.webhook import WebhookHandler, MessageEvent
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging.models import TextMessage
import os

# 讀取環境變數
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

# 確保環境變數沒有漏掉
if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_CHANNEL_SECRET:
    raise ValueError("❌ 環境變數未設置，請檢查 Render 的 Environment Variables 是否正確設置！")

# 初始化 Flask
app = Flask(__name__)

# 設定 LINE Messaging API
config = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
line_bot_api = MessagingApi(Configuration)  # ✅ 修正：移除 `configuration=config`

handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    """處理 LINE 傳來的 Webhook 事件"""
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """處理接收到的訊息"""
    user_message = event.message.text  # 使用者傳來的文字訊息
    reply_message = f"你說了：{user_message}"
    
    line_bot_api.reply_message(
        event.reply_token,
        [TextMessage(text=reply_message)]
    )

# 啟動 Flask 伺服器
if __name__ == "__main__":
    app.run(port=5000, debug=True)
