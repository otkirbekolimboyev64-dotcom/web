import asyncio
import os
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from bot.handlers import router as handlers_router

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "")


async def main():
    if not BOT_TOKEN or "your_bot_token_here" in BOT_TOKEN:
        print("⚠️ BOT_TOKEN .env faylda yo'q. Bot ishga tushmaydi.")
        return
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(handlers_router)
    print("✅ Bot ishga tushdi")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
