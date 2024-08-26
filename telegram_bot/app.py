from loader import bot
from utils import on_startup_notify
# from utils.db_api import db_gino
from utils.set_bot_commands import set_default_commands


async def on_startup(dp):
    import filters
    import middlewares
    middlewares.setup(dp)

    # print("Подключаем БД")
    # await db_gino.on_startup(dp)
    # print("Готово")

    # print("Чистим базу")
    # await db.gino.drop_all()
    # # await db.gino.drop(Events)
    # # await delete_table_users_most() # TODO: разобраться как удалять одну таблицу (DROP TABLE {table name} — таблиця)
    # print("Готово")

    # print("Создаем таблицы")
    # await db.gino.create_all()
    # print("Готово")
    #
    # print("Обновляем БД")
    # await update_db()
    # print("Готово")

    # print("Запускаем запуск по расписанию")
    # set_scheduler_jobs(scheduler, bot, config)
    # scheduler.start()
    # print("Готово")

    # print("Запускаем виджеты")
    # registry = DialogRegistry(dp)
    # registry.register(make_schedule_dialog)
    # print("Готово")

    await on_startup_notify(dp)
    await set_default_commands(dp)


async def on_shutdown(dp):
    from utils.notify_admins import on_shutdown_notify
    await on_shutdown_notify(dp)
    await bot.close()


if __name__ == '__main__':
    from aiogram import executor
    from handlers import dp

    executor.start_polling(dp, on_startup=on_startup, skip_updates=True, on_shutdown=on_shutdown)
