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


menu = {
    "雞肉Taco": 100,
    "牛肉Taco": 120,
    "豬肉Taco": 110,
    "香菜": 10,
    "酪梨醬": 20,
    "紅椒醬": 20,
    "莎莎醬": 15,
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
    user_id = event.source.user_id
    user_message = event.message.text.strip()

    if user_id not in user_cart:
        user_cart[user_id] = {"items": [], "current_item": None}

    if user_message == "查看購物車":
        if not user_cart[user_id]["items"]:
            reply_text = "你的購物車是空的，請輸入『我要點餐』來開始點餐！"
        else:
            cart_details = ""
            for item in user_cart[user_id]["items"]:
                cart_details += f"{item['數量']} 份 {item['主餐']}，配料：{', '.join(item['配料']) if item['配料'] else '無'}，飲料：{item['飲料'] if item['飲料'] else '無'}\n"

            reply_text = f"你的購物車內容：\n{cart_details}"
    elif user_message == "我要點餐":
        send_menu(event)
        return

    elif user_message == "結帳":
        checkout_order(event, user_id)
        return

    else:
        reply_text = "你好！請輸入『我要點餐』來開始點餐，或輸入『查看購物車』來查看你的訂單。"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))





def send_menu(event):
    """發送主選單（獨立的 Taco 和 Taco Bowl 選單）"""
    print("[DEBUG] 發送主選單")  # DEBUG LOG

    try:
        carousel_template = CarouselTemplate(columns=[
            CarouselColumn(
                thumbnail_image_url="https://i.imgur.com/MAnWCCx.jpeg",
                title="Taco",
                text="請選擇 Taco 作為主餐",
                actions=[
                    PostbackAction(label="豬肉Taco", data="主餐_塔可豬肉"),
                    PostbackAction(label="雞肉Taco", data="主餐_塔可雞肉"),
                    PostbackAction(label="牛肉Taco", data="主餐_塔可牛肉"),
                ]
            ),
            CarouselColumn(
                thumbnail_image_url="https://i.imgur.com/MAnWCCx.jpeg",
                title="Taco Bowl",
                text="請選擇 Taco Bowl 作為主餐",
                actions=[
                    PostbackAction(label="豬肉TacoBowl", data="主餐_塔可豬肉"),
                    PostbackAction(label="雞肉TacoBowl", data="主餐_塔可雞肉"),
                    PostbackAction(label="牛肉TacoBowl", data="主餐_塔可牛肉"),
                ]
            )
        ])

        line_bot_api.reply_message(
            event.reply_token,
            [TemplateSendMessage(alt_text="請選擇主餐", template=carousel_template)]
        )
        print("[DEBUG] 主選單發送成功")

    except Exception as e:
        print(f"[ERROR] 發送主選單時發生錯誤: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            [TextSendMessage(text="發送主選單時發生錯誤，請稍後再試！")]
        )





def handle_postback(event):
    try:
        user_id = event.source.user_id
        postback_data = event.postback.data

        # 確保用戶有購物車資料
        if user_id not in user_cart:
            user_cart[user_id] = {"items": [], "current_item": None}

        # 確保 current_item 存在
        if user_cart[user_id]["current_item"] is None:
            user_cart[user_id]["current_item"] = {
                "主餐": None,
                "套餐": None,
                "配料": [],
                "飲料": None,
                "數量": None
            }

        current_item = user_cart[user_id]["current_item"]

        # 🏆【修正1】主餐選擇：這裡不能直接覆蓋 current_item，應該修改現有物件
        if postback_data.startswith("主餐_塔可"):
            selected_main = postback_data.replace("主餐_", "")
            current_item["主餐"] = selected_main
            send_singleormeal_menu(event)

        elif postback_data.startswith("singleormeal_"):
            if current_item["主餐"]:  # 確保已經有主餐
                selected_type = postback_data.replace("singleormeal_", "")
                current_item["套餐"] = selected_type
                send_side_menu(event)
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="⚠️ 請先選擇主餐！"))

        elif postback_data.startswith("side_"):
            if current_item["主餐"]:
                selected_side = postback_data.replace("side_", "")
                current_item["配料"].append(selected_side)
                send_drink_menu(event)
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="⚠️ 請先選擇主餐！"))

        elif postback_data.startswith("drink_"):
            if current_item["主餐"]:
                selected_drink = postback_data.replace("drink_", "")
                current_item["飲料"] = selected_drink
                send_quantity_menu(event)
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="⚠️ 請先選擇主餐！"))

        elif postback_data.startswith("quantity_"):
            if current_item["主餐"]:
                selected_quantity = int(postback_data.replace("quantity_", ""))
                current_item["數量"] = selected_quantity  # 記錄數量

                # ✅ 【修正2】確保 `current_item` 被正確存入購物車
                user_cart[user_id]["items"].append(current_item.copy())  # **使用 `.copy()` 避免清空問題**
                user_cart[user_id]["current_item"] = None  # 清除當前商品，準備下一次點餐

                reply_text = "✅ 已將餐點加入購物車！\n輸入『查看購物車』來查看訂單，或輸入『結帳』完成訂單。"
            else:
                reply_text = "⚠️ 請先選擇主餐！"

            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

    except Exception as e:
        print(f"[ERROR] handle_postback() 錯誤: {e}")
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="⚠️ 發生錯誤，請稍後再試！"))







