"""Abstract Base Class para scrapers de tribunais."""

from abc import ABC, abstractmethod
from typing import List

from app.services.scraping.models import ProcessoEncontrado


class TribunalScraper(ABC):
    """Interface abstrata para scrapers de tribunais.

    Cada tribunal que suporta busca por CPF deve implementar
    esta interface com sua lógica específica de scraping.
    """

    @property
    @abstractmethod
    def tribunal_id(self) -> str:
        """Identificador único do tribunal (ex: 'tjsp')."""
        ...

    @property
    @abstractmethod
    def tribunal_nome(self) -> str:
        """Nome legível do tribunal (ex: 'TJSP - Tribunal de Justiça de São Paulo')."""
        ...

    @abstractmethod
    def buscar_por_cpf(self, cpf: str) -> List[ProcessoEncontrado]:
        """Busca processos associados a um CPF no tribunal.

        Args:
            cpf: CPF normalizado (11 dígitos numéricos, já validado).

        Returns:
            Lista de ProcessoEncontrado com dados extraídos.

        Raises:
            TribunalIndisponivelError: Tribunal offline ou timeout.
            CaptchaDetectadoError: Tribunal exigindo CAPTCHA.
            ScrapingError: Erro ao interpretar resposta do tribunal.
        """
        ...
