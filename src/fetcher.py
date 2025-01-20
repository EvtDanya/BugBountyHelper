import requests
from bs4 import BeautifulSoup
from typing import List
import logging

from .models import BugBountyProgram

logger = logging.getLogger("bbHelper")


class BugBountyFetcher:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def fetch_programs(self, page: str) -> List[BugBountyProgram]:
        """
        Функция для получения списка программ standoff365
        """
        url = f"{self.base_url}{page}"

        headers = {"Accept-Language": "ru-RU"}
        logger.debug(f"Запрос к {url}")

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            logger.debug(f"Ответ: {response.text[:200]}...")
            soup = BeautifulSoup(response.text, "lxml")

            return self._parse_programs(soup)

        except requests.RequestException as e:
            logger.error(f"Ошибка при запросе данных: {e}")
            return []

    def _parse_programs(self, soup: BeautifulSoup) -> List[BugBountyProgram]:
        """
        Функция для парсинга HTML-кода
        """
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
                url = program["href"]

                programs.append(
                    BugBountyProgram(
                        name=name,
                        company=company,
                        description=description,
                        reward=reward,
                        url=url
                    )
                )
            except Exception as e:
                logger.warning(f"Ошибка при обработке программы: {e}")
                continue

        return programs
