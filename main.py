import telebot
import cloudscraper
from bs4 import BeautifulSoup
import time
import threading
import os
from datetime import datetime

# Telegram Setup
tele_token = os.environ.get("TELE")  # Make sure your TELE secret is set
TOKEN = str(tele_token)
print("Telegram Bot Token:", TOKEN)
USER_ID = 6264741586
bot = telebot.TeleBot(TOKEN)

# URLs
incredible_url = "https://www.incredible.co.za/soundcore-space-one-headphone-black"
amazon_short_url = "https://amzn.eu/d/73fgzvN"

# ✅ Incredible Price Scraper
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

# ✅ Amazon Price Scraper using short URL logic
def get_amazon_price(short_url):
    scraper = cloudscraper.create_scraper()
    try:
        # Resolve redirect to full URL
        response = scraper.get(short_url, allow_redirects=True)
        product_url = response.url

        # Fetch full product page
        res = scraper.get(product_url)
        soup = BeautifulSoup(res.content, "html.parser")

        # Try common Amazon price selectors
        price = None
        selectors = [
            '#priceblock_ourprice',
            '#priceblock_dealprice',
            '#priceblock_saleprice',
            '.a-price .a-offscreen'
        ]
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

# 📨 One-time Scheduled Message (for 4 July 2025 at 09:00 AM)
target_date = datetime(2025, 7, 4, 9, 0)

def run_schedule_once():
    sent = False
    while not sent:
        now = datetime.now()
        if now >= target_date:
            try:
                inc_price = price()
                ama_price = get_amazon_price(amazon_short_url)
                bot.send_message(USER_ID,
                    f"📦 *Special Price Update*\n\n"
                    f"💰 *Incredible:* `{inc_price}`\n"
                    f"🛍️ [Soundcore Space One - Incredible]({incredible_url})\n\n"
                    f"💸 *Amazon:* `{ama_price}`\n"
                    f"🎧 [JBL Tune Live - Amazon]({amazon_short_url})",
                    parse_mode="Markdown"
                )
                sent = True
                print("✅ Message sent on scheduled time.")
            except Exception as e:
                print("❌ Failed to send scheduled message:", e)
            break
        time.sleep(30)

# 📩 /info command handler
@bot.message_handler(commands=['info'])
def handle_info(message):
    if message.from_user.id == USER_ID:
        inc_price = price()
        ama_price = get_amazon_price(amazon_short_url)
        bot.reply_to(message,
            f"🔔 *Price Updates Found!*\n\n"
            f"💰 *Incredible:* `{inc_price}`\n"
            f"🛍️ [Soundcore Space One - Incredible]({incredible_url})\n\n"
            f"💸 *Amazon:* `{ama_price}`\n"
            f"🎧 [JBL Tune Live - Amazon]({amazon_short_url})",
            parse_mode="Markdown"
        )

# 🚀 Startup
if __name__ == "__main__":
    threading.Thread(target=run_schedule_once, daemon=True).start()
    try:
        bot.send_message(USER_ID, "Bot started successfully 🚀")
    except Exception as e:
        print("Startup message error:", e)
    bot.infinity_polling()
