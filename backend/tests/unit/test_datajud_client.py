"""Testes unitários para o cliente DataJud API.

Todos os testes mockam as chamadas HTTP para evitar dependência da API real.
"""

from unittest.mock import MagicMock, patch

import pytest
import requests

from backend.app.services.datajud_client import (
    DataJudAPIError,
    DataJudClient,
    DataJudNotFoundError,
    DataJudTimeoutError,
    HealthStatus,
    MovimentacaoDTO,
    ParteDTO,
    ProcessoDTO,
    _should_retry_for_query,
)


# --- Fixtures ---


@pytest.fixture
def client():
    """Cria uma instância do DataJudClient para testes."""
    return DataJudClient()


@pytest.fixture
def sample_api_response():
    """Resposta de exemplo da DataJud API."""
    return {
        "hits": {
            "total": {"value": 1},
            "hits": [
                {
                    "_source": {
                        "numeroProcesso": "0001234-56.2023.8.26.0100",
                        "classe": {"codigo": 7, "nome": "Procedimento Comum Cível"},
                        "assuntos": [{"codigo": 899, "nome": "Direito Civil"}],
                        "tribunal": "TJSP",
                        "dataAjuizamento": "2023-03-15",
                        "valorCausa": 50000.00,
                        "movimentos": [
                            {
                                "codigo": 12345,
                                "nome": "Juntada de Petição",
                                "dataHora": "2024-01-10T14:30:00",
                                "complementosTabelados": [
                                    {"nome": "tipo_documento", "valor": "Petição Inicial"}
                                ],
                            },
                            {
                                "codigo": 12346,
                                "nome": "Distribuição",
                                "dataHora": "2023-03-15T10:00:00",
                                "complementosTabelados": [],
                            },
                        ],
                        "partes": [
                            {
                                "nome": "João da Silva",
                                "tipo": "AUTOR",
                                "advogados": [
                                    {"nome": "Maria Advogada", "inscricao": "OAB/SP 123456"}
                                ],
                            },
                            {
                                "nome": "Empresa XYZ Ltda",
                                "tipo": "REU",
                                "advogados": [
                                    {"nome": "Pedro Defensor", "inscricao": "OAB/SP 654321"}
                                ],
                            },
                        ],
                    }
                }
            ],
        }
    }


@pytest.fixture
def empty_api_response():
    """Resposta da API quando nenhum processo é encontrado."""
    return {
        "hits": {
            "total": {"value": 0},
            "hits": [],
        }
    }


# --- Testes de buscar_processo ---


