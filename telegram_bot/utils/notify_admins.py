import logging

from aiogram import Dispatcher, types

from telegram_bot.data.config import ADMINS


# from utils.db_api import quick_commands as commands


async def on_startup_notify(dp: Dispatcher):
    for admin in ADMINS:
        try:
            await dp.bot.send_message(admin, "Хух-бот прокинувся і готовий до роботи")

        except Exception as err:
            logging.exception(err)


async def on_shutdown_notify(dp: Dispatcher):
    for admin in ADMINS:
        try:
            await dp.bot.send_message(admin, "Хух-бот пішов спати")

        except Exception as err:
            logging.exception(err)


async def send_message_to_admin(dp: Dispatcher, message: types.Message):
    for admin in ADMINS:
        await dp.bot.send_message(
            admin, text=message, disable_notification=True)


async def new_chat_member_notify(dp: Dispatcher, message: types.Message, new_user):
    user_info = f"{new_user.mention}, {new_user.full_name}"
    chat_id = message.chat.id
    count = await dp.bot.get_chat_members_count(chat_id=chat_id)
    count_text = f"В чаті зараз {count} користувачів\n"
    text = (f"Новий користувач в чаті!\n"
            f"інфо користувача:\n"
            f"{user_info}\n"
            f"\n")
    referer_id = message.from_user.id
    if new_user.id != referer_id:
        ref_text = (f"Його додав {message.from_user.mention}, {message.from_user.full_name}\n"
                    f"\n")
        text += ref_text
    text += count_text

    for admin in ADMINS:
        await dp.bot.send_message(
            admin,
            text,
            disable_notification=True)


async def chat_member_left_chat_notify(dp: Dispatcher, message: types.Message):
    user_info = f"@{message.left_chat_member.username}, {message.left_chat_member.first_name}"
    referer_id = message.from_user.id
    user_id = message.left_chat_member.id
    text = (f"Користувач {user_info} покинув чат \n"
            f"\n")
    if user_id != referer_id:
        ref = message.from_user.mention
        text += f"Його видалив {ref}"
    for admin in ADMINS:
        await dp.bot.send_message(admin, text,
                                  disable_notification=True)


async def count_chat_members(dp: Dispatcher, message: types.Message):
    chat_id = message.chat.id
    count = await dp.bot.get_chat_members_count(chat_id=chat_id)
    for admin in ADMINS:
        await dp.bot.send_message(
            admin, text=f"В чаті зараз {count} користувачів", disable_notification=True)


async def some_problem_notify(dp: Dispatcher, message: types.Message, problem_stage: str = None):
    for admin in ADMINS:
        try:
            # count = await commands.count_users()
            await dp.bot.send_message(admin,
                                      f"Виникла помилка на етапі:\n"
                                      f"{problem_stage}\n"
                                      f"у користувача:\n"
                                      f"{message.from_user.id}"
                                      )

        except Exception as err:
            logging.exception(err)


async def new_order_notify(dp: Dispatcher, message: types.Message, form: dict = None):
    for admin in ADMINS:
        try:
            await dp.bot.send_message(admin,
                                      f"Нова заявка:\n"
                                      f"{form}\n"
                                      )

        except Exception as err:
            logging.exception(err)
