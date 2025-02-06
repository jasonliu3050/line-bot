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
    """處理用戶文字輸入"""
    user_id = event.source.user_id
    user_message = event.message.text.strip()

    if user_id not in user_cart:
        user_cart[user_id] = {"items": [], "current_item": None}

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
    """發送主選單（獨立的 Taco 和 Taco Bowl 選單）"""
    print("[DEBUG] 發送主選單")  # DEBUG LOG

    try:
        carousel_template = CarouselTemplate(columns=[
            CarouselColumn(
                thumbnail_image_url="https://i.imgur.com/MAnWCCx.jpeg",
                title="Taco",
                text="請選擇 Taco 作為主餐",
                actions=[
                    PostbackAction(label="豬肉Taco", data="選擇_塔可豬肉Taco"),
                    PostbackAction(label="雞肉Taco", data="選擇_塔可雞肉Taco"),
                    PostbackAction(label="牛肉Taco", data="選擇_塔可牛肉Taco"),
                ]
            ),
            CarouselColumn(
                thumbnail_image_url="https://i.imgur.com/MAnWCCx.jpeg",
                title="Taco Bowl",
                text="請選擇 Taco Bowl 作為主餐",
                actions=[
                    PostbackAction(label="豬肉TacoBowl", data="選擇_塔可豬肉TacoBowl"),
                    PostbackAction(label="雞肉TacoBowl", data="選擇_塔可雞肉TacoBowl"),
                    PostbackAction(label="牛肉TacoBowl", data="選擇_塔可牛肉TacoBowl"),
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





@handler.add(PostbackEvent)
def handle_postback(event):
    try:
        user_id = event.source.user_id
        postback_data = event.postback.data

        # 確保購物車初始化
        if user_id not in user_cart:
            user_cart[user_id] = {"items": [], "current_item": None}

        current_item = user_cart[user_id]["current_item"]

        # ✅ **步驟 1: 選擇塔可或塔可碗 + 口味**
        if postback_data.startswith("選擇_塔可"): 
            selected_main = postback_data.replace("選擇_", "")
            user_cart[user_id]["current_item"] = {
                "主餐": selected_main,
                "套餐": False,
                "配料": [],
                "飲料": None,
                "數量": None
            }
            send_single_or_meal(event)
            return

        # ✅ **步驟 2: 單點或套餐選擇**
        elif postback_data.startswith("選擇_單點"): 
            if not current_item:
                line_bot_api.reply_message(event.reply_token, [TextSendMessage(text="請先選擇塔可或塔可碗！")])
                return
            user_cart[user_id]["current_item"]["套餐"] = False
            send_quantity_menu(event)
            return

        elif postback_data.startswith("選擇_套餐"): 
            if not current_item:
                line_bot_api.reply_message(event.reply_token, [TextSendMessage(text="請先選擇塔可或塔可碗！")])
                return
            user_cart[user_id]["current_item"]["套餐"] = True
            send_side_and_drink_menu(event)
            return

        # ✅ **步驟 3: 選擇套餐的 Side & 飲料**
        elif postback_data.startswith("選擇_Side_"):
            selected_side = postback_data.replace("選擇_Side_", "")
            user_cart[user_id]["current_item"]["配料"].append(selected_side)
            send_drink_menu(event)
            return

        elif postback_data.startswith("選擇_飲料_"):
            selected_drink = postback_data.replace("選擇_飲料_", "")
            user_cart[user_id]["current_item"]["飲料"] = selected_drink
            send_quantity_menu(event)
            return

        # ✅ **步驟 4: 選擇數量**
        elif postback_data.startswith("數量_"):
            selected_quantity = int(postback_data.replace("數量_", ""))
            user_cart[user_id]["current_item"]["數量"] = selected_quantity
            user_cart[user_id]["items"].append(user_cart[user_id]["current_item"])
            user_cart[user_id]["current_item"] = None
            ask_if_need_more(event)
            return

        # ✅ **步驟 5: 詢問是否還需要其他東西**
        elif postback_data == "更多_是":
            send_menu(event)
            return

        elif postback_data == "更多_否":
            checkout_order(event, user_id)
            return
    
    except Exception as e:
        print(f"[ERROR] handle_postback() 錯誤: {e}")
        line_bot_api.reply_message(event.reply_token, [TextSendMessage(text="發生錯誤，請稍後再試！")])






def send_meat_menu(event, selected_main):
    """發送肉類選擇菜單（對應 Taco 或 Taco Bowl）"""
    print(f"[DEBUG] 發送肉類選單給用戶，主餐: {selected_main}")  # **DEBUG LOG**
    
    try:
        carousel_template = CarouselTemplate(columns=[
            CarouselColumn(
                thumbnail_image_url="https://i.imgur.com/MAnWCCx.jpeg",  # 確保圖片 URL 可用
                title=f"選擇 {selected_main} 的肉類",
                text="請選擇你想要的肉類：",
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

    except Exception as e:
        print(f"[ERROR] 發送肉類選單時出現錯誤: {e}")  # **輸出錯誤資訊**





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



def send_sauce_menu(event):
    """發送醬料選擇菜單"""
    print("[DEBUG] 發送醬料選單")  # DEBUG LOG
    
    try:
        # 構建 CarouselTemplate
        carousel_template = CarouselTemplate(columns=[
            CarouselColumn(
                thumbnail_image_url="https://i.imgur.com/MAnWCCx.jpeg",  # 確保圖片可用
                title="選擇醬料",
                text="最多可選三種醬料：",
                actions=[
                    PostbackAction(label="紅椒醬 (+$20)", data="醬料_紅椒醬"),
                    PostbackAction(label="酪梨醬 (+$20)", data="醬料_酪梨醬"),
                    PostbackAction(label="莎莎醬 (+$15)", data="醬料_莎莎醬"),
                ]
            )
        ])
        
        # 發送消息
        line_bot_api.reply_message(
            event.reply_token,
            [TemplateSendMessage(alt_text="請選擇醬料", template=carousel_template)]
        )

    except Exception as e:
        # 捕獲並打印錯誤信息
        print(f"[ERROR] 發送醬料選單時出現錯誤: {e}")  # DEBUG LOG
        line_bot_api.reply_message(
            event.reply_token,
            [TextSendMessage(text="發送醬料選單時發生錯誤，請稍後再試！")]
        )




def checkout_order(event, user_id):
    """結帳功能，顯示完整訂單與總金額"""
    if user_id not in user_cart or not user_cart[user_id]["items"]:
        reply_text = "你的購物車是空的，請先點餐！"
    else:
        order_details = ""
        total = 0
        for item in user_cart[user_id]["items"]:
            # 主餐价格
            item_total = menu[item["主餐"]] * item["數量"]
            
            # 加入配料价格
            item_total += sum(menu.get(topping, 0) for topping in item["配料"])
            
            # 加入醬料价格
            item_total += sum(menu.get(sauce, 0) for sauce in item["醬料"])
            
            total += item_total
            order_details += (
                f"{item['數量']} 份 {item['主餐']}，肉類：{item['肉類']}，"
                f"配料：{', '.join(item['配料'])}，醬料：{', '.join(item['醬料'])}，小計：{item_total} 元\n"
            )

        # 折扣处理
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




if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
