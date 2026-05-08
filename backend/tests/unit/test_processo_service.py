"""Testes unitários para o serviço de processos judiciais."""
import sys
from pathlib import Path

# Add backend to path so 'app' module can be resolved
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app import create_app, db
from app.models.movimentacao import Movimentacao
from app.models.parte import Parte
from app.models.processo import Processo
from app.services.datajud_client import (
    DataJudAPIError,
    DataJudNotFoundError,
    DataJudTimeoutError,
    MovimentacaoDTO,
    ParteDTO,
    ProcessoDTO,
)
from app.models.log_execucao import LogExecucao
from app.services.processo_service import (
    AtualizacaoResult,
    CNJInvalidoError,
    MonitoramentoLog,
    ProcessoJaExisteError,
    ProcessoService,
)


@pytest.fixture
def app():
    """Cria instância da aplicação Flask para testes."""
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def mock_datajud_client():
    """Cria mock do DataJudClient."""
    return MagicMock()


@pytest.fixture
def service(app, mock_datajud_client):
    """Cria instância do ProcessoService com client mockado."""
    return ProcessoService(datajud_client=mock_datajud_client)


# --- Número CNJ válido para testes ---
VALID_CNJ = "0001234-56.2023.8.26.0100"
VALID_CNJ_2 = "1234567-89.2024.5.02.0001"


def _make_processo_dto(numero_cnj=VALID_CNJ):
    """Cria um ProcessoDTO de exemplo para testes."""
    return ProcessoDTO(
        numero_cnj=numero_cnj,
        tribunal="TJSP",
        classe="Procedimento Comum Cível",
        assunto="Direito Civil",
        partes=[
            ParteDTO(nome="João da Silva", tipo="AUTOR", polo="ativo"),
            ParteDTO(nome="Maria Souza", tipo="REU", polo="passivo"),
        ],
        movimentacoes=[
            MovimentacaoDTO(
                data="2024-01-10T14:30:00",
                nome="Juntada de Petição",
                complemento="Petição Inicial",
            ),
            MovimentacaoDTO(
                data="2024-01-15T09:00:00",
                nome="Despacho",
                complemento=None,
            ),
        ],
        valor_causa="10000.00",
        data_ajuizamento="2023-03-15",
    )


