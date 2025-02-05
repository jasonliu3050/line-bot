import os
from flask import Flask, request, abort
from linebot.v3.messaging import LineBotApi, MessagingApi
from linebot.v3.messaging.models.message import TextMessage  # ✅ 修正 `TextSendMessage` 为 `TextMessage`
from linebot.v3.webhook import WebhookHandler, PostbackEvent, MessageEvent
from linebot.v3.messaging.models import TemplateSendMessage, CarouselTemplate, CarouselColumn, PostbackAction


# ✅ 先正确读取环境变量
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

# ✅ 初始化 Flask 应用
app = Flask(__name__)

# ✅ 正确初始化 MessagingApi（v3）
messaging_api = MessagingApi(channel_access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)


# 完整分類菜單
menu = {
    "主餐": {
        "雞肉Taco": 100,
        "牛肉Taco": 120,
        "豬肉Taco": 110,
        "雞肉Taco Bowl": 130,
        "牛肉Taco Bowl": 150,
        "豬肉Taco Bowl": 140
    },
    "配料": {
        "香菜": 10,
        "洋蔥": 10,
        "番茄": 10,
        "生菜": 10,
        "玉米": 15
    },
    "醬汁": {
        "莎莎醬": 15,
        "酪梨醬": 20,
        "紅椒醬": 20,
        "酸奶醬": 15
    },
    "點心": {
        "玉米脆片": 50,
        "墨西哥風味飯": 60,
        "起司棒": 55,
        "炸薯條": 45
    },
    "飲料": {
        "咖啡": 40,
        "紅茶": 35,
        "柳橙汁": 45,
        "可樂": 30,
        "檸檬水": 25
    }
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
    """發送主選單（獨立的 Taco 和 Taco Bowl 選單）"""
    print("[DEBUG] 發送主選單")  # DEBUG LOG
    
    try:
        carousel_template = CarouselTemplate(columns=[
            CarouselColumn(
                thumbnail_image_url="https://i.imgur.com/MAnWCCx.jpeg",
                title="Taco",
                text="請選擇 Taco 作為主餐",
                actions=[
                    PostbackAction(label="選擇 Taco", data="主餐_Taco")
                ]
            ),
            CarouselColumn(
                thumbnail_image_url="https://i.imgur.com/MAnWCCx.jpeg",
                title="Taco Bowl",
                text="請選擇 Taco Bowl 作為主餐",
                actions=[
                    PostbackAction(label="選擇 Taco Bowl", data="主餐_TacoBowl")
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

        # **DEBUG LOG**
        print(f"[DEBUG] 收到 Postback 資料: {postback_data}")
        print(f"[DEBUG] 用戶 ID: {user_id}")

        # ✅ 初始化購物車
        if user_id not in user_cart:
            user_cart[user_id] = {"items": [], "current_item": None}

        # ✅ **主餐選擇**
        if postback_data.startswith("主餐_"):
            selected_main = postback_data.replace("主餐_", "")
            user_cart[user_id]["current_item"] = {
                "主餐": selected_main,
                "肉類": None,
                "配料": [],
                "醬料": [],
                "數量": None
            }
            print(f"[DEBUG] 用戶選擇主餐: {selected_main}")
            send_meat_menu(event, selected_main)
            return

        # ✅ **肉類選擇**
        elif postback_data.startswith("肉_"):
            selected_meat = postback_data.replace("肉_", "")

            if not user_cart[user_id]["current_item"]:
                print("[ERROR] 用戶未選擇主餐，無法選擇肉類！")
                line_bot_api.reply_message(event.reply_token, [TextSendMessage(text="請先選擇主餐！")])
                return

            user_cart[user_id]["current_item"]["肉類"] = selected_meat
            print(f"[DEBUG] 用戶選擇肉類: {selected_meat}")
            send_toppings_menu(event)
            return

        # ✅ **配料選擇**
        elif postback_data.startswith("配料_"):
            selected_topping = postback_data.replace("配料_", "")

            if not user_cart[user_id]["current_item"]:
                print("[ERROR] 用戶未選擇主餐，無法選擇配料！")
                line_bot_api.reply_message(event.reply_token, [TextSendMessage(text="請先選擇主餐與肉類！")])
                return

            user_cart[user_id]["current_item"]["配料"].append(selected_topping)
            print(f"[DEBUG] 用戶選擇配料: {selected_topping}")
            send_sauce_menu(event)
            return

        # ✅ **醬料選擇**
        elif postback_data.startswith("醬料_"):
            selected_sauce = postback_data.replace("醬料_", "")

            if not user_cart[user_id]["current_item"]:
                print("[ERROR] 用戶未選擇主餐，無法選擇醬料！")
                line_bot_api.reply_message(event.reply_token, [TextSendMessage(text="請先選擇主餐與肉類！")])
                return

            # 限制最多 3 種醬料
            if len(user_cart[user_id]["current_item"]["醬料"]) >= 3:
                print("[ERROR] 已達醬料選擇上限")
                line_bot_api.reply_message(event.reply_token, [TextSendMessage(text="最多可選 3 種醬料！")])
                return

            user_cart[user_id]["current_item"]["醬料"].append(selected_sauce)
            print(f"[DEBUG] 用戶選擇醬料: {selected_sauce}")

            # **達到醬料上限，進入數量選擇**
            if len(user_cart[user_id]["current_item"]["醬料"]) == 3:
                send_quantity_menu(event)
            else:
                send_sauce_menu(event)  # 允許繼續選擇醬料
            return

        # ✅ **數量選擇**
        elif postback_data.startswith("數量_"):
            try:
                selected_quantity = int(postback_data.replace("數量_", ""))

                if user_id not in user_cart:
                    user_cart[user_id] = {"items": [], "current_item": None}

                if not user_cart[user_id]["current_item"]:
                    print("[ERROR] current_item 未初始化，無法選擇數量！")
                    line_bot_api.reply_message(event.reply_token, [TextSendMessage(text="請先選擇主餐與肉類！")])
                    return

                if not user_cart[user_id]["current_item"].get("肉類"):
                    print("[ERROR] 肉類未選擇！")
                    line_bot_api.reply_message(event.reply_token, [TextSendMessage(text="請先選擇肉類，再選擇數量！")])
                    return

                # ✅ 設定數量
                user_cart[user_id]["current_item"]["數量"] = selected_quantity

                # ✅ 把 current_item 加入 items 並清空 current_item
                user_cart[user_id]["items"].append(user_cart[user_id]["current_item"])
                user_cart[user_id]["current_item"] = None  # 清空 current_item，避免影響下次點餐

                # ✅ 获取完整订单信息，防止 KeyError
                current_item = user_cart[user_id]["items"][-1]
                主餐 = current_item.get("主餐", "未知主餐")
                肉類 = current_item.get("肉類", "未知肉類")
                配料 = current_item.get("配料", [])
                醬料 = current_item.get("醬料", [])

                # ✅ 生成回應訊息
                reply_text = (
                    f"你已完成一份訂單：\n"
                    f"{selected_quantity} 份 {主餐}，肉類：{肉類}，"
                    f"配料：{', '.join(配料) if 配料 else '無'}，"
                    f"醬料：{', '.join(醬料) if 醬料 else '無'}\n"
                    f"目前購物車內有 {len(user_cart[user_id]['items'])} 筆訂單。"
                )

                line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=reply_text)])

            except ValueError:
                print("[ERROR] 無效的數量數據")
                line_bot_api.reply_message(
                    event.reply_token, [TextSendMessage(text="請選擇有效的數量！")]
                )
            except Exception as e:
                print(f"[ERROR] 在 handle_postback 數量選擇時發生錯誤: {e}")
                line_bot_api.reply_message(
                    event.reply_token, [TextSendMessage(text="發生錯誤，請稍後再試！")]
                )
            return

    except Exception as e:
        print(f"[ERROR] 在 handle_postback 中發生錯誤: {e}")
        line_bot_api.reply_message(
            event.reply_token, [TextSendMessage(text="發生錯誤，請稍後再試！")]
        )







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
    if user_id not in user_cart or "items" not in user_cart[user_id] or not user_cart[user_id]["items"]:
        reply_text = "你的購物車是空的，請先點餐！"
    else:
        order_details = ""
        total = 0

        for item in user_cart[user_id]["items"]:
            主餐 = item.get("主餐", "")
            肉類 = item.get("肉類", "")
            配料 = item.get("配料", [])
            醬料 = item.get("醬料", [])
            數量 = item.get("數量", 1)

            # **主餐價格**
            item_total = menu["主餐"].get(主餐, 0) * 數量

            # **肉類價格**（假設肉類價格與 Taco 相同）
            if 肉類:
                item_total += menu["主餐"].get(f"{肉類}Taco", 0) * 數量

            # **配料價格**
            item_total += sum(menu["配料"].get(topping, 0) for topping in 配料) * 數量

            # **醬料價格**
            item_total += sum(menu["醬汁"].get(sauce, 0) for sauce in 醬料) * 數量

            total += item_total
            order_details += (
                f"{數量} 份 {主餐}，肉類：{肉類}，"
                f"配料：{', '.join(配料) if 配料 else '無'}，"
                f"醬料：{', '.join(醬料) if 醬料 else '無'}，"
                f"小計：{item_total} 元\n"
            )

        # **折扣计算**
        discount = 0.9 if total >= 200 else 1.0
        final_price = int(total * discount)

        reply_text = (
            f"你的訂單如下：\n{order_details}"
            f"總金額：{total} 元\n"
            f"折扣後金額：{final_price} 元\n"
            f"請使用以下 Line Pay 付款連結：\nhttps://pay.line.me/123456789"
        )

        # **清空購物車**
        user_cart[user_id] = {"items": []}

    line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=reply_text)])


       



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
