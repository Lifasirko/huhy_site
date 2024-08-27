import asyncio

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery

from telegram_bot.data.greetings import personal_greetings, url_rules
from telegram_bot.keyboards.callback_datas import i_am_human_callback
from telegram_bot.keyboards.human_button import i_am_human_button_menu_func
from telegram_bot.loader import dp, bot
from telegram_bot.utils.notify_admins import new_chat_member_notify, count_chat_members, chat_member_left_chat_notify, \
    send_message_to_admin


class UserState(StatesGroup):
    reading_rules = State()


# async def delete_bots(state: FSMContext):

async def check_state(state: FSMContext):
    current_state = await state.get_state()
    return current_state
    # print(current_state)


async def check_rules_read(user, chat_id, state: FSMContext):
    user_id = user.id
    print(await check_state(state))
    # Чекаємо 5 хвилин перед нагадуванням
    await asyncio.sleep(300)  # 5 хвилин
    current_state = await check_state(state)
    # print(1)
    if current_state == "UserState:reading_rules":
        # print(2)
        warning_message = await bot.send_message(
            chat_id,
            f"{user.mention}, будь ласка, тицьніть, що ознайомлені з правилами, інакше втратите доступ до чату 🫣",
            disable_notification=True)
        warning_message_id = warning_message.message_id
        await asyncio.sleep(300)  # Ще 5 хвилин
        cur_st = await check_state(state)
        # print(3)
        if cur_st == "UserState:reading_rules":
            # print(4)
            try:
                await bot.kick_chat_member(chat_id, user_id)
                mes = int(await state.get_data('mes'))
                await bot.delete_message(chat_id, mes)
            except Exception as e:
                print(f"Помилка при видаленні користувача: {e}")
                await send_message_to_admin(dp, e)
            finally:

                await state.finish()
        await bot.delete_message(chat_id, warning_message_id)


@dp.message_handler(content_types=types.ContentType.NEW_CHAT_MEMBERS)
async def new_member(message: types.Message, state: FSMContext):
    for user in message.new_chat_members:
        markup = await i_am_human_button_menu_func(user_id=user.id)
        t = await personal_greetings(user) + url_rules
        sent_message = await message.reply(text=t, reply_markup=markup, disable_notification=True)
        # Ініціалізація стану користувача
        user_state = dp.current_state(user=user.id, chat=message.chat.id)
        await user_state.set_state(UserState.reading_rules)
        mes = sent_message.message_id
        await user_state.set_data(mes)
        permissions = types.ChatPermissions(can_send_messages=False, can_send_media_messages=False,
                                            can_send_other_messages=False, can_add_web_page_previews=False)
        await dp.bot.restrict_chat_member(message.chat.id, user.id, can_send_messages=False, permissions=permissions)
        await new_chat_member_notify(dp, message, user)
        # Створення асинхронної задачі для нагадування та потенційного видалення
        await asyncio.create_task(check_rules_read(user, message.chat.id, user_state))


@dp.message_handler(content_types=types.ContentType.LEFT_CHAT_MEMBER)
async def left_member(message: types.Message):
    await chat_member_left_chat_notify(dp, message)
    await count_chat_members(dp, message)


@dp.callback_query_handler(i_am_human_callback.filter(), state=UserState.reading_rules)
async def i_am_human(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await call.answer()
    human_id = int(callback_data.get("user_id"))
    # print(f"human_id = {human_id}")
    # print(f"call.from_user.id = {call.from_user.id}")
    if call.from_user.id == human_id:
        permissions = types.ChatPermissions(can_send_messages=True, can_send_media_messages=True,
                                            can_send_other_messages=True, can_add_web_page_previews=True)
        await dp.bot.restrict_chat_member(call.message.chat.id, call.from_user.id, can_send_messages=True,
                                          permissions=permissions)
        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        message = f"Людина {human_id} прочитала правила"
        await send_message_to_admin(dp, message)
        await state.reset_state()
        print(await check_state(state))


@dp.callback_query_handler(i_am_human_callback.filter())
async def pressed_button_not_new_user(call: CallbackQuery):
    await call.answer()
    joke = await call.message.answer("Не для тебе Хуха кнопочку пилила!)")
    await asyncio.sleep(10)
    await bot.delete_message(call.message.chat.id, joke.message_id)