class TestBuscarProcesso:
    """Testes para o método buscar_processo."""

    def test_busca_processo_com_sucesso(self, client, sample_api_response):
        """Deve retornar ProcessoDTO quando processo é encontrado."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_api_response

        with patch.object(client._session, "post", return_value=mock_response):
            resultado = client.buscar_processo("0001234-56.2023.8.26.0100")

        assert resultado is not None
        assert isinstance(resultado, ProcessoDTO)
        assert resultado.numero_cnj == "0001234-56.2023.8.26.0100"
        assert resultado.tribunal == "TJSP"
        assert resultado.classe == "Procedimento Comum Cível"
        assert resultado.assunto == "Direito Civil"
        assert resultado.valor_causa == "50000.0"
        assert resultado.data_ajuizamento == "2023-03-15"

    def test_busca_processo_partes(self, client, sample_api_response):
        """Deve parsear corretamente as partes do processo."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_api_response

        with patch.object(client._session, "post", return_value=mock_response):
            resultado = client.buscar_processo("0001234-56.2023.8.26.0100")

        assert len(resultado.partes) == 2
        autor = resultado.partes[0]
        assert autor.nome == "João da Silva"
        assert autor.tipo == "AUTOR"
        assert autor.polo == "ativo"
        assert "Maria Advogada" in autor.advogados

        reu = resultado.partes[1]
        assert reu.nome == "Empresa XYZ Ltda"
        assert reu.tipo == "REU"
        assert reu.polo == "passivo"
        assert "Pedro Defensor" in reu.advogados

    def test_busca_processo_movimentacoes(self, client, sample_api_response):
        """Deve parsear corretamente as movimentações."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_api_response

        with patch.object(client._session, "post", return_value=mock_response):
            resultado = client.buscar_processo("0001234-56.2023.8.26.0100")

        assert len(resultado.movimentacoes) == 2
        mov1 = resultado.movimentacoes[0]
        assert mov1.nome == "Juntada de Petição"
        assert mov1.data == "2024-01-10T14:30:00"
        assert mov1.complemento == "Petição Inicial"

        mov2 = resultado.movimentacoes[1]
        assert mov2.nome == "Distribuição"
        assert mov2.complemento is None

    def test_busca_processo_nao_encontrado(self, client, empty_api_response):
        """Deve retornar None quando processo não é encontrado na resposta."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = empty_api_response

        with patch.object(client._session, "post", return_value=mock_response):
            resultado = client.buscar_processo("0001234-56.2023.8.26.0100")

        assert resultado is None

    def test_busca_processo_http_404(self, client):
        """Deve levantar DataJudNotFoundError quando API retorna 404."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch.object(client._session, "post", return_value=mock_response):
            with pytest.raises(DataJudNotFoundError):
                client.buscar_processo("0001234-56.2023.8.26.0100")

    def test_busca_processo_numero_invalido(self, client):
        """Deve levantar ValueError para número CNJ inválido."""
        with pytest.raises(ValueError, match="Número CNJ inválido"):
            client.buscar_processo("numero-invalido")

    def test_busca_processo_timeout(self, client):
        """Deve levantar DataJudTimeoutError em caso de timeout."""
        with patch.object(
            client._session, "post", side_effect=requests.exceptions.Timeout()
        ):
            with pytest.raises(DataJudTimeoutError):
                client.buscar_processo("0001234-56.2023.8.26.0100")

    def test_busca_processo_erro_conexao(self, client):
        """Deve levantar DataJudAPIError em caso de erro de conexão."""
        with patch.object(
            client._session,
            "post",
            side_effect=requests.exceptions.ConnectionError("Connection refused"),
        ):
            with pytest.raises(DataJudAPIError, match="Erro de conexão"):
                client.buscar_processo("0001234-56.2023.8.26.0100")

    def test_busca_processo_http_401(self, client):
        """Deve levantar DataJudAPIError para erro de autenticação."""
        mock_response = MagicMock()
        mock_response.status_code = 401

        with patch.object(client._session, "post", return_value=mock_response):
            with pytest.raises(DataJudAPIError, match="autenticação"):
                client.buscar_processo("0001234-56.2023.8.26.0100")

    def test_busca_processo_http_403(self, client):
        """Deve levantar DataJudAPIError para erro de autorização."""
        mock_response = MagicMock()
        mock_response.status_code = 403

        with patch.object(client._session, "post", return_value=mock_response):
            with pytest.raises(DataJudAPIError, match="autenticação"):
                client.buscar_processo("0001234-56.2023.8.26.0100")

    def test_busca_processo_http_429(self, client):
        """Deve levantar DataJudAPIError para rate limit."""
        mock_response = MagicMock()
        mock_response.status_code = 429

        with patch.object(client._session, "post", return_value=mock_response):
            with pytest.raises(DataJudAPIError, match="Rate limit"):
                client.buscar_processo("0001234-56.2023.8.26.0100")

    def test_busca_processo_http_500(self, client):
        """Deve levantar DataJudAPIError para erro interno do servidor."""
        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch.object(client._session, "post", return_value=mock_response):
            with pytest.raises(DataJudAPIError, match="Erro interno"):
                client.buscar_processo("0001234-56.2023.8.26.0100")

    def test_busca_processo_endpoint_correto(self, client, sample_api_response):
        """Deve chamar o endpoint correto baseado no tribunal do CNJ."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_api_response

        with patch.object(client._session, "post", return_value=mock_response) as mock_post:
            client.buscar_processo("0001234-56.2023.8.26.0100")

        # Verifica que chamou o endpoint do TJSP
        call_args = mock_post.call_args
        assert "api_publica_tjsp/_search" in call_args[0][0]

    def test_busca_processo_query_body_correto(self, client, sample_api_response):
        """Deve enviar a query Elasticsearch DSL correta."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_api_response

        with patch.object(client._session, "post", return_value=mock_response) as mock_post:
            client.buscar_processo("0001234-56.2023.8.26.0100")

        call_kwargs = mock_post.call_args[1]
        expected_body = {
            "query": {
                "match": {
                    "numeroProcesso": "0001234-56.2023.8.26.0100"
                }
            }
        }
        assert call_kwargs["json"] == expected_body

    def test_busca_processo_timeout_configurado(self, client, sample_api_response):
        """Deve usar timeout de 30 segundos."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_api_response

        with patch.object(client._session, "post", return_value=mock_response) as mock_post:
            client.buscar_processo("0001234-56.2023.8.26.0100")

        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["timeout"] == 30


