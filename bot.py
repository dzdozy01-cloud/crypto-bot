import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from config import TELEGRAM_TOKEN, CHECK_INTERVAL
from database import (
    init_db, add_alert, get_alerts, mark_alert_triggered,
    delete_alert, add_to_watchlist, get_watchlist, remove_from_watchlist
)
from price_tracker import (
    get_price, get_multiple_prices, search_coin,
    get_trending, get_market_overview
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def format_price(price):
    if price >= 1:
        return f"${price:,.2f}"
    elif price >= 0.01:
        return f"${price:.4f}"
    else:
        return f"${price:.8f}"

def format_change(change):
    emoji = "up" if change >= 0 else "down"
    return f"{emoji} {change:+.2f}%"

def format_large_number(num):
    if num >= 1_000_000_000:
        return f"${num / 1_000_000_000:.2f}B"
    elif num >= 1_000_000:
        return f"${num / 1_000_000:.2f}M"
    else:
        return f"${num:,.0f}"

async def start(update, context):
    keyboard = [
        [
            InlineKeyboardButton("Top Coins", callback_data="market"),
            InlineKeyboardButton("Trending", callback_data="trending"),
        ],
        [
            InlineKeyboardButton("Watchlist", callback_data="watchlist"),
            InlineKeyboardButton("My Alerts", callback_data="my_alerts"),
        ],
        [InlineKeyboardButton("Help", callback_data="help")]
    ]
    await update.message.reply_text(
        "Welcome to CryptoTracker Bot!\n\n"
        "Commands:\n"
        "/price bitcoin - Get price\n"
        "/alert bitcoin above 50000 - Set alert\n"
        "/watch ethereum - Add to watchlist\n"
        "/market - Top 10 coins\n"
        "/trending - Trending coins\n",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def price_command(update, context):
    if not context.args:
        await update.message.reply_text("Usage: /price bitcoin")
        return
    coin_id = context.args[0].lower()
    msg = await update.message.reply_text(f"Fetching {coin_id}...")
    data = get_price(coin_id)
    if not data:
        await msg.edit_text(f"Coin {coin_id} not found.")
        return
    price = data.get("usd", 0)
    change_24h = data.get("usd_24h_change", 0) or 0
    market_cap = data.get("usd_market_cap", 0)
    keyboard = [[
        InlineKeyboardButton("Set Alert", callback_data=f"setalert_{coin_id}"),
        InlineKeyboardButton("Watch", callback_data=f"addwatch_{coin_id}"),
    ],[InlineKeyboardButton("Refresh", callback_data=f"refresh_{coin_id}")]]
    await msg.edit_text(
        f"{coin_id.upper()}\n\n"
        f"Price: {format_price(price)}\n"
        f"24h: {format_change(change_24h)}\n"
        f"Market Cap: {format_large_number(market_cap)}\n",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def market_command(update, context):
    msg = await update.message.reply_text("Fetching market...")
    coins = get_market_overview(limit=10)
    if not coins:
        await msg.edit_text("Could not fetch market data.")
        return
    text = "Top 10 Cryptocurrencies\n\n"
    for i, coin in enumerate(coins, 1):
        change = coin.get("price_change_percentage_24h", 0) or 0
        arrow = "up" if change >= 0 else "down"
        text += f"{i}. {coin['name']} - {format_price(coin['current_price'])} {arrow} {change:+.2f}%\n"
    await msg.edit_text(text)

async def trending_command(update, context):
    msg = await update.message.reply_text("Fetching trending...")
    trending = get_trending()
    if not trending:
        await msg.edit_text("Could not fetch trending.")
        return
    text = "Trending Coins\n\n"
    for i, item in enumerate(trending[:7], 1):
        coin = item.get("item", {})
        text += f"{i}. {coin.get('name')} ({coin.get('symbol','').upper()})\n"
    await msg.edit_text(text)

async def alert_command(update, context):
    if len(context.args) < 3:
        await update.message.reply_text("Usage: /alert bitcoin above 50000")
        return
    coin_id = context.args[0].lower()
    condition = context.args[1].lower()
    if condition not in ["above", "below"]:
        await update.message.reply_text("Use above or below")
        return
    try:
        target_price = float(context.args[2].replace(",", ""))
    except ValueError:
        await update.message.reply_text("Invalid price.")
        return
    data = get_price(coin_id)
    if not data:
        await update.message.reply_text(f"Coin {coin_id} not found.")
        return
    add_alert(update.effective_chat.id, coin_id, target_price, condition)
    await update.message.reply_text(
        f"Alert Set!\n"
        f"{coin_id.upper()} {condition} {format_price(target_price)}"
    )

async def alerts_command(update, context):
    alerts = get_alerts(update.effective_chat.id)
    if not alerts:
        await update.message.reply_text("No active alerts.")
        return
    text = "Your Alerts:\n\n"
    keyboard = []
    for alert in alerts:
        alert_id, _, coin, price, condition, _, _ = alert
        text += f"#{alert_id} {coin.upper()} {condition} {format_price(price)}\n"
        keyboard.append([InlineKeyboardButton(
            f"Delete #{alert_id}",
            callback_data=f"delalert_{alert_id}"
        )])
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def watch_command(update, context):
    if not context.args:
        await update.message.reply_text("Usage: /watch bitcoin")
        return
    coin_id = context.args[0].lower()
    data = get_price(coin_id)
    if not data:
        await update.message.reply_text("Coin not found.")
        return
    if add_to_watchlist(update.effective_chat.id, coin_id):
        await update.message.reply_text(f"{coin_id.upper()} added to watchlist!")
    else:
        await update.message.reply_text("Already in watchlist!")

async def watchlist_command(update, context):
    coins = get_watchlist(update.effective_chat.id)
    if not coins:
        await update.message.reply_text("Watchlist empty. Use /watch bitcoin")
        return
    msg = await update.message.reply_text("Fetching watchlist...")
    prices = get_multiple_prices(coins)
    text = "Your Watchlist\n\n"
    for coin in coins:
        data = prices.get(coin, {})
        if data:
            price = data.get("usd", 0)
            change = data.get("usd_24h_change", 0) or 0
            text += f"{coin.upper()}: {format_price(price)} {format_change(change)}\n"
    await msg.edit_text(text)

async def button_callback(update, context):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "market":
        coins = get_market_overview(limit=10)
        text = "Top 10 Cryptocurrencies\n\n"
        for i, coin in enumerate(coins, 1):
            change = coin.get("price_change_percentage_24h", 0) or 0
            arrow = "up" if change >= 0 else "down"
            text += f"{i}. {coin['name']} - {format_price(coin['current_price'])} {arrow} {change:+.2f}%\n"
        await query.edit_message_text(text)

    elif data == "trending":
        trending = get_trending()
        text = "Trending Coins\n\n"
        for i, item in enumerate(trending[:7], 1):
            coin = item.get("item", {})
            text += f"{i}. {coin.get('name')} ({coin.get('symbol','').upper()})\n"
        await query.edit_message_text(text)

    elif data == "watchlist":
        coins = get_watchlist(query.message.chat_id)
        if not coins:
            await query.edit_message_text("Watchlist empty.")
            return
        prices = get_multiple_prices(coins)
        text = "Your Watchlist\n\n"
        for coin in coins:
            d = prices.get(coin, {})
            if d:
                price = d.get("usd", 0)
                change = d.get("usd_24h_change", 0) or 0
                text += f"{coin.upper()}: {format_price(price)} {format_change(change)}\n"
        await query.edit_message_text(text)

    elif data == "my_alerts":
        alerts = get_alerts(query.message.chat_id)
        if not alerts:
            await query.edit_message_text("No active alerts.")
            return
        text = "Your Alerts:\n\n"
        for alert in alerts:
            alert_id, _, coin, price, condition, _, _ = alert
            text += f"#{alert_id} {coin.upper()} {condition} {format_price(price)}\n"
        await query.edit_message_text(text)

    elif data == "help":
        await query.edit_message_text(
            "Commands:\n\n"
            "/price bitcoin\n"
            "/market\n"
            "/trending\n"
            "/alert bitcoin above 50000\n"
            "/alerts\n"
            "/watch bitcoin\n"
            "/watchlist\n"
        )

    elif data.startswith("refresh_"):
        coin_id = data.split("_", 1)[1]
        price_data = get_price(coin_id)
        if price_data:
            price = price_data.get("usd", 0)
            change_24h = price_data.get("usd_24h_change", 0) or 0
            market_cap = price_data.get("usd_market_cap", 0)
            keyboard = [[
                InlineKeyboardButton("Alert", callback_data=f"setalert_{coin_id}"),
                InlineKeyboardButton("Watch", callback_data=f"addwatch_{coin_id}"),
            ],[InlineKeyboardButton("Refresh", callback_data=f"refresh_{coin_id}")]]
            await query.edit_message_text(
                f"{coin_id.upper()}\n\n"
                f"Price: {format_price(price)}\n"
                f"24h: {format_change(change_24h)}\n"
                f"Market Cap: {format_large_number(market_cap)}\n",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

    elif data.startswith("addwatch_"):
        coin_id = data.split("_", 1)[1]
        if add_to_watchlist(query.message.chat_id, coin_id):
            await query.answer(f"{coin_id.upper()} added!", show_alert=True)
        else:
            await query.answer("Already in watchlist!", show_alert=True)

    elif data.startswith("delalert_"):
        alert_id = int(data.split("_", 1)[1])
        delete_alert(alert_id, query.message.chat_id)
        await query.answer("Alert deleted!", show_alert=True)
        await query.edit_message_text(f"Alert #{alert_id} deleted.")

async def check_alerts(application):
    alerts = get_alerts()
    if not alerts:
        return
    coin_ids = list(set(alert[2] for alert in alerts))
    prices = get_multiple_prices(coin_ids)
    for alert in alerts:
        alert_id, chat_id, coin_id, target_price, condition, _, _ = alert
        coin_data = prices.get(coin_id, {})
        if not coin_data:
            continue
        current_price = coin_data.get("usd", 0)
        triggered = False
        if condition == "above" and current_price >= target_price:
            triggered = True
        elif condition == "below" and current_price <= target_price:
            triggered = True
        if triggered:
            mark_alert_triggered(alert_id)
            try:
                await application.bot.send_message(
                    chat_id=chat_id,
                    text=(
                        f"Alert Triggered!\n\n"
                        f"{coin_id.upper()} is {condition} {format_price(target_price)}\n"
                        f"Current: {format_price(current_price)}"
                    )
                )
            except Exception as e:
                logger.error(f"Failed to send alert: {e}")

def main():
    init_db()
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("price", price_command))
    application.add_handler(CommandHandler("market", market_command))
    application.add_handler(CommandHandler("trending", trending_command))
    application.add_handler(CommandHandler("alert", alert_command))
    application.add_handler(CommandHandler("alerts", alerts_command))
    application.add_handler(CommandHandler("watch", watch_command))
    application.add_handler(CommandHandler("watchlist", watchlist_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    job_queue = application.job_queue
    job_queue.run_repeating(
        lambda ctx: asyncio.create_task(check_alerts(application)),
        interval=CHECK_INTERVAL,
        first=10
    )
    logger.info("Bot started!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
