"""Pacote de scraping de tribunais para busca de processos por CPF."""

from app.services.scraping.base import TribunalScraper
from app.services.scraping.cpf_validator import CPFValidator
from app.services.scraping.exceptions import (
    CaptchaDetectadoError,
    CPFInvalidoError,
    ScrapingError,
    TribunalIndisponivelError,
    TribunalNaoSuportadoError,
)
from app.services.scraping.models import ProcessoEncontrado
from app.services.scraping.rate_limiter import RateLimiter
from app.services.scraping.registry import ScraperRegistry

__all__ = [
    "TribunalScraper",
    "ProcessoEncontrado",
    "ScraperRegistry",
    "RateLimiter",
    "CPFValidator",
    "TribunalIndisponivelError",
    "CaptchaDetectadoError",
    "ScrapingError",
    "TribunalNaoSuportadoError",
    "CPFInvalidoError",
]