# --- Testes de retry ---


class TestRetryBehavior:
    """Testes para o comportamento de retry com tenacity."""

    def test_retry_on_http_500(self, client):
        """Deve fazer retry quando API retorna 500."""
        mock_response_500 = MagicMock()
        mock_response_500.status_code = 500

        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {
            "hits": {"total": {"value": 0}, "hits": []}
        }

        with patch.object(
            client._session, "post", side_effect=[mock_response_500, mock_response_200]
        ) as mock_post:
            resultado = client.buscar_processo("0001234-56.2023.8.26.0100")

        assert resultado is None
        assert mock_post.call_count == 2

    def test_retry_on_timeout(self, client):
        """Deve fazer retry quando ocorre timeout."""
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {
            "hits": {"total": {"value": 0}, "hits": []}
        }

        with patch.object(
            client._session,
            "post",
            side_effect=[requests.exceptions.Timeout(), mock_response_200],
        ) as mock_post:
            resultado = client.buscar_processo("0001234-56.2023.8.26.0100")

        assert resultado is None
        assert mock_post.call_count == 2

    def test_retry_on_rate_limit_429(self, client):
        """Deve fazer retry quando API retorna 429 (rate limit)."""
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429

        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {
            "hits": {"total": {"value": 0}, "hits": []}
        }

        with patch.object(
            client._session, "post", side_effect=[mock_response_429, mock_response_200]
        ) as mock_post:
            resultado = client.buscar_processo("0001234-56.2023.8.26.0100")

        assert resultado is None
        assert mock_post.call_count == 2

    def test_no_retry_on_http_401(self, client):
        """Não deve fazer retry quando API retorna 401."""
        mock_response = MagicMock()
        mock_response.status_code = 401

        with patch.object(client._session, "post", return_value=mock_response) as mock_post:
            with pytest.raises(DataJudAPIError, match="autenticação"):
                client.buscar_processo("0001234-56.2023.8.26.0100")

        assert mock_post.call_count == 1

    def test_no_retry_on_http_403(self, client):
        """Não deve fazer retry quando API retorna 403."""
        mock_response = MagicMock()
        mock_response.status_code = 403

        with patch.object(client._session, "post", return_value=mock_response) as mock_post:
            with pytest.raises(DataJudAPIError, match="autenticação"):
                client.buscar_processo("0001234-56.2023.8.26.0100")

        assert mock_post.call_count == 1

    def test_no_retry_on_http_404(self, client):
        """Não deve fazer retry quando API retorna 404."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch.object(client._session, "post", return_value=mock_response) as mock_post:
            with pytest.raises(DataJudNotFoundError):
                client.buscar_processo("0001234-56.2023.8.26.0100")

        assert mock_post.call_count == 1

    def test_no_retry_on_invalid_cnj(self, client):
        """Não deve fazer retry para número CNJ inválido."""
        with pytest.raises(ValueError, match="Número CNJ inválido"):
            client.buscar_processo("numero-invalido")

    def test_max_2_attempts_for_query(self, client):
        """Deve fazer no máximo 2 tentativas para consultas do usuário."""
        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch.object(client._session, "post", return_value=mock_response) as mock_post:
            with pytest.raises(DataJudAPIError, match="Erro interno"):
                client.buscar_processo("0001234-56.2023.8.26.0100")

        assert mock_post.call_count == 2

    def test_buscar_processo_monitoramento_exists(self, client, sample_api_response):
        """Deve ter método buscar_processo_monitoramento disponível."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_api_response

        with patch.object(client._session, "post", return_value=mock_response):
            resultado = client.buscar_processo_monitoramento("0001234-56.2023.8.26.0100")

        assert resultado is not None
        assert isinstance(resultado, ProcessoDTO)


