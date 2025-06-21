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

# Utilities
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

# Scrapers
def price():
    scraper = cloudscraper.create_scraper()
    try:
        response = scraper.get(incredible_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            price_elements = soup.find_all("span", class_="price")
            if len(price_elements) >= 3:
                third_price = price_elements[2].text.strip()
                print("✅ Incredible Price Found:", third_price)
                return third_price
            else:
                print("❌ Less than 3 price elements found.")
                return "Price not found"
        else:
            print("❌ Failed to fetch Incredible page.")
            return "Failed to fetch price"
    except Exception as e:
        print("❌ Error fetching Incredible price:", e)
        return "Error fetching price"

def get_amazon_price(short_url):
    scraper = cloudscraper.create_scraper()
    try:
        response = scraper.get(short_url, allow_redirects=True)
        product_url = response.url

        res = scraper.get(product_url)
        soup = BeautifulSoup(res.content, "html.parser")

        selectors = [
            '#priceblock_ourprice',
            '#priceblock_dealprice',
            '#priceblock_saleprice',
            '.a-price .a-offscreen'
        ]
        price = None
        for selector in selectors:
            el = soup.select_one(selector)
            if el and el.text.strip():
                price = el.text.strip()
                break

        print("✅ Amazon Price Found:", price or "Price not found")
        return price or "Price not found"
    except Exception as e:
        print("❌ Amazon exception:", e)
        return "Error fetching Amazon price"

# Periodic price check every 2 hours - alerts only on drops
def run_periodic_price_check():
    while True:
        try:
            inc_price_raw = price()
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

        time.sleep(2 * 60 * 60)  # 2 hours

# One-time alert on 4th July 2025 09:00 — alerts on any price change (up/down)
def run_one_time_alert():
    alerted = False
    target_date = datetime(2025, 7, 4, 9, 0)

    while not alerted:
        now = datetime.now()
        if now >= target_date:
            try:
                inc_price_raw = price()
                ama_price_raw = get_amazon_price(amazon_short_url)
                inc_price_val = extract_numeric_price(inc_price_raw)
                ama_price_val = extract_numeric_price(ama_price_raw)

                prev_prices = load_price_data()
                prev_inc = prev_prices.get("incredible", None)
                prev_ama = prev_prices.get("amazon", None)

                message = ""
                send = False

                # Check Incredible price change
                if prev_inc is None or inc_price_val != prev_inc:
                    direction = "⬇ Dropped" if prev_inc and inc_price_val < prev_inc else "⬆ Increased"
                    message += (
                        f"💰 *Incredible Price {direction}!*\n"
                        f"Was: `{prev_inc if prev_inc is not None else 'N/A'}` → Now: `{inc_price_raw}`\n"
                        f"🛍️ [Soundcore Space One - Incredible]({incredible_url})\n\n"
                    )
                    send = True

                # Check Amazon price change
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
                # Optionally wait some before retrying

        time.sleep(30)  # Check every 30 seconds if time reached

# Telegram /info command
@bot.message_handler(commands=['info'])
def handle_info(message):
    if message.from_user.id == USER_ID:
        inc_price = price()
        ama_price = get_amazon_price(amazon_short_url)
        bot.reply_to(message,
            f"🔔 *Price Info*\n\n"
            f"💰 *Incredible:* `{inc_price}`\n"
            f"🛍️ [Soundcore Space One - Incredible]({incredible_url})\n\n"
            f"💸 *Amazon:* `{ama_price}`\n"
            f"🎧 [JBL Tune Live - Amazon]({amazon_short_url})",
            parse_mode="Markdown"
        )

# Main app start
if __name__ == "__main__":
    threading.Thread(target=run_periodic_price_check, daemon=True).start()
    threading.Thread(target=run_one_time_alert, daemon=True).start()
    try:
        bot.send_message(USER_ID, "Bot started successfully 🚀")
    except Exception as e:
        print("Startup message error:", e)
    bot.infinity_polling()
