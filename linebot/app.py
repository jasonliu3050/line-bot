from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os

# 初始化 Flask 應用
app = Flask(__name__)

# 讀取環境變數
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

# 確保環境變數已設置
if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_CHANNEL_SECRET:
    raise ValueError("❌ 環境變數未設置，請檢查 Render 的 Environment Variables 是否正確設置！")

# 初始化 LINE Messaging API 和 WebhookHandler
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/", methods=["GET"])
def home():
    return "Hello, this is my LINE bot server!"

@app.route("/callback", methods=["POST"])
def callback():
    # 獲取 LINE 傳來的簽名
    signature = request.headers.get("X-Line-Signature")
    # 獲取 Webhook 的內容
    body = request.get_data(as_text=True)
    print(f"收到的 Webhook 請求內容：{body}")  # 日誌輸出內容

    try:
        # 驗證簽名並處理事件
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("簽名驗證失敗")
        abort(400)  # 如果驗證失敗，返回 400 狀態碼

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # 獲取用戶發送的消息
    user_message = event.message.text.strip()
    print(f"用戶訊息：{user_message}")  # 日誌輸出

    # 回覆的邏輯
    if user_message.lower() == "hello":  # 如果用戶發送 "hello"
        reply_text = "你好，請問你需要什麼服務？"
    else:
        reply_text = f"我收到你的訊息了：{user_message}"

    # 回覆用戶
    try:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )
        print(f"成功回覆用戶：{reply_text}")  # 日誌輸出
    except Exception as e:
        print(f"回覆訊息時發生錯誤：{e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)


