from aiogram import types


async def set_default_commands(dp):
    await dp.bot.set_my_commands([
        # types.BotCommand("test", "test"),  # TODO:убрать
        types.BotCommand("start", "Запустити бота"),
        types.BotCommand("rules", "Отримати правила спільноти"),
        # types.BotCommand("help", "Отримати довідку"),
        # types.BotCommand("options", "Опції"),
        # types.BotCommand("get_ref_link", "Отримати лінк реферера"),
        # types.BotCommand("reset_state", "Скинути стани користувача"),

    ])