# --- Testes de validação de estrutura da resposta ---


class TestValidacaoEstruturaResposta:
    """Testes para a validação de estrutura da resposta da API."""

    def test_resposta_valida_nao_levanta_erro(self, client):
        """Não deve levantar erro para resposta com estrutura válida."""
        data = {"hits": {"total": {"value": 0}, "hits": []}}
        # Não deve levantar exceção
        client._validar_estrutura_resposta(data, "0001234-56.2023.8.26.0100")

    def test_resposta_sem_campo_hits(self, client):
        """Deve levantar DataJudAPIError quando campo 'hits' está ausente."""
        data = {"other_field": "value"}
        with pytest.raises(DataJudAPIError, match="hits"):
            client._validar_estrutura_resposta(data, "0001234-56.2023.8.26.0100")

    def test_resposta_hits_tipo_invalido(self, client):
        """Deve levantar DataJudAPIError quando 'hits' não é dicionário."""
        data = {"hits": "not_a_dict"}
        with pytest.raises(DataJudAPIError, match="hits.*tipo inválido"):
            client._validar_estrutura_resposta(data, "0001234-56.2023.8.26.0100")

    def test_resposta_sem_hits_hits(self, client):
        """Deve levantar DataJudAPIError quando 'hits.hits' está ausente."""
        data = {"hits": {"total": {"value": 0}}}
        with pytest.raises(DataJudAPIError, match="hits.hits"):
            client._validar_estrutura_resposta(data, "0001234-56.2023.8.26.0100")

    def test_resposta_hits_hits_tipo_invalido(self, client):
        """Deve levantar DataJudAPIError quando 'hits.hits' não é lista."""
        data = {"hits": {"hits": "not_a_list"}}
        with pytest.raises(DataJudAPIError, match="hits.hits.*tipo inválido"):
            client._validar_estrutura_resposta(data, "0001234-56.2023.8.26.0100")

    def test_resposta_sem_source(self, client):
        """Deve levantar DataJudAPIError quando '_source' está ausente no primeiro hit."""
        data = {"hits": {"hits": [{"_id": "123"}]}}
        with pytest.raises(DataJudAPIError, match="_source"):
            client._validar_estrutura_resposta(data, "0001234-56.2023.8.26.0100")

    def test_resposta_hits_vazio_valida(self, client):
        """Não deve levantar erro quando hits.hits é lista vazia (sem resultados)."""
        data = {"hits": {"total": {"value": 0}, "hits": []}}
        # Não deve levantar exceção
        client._validar_estrutura_resposta(data, "0001234-56.2023.8.26.0100")

    def test_resposta_nao_dicionario(self, client):
        """Deve levantar DataJudAPIError quando resposta não é dicionário."""
        with pytest.raises(DataJudAPIError, match="estrutura inválida"):
            client._validar_estrutura_resposta("not_a_dict", "0001234-56.2023.8.26.0100")

    def test_resposta_hit_tipo_invalido(self, client):
        """Deve levantar DataJudAPIError quando primeiro hit não é dicionário."""
        data = {"hits": {"hits": ["not_a_dict"]}}
        with pytest.raises(DataJudAPIError, match="hits.hits\\[0\\].*tipo inválido"):
            client._validar_estrutura_resposta(data, "0001234-56.2023.8.26.0100")

    def test_resposta_completa_valida(self, client, sample_api_response):
        """Não deve levantar erro para resposta completa válida."""
        client._validar_estrutura_resposta(sample_api_response, "0001234-56.2023.8.26.0100")


