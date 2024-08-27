# import gspread_asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode  # Правильний імпорт ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
# from aiogram_dialog import DialogRegistry
# from apscheduler.schedulers.asyncio import AsyncIOScheduler

from telegram_bot.data import config
# from utils.db_api.db_gino import db

default_properties = DefaultBotProperties(parse_mode=ParseMode.HTML)


bot = Bot(token=config.BOT_TOKEN, default=default_properties)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# scheduler = AsyncIOScheduler()
# registry = DialogRegistry(dp)
# google_client_manager = gspread_asyncio.AsyncioGspreadClientManager(
#         config.scoped_credentials
#     )


__all__ = [
    "bot", "storage", "dp",
    # "db", "scheduler", "registry"
    # , "google_client_manager"
           ]
