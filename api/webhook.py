import json
import asyncio
import sys
import os

# Ensure project root is importable from api/ subdirectory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from http.server import BaseHTTPRequestHandler
from aiogram.types import Update
from bot import bot, dp

# Persistent event loop — survives across warm invocations in serverless,
# so the bot's aiohttp session stays valid between requests.
_loop = asyncio.new_event_loop()
asyncio.set_event_loop(_loop)


class handler(BaseHTTPRequestHandler):
    """Vercel serverless function: receives Telegram webhook updates."""

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        update_data = json.loads(body)

        update = Update.model_validate(update_data, context={"bot": bot})
        _loop.run_until_complete(dp.feed_update(bot, update))

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"ok")

    def do_GET(self):
        """Health-check endpoint."""
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot webhook is active")
