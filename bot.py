import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from crypto import get_price, get_multiple_prices, format_price

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

user_watchlists = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("BTC Price", callback_data="price_btc"),
            InlineKeyboardButton("ETH Price", callback_data="price_eth"),
        ],
        [
            InlineKeyboardButton("Market Overview", callback_data="market"),
            InlineKeyboardButton("My Watchlist", callback_data="watchlist"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Welcome to CryptoTracker Bot!\n\n"
        "Commands:\n"
        "/price btc - Get BTC price\n"
        "/market - Market overview\n"
        "/watch btc eth - Add to watchlist\n"
        "/watchlist - View watchlist\n"
        "/help - All commands",
        reply_markup=reply_markup,
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Available Commands:\n\n"
        "/price btc - Get coin price\n"
        "/market - Market overview\n"
        "/watch btc eth - Add to watchlist\n"
        "/watchlist - View watchlist\n"
        "/unwatch btc - Remove from watchlist\n"
    )

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Please specify a coin. Example: /price btc")
        return
    symbol = context.args[0].lower()
    msg = await update.message.reply_text(f"Fetching {symbol.upper()} price...")
    data = get_price(symbol)
    if not data:
        await msg.edit_text(f"Could not find price for {symbol.upper()}")
        return
    keyboard = [
        [
            InlineKeyboardButton("Refresh", callback_data=f"price_{symbol}"),
            InlineKeyboardButton("Add to Watchlist", callback_data=f"watch_{symbol}"),
        ]
    ]
    await msg.edit_text(
        format_price(data),
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def market_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("Fetching market data...")
    top_coins = ["btc", "eth", "bnb", "sol", "xrp", "ada", "doge"]
    results = get_multiple_prices(top_coins)
    if not results:
        await msg.edit_text("Failed to fetch market data. Try again.")
        return
    text = "Market Overview\n\n"
    for coin in results:
        change = coin["change_24h"]
        arrow = "UP" if change >= 0 else "DOWN"
        price = coin["price"]
        price_str = f"${price:,.2f}" if price >= 1 else f"${price:.6f}"
        text += f"{coin['symbol']}: {price_str} ({arrow} {abs(change):.2f}%)\n"
    keyboard = [[InlineKeyboardButton("Refresh", callback_data="market")]]
    await msg.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def watch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Example: /watch btc eth sol")
        return
    if user_id not in user_watchlists:
        user_watchlists[user_id] = []
    added = []
    for symbol in context.args:
        s = symbol.upper()
        if s not in user_watchlists[user_id]:
            user_watchlists[user_id].append(s)
            added.append(s)
    if added:
        await update.message.reply_text(f"Added to watchlist: {', '.join(added)}")
    else:
        await update.message.reply_text("Those coins are already in your watchlist.")

async def watchlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_watchlists or not user_watchlists[user_id]:
        await update.message.reply_text(
            "Your watchlist is empty.\nUse /watch btc eth to add coins."
        )
        return
    msg = await update.message.reply_text("Loading your watchlist...")
    symbols = [s.lower() for s in user_watchlists[user_id]]
    results = get_multiple_prices(symbols)
    text = "Your Watchlist\n\n"
    for coin in results:
        change = coin["change_24h"]
        arrow = "UP" if change >= 0 else "DOWN"
        price = coin["price"]
        price_str = f"${price:,.2f}" if price >= 1 else f"${price:.6f}"
        text += f"{coin['symbol']}: {price_str} ({arrow} {abs(change):.2f}%)\n"
    keyboard = [
        [
            InlineKeyboardButton("Refresh", callback_data="watchlist"),
            InlineKeyboardButton("Clear All", callback_data="clear_watchlist"),
        ]
    ]
    await msg.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def unwatch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Example: /unwatch btc")
        return
    symbol = context.args[0].upper()
    if user_id in user_watchlists and symbol in user_watchlists[user_id]:
        user_watchlists[user_id].remove(symbol)
        await update.message.reply_text(f"Removed {symbol} from watchlist.")
    else:
        await update.message.reply_text(f"{symbol} is not in your watchlist.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data.startswith("price_"):
        symbol = data.split("_")[1]
        coin_data = get_price(symbol)
        if coin_data:
            keyboard = [
                [
                    InlineKeyboardButton("Refresh", callback_data=f"price_{symbol}"),
                    InlineKeyboardButton("Add to Watchlist", callback_data=f"watch_{symbol}"),
                ]
            ]
            await query.edit_message_text(
                format_price(coin_data),
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        else:
            await query.edit_message_text(f"Failed to fetch {symbol.upper()} price.")

    elif data.startswith("watch_"):
        symbol = data.split("_")[1].upper()
        if user_id not in user_watchlists:
            user_watchlists[user_id] = []
        if symbol not in user_watchlists[user_id]:
            user_watchlists[user_id].append(symbol)
            await query.answer(f"{symbol} added to watchlist!", show_alert=True)
        else:
            await query.answer(f"{symbol} already in watchlist.", show_alert=True)

    elif data == "market":
        top_coins = ["btc", "eth", "bnb", "sol", "xrp", "ada", "doge"]
        results = get_multiple_prices(top_coins)
        text = "Market Overview\n\n"
        for coin in results:
            change = coin["change_24h"]
            arrow = "UP" if change >= 0 else "DOWN"
            price = coin["price"]
            price_str = f"${price:,.2f}" if price >= 1 else f"${price:.6f}"
            text += f"{coin['symbol']}: {price_str} ({arrow} {abs(change):.2f}%)\n"
        keyboard = [[InlineKeyboardButton("Refresh", callback_data="market")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "watchlist":
        if user_id not in user_watchlists or not user_watchlists[user_id]:
            await query.answer("Your watchlist is empty!", show_alert=True)
            return
        symbols = [s.lower() for s in user_watchlists[user_id]]
        results = get_multiple_prices(symbols)
        text = "Your Watchlist\n\n"
        for coin in results:
            change = coin["change_24h"]
            arrow = "UP" if change >= 0 else "DOWN"
            price = coin["price"]
            price_str = f"${price:,.2f}" if price >= 1 else f"${price:.6f}"
            text += f"{coin['symbol']}: {price_str} ({arrow} {abs(change):.2f}%)\n"
        keyboard = [
            [
                InlineKeyboardButton("Refresh", callback_data="watchlist"),
                InlineKeyboardButton("Clear All", callback_data="clear_watchlist"),
            ]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "clear_watchlist":
        user_watchlists[user_id] = []
        await query.edit_message_text("Watchlist cleared!")

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Unknown command. Use /help to see available commands.")

def main():
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN not set")
        return
    print("Starting CryptoTracker Bot...")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("price", price_command))
    app.add_handler(CommandHandler("market", market_command))
    app.add_handler(CommandHandler("watch", watch_command))
    app.add_handler(CommandHandler("watchlist", watchlist_command))
    app.add_handler(CommandHandler("unwatch", unwatch_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    print("Bot is running!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
