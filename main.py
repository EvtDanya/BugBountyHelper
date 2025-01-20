import asyncio
import requests
from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message
from aiogram.filters import Command
from bs4 import BeautifulSoup
from dataclasses import dataclass
import logging

from src.config import settings
from src.logging import init_logging

logger = logging.getLogger(__name__)
init_logging(logger)

bot = Bot(token=settings.app.bot_token)
dp = Dispatcher()
router = Router()


@dataclass
class BugBountyProgram(object):
    program_type: str = "Bug Bounty"
    name: str = None
    company: str = None
    description: str = None
    reward: str = None
    url: str = None

    def __init__(
        self,
        name: str,
        company: str,
        description: str,
        reward: str,
        url: str
    ):
        """
        Initialize an object
        """
        self.name = name
        self.company = company
        self.description = description
        self.reward = reward
        self.url = url

        self._check_type()

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name

    def _check_type(self):
        if self.company == "Кибериспытание":
            self.company = self.name
            self.program_type = "Кибериспытание"


known_programs: set[BugBountyProgram] = set()


def fetch_programs(page: str = None):
    """
    Функция для получения списка программ standoff365
    """
    try:
        url = f"{settings.app.bug_bounty_url}/programs"
        if page:
            url = f"{url}{page}"

        headers = {
            'Accept-Language': 'ru-RU'
        }

        logger.debug(f"Запрос к {url}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        logger.debug(f"Ответ: {response.text[:200]}...")

        soup = BeautifulSoup(response.text, 'lxml')
        programs = []

        for program in soup.select('.link-no-color.flex.h-full'):
            try:
                name = program.select_one(
                    '[data-testid="programName"]'
                ).get_text(strip=True)

                company = program.select_one(
                    '[data-testid="vendorName"]'
                ).get_text(strip=True)

                description = program.select_one(
                    '.ProgramCard_cardDescription__l7AfK'
                ).get_text(strip=True)

                reward = program.select_one(
                    '[data-testid="minMaxRewardsText"]'
                ).get_text(strip=True)

                url = program['href']

                new_program = BugBountyProgram(
                    name=name,
                    company=company,
                    description=description,
                    reward=reward,
                    url=url
                )

                programs.append(new_program)
            except Exception as inner_e:
                logger.warning(
                    f"Ошибка при обработке карточки программы: {inner_e}"
                )
                continue

        logger.debug(f"Полученные программы: {programs}")
        return programs
    except Exception as e:
        logger.error(f"Ошибка при запросе данных программ: {e}")
        return []


async def check_new_programs(page: str = None):
    """
    Функция для проверки новых программ и уведомления standoff365
    """
    global known_programs
    while True:
        programs = fetch_programs(page)
        new_programs = [p for p in programs if p not in known_programs]

        for program in new_programs:
            known_programs.add(program)
            logger.info(f"Найдена новая программа: {program.name}")

            await bot.send_message(
                settings.app.user_id,
                f"Платформа <b>Standoff365</b>\n\n"
                f"<b>Тип:</b> {program.program_type}\n"
                f"<b>Название:</b> {program.name}\n"
                f"<b>Компания:</b> {program.company}\n"
                f"<b>Максимальное вознаграждение:</b> {program.reward}\n"
                f"<b>Ссылка:</b> <a href=\"{settings.app.bug_bounty_url}{program.url}\">{program.url}</a>\n\n"  # noqa
                f"<b>Описание:</b> {program.description}\n",
                parse_mode="HTML"
            )

        await asyncio.sleep(settings.app.check_interval)


@router.message(Command("start"))
async def start_command(message: Message):
    """
    Обработчик команды /start
    """
    await message.answer(
        "Бот запущен! Я буду уведомлять о новых программах bug bounty")


async def main():
    """
    Главная функция запуска бота
    """
    dp.include_router(router)
    asyncio.create_task(check_new_programs(page="/?sort=created_at"))
    asyncio.create_task(check_new_programs(page="/?sort=created_at&page=2"))
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
