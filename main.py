import telebot

# Your bot token
TOKEN = "7957967714:AAErDKh6PfLHw6dwTsMH1AGtNd9eGMS13qU"

# Initialize bot
bot = telebot.TeleBot(TOKEN)

# Send "Hello" when the bot starts
bot.send_message(6264741586, "Hello")

# Command handler for "INFO" (case-insensitive)
@bot.message_handler(func=lambda message: message.text and message.text.strip().lower() == "info")
def send_info(message):
    bot.reply_to(message, "HELLO DEVELOPMENT IS ONGOING")

# Keep bot running
bot.polling()
