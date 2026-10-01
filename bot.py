import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ChatAction
from aiogram.filters import CommandStart
from google import genai
from google.genai import types as genai_types

# Ensure project root is importable when running from api/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from prompts import SYSTEM_PROMPT

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
GEMINI_KEY = os.getenv("GEMINI_KEY", "")

# Lazy init — don't crash at import if env vars are missing (Vercel build phase)
bot: Bot | None = None
dp = Dispatcher()
gemini_client = None

PRIMARY_MODEL = "gemini-flash-latest"
FALLBACK_MODEL = "gemini-3.5-flash"


def _ensure_init():
    """Initialize bot and Gemini client on first request."""
    global bot, gemini_client
    if bot is None:
        token = os.getenv("BOT_TOKEN", "")
        if not token:
            raise RuntimeError("BOT_TOKEN is not set")
        bot = Bot(token=token)
    if gemini_client is None:
        key = os.getenv("GEMINI_KEY", "")
        if not key:
            raise RuntimeError("GEMINI_KEY is not set")
        gemini_client = genai.Client(api_key=key)


async def ask_gemini(user_text: str) -> str:
    """Send a request to Gemini. Retry with fallback model on 503."""
    _ensure_init()
    models_to_try = [PRIMARY_MODEL, FALLBACK_MODEL]

    for model_name in models_to_try:
        try:
            response = await asyncio.to_thread(
                gemini_client.models.generate_content,
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


@dp.message(CommandStart())
async def cmd_start(message: types.Message) -> None:
    await message.answer(
        "Приветствую. Я — сказочник.\n"
        "Напиши тему, персонажа или идею — и я расскажу тебе сказку."
    )


@dp.message()
async def handle_message(message: types.Message) -> None:
    if not message.text:
        return

    _ensure_init()
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

    try:
        answer = await ask_gemini(message.text)
    except Exception:
        log.exception("Gemini request failed")
        answer = "Произошла ошибка при обращении к модели. Попробуй позже."

    for i in range(0, len(answer), 4096):
        await message.answer(answer[i : i + 4096])


# --- Local development: long polling ---
if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    _ensure_init()

    async def main() -> None:
        log.info("Bot starting (long polling)…")
        await dp.start_polling(bot)

    asyncio.run(main())
