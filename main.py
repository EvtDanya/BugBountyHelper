import asyncio
import aiogram
import logging

from src.config import settings
from src.logging import init_logging
from src.fetcher import BugBountyFetcher
from src.models import BugBountyProgram

logger = logging.getLogger("bbHelper")
init_logging(logger)

bot = aiogram.Bot(token=settings.app.bot_token)
dp = aiogram.Dispatcher()
router = aiogram.Router()

known_programs: set[BugBountyProgram] = set()
fetcher = BugBountyFetcher(settings.app.bug_bounty_url)


async def initialize_known_programs():
    """
    Инициализация известных программ при запуске
    """
    global known_programs
    logger.info("Инициализация известных программ...")
    try:
        programs = fetcher.fetch_programs(
            page="/programs/?sort=created_at"
        )
        programs_second = fetcher.fetch_programs(
            page="/programs/?sort=created_at&page=2"
        )
        known_programs.update(programs + programs_second)
        logger.info(f"Инициализировано {len(known_programs)} программ.")
    except Exception as e:
        logger.error(f"Ошибка при инициализации программ: {e}")


async def send_program_notification(program: BugBountyProgram):
    """
    Отправляет уведомление о новой программе

    :param program: Объект BugBountyProgram
    """
    await bot.send_message(
        settings.app.user_id,
        f"Платформа <b>Standoff365</b>\n\n"
        f"<b>Тип:</b> {program.program_type}\n"
        f"<b>Название:</b> {program.name}\n"
        f"<b>Компания:</b> {program.company}\n"
        f"<b>Максимальное вознаграждение:</b> {program.reward}\n"
        f"<b>Ссылка:</b> <a href=\"{settings.app.bug_bounty_url}{program.url}\">{program.url}</a>\n\n"  # noqa
        f"<b>Описание:</b> {program.description}\n",
        parse_mode="HTML",
    )


def process_programs(page: str) -> list[BugBountyProgram]:
    """
    Запрашивает и обрабатывает программы с указанной страницы

    :param page: URL страницы для проверки
    :return: Список программ
    """
    logger.info(f"Проверка страницы: {page}")
    programs = fetcher.fetch_programs(page=page)
    new_programs = [p for p in programs if p not in known_programs]

    for program in new_programs:
        known_programs.add(program)
        logger.info(f"Найдена новая программа: {program.name}")
        asyncio.create_task(send_program_notification(program))

    return new_programs


async def check_new_programs():
    """
    Проверяет новые программы на страницах и уведомляет пользователя
    Проверяет вторую страницу только если найдены новые программы на первой
    """
    global known_programs

    while True:
        first_page_new_programs = process_programs(
            page="/programs/?sort=created_at"
        )

        if first_page_new_programs:
            process_programs(
                page="/programs/?sort=created_at&page=2"
            )

        await asyncio.sleep(settings.app.check_interval)


@router.message(aiogram.filters.Command("start"))
async def start_command(message: aiogram.types.Message):
    """
    Обработчик команды /start
    """
    await message.answer(
        "✅ Бот запущен и уведомляет о новых программах Bug Bounty!"
    )


async def main():
    """
    Главная функция запуска бота
    """
    dp.include_router(router)
    await initialize_known_programs()
    asyncio.create_task(check_new_programs())
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