# --- Testes de should_retry helpers ---


class TestShouldRetryHelpers:
    """Testes para as funções auxiliares de retry."""

    def test_should_retry_timeout_error(self):
        """Deve retornar True para DataJudTimeoutError."""
        assert _should_retry_for_query(DataJudTimeoutError()) is True

    def test_should_retry_connection_error(self):
        """Deve retornar True para ConnectionError."""
        assert _should_retry_for_query(ConnectionError("refused")) is True

    def test_should_not_retry_not_found_error(self):
        """Deve retornar False para DataJudNotFoundError."""
        assert _should_retry_for_query(DataJudNotFoundError("123")) is False

    def test_should_retry_500_error(self):
        """Deve retornar True para DataJudAPIError com status 500."""
        assert _should_retry_for_query(DataJudAPIError("err", status_code=500)) is True

    def test_should_retry_502_error(self):
        """Deve retornar True para DataJudAPIError com status 502."""
        assert _should_retry_for_query(DataJudAPIError("err", status_code=502)) is True

    def test_should_retry_429_error(self):
        """Deve retornar True para DataJudAPIError com status 429."""
        assert _should_retry_for_query(DataJudAPIError("err", status_code=429)) is True

    def test_should_not_retry_401_error(self):
        """Deve retornar False para DataJudAPIError com status 401."""
        assert _should_retry_for_query(DataJudAPIError("err", status_code=401)) is False

    def test_should_not_retry_403_error(self):
        """Deve retornar False para DataJudAPIError com status 403."""
        assert _should_retry_for_query(DataJudAPIError("err", status_code=403)) is False

    def test_should_not_retry_value_error(self):
        """Deve retornar False para ValueError."""
        assert _should_retry_for_query(ValueError("invalid")) is False

    def test_should_not_retry_generic_api_error_no_status(self):
        """Deve retornar False para DataJudAPIError sem status_code."""
        assert _should_retry_for_query(DataJudAPIError("err")) is False


# --- Testes de health_check ---


