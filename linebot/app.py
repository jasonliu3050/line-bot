import sys
print(sys.path)

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import (
    MessageEvent, PostbackEvent, TextSendMessage, PostbackAction,
    CarouselTemplate, CarouselColumn, TemplateSendMessage
)
import os


app = Flask(__name__)

# 讀取環境變數
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

# 初始化 LINE Bot API（v3）
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
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

# 用戶購物車
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
    except Exception as e:
        print(f"Webhook Error: {e}")
        abort(400)

    return "OK"

@handler.add(MessageEvent)
def handle_message(event):
    """處理用戶文字輸入"""
    user_id = event.source.user_id
    user_message = event.message.text.strip()

    if user_id not in user_cart:
        user_cart[user_id] = []

    if user_message == "我要點餐":
        send_menu(event)
        return

    elif user_message == "查看購物車":
        if user_cart[user_id]:
            reply_text = f"你的購物車內有：{', '.join(user_cart[user_id])}"
        else:
            reply_text = "你的購物車是空的，請輸入『我要點餐』來開始點餐！"

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
    """發送主選單（Taco & Taco Bowl）"""
    carousel_template = CarouselTemplate(columns=[
        CarouselColumn(
            thumbnail_image_url="https://i.imgur.com/MAnWCCx.jpeg",
            title="選擇你的主餐",
            text="請選擇 Taco 或 Taco Bowl",
            actions=[
                PostbackAction(label="Taco", data="選擇_Taco"),
                PostbackAction(label="Taco Bowl", data="選擇_TacoBowl")
            ]
        )
    ])

    line_bot_api.reply_message(
        event.reply_token,
        [TemplateSendMessage(alt_text="請選擇主餐", template=carousel_template)]
    )




@handler.add(PostbackEvent)
def handle_postback(event):
    """處理 Postback 事件"""
    user_id = event.source.user_id
    postback_data = event.postback.data

    # 記錄購物車（初始化）
    if user_id not in user_cart:
        user_cart[user_id] = []

    # 第一層：選擇主餐
    if postback_data.startswith("選擇_"):
        selected_main = postback_data.replace("選擇_", "")
        user_cart[user_id].append(selected_main)

        # 發送肉類選擇菜單
        send_meat_menu(event, selected_main)

    # 第二層：選擇肉類
    elif postback_data.startswith("肉_"):
        selected_meat = postback_data.replace("肉_", "")
        user_cart[user_id].append(selected_meat)

        # 發送配料選單
        send_toppings_menu(event)

    # 第三層：選擇配料
    elif postback_data.startswith("配料_"):
        selected_topping = postback_data.replace("配料_", "")
        user_cart[user_id].append(selected_topping)

        reply_text = f"你已加入 {selected_topping}！目前購物車內容：{', '.join(user_cart[user_id])}"
        line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=reply_text)])


def send_meat_menu(event, selected_main):
    """發送肉類選擇菜單（對應 Taco 或 Taco Bowl）"""
    carousel_template = CarouselTemplate(columns=[
        CarouselColumn(
            thumbnail_image_url="https://i.imgur.com/MAnWCCx.jpeg",
            title=f"選擇{selected_main}的肉類",
            text="請選擇你想要的肉類",
            actions=[
                PostbackAction(label="雞肉", data="肉_雞肉"),
                PostbackAction(label="牛肉", data="肉_牛肉"),
                PostbackAction(label="豬肉", data="肉_豬肉"),
            ]
        )
    ])

    line_bot_api.reply_message(
        event.reply_token,
        [TemplateSendMessage(alt_text="請選擇肉類", template=carousel_template)]
    )


def send_toppings_menu(event):
    """發送配料選擇菜單"""
    carousel_template = CarouselTemplate(columns=[
        CarouselColumn(
            thumbnail_image_url="https://i.imgur.com/MAnWCCx.jpeg",
            title="選擇你的配料",
            text="請選擇你想加的配料",
            actions=[
                PostbackAction(label="香菜 (+$10)", data="配料_香菜"),
                PostbackAction(label="酪梨醬 (+$20)", data="配料_酪梨醬"),
                PostbackAction(label="紅椒醬 (+$20)", data="配料_紅椒醬"),
            ]
        )
    ])

    line_bot_api.reply_message(
        event.reply_token,
        [TemplateSendMessage(alt_text="請選擇配料", template=carousel_template)]
    )



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)


