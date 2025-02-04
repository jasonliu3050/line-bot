from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os

app = Flask(__name__)

# 讀取環境變數
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

# 初始化 LINE Bot API
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 設定商品價格表
menu = {
    "咖啡": 50,
    "蛋糕": 80,
    "三明治": 100
}

# 模擬用戶購物車
user_cart = {}

@app.route("/", methods=["GET"])
def home():
    return "Hello, this is my LINE bot server!"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id  # 獲取用戶 ID
    user_message = event.message.text.strip()
    
    # 初始化用戶購物車
    if user_id not in user_cart:
        user_cart[user_id] = []

    # 處理點餐
    if user_message.startswith("我要點"):
        item = user_message.replace("我要點", "").strip()
        if item in menu:
            user_cart[user_id].append(item)
            reply_text = f"已加入 {item} 到你的購物車！目前購物車內容：{', '.join(user_cart[user_id])}"
        else:
            reply_text = "抱歉，我們沒有這個商品喔！請輸入有效的商品名稱：咖啡、蛋糕、三明治"

    # 查看購物車內容
    elif user_message == "查看購物車":
        if user_cart[user_id]:
            reply_text = f"你的購物車內有：{', '.join(user_cart[user_id])}"
        else:
            reply_text = "你的購物車是空的，請輸入『我要點 咖啡』來開始點餐！"

    # 處理結帳
    elif user_message == "結帳":
        if not user_cart[user_id]:
            reply_text = "你的購物車是空的，請先點餐！"
        else:
            # 計算總金額
            total = sum(menu[item] for item in user_cart[user_id])

            # 設定折扣（滿 200 元打 9 折）
            discount = 0.9 if total >= 200 else 1.0
            final_price = int(total * discount)

            # 清空購物車
            user_cart[user_id] = []

            reply_text = f"總金額為 {total} 元，折扣後金額：{final_price} 元\n請使用以下 Line Pay 連結付款：\nhttps://pay.line.me/123456789"

    else:
        reply_text = "你好！請輸入『我要點 咖啡』來開始點餐，或輸入『查看購物車』來查看你的訂單。"

    # 回覆訊息
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)