class TestCadastrarProcesso:
    """Testes para o método cadastrar_processo."""

    def test_cadastro_sucesso_com_dados_api(self, app, service, mock_datajud_client):
        """Testa cadastro bem-sucedido com dados retornados pela API."""
        with app.app_context():
            mock_datajud_client.buscar_processo.return_value = _make_processo_dto()

            processo = service.cadastrar_processo(VALID_CNJ)

            assert processo.id is not None
            assert processo.numero_cnj == VALID_CNJ
            assert processo.tribunal == "TJSP"
            assert processo.classe == "Procedimento Comum Cível"
            assert processo.assunto == "Direito Civil"
            assert processo.valor_causa == "10000.00"
            assert processo.status == "ativo"
            assert processo.ativo is True
            assert processo.data_cadastro is not None
            assert processo.ultima_atualizacao is not None

    def test_cadastro_cria_movimentacoes(self, app, service, mock_datajud_client):
        """Testa que movimentações são criadas corretamente."""
        with app.app_context():
            mock_datajud_client.buscar_processo.return_value = _make_processo_dto()

            processo = service.cadastrar_processo(VALID_CNJ)

            movimentacoes = Movimentacao.query.filter_by(processo_id=processo.id).all()
            assert len(movimentacoes) == 2
            assert movimentacoes[0].nome == "Juntada de Petição"
            assert movimentacoes[0].complemento == "Petição Inicial"
            assert movimentacoes[0].nova is True
            assert movimentacoes[1].nome == "Despacho"

    def test_cadastro_cria_partes(self, app, service, mock_datajud_client):
        """Testa que partes são criadas corretamente."""
        with app.app_context():
            mock_datajud_client.buscar_processo.return_value = _make_processo_dto()

            processo = service.cadastrar_processo(VALID_CNJ)

            partes = Parte.query.filter_by(processo_id=processo.id).all()
            assert len(partes) == 2
            assert partes[0].nome == "João da Silva"
            assert partes[0].tipo == "AUTOR"
            assert partes[0].polo == "ativo"
            assert partes[1].nome == "Maria Souza"
            assert partes[1].tipo == "REU"
            assert partes[1].polo == "passivo"

    def test_cadastro_cnj_invalido_levanta_erro(self, app, service):
        """Testa que CNJ inválido levanta CNJInvalidoError."""
        with app.app_context():
            with pytest.raises(CNJInvalidoError) as exc_info:
                service.cadastrar_processo("numero-invalido")

            assert "numero-invalido" in str(exc_info.value)

    def test_cadastro_cnj_formato_parcial_invalido(self, app, service):
        """Testa que CNJ com formato parcialmente correto é rejeitado."""
        with app.app_context():
            with pytest.raises(CNJInvalidoError):
                service.cadastrar_processo("1234567-89.2024.8.26")

    def test_cadastro_duplicado_levanta_erro(self, app, service, mock_datajud_client):
        """Testa que cadastro duplicado levanta ProcessoJaExisteError."""
        with app.app_context():
            mock_datajud_client.buscar_processo.return_value = _make_processo_dto()

            # Primeiro cadastro
            service.cadastrar_processo(VALID_CNJ)

            # Segundo cadastro do mesmo processo
            with pytest.raises(ProcessoJaExisteError) as exc_info:
                service.cadastrar_processo(VALID_CNJ)

            assert VALID_CNJ in str(exc_info.value)

    def test_cadastro_api_indisponivel_timeout(self, app, service, mock_datajud_client):
        """Testa cadastro quando API retorna timeout (cadastra sem dados)."""
        with app.app_context():
            mock_datajud_client.buscar_processo.side_effect = DataJudTimeoutError()

            processo = service.cadastrar_processo(VALID_CNJ)

            assert processo.id is not None
            assert processo.numero_cnj == VALID_CNJ
            assert processo.tribunal == "8.26"  # código extraído do CNJ
            assert processo.classe is None
            assert processo.assunto is None
            assert processo.status == "ativo"
            assert processo.ativo is True

    def test_cadastro_api_indisponivel_erro_generico(
        self, app, service, mock_datajud_client
    ):
        """Testa cadastro quando API retorna erro genérico (cadastra sem dados)."""
        with app.app_context():
            mock_datajud_client.buscar_processo.side_effect = DataJudAPIError(
                "Erro interno", status_code=500
            )

            processo = service.cadastrar_processo(VALID_CNJ)

            assert processo.id is not None
            assert processo.numero_cnj == VALID_CNJ
            assert processo.tribunal == "8.26"
            assert processo.classe is None

    def test_cadastro_api_indisponivel_sem_movimentacoes(
        self, app, service, mock_datajud_client
    ):
        """Testa que cadastro sem API não cria movimentações nem partes."""
        with app.app_context():
            mock_datajud_client.buscar_processo.side_effect = DataJudTimeoutError()

            processo = service.cadastrar_processo(VALID_CNJ)

            movimentacoes = Movimentacao.query.filter_by(processo_id=processo.id).all()
            partes = Parte.query.filter_by(processo_id=processo.id).all()
            assert len(movimentacoes) == 0
            assert len(partes) == 0

    def test_cadastro_api_retorna_none(self, app, service, mock_datajud_client):
        """Testa cadastro quando API retorna None (processo não encontrado)."""
        with app.app_context():
            mock_datajud_client.buscar_processo.return_value = None

            processo = service.cadastrar_processo(VALID_CNJ)

            # Quando API retorna None, cadastra sem dados iniciais
            assert processo.id is not None
            assert processo.numero_cnj == VALID_CNJ
            assert processo.tribunal == "8.26"

    def test_cadastro_extrai_tribunal_correto(self, app, service, mock_datajud_client):
        """Testa que o tribunal é extraído corretamente do número CNJ."""
        with app.app_context():
            mock_datajud_client.buscar_processo.return_value = None

            # CNJ com tribunal 5.02 (TRT 2ª Região)
            processo = service.cadastrar_processo(VALID_CNJ_2)

            assert processo.tribunal == "5.02"

    def test_cadastro_persiste_no_banco(self, app, service, mock_datajud_client):
        """Testa que o processo é efetivamente persistido no banco."""
        with app.app_context():
            mock_datajud_client.buscar_processo.return_value = _make_processo_dto()

            service.cadastrar_processo(VALID_CNJ)

            # Verifica diretamente no banco
            processo_db = Processo.query.filter_by(numero_cnj=VALID_CNJ).first()
            assert processo_db is not None
            assert processo_db.numero_cnj == VALID_CNJ

    def test_cadastro_com_movimentacao_data_formato_iso(
        self, app, service, mock_datajud_client
    ):
        """Testa parsing de data no formato ISO completo."""
        with app.app_context():
            dto = ProcessoDTO(
                numero_cnj=VALID_CNJ,
                tribunal="TJSP",
                classe="Cível",
                assunto="Direito Civil",
                partes=[],
                movimentacoes=[
                    MovimentacaoDTO(
                        data="2024-01-10T14:30:00",
                        nome="Despacho",
                        complemento=None,
                    )
                ],
            )
            mock_datajud_client.buscar_processo.return_value = dto

            processo = service.cadastrar_processo(VALID_CNJ)

            mov = Movimentacao.query.filter_by(processo_id=processo.id).first()
            assert mov.data_movimentacao == datetime(2024, 1, 10, 14, 30, 0)

    def test_cadastro_com_movimentacao_data_formato_simples(
        self, app, service, mock_datajud_client
    ):
        """Testa parsing de data no formato YYYY-MM-DD."""
        with app.app_context():
            dto = ProcessoDTO(
                numero_cnj=VALID_CNJ,
                tribunal="TJSP",
                classe="Cível",
                assunto="Direito Civil",
                partes=[],
                movimentacoes=[
                    MovimentacaoDTO(
                        data="2024-01-10",
                        nome="Despacho",
                        complemento=None,
                    )
                ],
            )
            mock_datajud_client.buscar_processo.return_value = dto

            processo = service.cadastrar_processo(VALID_CNJ)

            mov = Movimentacao.query.filter_by(processo_id=processo.id).first()
            assert mov.data_movimentacao == datetime(2024, 1, 10)


