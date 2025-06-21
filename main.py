import telebot
import cloudscraper
from bs4 import BeautifulSoup
import time
import threading
import os
import json
import re
from datetime import datetime

# Telegram Setup
tele_token = os.environ.get("TELE")
TOKEN = str(tele_token)
print("Telegram Bot Token:", TOKEN)
USER_ID = 6264741586
bot = telebot.TeleBot(TOKEN)

# URLs
incredible_url = "https://www.incredible.co.za/soundcore-space-one-headphone-black"
amazon_short_url = "https://amzn.eu/d/73fgzvN"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/114.0.0.0 Safari/537.36"
}

# ========================== Price Utilities ==========================
def load_price_data():
    if os.path.exists("price_data.json"):
        with open("price_data.json", "r") as f:
            return json.load(f)
    return {}

def save_price_data(data):
    with open("price_data.json", "w") as f:
        json.dump(data, f)

def extract_numeric_price(price_str):
    if not price_str or not isinstance(price_str, str):
        return float('inf')
    price_str = re.sub(r'[^\d.,]', '', price_str).replace(",", "")
    try:
        return float(price_str)
    except:
        return float('inf')

# ========================== Scrapers with retries ==========================
def get_incredible_price(retries=3, delay=3):
    scraper = cloudscraper.create_scraper()
    for attempt in range(1, retries + 1):
        try:
            response = scraper.get(incredible_url, headers=HEADERS)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                price_elements = soup.find_all("span", class_="price")
                if len(price_elements) >= 3:
                    third_price = price_elements[2].text.strip()
                    print(f"✅ Incredible Price Found: {third_price}")
                    return third_price
                else:
                    print(f"❌ Less than 3 price elements found (Attempt {attempt})")
            else:
                print(f"❌ Failed to fetch Incredible page. Status {response.status_code} (Attempt {attempt})")
        except Exception as e:
            print(f"❌ Error fetching Incredible price (Attempt {attempt}): {e}")

        if attempt < retries:
            time.sleep(delay)
    return "Price not found"

def get_amazon_price(short_url, retries=3, delay=3):
    scraper = cloudscraper.create_scraper()
    selectors = [
        '#priceblock_ourprice',
        '#priceblock_dealprice',
        '#priceblock_saleprice',
        '.a-price .a-offscreen',
        'span[data-a-color="price"] span.a-offscreen'
    ]
    for attempt in range(1, retries + 1):
        try:
            response = scraper.get(short_url, allow_redirects=True, headers=HEADERS)
            product_url = response.url

            res = scraper.get(product_url, headers=HEADERS)
            soup = BeautifulSoup(res.content, "html.parser")

            for selector in selectors:
                el = soup.select_one(selector)
                if el and el.text.strip():
                    price = el.text.strip()
                    print(f"✅ Amazon Price Found: {price}")
                    return price

            print(f"❌ Amazon price not found with selectors (Attempt {attempt})")
        except Exception as e:
            print(f"❌ Amazon exception (Attempt {attempt}): {e}")

        if attempt < retries:
            time.sleep(delay)
    return "Price not found"

# ========================== Periodic Price Check (Every 2 Hours) ==========================
def run_periodic_price_check():
    while True:
        try:
            inc_price_raw = get_incredible_price()
            ama_price_raw = get_amazon_price(amazon_short_url)
            inc_price_val = extract_numeric_price(inc_price_raw)
            ama_price_val = extract_numeric_price(ama_price_raw)

            prev_prices = load_price_data()
            prev_inc = prev_prices.get("incredible", float('inf'))
            prev_ama = prev_prices.get("amazon", float('inf'))

            messages = []

            if inc_price_val < prev_inc:
                messages.append(
                    f"💰 *Incredible Price Dropped!*\nWas: `{prev_inc}` → Now: `{inc_price_raw}`\n"
                    f"🛍️ [Soundcore Space One - Incredible]({incredible_url})"
                )
                prev_prices["incredible"] = inc_price_val

            if ama_price_val < prev_ama:
                messages.append(
                    f"💸 *Amazon Price Dropped!*\nWas: `{prev_ama}` → Now: `{ama_price_raw}`\n"
                    f"🎧 [JBL Tune Live - Amazon]({amazon_short_url})"
                )
                prev_prices["amazon"] = ama_price_val

            if messages:
                msg_text = "🔔 *Price Drop Alert!*\n\n" + "\n\n".join(messages)
                bot.send_message(USER_ID, msg_text, parse_mode="Markdown")
                save_price_data(prev_prices)
                print("✅ Price drop alert sent.")
            else:
                print("ℹ No price drop detected.")

        except Exception as e:
            print("❌ Error checking prices:", e)

        time.sleep(2 * 60 * 60)  # Sleep for 2 hours

