import asyncio
import json
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from http.server import BaseHTTPRequestHandler

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ChatAction
from aiogram.filters import CommandStart
from aiogram.types import Update
from google import genai
from google.genai import types as genai_types

from prompts import SYSTEM_PROMPT

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

PRIMARY_MODEL = "gemini-flash-latest"
FALLBACK_MODEL = "gemini-3.5-flash"

_bot: Bot | None = None
_dp: Dispatcher | None = None
_gemini = None
_loop = asyncio.new_event_loop()
asyncio.set_event_loop(_loop)


def _init():
    global _bot, _dp, _gemini
    if _bot is None:
        _bot = Bot(token=os.environ["BOT_TOKEN"])
    if _gemini is None:
        _gemini = genai.Client(api_key=os.environ["GEMINI_KEY"])
    if _dp is None:
        _dp = Dispatcher()
        _register_handlers(_dp)


def _register_handlers(dp: Dispatcher):
    @dp.message(CommandStart())
    async def cmd_start(message: types.Message):
        await message.answer(
            "Приветствую. Я — сказочник.\n"
            "Напиши тему, персонажа или идею — и я расскажу тебе сказку."
        )

    @dp.message()
    async def handle_message(message: types.Message):
        if not message.text:
            return
        await _bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
        try:
            answer = await _ask_gemini(message.text)
        except Exception:
            log.exception("Gemini request failed")
            answer = "Произошла ошибка при обращении к модели. Попробуй позже."
        for i in range(0, len(answer), 4096):
            await message.answer(answer[i : i + 4096])


async def _ask_gemini(user_text: str) -> str:
    for model_name in [PRIMARY_MODEL, FALLBACK_MODEL]:
        try:
            response = await asyncio.to_thread(
                _gemini.models.generate_content,
                model=model_name,
                contents=user_text,
                config=genai_types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                ),
            )
            return response.text or "Сказка не сложилась… Попробуй ещё раз."
        except Exception as exc:
            if "503" in str(exc):
                log.warning("Model %s returned 503, trying fallback…", model_name)
                continue
            raise
    return "К сожалению, сервер сказок временно недоступен. Попробуй позже."


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        _init()
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        update_data = json.loads(body)

        update = Update.model_validate(update_data, context={"bot": _bot})
        _loop.run_until_complete(_dp.feed_update(_bot, update))

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"ok")

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot webhook is active")