class TestParseData:
    """Testes para o método _parse_data."""

    def test_parse_iso_datetime(self):
        """Testa parsing de formato ISO com hora."""
        result = ProcessoService._parse_data("2024-01-10T14:30:00")
        assert result == datetime(2024, 1, 10, 14, 30, 0)

    def test_parse_iso_datetime_with_millis(self):
        """Testa parsing de formato ISO com milissegundos."""
        result = ProcessoService._parse_data("2024-01-10T14:30:00.123456")
        assert result == datetime(2024, 1, 10, 14, 30, 0, 123456)

    def test_parse_date_only(self):
        """Testa parsing de formato apenas data."""
        result = ProcessoService._parse_data("2024-01-10")
        assert result == datetime(2024, 1, 10)

    def test_parse_br_format(self):
        """Testa parsing de formato brasileiro DD/MM/YYYY."""
        result = ProcessoService._parse_data("10/01/2024")
        assert result == datetime(2024, 1, 10)

    def test_parse_invalid_returns_current(self):
        """Testa que formato inválido retorna data atual."""
        result = ProcessoService._parse_data("invalid-date")
        # Deve retornar algo próximo de agora
        assert isinstance(result, datetime)
        assert (datetime.utcnow() - result).total_seconds() < 5


class TestAtualizarProcesso:
    """Testes para o método atualizar_processo."""

    def _cadastrar_processo_com_movimentacoes(self, service, mock_datajud_client):
        """Helper: cadastra um processo com movimentações iniciais."""
        mock_datajud_client.buscar_processo.return_value = _make_processo_dto()
        processo = service.cadastrar_processo(VALID_CNJ)
        return processo

    def test_atualizar_sem_novas_movimentacoes(
        self, app, service, mock_datajud_client
    ):
        """Testa atualização quando API retorna mesmas movimentações (sem novidades)."""
        with app.app_context():
            processo = self._cadastrar_processo_com_movimentacoes(
                service, mock_datajud_client
            )

            # API retorna as mesmas movimentações
            mock_datajud_client.buscar_processo.return_value = _make_processo_dto()

            result = service.atualizar_processo(processo.id)

            assert result.atualizado is False
            assert result.novas_movimentacoes == 0
            assert result.erro is None

    def test_atualizar_com_novas_movimentacoes(
        self, app, service, mock_datajud_client
    ):
        """Testa atualização quando API retorna movimentações novas."""
        with app.app_context():
            processo = self._cadastrar_processo_com_movimentacoes(
                service, mock_datajud_client
            )

            # API retorna movimentações existentes + uma nova
            dto_atualizado = ProcessoDTO(
                numero_cnj=VALID_CNJ,
                tribunal="TJSP",
                classe="Procedimento Comum Cível",
                assunto="Direito Civil",
                partes=[],
                movimentacoes=[
                    MovimentacaoDTO(
                        data="2024-01-10T14:30:00",
                        nome="Juntada de Petição",
                        complemento="Petição Inicial",
                    ),
                    MovimentacaoDTO(
                        data="2024-01-15T09:00:00",
                        nome="Despacho",
                        complemento=None,
                    ),
                    MovimentacaoDTO(
                        data="2024-02-01T10:00:00",
                        nome="Sentença",
                        complemento="Procedente",
                    ),
                ],
            )
            mock_datajud_client.buscar_processo.return_value = dto_atualizado

            result = service.atualizar_processo(processo.id)

            assert result.atualizado is True
            assert result.novas_movimentacoes == 1
            assert result.erro is None

    def test_atualizar_novas_movimentacoes_marcadas_como_nova(
        self, app, service, mock_datajud_client
    ):
        """Testa que novas movimentações são marcadas com nova=True."""
        with app.app_context():
            processo = self._cadastrar_processo_com_movimentacoes(
                service, mock_datajud_client
            )

            dto_atualizado = ProcessoDTO(
                numero_cnj=VALID_CNJ,
                tribunal="TJSP",
                classe="Procedimento Comum Cível",
                assunto="Direito Civil",
                partes=[],
                movimentacoes=[
                    MovimentacaoDTO(
                        data="2024-01-10T14:30:00",
                        nome="Juntada de Petição",
                        complemento="Petição Inicial",
                    ),
                    MovimentacaoDTO(
                        data="2024-02-01T10:00:00",
                        nome="Sentença",
                        complemento="Procedente",
                    ),
                ],
            )
            mock_datajud_client.buscar_processo.return_value = dto_atualizado

            service.atualizar_processo(processo.id)

            # Buscar a movimentação nova
            sentenca = Movimentacao.query.filter_by(
                processo_id=processo.id, nome="Sentença"
            ).first()
            assert sentenca is not None
            assert sentenca.nova is True
            assert sentenca.data_movimentacao == datetime(2024, 2, 1, 10, 0, 0)
            assert sentenca.complemento == "Procedente"

    def test_atualizar_deduplicacao_por_data_e_nome(
        self, app, service, mock_datajud_client
    ):
        """Testa que deduplicação funciona por combinação de data + nome."""
        with app.app_context():
            processo = self._cadastrar_processo_com_movimentacoes(
                service, mock_datajud_client
            )

            # Mesma data mas nome diferente = nova movimentação
            dto_atualizado = ProcessoDTO(
                numero_cnj=VALID_CNJ,
                tribunal="TJSP",
                classe="Procedimento Comum Cível",
                assunto="Direito Civil",
                partes=[],
                movimentacoes=[
                    MovimentacaoDTO(
                        data="2024-01-10T14:30:00",
                        nome="Juntada de Petição",
                        complemento="Petição Inicial",
                    ),
                    MovimentacaoDTO(
                        data="2024-01-10T14:30:00",
                        nome="Distribuição",
                        complemento=None,
                    ),
                ],
            )
            mock_datajud_client.buscar_processo.return_value = dto_atualizado

            result = service.atualizar_processo(processo.id)

            assert result.atualizado is True
            assert result.novas_movimentacoes == 1

    def test_atualizar_atualiza_ultima_atualizacao(
        self, app, service, mock_datajud_client
    ):
        """Testa que ultima_atualizacao é atualizada após a operação."""
        with app.app_context():
            processo = self._cadastrar_processo_com_movimentacoes(
                service, mock_datajud_client
            )
            data_anterior = processo.ultima_atualizacao

            mock_datajud_client.buscar_processo.return_value = _make_processo_dto()

            service.atualizar_processo(processo.id)

            processo_atualizado = Processo.query.get(processo.id)
            assert processo_atualizado.ultima_atualizacao >= data_anterior

    def test_atualizar_processo_nao_encontrado(self, app, service):
        """Testa atualização de processo inexistente."""
        with app.app_context():
            result = service.atualizar_processo(99999)

            assert result.atualizado is False
            assert result.novas_movimentacoes == 0
            assert result.erro is not None
            assert "99999" in result.erro

    def test_atualizar_api_timeout(self, app, service, mock_datajud_client):
        """Testa atualização quando API retorna timeout."""
        with app.app_context():
            processo = self._cadastrar_processo_com_movimentacoes(
                service, mock_datajud_client
            )

            mock_datajud_client.buscar_processo.side_effect = DataJudTimeoutError()

            result = service.atualizar_processo(processo.id)

            assert result.atualizado is False
            assert result.novas_movimentacoes == 0
            assert result.erro is not None

    def test_atualizar_api_erro_generico(self, app, service, mock_datajud_client):
        """Testa atualização quando API retorna erro genérico."""
        with app.app_context():
            processo = self._cadastrar_processo_com_movimentacoes(
                service, mock_datajud_client
            )

            mock_datajud_client.buscar_processo.side_effect = DataJudAPIError(
                "Erro interno", status_code=500
            )

            result = service.atualizar_processo(processo.id)

            assert result.atualizado is False
            assert result.novas_movimentacoes == 0
            assert result.erro is not None
            assert "Erro interno" in result.erro

    def test_atualizar_api_retorna_none(self, app, service, mock_datajud_client):
        """Testa atualização quando API retorna None (processo não encontrado na API)."""
        with app.app_context():
            processo = self._cadastrar_processo_com_movimentacoes(
                service, mock_datajud_client
            )

            mock_datajud_client.buscar_processo.return_value = None

            result = service.atualizar_processo(processo.id)

            assert result.atualizado is False
            assert result.novas_movimentacoes == 0
            assert result.erro is None

            # ultima_atualizacao still updated
            processo_db = Processo.query.get(processo.id)
            assert processo_db.ultima_atualizacao is not None

    def test_atualizar_multiplas_novas_movimentacoes(
        self, app, service, mock_datajud_client
    ):
        """Testa atualização com múltiplas movimentações novas."""
        with app.app_context():
            processo = self._cadastrar_processo_com_movimentacoes(
                service, mock_datajud_client
            )

            dto_atualizado = ProcessoDTO(
                numero_cnj=VALID_CNJ,
                tribunal="TJSP",
                classe="Procedimento Comum Cível",
                assunto="Direito Civil",
                partes=[],
                movimentacoes=[
                    # Existentes
                    MovimentacaoDTO(
                        data="2024-01-10T14:30:00",
                        nome="Juntada de Petição",
                        complemento="Petição Inicial",
                    ),
                    MovimentacaoDTO(
                        data="2024-01-15T09:00:00",
                        nome="Despacho",
                        complemento=None,
                    ),
                    # Novas
                    MovimentacaoDTO(
                        data="2024-02-01T10:00:00",
                        nome="Sentença",
                        complemento="Procedente",
                    ),
                    MovimentacaoDTO(
                        data="2024-02-05T11:00:00",
                        nome="Trânsito em Julgado",
                        complemento=None,
                    ),
                    MovimentacaoDTO(
                        data="2024-02-10T08:30:00",
                        nome="Arquivamento",
                        complemento="Definitivo",
                    ),
                ],
            )
            mock_datajud_client.buscar_processo.return_value = dto_atualizado

            result = service.atualizar_processo(processo.id)

            assert result.atualizado is True
            assert result.novas_movimentacoes == 3
            assert result.erro is None

            # Verify total movimentações in DB
            total = Movimentacao.query.filter_by(processo_id=processo.id).count()
            assert total == 5


