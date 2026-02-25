import os
import time
import requests
import threading
from bs4 import BeautifulSoup
from flask import Flask

app = Flask(__name__)

BOT_TOKEN = os.getenv("8629112249:AAH6MebXra4Fyc9BJuSd8boUItObFVQJY9U")
CHAT_ID = os.getenv("1250820754")

PRODUCTS = [
    "https://www.amazon.in/dp/B0762QTS6T",
    "https://www.amazon.in/dp/B00UAFNCS2",
    "https://www.amazon.in/dp/B00BH4Y4FA",
    "https://www.amazon.in/dp/B084VQXFQP"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-IN,en;q=0.9"
}

previous_data = {}

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

def fetch_product(url):
    r = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")

    title = soup.find(id="productTitle")
    price = soup.find("span", class_="a-price-whole")
    seller = soup.find(id="sellerProfileTriggerId")

    title = title.get_text(strip=True) if title else "N/A"
    price = price.get_text(strip=True) if price else "N/A"
    seller = seller.get_text(strip=True) if seller else "Amazon"

    return title, price, seller

def monitor():
    send_telegram("🔥 Amazon Monitor Started")

    while True:
        try:
            for url in PRODUCTS:
                title, price, seller = fetch_product(url)

                if url not in previous_data:
                    previous_data[url] = (price, seller)
                else:
                    old_price, old_seller = previous_data[url]

                    if price != old_price:
                        send_telegram(
                            f"💰 PRICE CHANGE\n{title}\nOld: {old_price}\nNew: {price}"
                        )

                    if seller != old_seller:
                        send_telegram(
                            f"🏪 SELLER CHANGE\n{title}\nOld: {old_seller}\nNew: {seller}"
                        )

                    previous_data[url] = (price, seller)

            time.sleep(300)

        except Exception as e:
            print("Error:", e)
            time.sleep(60)

@app.route("/")
def home():
    return "Amazon Monitor Running"

if __name__ == "__main__":
    threading.Thread(target=monitor).start()
    app.run(host="0.0.0.0", port=10000)
