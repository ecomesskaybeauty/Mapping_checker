import os
import time
import threading
import re
import requests
from bs4 import BeautifulSoup
from flask import Flask

BOT_TOKEN = os.getenv("8629112249:AAH6MebXra4Fyc9BJuSd8boUItObFVQJY9U")
CHAT_ID = os.getenv("1250820754")

CHECK_EVERY_SECONDS = 300  # 5 minutes

PRODUCTS = {
    "White Chocolate Wax 800ml": "B0762QTS6T",
    "Rica Aloe 800ml": "B00UAFNCS2",
    "Rica Brazilian Avocado": "B00BH4Y4FA",
    "Rica Liposoluble White": "B084VQXFQP"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-IN,en;q=0.9",
}

app = Flask(__name__)

last_data = {}


def telegram_send(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": message
        })
        print("Telegram:", r.text)
    except Exception as e:
        print("Telegram error:", e)


def fetch_product(asin):
    url = f"https://www.amazon.in/dp/{asin}"
    r = requests.get(url, headers=HEADERS, timeout=25)
    soup = BeautifulSoup(r.text, "html.parser")

    # PRICE
    price = None
    text = soup.get_text(" ", strip=True)
    m = re.search(r"₹\s*([\d,]+)", text)
    if m:
        price = float(m.group(1).replace(",", ""))

    # SELLER
    seller = None
    merchant = soup.find(id="merchant-info")
    if merchant:
        t = merchant.get_text(" ", strip=True)
        m2 = re.search(r"Sold by\s+([^\.,]+)", t)
        if m2:
            seller = m2.group(1)

    return price, seller


def monitor():
    telegram_send("✅ Multi-product monitor started")

    while True:
        try:
            for name, asin in PRODUCTS.items():
                price, seller = fetch_product(asin)

                print(name, price, seller)

                if name not in last_data:
                    last_data[name] = {
                        "price": price,
                        "seller": seller
                    }
                    continue

                old_price = last_data[name]["price"]
                old_seller = last_data[name]["seller"]

                # PRICE DROP
                if price and old_price and price < old_price:
                    telegram_send(
                        f"📉 PRICE DROP!\n{name}\nOld: ₹{old_price}\nNew: ₹{price}\nSeller: {seller}"
                    )

                # SELLER CHANGE
                if seller and old_seller and seller != old_seller:
                    telegram_send(
                        f"🛒 SELLER CHANGED!\n{name}\nOld: {old_seller}\nNew: {seller}\nPrice: ₹{price}"
                    )

                last_data[name]["price"] = price
                last_data[name]["seller"] = seller

        except Exception as e:
            print("Monitor error:", e)

        time.sleep(CHECK_EVERY_SECONDS)


@app.route("/")
def home():
    return "Amazon multi monitor running"


if __name__ == "__main__":
    thread = threading.Thread(target=monitor)
    thread.daemon = True
    thread.start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
