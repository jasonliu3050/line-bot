import sys
print(sys.path)

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import (
    MessageEvent, PostbackEvent, TextSendMessage, PostbackAction,
    CarouselTemplate, CarouselColumn, TemplateSendMessage
)
import os


from flask import Flask, request, jsonify

app = Flask(__name__)

# 商品價格表
menu = {
    "主餐": {"Taco": 100, "Taco Bowl": 120},
    "肉類": {"雞肉": 20, "牛肉": 30, "豬肉": 25},
    "配料": {"香菜": 10, "起司": 15, "酸奶": 10},
    "醬料": {"紅椒醬": 20, "酪梨醬": 20, "莎莎醬": 15},
    "飲料": {"可樂": 40, "紅茶": 35, "水": 10},
}

# 用戶購物車
user_cart = {}

# 初始化購物車
def initialize_cart(user_id):
    if user_id not in user_cart:
        user_cart[user_id] = {
            "items": [],
            "current_item": {"主餐": None, "肉類": None, "配料": [], "醬料": [], "飲料": None, "數量": 0},
        }


@app.route("/start", methods=["POST"])
def start_order():
    user_id = request.json.get("user_id")
    initialize_cart(user_id)
    return jsonify({"message": "歡迎點餐！請選擇主餐：Taco 或 Taco Bowl"})


@app.route("/select_main", methods=["POST"])
def select_main():
    user_id = request.json.get("user_id")
    main_course = request.json.get("main_course")

    if main_course not in menu["主餐"]:
        return jsonify({"error": "無效的主餐選項！請重新選擇 Taco 或 Taco Bowl"})

    user_cart[user_id]["current_item"]["主餐"] = main_course
    return jsonify({"message": f"你選擇了 {main_course}，請選擇肉類：雞肉、牛肉或豬肉"})


@app.route("/select_meat", methods=["POST"])
def select_meat():
    user_id = request.json.get("user_id")
    meat = request.json.get("meat")

    if meat not in menu["肉類"]:
        return jsonify({"error": "無效的肉類選項！請重新選擇"})

    user_cart[user_id]["current_item"]["肉類"] = meat
    return jsonify({"message": f"你選擇了 {meat}，請選擇配料（可多選）：香菜、起司、酸奶"})


@app.route("/select_toppings", methods=["POST"])
def select_toppings():
    user_id = request.json.get("user_id")
    toppings = request.json.get("toppings")  # 傳入列表，例如 ["香菜", "起司"]

    invalid_toppings = [topping for topping in toppings if topping not in menu["配料"]]
    if invalid_toppings:
        return jsonify({"error": f"無效的配料選項：{', '.join(invalid_toppings)}"})

    user_cart[user_id]["current_item"]["配料"].extend(toppings)
    return jsonify({"message": f"你選擇了 {', '.join(toppings)}，請選擇醬料：紅椒醬、酪梨醬或莎莎醬"})


@app.route("/select_sauce", methods=["POST"])
def select_sauce():
    user_id = request.json.get("user_id")
    sauce = request.json.get("sauce")

    if sauce not in menu["醬料"]:
        return jsonify({"error": "無效的醬料選項！請重新選擇"})

    user_cart[user_id]["current_item"]["醬料"].append(sauce)
    return jsonify({"message": f"你選擇了 {sauce}，請選擇飲料：可樂、紅茶或水"})


@app.route("/select_drink", methods=["POST"])
def select_drink():
    user_id = request.json.get("user_id")
    drink = request.json.get("drink")

    if drink not in menu["飲料"]:
        return jsonify({"error": "無效的飲料選項！請重新選擇"})

    user_cart[user_id]["current_item"]["飲料"] = drink
    return jsonify({"message": f"你選擇了 {drink}，請輸入數量"})


@app.route("/select_quantity", methods=["POST"])
def select_quantity():
    user_id = request.json.get("user_id")
    quantity = request.json.get("quantity")

    if not isinstance(quantity, int) or quantity <= 0:
        return jsonify({"error": "數量必須為正整數！"})

    user_cart[user_id]["current_item"]["數量"] = quantity
    # 將當前項目加入購物車
    user_cart[user_id]["items"].append(user_cart[user_id].pop("current_item"))
    user_cart[user_id]["current_item"] = {"主餐": None, "肉類": None, "配料": [], "醬料": [], "飲料": None, "數量": 0}

    return jsonify({"message": f"已將商品加入購物車！你想要選擇其他產品嗎？"})


@app.route("/checkout", methods=["POST"])
def checkout():
    user_id = request.json.get("user_id")

    if not user_cart[user_id]["items"]:
        return jsonify({"error": "購物車是空的！"})

    total = 0
    details = []
    for item in user_cart[user_id]["items"]:
        item_total = (
            menu["主餐"][item["主餐"]]
            + menu["肉類"][item["肉類"]]
            + sum(menu["配料"][topping] for topping in item["配料"])
            + sum(menu["醬料"][sauce] for sauce in item["醬料"])
            + menu["飲料"][item["飲料"]]
        ) * item["數量"]
        total += item_total
        details.append(f"{item['數量']} 份 {item['主餐']} (總金額: {item_total} 元)")

    discount = 0.9 if total >= 300 else 1.0
    final_price = int(total * discount)

    return jsonify({
        "message": "結帳完成！",
        "details": details,
        "總金額": total,
        "折扣後金額": final_price,
    })






if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
