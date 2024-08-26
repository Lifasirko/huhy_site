from aiogram import types
from aiogram.dispatcher.filters import Command


from data.greetings import chat_rules
from loader import dp


@dp.message_handler(Command("rules"))
async def get_rules_command(message: types.Message):
    await message.answer(text=chat_rules)
