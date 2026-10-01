import asyncio
import os
import sys

from flask import Flask, request

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram.types import Update
from bot import bot, dp, _ensure_init

app = Flask(__name__)

# Persistent event loop — survives across warm invocations
_loop = asyncio.new_event_loop()
asyncio.set_event_loop(_loop)


@app.route("/api/webhook", methods=["POST"])
def webhook():
    """Receive Telegram webhook updates."""
    _ensure_init()
    update_data = request.get_json(force=True)
    update = Update.model_validate(update_data, context={"bot": bot})
    _loop.run_until_complete(dp.feed_update(bot, update))
    return "ok", 200


@app.route("/api/set_webhook", methods=["GET"])
def set_webhook():
    """One-time: register webhook URL with Telegram."""
    _ensure_init()
    host = request.host
    webhook_url = f"https://{host}/api/webhook"

    async def _set():
        await bot.set_webhook(webhook_url)

    _loop.run_until_complete(_set())
    return f"Webhook set to {webhook_url}", 200


@app.route("/", methods=["GET"])
def health():
    return "Bot is running", 200
