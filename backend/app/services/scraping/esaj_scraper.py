"""Scraper para o sistema ESAJ do TJSP."""

import logging
from typing import List

import requests
from bs4 import BeautifulSoup

from app.services.scraping.base import TribunalScraper
from app.services.scraping.exceptions import (
    CaptchaDetectadoError,
    ScrapingError,
    TribunalIndisponivelError,
)
from app.services.scraping.models import ProcessoEncontrado
from app.services.scraping.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class ESAJScraperTJSP(TribunalScraper):
    """Scraper para o sistema ESAJ do TJSP.

    URL base: https://esaj.tjsp.jus.br/cpopg/search.do
    Método de busca: GET com parâmetros de documento da parte.
    """

    BASE_URL = "https://esaj.tjsp.jus.br/cpopg/search.do"
    TIMEOUT = 30  # segundos

    def __init__(self, rate_limiter: RateLimiter):
        self._rate_limiter = rate_limiter
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; MonitorJudicial/1.0)",
        })

    @property
    def tribunal_id(self) -> str:
        return "tjsp"

    @property
    def tribunal_nome(self) -> str:
        return "TJSP - Tribunal de Justiça de São Paulo"

    def buscar_por_cpf(self, cpf: str) -> List[ProcessoEncontrado]:
        """Busca processos por CPF no ESAJ/TJSP.

        Fluxo:
        1. Envia requisição de busca com CPF como documento da parte
        2. Parseia HTML de resultados com BeautifulSoup
        3. Se há paginação, navega por todas as páginas
        4. Retorna lista consolidada de processos

        Args:
            cpf: CPF normalizado (11 dígitos numéricos, já validado).

        Returns:
            Lista de ProcessoEncontrado com dados extraídos.

        Raises:
            TribunalIndisponivelError: Tribunal offline ou timeout.
            CaptchaDetectadoError: Tribunal exigindo CAPTCHA.
            ScrapingError: Erro ao interpretar resposta do tribunal.
        """
        self._rate_limiter.aguardar()
        html = self._fazer_requisicao_busca(cpf, pagina=1)

        if self._detectar_captcha(html):
            raise CaptchaDetectadoError(tribunal="tjsp")

        total_paginas = self._obter_total_paginas(html)
        processos = self._parsear_resultados(html)

        for pagina in range(2, total_paginas + 1):
            self._rate_limiter.aguardar_paginacao()
            html_pagina = self._fazer_requisicao_busca(cpf, pagina=pagina)

            if self._detectar_captcha(html_pagina):
                raise CaptchaDetectadoError(tribunal="tjsp")

            processos.extend(self._parsear_resultados(html_pagina))

        return processos

    def _fazer_requisicao_busca(self, cpf: str, pagina: int = 1) -> str:
        """Faz requisição ao ESAJ e retorna HTML da resposta.

        Args:
            cpf: CPF normalizado (11 dígitos).
            pagina: Número da página de resultados (1-indexed).

        Returns:
            HTML da resposta como string.

        Raises:
            TribunalIndisponivelError: Timeout ou erro de conexão.
        """
        params = {
            "conversationId": "",
            "dadosConsulta.localPesquisa.cdLocal": "-1",
            "cbPesquisa": "DOCPARTE",
            "dadosConsulta.tipoNuProcesso": "UNIFICADO",
            "numeroDigitoAnoUnificado": "",
            "foroNumeroUnificado": "",
            "dadosConsulta.valorConsultaNuUnificado": "",
            "dadosConsulta.valorConsulta": cpf,
            "paginaConsulta": str(pagina),
        }

        try:
            response = self._session.get(
                self.BASE_URL,
                params=params,
                timeout=self.TIMEOUT,
            )
            response.raise_for_status()
            return response.text
        except requests.exceptions.Timeout:
            logger.error(
                "Timeout ao consultar ESAJ/TJSP (CPF: ***.***%s)",
                f".{cpf[6:9]}-{cpf[9:]}",
            )
            raise TribunalIndisponivelError(
                tribunal="tjsp",
                motivo="Timeout na conexão com o ESAJ",
            )
        except requests.exceptions.ConnectionError:
            logger.error(
                "Erro de conexão ao consultar ESAJ/TJSP (CPF: ***.***%s)",
                f".{cpf[6:9]}-{cpf[9:]}",
            )
            raise TribunalIndisponivelError(
                tribunal="tjsp",
                motivo="Erro de conexão com o ESAJ",
            )
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response is not None else 0
            logger.error(
                "HTTP %d ao consultar ESAJ/TJSP (CPF: ***.***%s)",
                status_code,
                f".{cpf[6:9]}-{cpf[9:]}",
            )
            raise TribunalIndisponivelError(
                tribunal="tjsp",
                motivo=f"HTTP {status_code} retornado pelo ESAJ",
            )

    def _parsear_resultados(self, html: str) -> List[ProcessoEncontrado]:
        """Extrai processos do HTML de resultados do ESAJ.

        Args:
            html: HTML da página de resultados.

        Returns:
            Lista de ProcessoEncontrado extraídos.

        Raises:
            ScrapingError: Estrutura HTML inesperada.
        """
        soup = BeautifulSoup(html, "html.parser")

        container = soup.find("div", id="listagemDeProcessos")
        if container is None:
            # Check if it's a "no results" page
            mensagem = soup.find("div", id="mensagemRetorno")
            if mensagem is None:
                mensagem = soup.find(string=lambda t: t and "Não existem informações" in t)
            if mensagem is not None:
                return []
            raise ScrapingError(
                tribunal="tjsp",
                detalhes="Container de resultados não encontrado no HTML",
            )

        processos_divs = container.find_all(
            "div", class_=lambda c: c and ("fundoClaro" in c or "fundoEscuro" in c)
        )

        if not processos_divs:
            return []

        processos = []
        for div in processos_divs:
            try:
                processo = self._extrair_processo(div)
                processos.append(processo)
            except Exception as e:
                logger.warning(
                    "Erro ao extrair processo individual: %s", str(e)
                )
                continue

        return processos

    def _extrair_processo(self, div) -> ProcessoEncontrado:
        """Extrai dados de um processo individual do HTML.

        Args:
            div: Elemento BeautifulSoup representando um processo.

        Returns:
            ProcessoEncontrado com dados extraídos.
        """
        # Extract process number from link
        link = div.find("a", class_="linkProcesso")
        numero_cnj = link.get_text(strip=True) if link else ""

        # Extract labeled fields
        classe = self._extrair_campo_label(div, "Classe")
        assunto = self._extrair_campo_label(div, "Assunto")
        vara = self._extrair_campo_label(div, "Vara")

        return ProcessoEncontrado(
            numero_cnj=numero_cnj,
            classe=classe,
            assunto=assunto,
            vara=vara if vara else None,
        )

    def _extrair_campo_label(self, div, label: str) -> str:
        """Extrai o valor de um campo com label no HTML do ESAJ.

        O ESAJ usa o padrão:
            <span class="labelClass">Label:</span> Valor

        Args:
            div: Elemento BeautifulSoup do processo.
            label: Nome do label a buscar (ex: "Classe").

        Returns:
            Valor do campo ou string vazia se não encontrado.
        """
        span = div.find("span", class_="labelClass", string=lambda t: t and label in t)
        if span is None:
            return ""

        # The value is the next sibling text node after the span
        next_sibling = span.next_sibling
        if next_sibling is None:
            return ""

        # Handle NavigableString (text node)
        text = str(next_sibling).strip()
        return text

    def _detectar_captcha(self, html: str) -> bool:
        """Verifica se a resposta contém CAPTCHA.

        Args:
            html: HTML da resposta.

        Returns:
            True se CAPTCHA detectado, False caso contrário.
        """
        soup = BeautifulSoup(html, "html.parser")

        # Check for common CAPTCHA indicators
        captcha_indicators = [
            soup.find("div", id="captcha"),
            soup.find("div", class_="g-recaptcha"),
            soup.find("img", id="captchaImg"),
            soup.find("input", {"name": "captcha"}),
            soup.find("div", id="divCaptcha"),
        ]

        if any(indicator is not None for indicator in captcha_indicators):
            return True

        # Check for captcha-related text
        html_lower = html.lower()
        if "captcha" in html_lower and ("digite" in html_lower or "informe" in html_lower):
            return True

        return False

    def _obter_total_paginas(self, html: str) -> int:
        """Extrai número total de páginas dos resultados.

        Args:
            html: HTML da primeira página de resultados.

        Returns:
            Número total de páginas (mínimo 1).
        """
        soup = BeautifulSoup(html, "html.parser")

        paginacao = soup.find("div", id="paginacaoSuperior")
        if paginacao is None:
            return 1

        links = paginacao.find_all("a", class_="paginacao")
        if not links:
            return 1

        # Find the highest page number
        max_pagina = 1
        for link in links:
            texto = link.get_text(strip=True)
            try:
                pagina = int(texto)
                if pagina > max_pagina:
                    max_pagina = pagina
            except ValueError:
                continue

        return max_pagina
