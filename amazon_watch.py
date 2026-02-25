import os
import time
import json
import threading
import requests
from bs4 import BeautifulSoup
from flask import Flask

ASIN = os.getenv("B084VQXFQP")
BOT_TOKEN = os.getenv("8629112249:AAEe2IIhmu7kHGUMmkJvgCMwsNJ1m_O_Ptw")
CHAT_ID = os.getenv("1250820754")

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-IN,en;q=0.9",
}

STATE_FILE = "last_sellers.json"

app = Flask(__name__)

def telegram_send(msg):
    try:
        url = "https://api.telegram.org/bot" + str(BOT_TOKEN) + "/sendMessage"
        response = requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": msg
        })
        print("Telegram response:", response.text)
    except Exception as e:
        print("Telegram error:", e)
def fetch_offers_page():
    url = f"https://www.amazon.in/gp/offer-listing/{ASIN}"
    r = requests.get(url, headers=HEADERS)
    return r.text

def parse_sellers(html):
    soup = BeautifulSoup(html, "html.parser")
    sellers = {}
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "seller=" in href:
            seller_id = href.split("seller=")[1].split("&")[0]
            name = a.get_text(strip=True)
            sellers[seller_id] = name
    return sellers

def monitor():
    print("Monitor thread started")
    try:
        telegram_send("Amazon monitoring started")
        print("Startup message sent")
    except Exception as e:
        print("Telegram startup error:", e)

    prev = {}

    while True:
        try:
            html = fetch_offers_page()
            current = parse_sellers(html)

            if current != prev:
                telegram_send("Seller change detected")
                print("Seller change alert sent")
                prev = current

        except Exception as e:
            print("Monitoring error:", e)

        time.sleep(300)
@app.route("/")
def home():
    return "Amazon Monitor Running"

if __name__ == "__main__":
    monitor_thread = threading.Thread(target=monitor)
    monitor_thread.daemon = True
    monitor_thread.start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
