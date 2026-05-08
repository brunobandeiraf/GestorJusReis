"""Cliente HTTP para a API pública DataJud do CNJ.

Este módulo implementa a comunicação com a API DataJud, que utiliza
Elasticsearch como motor de busca e cobre todos os tribunais brasileiros.

Endpoint pattern: POST {base_url}/api_publica_{sigla_tribunal}/_search
Autenticação: Header Authorization com ApiKey
"""

import logging
import re
import time
from dataclasses import dataclass, field
from typing import List, Optional

import requests
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_fixed,
)

from app.services.cnj_validator import extrair_tribunal, validar_numero_cnj
from app.utils.tribunal_mapper import obter_endpoint_tribunal

logger = logging.getLogger(__name__)


# --- Exceções customizadas ---


class DataJudAPIError(Exception):
    """Erro genérico de comunicação com a DataJud API."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class DataJudTimeoutError(DataJudAPIError):
    """Timeout na comunicação com a DataJud API."""

    def __init__(self, message: str = "Timeout na requisição à DataJud API"):
        super().__init__(message)


class DataJudNotFoundError(DataJudAPIError):
    """Processo não encontrado na DataJud API."""

    def __init__(self, numero_cnj: str):
        super().__init__(f"Processo não encontrado: {numero_cnj}", status_code=404)
        self.numero_cnj = numero_cnj


# --- DTOs ---


@dataclass
class MovimentacaoDTO:
    """Representa uma movimentação/andamento processual."""

    data: str
    nome: str
    complemento: Optional[str] = None


@dataclass
class ParteDTO:
    """Representa uma parte envolvida no processo."""

    nome: str
    tipo: str
    polo: Optional[str] = None
    advogados: List[str] = field(default_factory=list)


@dataclass
class ProcessoDTO:
    """Representa os dados de um processo judicial retornados pela API."""

    numero_cnj: str
    tribunal: str
    classe: str
    assunto: str
    partes: List[ParteDTO] = field(default_factory=list)
    movimentacoes: List[MovimentacaoDTO] = field(default_factory=list)
    valor_causa: Optional[str] = None
    data_ajuizamento: Optional[str] = None


@dataclass
class HealthStatus:
    """Status de saúde da conexão com a DataJud API."""

    disponivel: bool
    latencia_ms: int
    mensagem: str


# --- Retry helpers ---


def _should_retry_for_query(exception: BaseException) -> bool:
    """Determina se uma exceção deve ser retentada para consultas do usuário.

    Retry on:
    - DataJudAPIError com status_code >= 500 ou 429 (rate limit)
    - DataJudTimeoutError
    - ConnectionError

    Do NOT retry on:
    - HTTP 401/403 (auth errors)
    - HTTP 404 (not found)
    - ValueError (invalid CNJ)
    - DataJudNotFoundError
    """
    if isinstance(exception, DataJudTimeoutError):
        return True
    if isinstance(exception, ConnectionError):
        return True
    if isinstance(exception, DataJudNotFoundError):
        return False
    if isinstance(exception, DataJudAPIError):
        if exception.status_code is not None:
            if exception.status_code in (401, 403):
                return False
            if exception.status_code >= 500 or exception.status_code == 429:
                return True
        return False
    return False


def _should_retry_for_monitoring(exception: BaseException) -> bool:
    """Determina se uma exceção deve ser retentada para monitoramento.

    Same logic as query retry but used with different stop/wait config.
    """
    return _should_retry_for_query(exception)


# --- Cliente ---


class DataJudClient:
    """Cliente para a API pública DataJud do CNJ.

    Realiza consultas de processos judiciais via Elasticsearch Query DSL.
    Utiliza autenticação por ApiKey no header Authorization.
    """

    BASE_URL = "https://api-publica.datajud.cnj.jus.br"
    API_KEY = "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="
    TIMEOUT = 30  # segundos

    def __init__(self):
        """Inicializa o cliente com headers de autenticação."""
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"ApiKey {self.API_KEY}",
            "Content-Type": "application/json",
        })

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_fixed(3),
        retry=retry_if_exception(_should_retry_for_query),
        reraise=True,
    )
    def buscar_processo(self, numero_cnj: str) -> Optional[ProcessoDTO]:
        """Busca um processo pelo número CNJ na DataJud API.

        Retry policy (user-facing queries):
        - Max 2 attempts, 3 seconds wait between attempts
        - Retries on: 5xx errors, 429 rate limit, timeout, connection errors
        - Does NOT retry on: 401/403, 404, ValueError

        Args:
            numero_cnj: Número do processo no formato NNNNNNN-DD.AAAA.J.TR.OOOO

        Returns:
            ProcessoDTO com dados do processo ou None se não encontrado.

        Raises:
            ValueError: Se o número CNJ é inválido.
            DataJudAPIError: Em caso de erro de comunicação.
            DataJudTimeoutError: Em caso de timeout.
            DataJudNotFoundError: Se o processo não é encontrado (HTTP 404).
        """
        return self._buscar_processo_interno(numero_cnj)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1800),  # 30 minutos
        retry=retry_if_exception(_should_retry_for_monitoring),
        reraise=True,
    )
    def buscar_processo_monitoramento(self, numero_cnj: str) -> Optional[ProcessoDTO]:
        """Busca um processo com retry configurado para monitoramento diário.

        Retry policy (monitoring):
        - Max 3 attempts, 30 minutes wait between attempts
        - Retries on: 5xx errors, 429 rate limit, timeout, connection errors
        - Does NOT retry on: 401/403, 404, ValueError

        Args:
            numero_cnj: Número do processo no formato NNNNNNN-DD.AAAA.J.TR.OOOO

        Returns:
            ProcessoDTO com dados do processo ou None se não encontrado.

        Raises:
            ValueError: Se o número CNJ é inválido.
            DataJudAPIError: Em caso de erro de comunicação.
            DataJudTimeoutError: Em caso de timeout.
            DataJudNotFoundError: Se o processo não é encontrado (HTTP 404).
        """
        return self._buscar_processo_interno(numero_cnj)

    def _buscar_processo_interno(self, numero_cnj: str) -> Optional[ProcessoDTO]:
        """Lógica interna de busca de processo (sem retry).

        Args:
            numero_cnj: Número do processo no formato NNNNNNN-DD.AAAA.J.TR.OOOO

        Returns:
            ProcessoDTO com dados do processo ou None se não encontrado.

        Raises:
            ValueError: Se o número CNJ é inválido.
            DataJudAPIError: Em caso de erro de comunicação.
            DataJudTimeoutError: Em caso de timeout.
            DataJudNotFoundError: Se o processo não é encontrado (HTTP 404).
        """
        if not validar_numero_cnj(numero_cnj):
            raise ValueError(f"Número CNJ inválido: {numero_cnj}")

        # Identifica o tribunal e obtém o endpoint correto
        codigo_tribunal = extrair_tribunal(numero_cnj)
        endpoint = obter_endpoint_tribunal(codigo_tribunal)

        # Monta a query Elasticsearch DSL
        # A API DataJud armazena números sem formatação (20 dígitos puros)
        numero_busca = re.sub(r'\D', '', numero_cnj)
        query_body = {
            "query": {
                "match": {
                    "numeroProcesso": numero_busca
                }
            }
        }

        try:
            response = self._session.post(
                endpoint,
                json=query_body,
                timeout=self.TIMEOUT,
            )
        except requests.exceptions.Timeout:
            raise DataJudTimeoutError()
        except requests.exceptions.ConnectionError as e:
            raise DataJudAPIError(f"Erro de conexão com a DataJud API: {e}")
        except requests.exceptions.RequestException as e:
            raise DataJudAPIError(f"Erro na requisição à DataJud API: {e}")

        # Trata códigos de erro HTTP
        if response.status_code == 404:
            raise DataJudNotFoundError(numero_cnj)
        if response.status_code in (401, 403):
            raise DataJudAPIError(
                f"Erro de autenticação na DataJud API (HTTP {response.status_code})",
                status_code=response.status_code,
            )
        if response.status_code == 429:
            raise DataJudAPIError(
                "Rate limit excedido na DataJud API",
                status_code=429,
            )
        if response.status_code >= 500:
            raise DataJudAPIError(
                f"Erro interno da DataJud API (HTTP {response.status_code})",
                status_code=response.status_code,
            )
        if response.status_code != 200:
            raise DataJudAPIError(
                f"Resposta inesperada da DataJud API (HTTP {response.status_code})",
                status_code=response.status_code,
            )

        # Parse da resposta JSON com validation
        data = response.json()
        self._validar_estrutura_resposta(data, numero_cnj)
        return self._parse_response(data, numero_cnj)

    def health_check(self) -> HealthStatus:
        """Verifica conectividade com a DataJud API.

        Realiza uma requisição leve ao endpoint do TJSP para medir latência
        e verificar disponibilidade.

        Returns:
            HealthStatus com informações de disponibilidade e latência.
        """
        endpoint = obter_endpoint_tribunal("8.26")  # TJSP como referência

        # Query mínima para testar conectividade
        query_body = {
            "query": {
                "match": {
                    "numeroProcesso": "0000000-00.0000.0.00.0000"
                }
            }
        }

        start_time = time.time()

        try:
            response = self._session.post(
                endpoint,
                json=query_body,
                timeout=self.TIMEOUT,
            )
            latencia_ms = int((time.time() - start_time) * 1000)

            if response.status_code == 200:
                return HealthStatus(
                    disponivel=True,
                    latencia_ms=latencia_ms,
                    mensagem="DataJud API disponível",
                )
            else:
                return HealthStatus(
                    disponivel=False,
                    latencia_ms=latencia_ms,
                    mensagem=f"DataJud API retornou HTTP {response.status_code}",
                )

        except requests.exceptions.Timeout:
            latencia_ms = int((time.time() - start_time) * 1000)
            return HealthStatus(
                disponivel=False,
                latencia_ms=latencia_ms,
                mensagem="Timeout na conexão com DataJud API",
            )
        except requests.exceptions.RequestException as e:
            latencia_ms = int((time.time() - start_time) * 1000)
            return HealthStatus(
                disponivel=False,
                latencia_ms=latencia_ms,
                mensagem=f"Erro de conexão: {e}",
            )

    def _validar_estrutura_resposta(self, data: dict, numero_cnj: str) -> None:
        """Valida que a resposta da API tem a estrutura esperada.

        Verifica a presença dos campos obrigatórios: hits, hits.hits, _source.
        Loga erro detalhado quando a estrutura não corresponde ao esperado.

        Args:
            data: Dicionário com a resposta JSON da API.
            numero_cnj: Número CNJ buscado (para referência no log).

        Raises:
            DataJudAPIError: Se a estrutura da resposta é inválida.
        """
        campos_ausentes = []

        if not isinstance(data, dict):
            logger.error(
                "Resposta da DataJud API não é um dicionário JSON válido "
                "para processo %s. Tipo recebido: %s",
                numero_cnj,
                type(data).__name__,
            )
            raise DataJudAPIError(
                f"Resposta da DataJud API com estrutura inválida: "
                f"esperado dicionário, recebido {type(data).__name__}"
            )

        if "hits" not in data:
            campos_ausentes.append("hits")
        else:
            hits = data["hits"]
            if not isinstance(hits, dict):
                campos_ausentes.append("hits (tipo inválido)")
            else:
                if "hits" not in hits:
                    campos_ausentes.append("hits.hits")
                else:
                    hits_list = hits["hits"]
                    if not isinstance(hits_list, list):
                        campos_ausentes.append("hits.hits (tipo inválido, esperado lista)")
                    elif len(hits_list) > 0:
                        first_hit = hits_list[0]
                        if not isinstance(first_hit, dict):
                            campos_ausentes.append("hits.hits[0] (tipo inválido)")
                        elif "_source" not in first_hit:
                            campos_ausentes.append("hits.hits[0]._source")

        if campos_ausentes:
            campos_str = ", ".join(campos_ausentes)
            logger.error(
                "Resposta da DataJud API com estrutura inesperada para processo %s. "
                "Campos ausentes ou inválidos: %s. "
                "Possível alteração na API.",
                numero_cnj,
                campos_str,
            )
            raise DataJudAPIError(
                f"Resposta da DataJud API com estrutura inválida. "
                f"Campos ausentes ou inválidos: {campos_str}"
            )

    def _parse_response(
        self, data: dict, numero_cnj: str
    ) -> Optional[ProcessoDTO]:
        """Faz o parsing da resposta JSON da DataJud API para o DTO interno.

        Args:
            data: Dicionário com a resposta JSON da API.
            numero_cnj: Número CNJ buscado (para referência).

        Returns:
            ProcessoDTO com os dados parseados ou None se não encontrado.
        """
        hits = data.get("hits", {})
        total = hits.get("total", {})

        # Verifica se encontrou resultados
        total_value = total.get("value", 0) if isinstance(total, dict) else total
        if total_value == 0:
            return None

        hit_list = hits.get("hits", [])
        if not hit_list:
            return None

        source = hit_list[0].get("_source", {})
        if not source:
            return None

        # Extrai dados do processo
        classe_obj = source.get("classe", {})
        classe = classe_obj.get("nome", "") if isinstance(classe_obj, dict) else str(classe_obj)

        assuntos = source.get("assuntos", [])
        assunto = ""
        if assuntos and isinstance(assuntos, list) and len(assuntos) > 0:
            primeiro_assunto = assuntos[0]
            assunto = primeiro_assunto.get("nome", "") if isinstance(primeiro_assunto, dict) else str(primeiro_assunto)

        tribunal = source.get("tribunal", "")
        valor_causa = source.get("valorCausa", None)
        if valor_causa is not None:
            valor_causa = str(valor_causa)

        data_ajuizamento = source.get("dataAjuizamento", None)

        # Extrai movimentações
        movimentacoes = self._parse_movimentacoes(source.get("movimentos", []))

        # Extrai partes
        partes = self._parse_partes(source.get("partes", []))

        return ProcessoDTO(
            numero_cnj=numero_cnj,
            tribunal=tribunal,
            classe=classe,
            assunto=assunto,
            partes=partes,
            movimentacoes=movimentacoes,
            valor_causa=valor_causa,
            data_ajuizamento=data_ajuizamento,
        )

    def _parse_movimentacoes(self, movimentos: list) -> List[MovimentacaoDTO]:
        """Faz o parsing da lista de movimentações da resposta da API.

        Args:
            movimentos: Lista de dicionários com dados de movimentações.

        Returns:
            Lista de MovimentacaoDTO.
        """
        resultado = []
        if not isinstance(movimentos, list):
            return resultado

        for mov in movimentos:
            if not isinstance(mov, dict):
                continue

            data = mov.get("dataHora", "")
            nome = mov.get("nome", "")

            # Monta complemento a partir dos complementos tabelados
            complementos = mov.get("complementosTabelados", [])
            complemento = None
            if complementos and isinstance(complementos, list):
                partes_complemento = []
                for comp in complementos:
                    if isinstance(comp, dict):
                        valor = comp.get("valor", "")
                        if valor:
                            partes_complemento.append(str(valor))
                if partes_complemento:
                    complemento = "; ".join(partes_complemento)

            resultado.append(MovimentacaoDTO(
                data=data,
                nome=nome,
                complemento=complemento,
            ))

        return resultado

    def _parse_partes(self, partes_raw: list) -> List[ParteDTO]:
        """Faz o parsing da lista de partes da resposta da API.

        Args:
            partes_raw: Lista de dicionários com dados das partes.

        Returns:
            Lista de ParteDTO.
        """
        resultado = []
        if not isinstance(partes_raw, list):
            return resultado

        for parte in partes_raw:
            if not isinstance(parte, dict):
                continue

            nome = parte.get("nome", "")
            tipo = parte.get("tipo", "")

            # Determina o polo com base no tipo
            polo = self._inferir_polo(tipo)

            # Extrai advogados
            advogados_raw = parte.get("advogados", [])
            advogados = []
            if isinstance(advogados_raw, list):
                for adv in advogados_raw:
                    if isinstance(adv, dict):
                        nome_adv = adv.get("nome", "")
                        if nome_adv:
                            advogados.append(nome_adv)
                    elif isinstance(adv, str):
                        advogados.append(adv)

            resultado.append(ParteDTO(
                nome=nome,
                tipo=tipo,
                polo=polo,
                advogados=advogados,
            ))

        return resultado

    @staticmethod
    def _inferir_polo(tipo: str) -> Optional[str]:
        """Infere o polo processual com base no tipo da parte.

        Args:
            tipo: Tipo da parte (ex: "AUTOR", "REU", "TERCEIRO").

        Returns:
            Polo inferido ("ativo", "passivo", "terceiro") ou None.
        """
        tipo_upper = tipo.upper() if tipo else ""
        if tipo_upper in ("AUTOR", "REQUERENTE", "EXEQUENTE", "RECLAMANTE"):
            return "ativo"
        elif tipo_upper in ("REU", "RÉU", "REQUERIDO", "EXECUTADO", "RECLAMADO"):
            return "passivo"
        elif tipo_upper in ("TERCEIRO", "INTERESSADO"):
            return "terceiro"
        return None