# ========================== One-time alert on 4th July 2025 9 AM ==========================
def run_one_time_alert():
    alerted = False
    target_date = datetime(2025, 7, 4, 9, 0)

    while not alerted:
        now = datetime.now()
        if now >= target_date:
            try:
                inc_price_raw = get_incredible_price()
                ama_price_raw = get_amazon_price(amazon_short_url)
                inc_price_val = extract_numeric_price(inc_price_raw)
                ama_price_val = extract_numeric_price(ama_price_raw)

                prev_prices = load_price_data()
                prev_inc = prev_prices.get("incredible", None)
                prev_ama = prev_prices.get("amazon", None)

                message = ""
                send = False

                if prev_inc is None or inc_price_val != prev_inc:
                    direction = "⬇ Dropped" if prev_inc and inc_price_val < prev_inc else "⬆ Increased"
                    message += (
                        f"💰 *Incredible Price {direction}!*\n"
                        f"Was: `{prev_inc if prev_inc is not None else 'N/A'}` → Now: `{inc_price_raw}`\n"
                        f"🛍️ [Soundcore Space One - Incredible]({incredible_url})\n\n"
                    )
                    send = True

                if prev_ama is None or ama_price_val != prev_ama:
                    direction = "⬇ Dropped" if prev_ama and ama_price_val < prev_ama else "⬆ Increased"
                    message += (
                        f"💸 *Amazon Price {direction}!*\n"
                        f"Was: `{prev_ama if prev_ama is not None else 'N/A'}` → Now: `{ama_price_raw}`\n"
                        f"🎧 [JBL Tune Live - Amazon]({amazon_short_url})\n"
                    )
                    send = True

                if send:
                    bot.send_message(USER_ID, f"🔔 *Price Change Alert!*\n\n{message}", parse_mode="Markdown")

                    new_data = {
                        "incredible": inc_price_val,
                        "amazon": ama_price_val
                    }
                    save_price_data(new_data)
                    print("✅ One-time alert sent and prices updated.")
                else:
                    print("ℹ No price change detected for one-time alert.")

                alerted = True
            except Exception as e:
                print("❌ Error in one-time alert:", e)
        time.sleep(30)

# ========================== Telegram /info Command ==========================
@bot.message_handler(commands=['info'])
def handle_info(message):
    if message.from_user.id == USER_ID:
        inc_price = get_incredible_price()
        ama_price = get_amazon_price(amazon_short_url)
        bot.reply_to(message,
            f"🔔 *Price Info*\n\n"
            f"💰 *Incredible:* `{inc_price}`\n"
            f"🛍️ [Soundcore Space One - Incredible]({incredible_url})\n\n"
            f"💸 *Amazon:* `{ama_price}`\n"
            f"🎧 [JBL Tune Live - Amazon]({amazon_short_url})",
            parse_mode="Markdown"
        )

# ========================== Main ==========================
if __name__ == "__main__":
    threading.Thread(target=run_periodic_price_check, daemon=True).start()
    threading.Thread(target=run_one_time_alert, daemon=True).start()
    try:
        bot.send_message(USER_ID, "Bot started successfully 🚀")
    except Exception as e:
        print("Startup message error:", e)
    bot.infinity_polling()
