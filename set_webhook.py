"""
Run this script ONCE after deploying to Vercel
to register the webhook URL with Telegram.

Usage:
    python set_webhook.py https://your-project.vercel.app
"""

import asyncio
import os
import sys

from dotenv import load_dotenv
from aiogram import Bot

load_dotenv()


async def main():
    if len(sys.argv) < 2:
        print("Usage: python set_webhook.py https://your-project.vercel.app")
        sys.exit(1)

    base_url = sys.argv[1].rstrip("/")
    webhook_url = f"{base_url}/api/webhook"
    token = os.getenv("BOT_TOKEN")

    if not token:
        print("Error: BOT_TOKEN is not set in .env")
        sys.exit(1)

    bot = Bot(token=token)
    await bot.set_webhook(webhook_url)
    info = await bot.get_webhook_info()
    await bot.session.close()

    print(f"Webhook set to: {info.url}")
    print(f"Pending updates: {info.pending_update_count}")


if __name__ == "__main__":
    asyncio.run(main())
