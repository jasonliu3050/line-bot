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
                PostbackAction(label="Taco", data="主餐_Taco"),
                PostbackAction(label="Taco Bowl", data="主餐_TacoBowl")
            ]
        )
    ])

    line_bot_api.reply_message(
        event.reply_token,
        [TemplateSendMessage(alt_text="請選擇主餐", template=carousel_template)]
    )




@handler.add(PostbackEvent)
def handle_postback(event):
    user_id = event.source.user_id
    postback_data = event.postback.data

    # 初始化用戶購物車（每次點餐開始）
    if user_id not in user_cart:
        user_cart[user_id] = {"items": []}  # 訂單格式：{"items": [{"主餐": "Taco", "肉類": "雞肉", "配料": ["香菜"], "數量": 1}]}

    # 主餐選擇
    if postback_data.startswith("主餐_"):
        selected_main = postback_data.replace("主餐_", "")
        user_cart[user_id]["current_item"] = {"主餐": selected_main, "肉類": None, "配料": [], "數量": None}

        send_meat_menu(event, selected_main)

    # 肉類選擇
    elif postback_data.startswith("肉_"):
        selected_meat = postback_data.replace("肉_", "")
        user_cart[user_id]["current_item"]["肉類"] = selected_meat

        send_toppings_menu(event)

    # 配料選擇
    elif postback_data.startswith("配料_"):
        selected_topping = postback_data.replace("配料_", "")
        user_cart[user_id]["current_item"]["配料"].append(selected_topping)

        # 提供數量選擇選單
        send_quantity_menu(event)

    # 數量選擇
    elif postback_data.startswith("數量_"):
        selected_quantity = int(postback_data.replace("數量_", ""))
        user_cart[user_id]["current_item"]["數量"] = selected_quantity

        # 儲存完成的訂單項目
        user_cart[user_id]["items"].append(user_cart[user_id].pop("current_item"))

        # 回饋完成的訂單
        current_item = user_cart[user_id]["items"][-1]
        reply_text = (
            f"你已完成一份訂單：\n"
            f"{current_item['數量']} 份 {current_item['主餐']}，肉類：{current_item['肉類']}，"
            f"配料：{', '.join(current_item['配料'])}\n"
            f"目前購物車有 {len(user_cart[user_id]['items'])} 筆訂單。"
        )
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


def checkout_order(event, user_id):
    """結帳功能，顯示完整訂單與總金額"""
    if user_id not in user_cart or not user_cart[user_id]["items"]:
        reply_text = "你的購物車是空的，請先點餐！"
    else:
        order_details = ""
        total = 0
        for item in user_cart[user_id]["items"]:
            item_total = menu[item["主餐"]] * item["數量"] + sum(menu[topping] for topping in item["配料"])
            total += item_total
            order_details += (
                f"{item['數量']} 份 {item['主餐']}，肉類：{item['肉類']}，"
                f"配料：{', '.join(item['配料'])}，小計：{item_total} 元\n"
            )

        discount = 0.9 if total >= 200 else 1.0
        final_price = int(total * discount)
        reply_text = (
            f"你的訂單如下：\n{order_details}"
            f"總金額：{total} 元\n折扣後金額：{final_price} 元\n"
            f"請使用以下 Line Pay 付款連結：\nhttps://pay.line.me/123456789"
        )

        # 清空購物車
        user_cart[user_id]["items"] = []

    line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=reply_text)])


@handler.add(MessageEvent)
def handle_message(event):
    user_id = event.source.user_id
    user_message = event.message.text.strip()

    if user_message == "我要點餐":
        send_menu(event)
    elif user_message == "查看購物車":
        items = user_cart.get(user_id, {}).get("items", [])
        if items:
            cart_details = "\n".join(
                [f"{item['數量']} 份 {item['主餐']}，肉類：{item['肉類']}，配料：{', '.join(item['配料'])}" for item in items]
            )
            reply_text = f"你的購物車內有：\n{cart_details}"
        else:
            reply_text = "你的購物車是空的，請輸入『我要點餐』來開始點餐！"
        line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=reply_text)])
    elif user_message == "結帳":
        checkout_order(event, user_id)




if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)