class TestConsultaAvulsa:
    """Testes para o método consulta_avulsa."""

    def test_consulta_avulsa_sucesso(self, app, service, mock_datajud_client):
        """Testa consulta avulsa bem-sucedida retorna ProcessoDTO."""
        with app.app_context():
            dto = _make_processo_dto()
            mock_datajud_client.buscar_processo.return_value = dto

            resultado = service.consulta_avulsa(VALID_CNJ)

            assert resultado is not None
            assert resultado.numero_cnj == VALID_CNJ
            assert resultado.tribunal == "TJSP"
            assert resultado.classe == "Procedimento Comum Cível"
            assert resultado.assunto == "Direito Civil"
            assert len(resultado.partes) == 2
            assert len(resultado.movimentacoes) == 2
            assert resultado.valor_causa == "10000.00"
            mock_datajud_client.buscar_processo.assert_called_once_with(VALID_CNJ)

    def test_consulta_avulsa_cnj_invalido(self, app, service):
        """Testa que CNJ inválido levanta CNJInvalidoError."""
        with app.app_context():
            with pytest.raises(CNJInvalidoError) as exc_info:
                service.consulta_avulsa("numero-invalido")

            assert "numero-invalido" in str(exc_info.value)

    def test_consulta_avulsa_cnj_formato_parcial(self, app, service):
        """Testa que CNJ com formato parcialmente correto é rejeitado."""
        with app.app_context():
            with pytest.raises(CNJInvalidoError):
                service.consulta_avulsa("1234567-89.2024.8.26")

    def test_consulta_avulsa_nao_persiste_dados(self, app, service, mock_datajud_client):
        """Testa que consulta avulsa NÃO persiste dados no banco."""
        with app.app_context():
            mock_datajud_client.buscar_processo.return_value = _make_processo_dto()

            service.consulta_avulsa(VALID_CNJ)

            # Verifica que nenhum processo foi salvo no banco
            processo_db = Processo.query.filter_by(numero_cnj=VALID_CNJ).first()
            assert processo_db is None

            # Verifica que nenhuma movimentação foi salva
            movimentacoes = Movimentacao.query.all()
            assert len(movimentacoes) == 0

            # Verifica que nenhuma parte foi salva
            partes = Parte.query.all()
            assert len(partes) == 0

    def test_consulta_avulsa_api_retorna_none(self, app, service, mock_datajud_client):
        """Testa que quando API retorna None, levanta DataJudNotFoundError."""
        with app.app_context():
            mock_datajud_client.buscar_processo.return_value = None

            with pytest.raises(DataJudNotFoundError) as exc_info:
                service.consulta_avulsa(VALID_CNJ)

            assert VALID_CNJ in str(exc_info.value)

    def test_consulta_avulsa_api_timeout(self, app, service, mock_datajud_client):
        """Testa que timeout da API é re-levantado."""
        with app.app_context():
            mock_datajud_client.buscar_processo.side_effect = DataJudTimeoutError()

            with pytest.raises(DataJudTimeoutError):
                service.consulta_avulsa(VALID_CNJ)

    def test_consulta_avulsa_api_erro_generico(self, app, service, mock_datajud_client):
        """Testa que erro genérico da API é re-levantado."""
        with app.app_context():
            mock_datajud_client.buscar_processo.side_effect = DataJudAPIError(
                "Erro interno", status_code=500
            )

            with pytest.raises(DataJudAPIError) as exc_info:
                service.consulta_avulsa(VALID_CNJ)

            assert "Erro interno" in str(exc_info.value)

    def test_consulta_avulsa_api_not_found_error(
        self, app, service, mock_datajud_client
    ):
        """Testa que DataJudNotFoundError da API é re-levantado."""
        with app.app_context():
            mock_datajud_client.buscar_processo.side_effect = DataJudNotFoundError(
                VALID_CNJ
            )

            with pytest.raises(DataJudNotFoundError):
                service.consulta_avulsa(VALID_CNJ)

    def test_consulta_avulsa_retorna_dto_completo(
        self, app, service, mock_datajud_client
    ):
        """Testa que o DTO retornado contém todos os campos esperados."""
        with app.app_context():
            dto = _make_processo_dto()
            mock_datajud_client.buscar_processo.return_value = dto

            resultado = service.consulta_avulsa(VALID_CNJ)

            # Verifica partes
            assert resultado.partes[0].nome == "João da Silva"
            assert resultado.partes[0].tipo == "AUTOR"
            assert resultado.partes[1].nome == "Maria Souza"
            assert resultado.partes[1].tipo == "REU"

            # Verifica movimentações
            assert resultado.movimentacoes[0].data == "2024-01-10T14:30:00"
            assert resultado.movimentacoes[0].nome == "Juntada de Petição"
            assert resultado.movimentacoes[0].complemento == "Petição Inicial"
            assert resultado.movimentacoes[1].data == "2024-01-15T09:00:00"
            assert resultado.movimentacoes[1].nome == "Despacho"

    def test_consulta_avulsa_valida_antes_de_chamar_api(
        self, app, service, mock_datajud_client
    ):
        """Testa que validação CNJ ocorre antes da chamada à API."""
        with app.app_context():
            with pytest.raises(CNJInvalidoError):
                service.consulta_avulsa("invalido")

            # API não deve ter sido chamada
            mock_datajud_client.buscar_processo.assert_not_called()


