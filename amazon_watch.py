import os, time, json
import requests
from bs4 import BeautifulSoup

ASIN = os.getenv("ASIN", "B084VQXFQP")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8629112249:AAEe2IIhmu7kHGUMmkJvgCMwsNJ1m_O_Ptw")
CHAT_ID = os.getenv("CHAT_ID", "1250820754")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122 Safari/537.36",
    "Accept-Language": "en-IN,en;q=0.9",
}

STATE_FILE = "last_sellers.json"

def telegram_send(msg: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=20)

def fetch_offers_page(asin: str) -> str:
    # Offers listing page (often better than /dp/ for seller detection)
    url = f"https://www.amazon.in/gp/offer-listing/{asin}"
    r = requests.get(url, headers=HEADERS, timeout=25)
    r.raise_for_status()
    return r.text

def parse_sellers(html: str):
    soup = BeautifulSoup(html, "html.parser")

    sellers = []

    # Seller links often contain "seller=" in href
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "seller=" in href:
            name = a.get_text(" ", strip=True)
            # Extract seller id
            # example: ...?seller=AXXXXXXXX&...
            seller_id = href.split("seller=")[1].split("&")[0]
            if name and seller_id:
                sellers.append({"id": seller_id, "name": name})

    # Deduplicate by seller id
    uniq = {}
    for s in sellers:
        uniq[s["id"]] = s["name"]
    return uniq  # {seller_id: seller_name}

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def main():
    telegram_send("✅ Amazon monitoring started")

    prev = load_state()

    while True:
        try:
            html = fetch_offers_page(ASIN)
            current = parse_sellers(html)

            if current != prev:
                added = set(current.keys()) - set(prev.keys())
                removed = set(prev.keys()) - set(current.keys())

                lines = ["🚨 Seller change detected!"]

                if added:
                    lines.append("✅ Added:")
                    for sid in added:
                        lines.append(f"- {current.get(sid,'(name unknown)')} | seller={sid}")

                if removed:
                    lines.append("❌ Removed:")
                    for sid in removed:
                        lines.append(f"- {prev.get(sid,'(name unknown)')} | seller={sid}")

                telegram_send("\n".join(lines))
                prev = current
                save_state(prev)

        except Exception as e:
            telegram_send(f"⚠️ Error: {type(e).__name__}: {e}")

        time.sleep(300)  # 5 minutes

if __name__ == "__main__":
    main()
