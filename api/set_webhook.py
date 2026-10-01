import asyncio
import os
from http.server import BaseHTTPRequestHandler
from aiogram import Bot


class handler(BaseHTTPRequestHandler):
    """One-time endpoint: visit GET /api/set_webhook to register the webhook URL with Telegram."""

    def do_GET(self):
        token = os.getenv("BOT_TOKEN", "")
        host = self.headers.get("Host", "")
        webhook_url = f"https://{host}/api/webhook"

        async def _set():
            _bot = Bot(token=token)
            await _bot.set_webhook(webhook_url)
            await _bot.session.close()

        asyncio.run(_set())

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(f"Webhook set to {webhook_url}".encode())
