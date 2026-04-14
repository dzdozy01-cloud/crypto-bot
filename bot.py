import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is working!")

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Price command works!")

def main():
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        try:
            with open(".env") as f:
                for line in f:
                    if line.startswith("TELEGRAM_BOT_TOKEN"):
                        TOKEN = line.strip().split("=", 1)[1]
                        break
        except:
            pass
    if not TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN not set")
        return
    print("Starting Bot...")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    print("Bot is running!")
    app.run_polling()

if __name__ == "__main__":
    main()