class TestHealthCheck:
    """Testes para o método health_check."""

    def test_health_check_disponivel(self, client):
        """Deve retornar disponível quando API responde com 200."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(client._session, "post", return_value=mock_response):
            status = client.health_check()

        assert isinstance(status, HealthStatus)
        assert status.disponivel is True
        assert status.latencia_ms >= 0
        assert "disponível" in status.mensagem

    def test_health_check_indisponivel_http_error(self, client):
        """Deve retornar indisponível quando API retorna erro HTTP."""
        mock_response = MagicMock()
        mock_response.status_code = 503

        with patch.object(client._session, "post", return_value=mock_response):
            status = client.health_check()

        assert status.disponivel is False
        assert "503" in status.mensagem

    def test_health_check_timeout(self, client):
        """Deve retornar indisponível em caso de timeout."""
        with patch.object(
            client._session, "post", side_effect=requests.exceptions.Timeout()
        ):
            status = client.health_check()

        assert status.disponivel is False
        assert "Timeout" in status.mensagem

    def test_health_check_erro_conexao(self, client):
        """Deve retornar indisponível em caso de erro de conexão."""
        with patch.object(
            client._session,
            "post",
            side_effect=requests.exceptions.ConnectionError("Connection refused"),
        ):
            status = client.health_check()

        assert status.disponivel is False
        assert "Erro de conexão" in status.mensagem


# --- Testes de parsing ---


class TestParsing:
    """Testes para o parsing de respostas da API."""

    def test_parse_resposta_sem_hits(self, client):
        """Deve retornar None quando resposta não tem hits."""
        resultado = client._parse_response({"hits": {"total": {"value": 0}, "hits": []}}, "test")
        assert resultado is None

    def test_parse_resposta_source_vazio(self, client):
        """Deve retornar None quando _source está vazio."""
        data = {
            "hits": {
                "total": {"value": 1},
                "hits": [{"_source": {}}],
            }
        }
        resultado = client._parse_response(data, "test")
        assert resultado is None

    def test_parse_movimentacoes_lista_vazia(self, client):
        """Deve retornar lista vazia para movimentações vazias."""
        resultado = client._parse_movimentacoes([])
        assert resultado == []

    def test_parse_movimentacoes_tipo_invalido(self, client):
        """Deve ignorar movimentações com tipo inválido."""
        resultado = client._parse_movimentacoes(["string_invalida", None, 123])
        assert resultado == []

    def test_parse_partes_lista_vazia(self, client):
        """Deve retornar lista vazia para partes vazias."""
        resultado = client._parse_partes([])
        assert resultado == []

    def test_parse_partes_advogados_como_strings(self, client):
        """Deve aceitar advogados como lista de strings."""
        partes = [{"nome": "Teste", "tipo": "AUTOR", "advogados": ["Adv 1", "Adv 2"]}]
        resultado = client._parse_partes(partes)
        assert len(resultado) == 1
        assert resultado[0].advogados == ["Adv 1", "Adv 2"]

    def test_inferir_polo_autor(self):
        """Deve inferir polo ativo para tipos de autor."""
        assert DataJudClient._inferir_polo("AUTOR") == "ativo"
        assert DataJudClient._inferir_polo("REQUERENTE") == "ativo"
        assert DataJudClient._inferir_polo("EXEQUENTE") == "ativo"
        assert DataJudClient._inferir_polo("RECLAMANTE") == "ativo"

    def test_inferir_polo_reu(self):
        """Deve inferir polo passivo para tipos de réu."""
        assert DataJudClient._inferir_polo("REU") == "passivo"
        assert DataJudClient._inferir_polo("RÉU") == "passivo"
        assert DataJudClient._inferir_polo("REQUERIDO") == "passivo"
        assert DataJudClient._inferir_polo("EXECUTADO") == "passivo"
        assert DataJudClient._inferir_polo("RECLAMADO") == "passivo"

    def test_inferir_polo_terceiro(self):
        """Deve inferir polo terceiro para tipos de terceiro."""
        assert DataJudClient._inferir_polo("TERCEIRO") == "terceiro"
        assert DataJudClient._inferir_polo("INTERESSADO") == "terceiro"

    def test_inferir_polo_desconhecido(self):
        """Deve retornar None para tipos desconhecidos."""
        assert DataJudClient._inferir_polo("ADVOGADO") is None
        assert DataJudClient._inferir_polo("") is None
        assert DataJudClient._inferir_polo("OUTRO") is None


# --- Testes de configuração ---


class TestConfiguracao:
    """Testes para a configuração do cliente."""

    def test_headers_autenticacao(self, client):
        """Deve configurar headers de autenticação corretamente."""
        headers = client._session.headers
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("ApiKey ")
        assert "Content-Type" in headers
        assert headers["Content-Type"] == "application/json"

    def test_base_url(self):
        """Deve ter a URL base correta."""
        assert DataJudClient.BASE_URL == "https://api-publica.datajud.cnj.jus.br"

    def test_timeout_30_segundos(self):
        """Deve ter timeout configurado para 30 segundos."""
        assert DataJudClient.TIMEOUT == 30
