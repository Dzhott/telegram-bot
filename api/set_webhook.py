import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from http.server import BaseHTTPRequestHandler

from aiogram import Bot


class handler(BaseHTTPRequestHandler):
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
