import telebot

# Your bot token
TOKEN = "7957967714:AAErDKh6PfLHw6dwTsMH1AGtNd9eGMS13qU"

# Target user ID
USER_ID = 6264741586

# Initialize bot
bot = telebot.TeleBot(TOKEN)

# Send "Hello" when the script starts
bot.send_message(USER_ID, "Hello")

# Keep bot alive (to avoid the script exiting)
bot.polling()
