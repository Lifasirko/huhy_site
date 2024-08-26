from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from keyboards.callback_datas import i_am_human_callback


async def i_am_human_button_menu_func(user_id):
    i_am_human_button_menu_func_kb = InlineKeyboardMarkup(row_width=1)
    i_am_human_button_menu_func_kb.row()
    # i_am_human_button_menu_func_kb.insert(
    #     InlineKeyboardButton(
    #         text="Правила",
    #         url="https://telegra.ph/Pravila-sp%D1%96lnoti-Huhispace-04-03",
    #         callback_data=i_am_human_callback.new(user_id=user_id)
    #     )
    # )
    i_am_human_button_menu_func_kb.insert(InlineKeyboardButton(
        # text="Я приймаю правила, як Ісуса в своє серце!)",
        text="Я приймаю правила",
        callback_data=i_am_human_callback.new(user_id=user_id)
    ))
    return i_am_human_button_menu_func_kb
