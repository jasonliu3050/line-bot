from flask import Flask, request, abort
from linebot.v3.messaging import MessagingApi
from linebot.v3.webhook import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, PostbackEvent
from linebot.v3.messaging.messages import TextMessage, TextSendMessage
from linebot.v3.messaging.templates import TemplateSendMessage, CarouselTemplate, CarouselColumn
from linebot.v3.messaging.actions import PostbackAction
import os

app = Flask(__name__)

# 讀取環境變數
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

# 初始化 LINE Bot API（v3）
line_bot_api = MessagingApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 設定商品價格表
menu = {
    "雞肉Taco": 100,
    "牛肉Taco": 120,
    "豬肉Taco": 110,
    "香菜": 10,
    "酪梨醬": 20,
    "紅椒醬": 20,
    "玉米脆片": 50,
    "墨西哥風味飯": 60,
    "咖啡": 40,
    "紅茶": 35
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
    """處理用戶文字輸入"""
    user_id = event.source.user_id
    user_message = event.message.text.strip()

    # 初始化購物車
    if user_id not in user_cart:
        user_cart[user_id] = []

    # 發送菜單
    if user_message == "我要點餐":
        send_menu(event)
        return

    # 查看購物車
    elif user_message == "查看購物車":
        if user_cart[user_id]:
            reply_text = f"你的購物車內有：{', '.join(user_cart[user_id])}"
        else:
            reply_text = "你的購物車是空的，請輸入『我要點餐』來開始點餐！"

    # 結帳
    elif user_message == "結帳":
        if not user_cart[user_id]:
            reply_text = "你的購物車是空的，請先點餐！"
        else:
            total = sum(menu[item] for item in user_cart[user_id])
            discount = 0.9 if total >= 200 else 1.0
            final_price = int(total * discount)

            user_cart[user_id] = []

            reply_text = f"總金額為 {total} 元，折扣後金額：{final_price} 元\n請使用以下 Line Pay 付款連結：\nhttps://pay.line.me/123456789"

    else:
        reply_text = "你好！請輸入『我要點餐』來開始點餐，或輸入『查看購物車』來查看你的訂單。"

    line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=reply_text)])

def send_menu(event):
    """發送圖文菜單 (CarouselTemplate)"""
    carousel_template = CarouselTemplate(columns=[
        CarouselColumn(
            thumbnail_image_url="https://example.com/chicken_taco.jpg",
            title="選擇 Taco",
            text="請選擇你的 Taco 口味",
            actions=[
                PostbackAction(label="雞肉 Taco", data="點 雞肉Taco"),
                PostbackAction(label="牛肉 Taco", data="點 牛肉Taco"),
                PostbackAction(label="豬肉 Taco", data="點 豬肉Taco"),
            ]
        ),
        CarouselColumn(
            thumbnail_image_url="https://example.com/toppings.jpg",
            title="選擇配料",
            text="可選擇額外配料",
            actions=[
                PostbackAction(label="加香菜 (+10元)", data="點 香菜"),
                PostbackAction(label="加酪梨醬 (+20元)", data="點 酪梨醬"),
                PostbackAction(label="無需配料", data="點 無配料"),
            ]
        ),
        CarouselColumn(
            thumbnail_image_url="https://example.com/side.jpg",
            title="選擇 Side",
            text="選擇你的 Side",
            actions=[
                PostbackAction(label="玉米脆片 (+50元)", data="點 玉米脆片"),
                PostbackAction(label="墨西哥風味飯 (+60元)", data="點 墨西哥風味飯"),
                PostbackAction(label="無 Side", data="點 無Side"),
            ]
        ),
        CarouselColumn(
            thumbnail_image_url="https://example.com/drinks.jpg",
            title="選擇飲料",
            text="請選擇飲料",
            actions=[
                PostbackAction(label="咖啡 (+40元)", data="點 咖啡"),
                PostbackAction(label="紅茶 (+35元)", data="點 紅茶"),
                PostbackAction(label="無飲料", data="點 無飲料"),
            ]
        ),
    ])

    line_bot_api.reply_message(
        event.reply_token,
        [TemplateSendMessage(alt_text="請選擇餐點", template=carousel_template)]
    )

@handler.add(PostbackEvent)
def handle_postback(event):
    """處理用戶的 Postback 選擇"""
    user_id = event.source.user_id
    postback_data = event.postback.data

    if postback_data.startswith("點 "):
        item = postback_data.replace("點 ", "").strip()

        if user_id not in user_cart:
            user_cart[user_id] = []

        user_cart[user_id].append(item)
        reply_text = f"你已加入 {item}！目前購物車內容：{', '.join(user_cart[user_id])}"

        line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=reply_text)])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)


