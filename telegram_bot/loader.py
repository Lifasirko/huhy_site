# import gspread_asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
# from aiogram_dialog import DialogRegistry
# from apscheduler.schedulers.asyncio import AsyncIOScheduler

from data import config
# from utils.db_api.db_gino import db

bot = Bot(token=config.BOT_TOKEN, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
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
