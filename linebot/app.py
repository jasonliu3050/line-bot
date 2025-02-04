from flask import Flask, request, abort
from linebot.v3.messaging import MessagingApi, ReplyMessageRequest
from linebot.v3.webhook import WebhookHandler, MessageEvent
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging.models import TextMessage
import os

# 讀取環境變數
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

# 確保環境變數都已設定
if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_CHANNEL_SECRET:
    raise ValueError("❌ 環境變數未設置，請檢查 Render 的 Environment Variables 是否正確設置！")

# 初始化 Flask 應用
app = Flask(__name__)

# 初始化 LINE Messaging API
line_bot_api = MessagingApi(LINE_CHANNEL_ACCESS_TOKEN)

# 初始化 WebhookHandler
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/", methods=["GET"])
def home():
    return "Hello, this is my LINE bot server!"

@app.route("/callback", methods=["POST"])
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
    user_message = event.message.text  # 取得使用者發送的文字
    reply_message = f"你說了：{user_message}"
    
    # 回覆訊息
    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text=reply_message)]
        )
    )

if __name__ == "__main__":
    # 取得 Render 提供的 PORT，若無則預設 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)





from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# 請將以下兩行替換為你的 LINE Bot Token 和 Secret
LINE_BOT_API = "你的 Channel Access Token"
HANDLER = WebhookHandler("你的 Channel Secret")

line_bot_api = LineBotApi(LINE_BOT_API)

@app.route("/callback", methods=["POST"])
def callback():
    # 獲取 LINE 傳來的 X-Line-Signature
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        HANDLER.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# 當接收到文字訊息時觸發
@HANDLER.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # 獲取用戶傳送的訊息
    user_message = event.message.text.lower().strip()  # 將訊息轉為小寫並去掉空格

    # 檢查用戶訊息是否為 "hello"
    if user_message == "hello":
        reply_text = "你好，請問你需要什麼服務？"
    else:
        reply_text = "抱歉，我不明白你的需求。"

    # 回覆用戶訊息
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    app.run(port=5000, debug=True)


