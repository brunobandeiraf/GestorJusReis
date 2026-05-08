"""Registry de scrapers disponíveis por tribunal."""

from typing import Dict, List

from app.services.scraping.base import TribunalScraper
from app.services.scraping.exceptions import TribunalNaoSuportadoError


class ScraperRegistry:
    """Registro de scrapers disponíveis por tribunal.

    Permite adicionar novos scrapers sem modificar código existente.
    """

    def __init__(self):
        self._scrapers: Dict[str, TribunalScraper] = {}

    def registrar(self, scraper: TribunalScraper) -> None:
        """Registra um scraper no registry."""
        self._scrapers[scraper.tribunal_id] = scraper

    def obter(self, tribunal_id: str) -> TribunalScraper:
        """Obtém scraper pelo ID do tribunal.

        Raises:
            TribunalNaoSuportadoError: Se não há scraper para o tribunal.
        """
        if tribunal_id not in self._scrapers:
            raise TribunalNaoSuportadoError(tribunal_id)
        return self._scrapers[tribunal_id]

    def listar_disponiveis(self) -> List[dict]:
        """Lista tribunais com scraper disponível.

        Returns:
            Lista de {id, nome} dos tribunais suportados.
        """
        return [
            {"id": scraper.tribunal_id, "nome": scraper.tribunal_nome}
            for scraper in self._scrapers.values()
        ]