class TestExecutarMonitoramentoDiario:
    """Testes para o método executar_monitoramento_diario."""

    def _cadastrar_processos_ativos(self, service, mock_datajud_client, count=3):
        """Helper: cadastra múltiplos processos ativos."""
        cnjs = [
            f"000{i:04d}-56.2023.8.26.0100" for i in range(1, count + 1)
        ]
        processos = []
        for cnj in cnjs:
            dto = ProcessoDTO(
                numero_cnj=cnj,
                tribunal="TJSP",
                classe="Cível",
                assunto="Direito Civil",
                partes=[],
                movimentacoes=[
                    MovimentacaoDTO(
                        data="2024-01-10T14:30:00",
                        nome="Despacho",
                        complemento=None,
                    )
                ],
            )
            mock_datajud_client.buscar_processo.return_value = dto
            processo = service.cadastrar_processo(cnj)
            processos.append(processo)
        return processos

    def test_monitoramento_sem_processos_ativos(self, app, service):
        """Testa monitoramento quando não há processos ativos."""
        with app.app_context():
            resultado = service.executar_monitoramento_diario()

            assert resultado.total_processos == 0
            assert resultado.processos_atualizados == 0
            assert resultado.processos_com_erro == 0
            assert resultado.status == "sucesso"
            assert resultado.detalhes_erros == []
            assert resultado.duracao_segundos >= 0

    def test_monitoramento_todos_sucesso_sem_atualizacao(
        self, app, service, mock_datajud_client
    ):
        """Testa monitoramento quando todos os processos são verificados sem novidades."""
        with app.app_context():
            self._cadastrar_processos_ativos(service, mock_datajud_client, count=3)

            # Na atualização, API retorna mesmas movimentações (sem novidades)
            mock_datajud_client.buscar_processo.return_value = ProcessoDTO(
                numero_cnj="dummy",
                tribunal="TJSP",
                classe="Cível",
                assunto="Direito Civil",
                partes=[],
                movimentacoes=[
                    MovimentacaoDTO(
                        data="2024-01-10T14:30:00",
                        nome="Despacho",
                        complemento=None,
                    )
                ],
            )

            resultado = service.executar_monitoramento_diario()

            assert resultado.total_processos == 3
            assert resultado.processos_atualizados == 0
            assert resultado.processos_com_erro == 0
            assert resultado.status == "sucesso"
            assert resultado.detalhes_erros == []

    def test_monitoramento_com_atualizacoes(
        self, app, service, mock_datajud_client
    ):
        """Testa monitoramento quando processos têm novas movimentações."""
        with app.app_context():
            self._cadastrar_processos_ativos(service, mock_datajud_client, count=2)

            # Na atualização, API retorna movimentação nova
            mock_datajud_client.buscar_processo.return_value = ProcessoDTO(
                numero_cnj="dummy",
                tribunal="TJSP",
                classe="Cível",
                assunto="Direito Civil",
                partes=[],
                movimentacoes=[
                    MovimentacaoDTO(
                        data="2024-01-10T14:30:00",
                        nome="Despacho",
                        complemento=None,
                    ),
                    MovimentacaoDTO(
                        data="2024-02-01T10:00:00",
                        nome="Sentença",
                        complemento="Procedente",
                    ),
                ],
            )

            resultado = service.executar_monitoramento_diario()

            assert resultado.total_processos == 2
            assert resultado.processos_atualizados == 2
            assert resultado.processos_com_erro == 0
            assert resultado.status == "sucesso"

    def test_monitoramento_com_erros_parciais(
        self, app, service, mock_datajud_client
    ):
        """Testa monitoramento quando alguns processos falham (status parcial)."""
        with app.app_context():
            self._cadastrar_processos_ativos(service, mock_datajud_client, count=3)

            # Simula: primeiro processo dá erro, demais OK
            call_count = [0]

            def side_effect(cnj):
                call_count[0] += 1
                if call_count[0] == 1:
                    raise DataJudTimeoutError()
                return ProcessoDTO(
                    numero_cnj=cnj,
                    tribunal="TJSP",
                    classe="Cível",
                    assunto="Direito Civil",
                    partes=[],
                    movimentacoes=[
                        MovimentacaoDTO(
                            data="2024-01-10T14:30:00",
                            nome="Despacho",
                            complemento=None,
                        )
                    ],
                )

            mock_datajud_client.buscar_processo.side_effect = side_effect

            resultado = service.executar_monitoramento_diario()

            assert resultado.total_processos == 3
            assert resultado.processos_com_erro == 1
            assert resultado.status == "parcial"
            assert len(resultado.detalhes_erros) == 1

    def test_monitoramento_todos_com_erro(
        self, app, service, mock_datajud_client
    ):
        """Testa monitoramento quando todos os processos falham (status falha)."""
        with app.app_context():
            self._cadastrar_processos_ativos(service, mock_datajud_client, count=2)

            # Todos dão erro
            mock_datajud_client.buscar_processo.side_effect = DataJudAPIError(
                "Erro interno", status_code=500
            )

            resultado = service.executar_monitoramento_diario()

            assert resultado.total_processos == 2
            assert resultado.processos_atualizados == 0
            assert resultado.processos_com_erro == 2
            assert resultado.status == "falha"
            assert len(resultado.detalhes_erros) == 2

    def test_monitoramento_ignora_processos_inativos(
        self, app, service, mock_datajud_client
    ):
        """Testa que processos com ativo=False não são verificados."""
        with app.app_context():
            # Cadastra 2 processos ativos
            self._cadastrar_processos_ativos(service, mock_datajud_client, count=2)

            # Desativa um processo
            processo = Processo.query.first()
            processo.ativo = False
            db.session.commit()

            # Na atualização, API retorna mesmas movimentações
            mock_datajud_client.buscar_processo.return_value = ProcessoDTO(
                numero_cnj="dummy",
                tribunal="TJSP",
                classe="Cível",
                assunto="Direito Civil",
                partes=[],
                movimentacoes=[
                    MovimentacaoDTO(
                        data="2024-01-10T14:30:00",
                        nome="Despacho",
                        complemento=None,
                    )
                ],
            )

            resultado = service.executar_monitoramento_diario()

            # Apenas 1 processo ativo deve ser verificado
            assert resultado.total_processos == 1

    def test_monitoramento_persiste_log_execucao(
        self, app, service, mock_datajud_client
    ):
        """Testa que um LogExecucao é persistido no banco após monitoramento."""
        with app.app_context():
            self._cadastrar_processos_ativos(service, mock_datajud_client, count=2)

            mock_datajud_client.buscar_processo.return_value = ProcessoDTO(
                numero_cnj="dummy",
                tribunal="TJSP",
                classe="Cível",
                assunto="Direito Civil",
                partes=[],
                movimentacoes=[
                    MovimentacaoDTO(
                        data="2024-01-10T14:30:00",
                        nome="Despacho",
                        complemento=None,
                    )
                ],
            )

            service.executar_monitoramento_diario()

            # Verifica que LogExecucao foi persistido
            log = LogExecucao.query.first()
            assert log is not None
            assert log.total_processos == 2
            assert log.processos_atualizados == 0
            assert log.processos_com_erro == 0
            assert log.status == "sucesso"
            assert log.duracao_segundos >= 0
            assert log.data_execucao is not None

    def test_monitoramento_log_com_detalhes_erros(
        self, app, service, mock_datajud_client
    ):
        """Testa que detalhes de erros são persistidos no LogExecucao."""
        with app.app_context():
            self._cadastrar_processos_ativos(service, mock_datajud_client, count=1)

            mock_datajud_client.buscar_processo.side_effect = DataJudTimeoutError()

            service.executar_monitoramento_diario()

            log = LogExecucao.query.first()
            assert log is not None
            assert log.processos_com_erro == 1
            assert log.detalhes_erros is not None
            # detalhes_erros is stored as JSON
            import json
            erros = json.loads(log.detalhes_erros)
            assert len(erros) == 1
            assert "Timeout" in erros[0]

    def test_monitoramento_retorna_dataclass_correta(
        self, app, service, mock_datajud_client
    ):
        """Testa que o retorno é uma instância de MonitoramentoLog."""
        with app.app_context():
            resultado = service.executar_monitoramento_diario()

            assert isinstance(resultado, MonitoramentoLog)

    def test_monitoramento_calcula_duracao(
        self, app, service, mock_datajud_client
    ):
        """Testa que a duração é calculada em segundos."""
        with app.app_context():
            resultado = service.executar_monitoramento_diario()

            # Duração deve ser >= 0 (execução rápida em testes)
            assert isinstance(resultado.duracao_segundos, int)
            assert resultado.duracao_segundos >= 0
