import telebot
import cloudscraper
from bs4 import BeautifulSoup
import schedule
import time
import threading
import os

# Telegram Setup
tele_token = os.environ.get("TELE")
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
        print("❌ Error:", e)
        return "Error fetching price"

# ✅ Amazon Price Scraper (Your Logic)
def get_amazon_price(short_url):
    scraper = cloudscraper.create_scraper()
    try:
        # Resolve redirect
        response = scraper.get(short_url, allow_redirects=True)
        product_url = response.url

        # Fetch full product page
        res = scraper.get(product_url)
        soup = BeautifulSoup(res.content, "html.parser")

        # Try various price selectors
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

# 📦 Daily Price Update
def send_daily_price():
    try:
        inc_price = price()
        ama_price = get_amazon_price(amazon_short_url)
        bot.send_message(USER_ID,
            f"📦 *Daily Price Update*\n\n"
            f"💰 *Incredible:* `{inc_price}`\n"
            f"🛍️ [Incredible Product]({incredible_url})\n\n"
            f"💸 *Amazon:* `{ama_price}`\n"
            f"🎧 [JBL Tune Live - Amazon]({amazon_short_url})",
            parse_mode="Markdown"
        )
    except Exception as e:
        print("Error sending daily price:", e)

# ⏰ Scheduler Setup
schedule.every().day.at("21:00").do(send_daily_price)

# 📩 Telegram Command
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

# 🌀 Schedule Thread
def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(30)

# 🚀 Startup
if __name__ == "__main__":
    threading.Thread(target=run_schedule, daemon=True).start()
    try:
        bot.send_message(USER_ID, "Bot started successfully 🚀")
    except Exception as e:
        print("Startup message error:", e)
    bot.infinity_polling()