def send_singleormeal_menu(event):
   
    print("[DEBUG] 發送")  # DEBUG LOG

    try:
        carousel_template = CarouselTemplate(columns=[
            CarouselColumn(
                thumbnail_image_url="https://i.imgur.com/MAnWCCx.jpeg",
                title="side",
                text="請選擇 side",
                actions=[
                    PostbackAction(label="單點", data="singleormeal_單點"),
                    PostbackAction(label="套餐", data="singleormeal_套餐")
                ]
            )
        ])

        line_bot_api.reply_message(
            event.reply_token,
            [TemplateSendMessage(alt_text="請選擇singleormeal", template=carousel_template)]
        )
        print("[DEBUG] singleormeal發送成功")

    except Exception as e:
        print(f"[ERROR] 發送singleormeal_時發生錯誤: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            [TextSendMessage(text="發送singleormeal_時發生錯誤，請稍後再試！")]
        )






def send_quantity_menu(event):
    try:
        message = TextSendMessage(text="請輸入您想要的數量（例如：2）")
        line_bot_api.reply_message(event.reply_token, message)
    except Exception as e:
        print(f"[ERROR] 發送數量請求時出現錯誤: {e}")






def send_side_menu(event):
   
    print("[DEBUG] 發送")  # DEBUG LOG

    try:
        carousel_template = CarouselTemplate(columns=[
            CarouselColumn(
                thumbnail_image_url="https://i.imgur.com/MAnWCCx.jpeg",
                title="side",
                text="請選擇 side",
                actions=[
                    PostbackAction(label="玉米脆片", data="side_玉米脆片"),
                    PostbackAction(label="墨西哥風味飯", data="side_墨西哥風味飯"),
                    PostbackAction(label="無", data="side_無"),
                ]
            )
        ])

        line_bot_api.reply_message(
            event.reply_token,
            [TemplateSendMessage(alt_text="請選擇side", template=carousel_template)]
        )
        print("[DEBUG] side發送成功")

    except Exception as e:
        print(f"[ERROR] 發送side時發生錯誤: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            [TextSendMessage(text="發送side時發生錯誤，請稍後再試！")]
        )






def send_drink_menu(event):
   
    print("[DEBUG] 發送")  # DEBUG LOG

    try:
        carousel_template = CarouselTemplate(columns=[
            CarouselColumn(
                thumbnail_image_url="https://i.imgur.com/MAnWCCx.jpeg",
                title="drink",
                text="請選擇 drink",
                actions=[
                    PostbackAction(label="咖啡", data="drink_咖啡"),
                ]
            )
        ])
        carousel_template = CarouselTemplate(columns=[
            CarouselColumn(
                thumbnail_image_url="https://i.imgur.com/MAnWCCx.jpeg",
                title="drink",
                text="請選擇 drink",
                actions=[
                    PostbackAction(label="紅茶", data="drink_紅茶"),
                ]
            )
        ])

        line_bot_api.reply_message(
            event.reply_token,
            [TemplateSendMessage(alt_text="請選擇drink", template=carousel_template)]
        )
        print("[DEBUG] side發送成功")

    except Exception as e:
        print(f"[ERROR] 發送drink時發生錯誤: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            [TextSendMessage(text="發送drink時發生錯誤，請稍後再試！")]
        )








def checkout_order(event, user_id):
    if user_id not in user_cart or not user_cart[user_id]["items"]:
        reply_text = "你的購物車是空的，請先點餐！"
    else:
        order_details = ""
        total = 0
        for item in user_cart[user_id]["items"]:
            item_total = menu[item["主餐"]] * item["數量"]
            item_total += sum(menu.get(topping, 0) for topping in item["配料"])
            total += item_total
            order_details += (
                f"{item['數量']} 份 {item['主餐']}，配料：{', '.join(item['配料']) if item['配料'] else '無'}，"
                f"飲料：{item['飲料'] if item['飲料'] else '無'}，小計：{item_total} 元\n"
            )

        discount = 0.9 if total >= 200 else 1.0
        final_price = int(total * discount)
        reply_text = (
            f"你的訂單如下：\n{order_details}"
            f"總金額：{total} 元\n折扣後金額：{final_price} 元\n"
            f"請使用以下 Line Pay 付款連結：\nhttps://pay.line.me/123456789"
        )

        # **只清空 items，保留 user_cart 結構**
        user_cart[user_id]["items"] = []

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))



    




if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
