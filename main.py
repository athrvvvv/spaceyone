import telebot
import cloudscraper
from bs4 import BeautifulSoup
import schedule

import time
import threading
import os

tele_token = os.environ.get("TELE")
TOKEN = tele_token
USER_ID = 6264741586

bot = telebot.TeleBot(TOKEN)

def price():
    url = "https://www.incredible.co.za/soundcore-space-one-headphone-black"
    scraper = cloudscraper.create_scraper()  # Handles Cloudflare & anti-bot protection
    try:
        response = scraper.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            price_elements = soup.find_all("span", class_="price")
            if len(price_elements) >= 3:
                third_price = price_elements[2].text.strip()
                print("✅ Price Found:", third_price)
                return third_price
            else:
                print("❌ Less than 3 prices found on the page.")
                return "Price not found"
        else:
            print(f"❌ Failed to fetch page. Status code: {response.status_code}")
            return "Failed to fetch price"
    except Exception as e:
        print(f"❌ Exception during request: {e}")
        return "Error fetching price"

def send_daily_price():
    try:
        p = price()
        bot.send_message(USER_ID, f"Daily Price Update: {p} ✅")
    except Exception as e:
        print(f"Error sending daily price: {e}")

# Schedule the job at 21:00 every day
schedule.every().day.at("21:00").do(send_daily_price)

@bot.message_handler(commands=['info'])
def handle_info(message):
    if message.from_user.id == USER_ID:
        p = price()
        bot.reply_to(message, f"Price Found to be: {p} ✅")

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(30)  # check every 30 seconds

if __name__ == "__main__":
    # Start scheduler thread
    scheduler_thread = threading.Thread(target=run_schedule, daemon=True)
    scheduler_thread.start()

    # Notify startup
    try:
        bot.send_message(USER_ID, "Hello there 👋")
    except Exception as e:
        print(f"Startup message error: {e}")

    # Start polling for telegram bot messages
    bot.infinity_polling()
