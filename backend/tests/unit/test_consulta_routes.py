"""Testes unitários para o blueprint de consulta avulsa."""
import sys
from pathlib import Path

# Add backend to path so 'app' module can be resolved
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from unittest.mock import patch

import pytest

from app import create_app, db
from app.services.datajud_client import (
    DataJudAPIError,
    DataJudNotFoundError,
    DataJudTimeoutError,
    MovimentacaoDTO,
    ParteDTO,
    ProcessoDTO,
)
from app.services.processo_service import CNJInvalidoError


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
def client(app):
    """Cria test client Flask."""
    return app.test_client()


def _make_processo_dto():
    """Cria um ProcessoDTO de exemplo para testes."""
    return ProcessoDTO(
        numero_cnj="0001234-56.2023.8.26.0100",
        tribunal="TJSP",
        classe="Procedimento Comum Cível",
        assunto="Direito Civil",
        valor_causa="10000.00",
        data_ajuizamento="2023-03-15",
        partes=[
            ParteDTO(
                nome="João da Silva",
                tipo="AUTOR",
                polo="ativo",
                advogados=["Maria Advogada"],
            ),
            ParteDTO(
                nome="Empresa XYZ",
                tipo="REU",
                polo="passivo",
                advogados=[],
            ),
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
    )


class TestConsultaAvulsa:
    """Testes para POST /api/consulta-avulsa."""

    @patch('app.routes.consulta.ProcessoService')
    def test_consulta_sucesso(self, MockService, client, app):
        """Retorna dados completos do processo com status 200."""
        with app.app_context():
            mock_instance = MockService.return_value
            mock_instance.consulta_avulsa.return_value = _make_processo_dto()

            response = client.post(
                '/api/consulta-avulsa',
                json={'numero_cnj': '0001234-56.2023.8.26.0100'},
            )

        assert response.status_code == 200
        data = response.get_json()
        assert data['numero_cnj'] == "0001234-56.2023.8.26.0100"
        assert data['tribunal'] == "TJSP"
        assert data['classe'] == "Procedimento Comum Cível"
        assert data['assunto'] == "Direito Civil"
        assert data['valor_causa'] == "10000.00"
        assert data['data_ajuizamento'] == "2023-03-15"

    @patch('app.routes.consulta.ProcessoService')
    def test_consulta_retorna_partes(self, MockService, client, app):
        """Retorna lista de partes com nome, tipo, polo e advogados."""
        with app.app_context():
            mock_instance = MockService.return_value
            mock_instance.consulta_avulsa.return_value = _make_processo_dto()

            response = client.post(
                '/api/consulta-avulsa',
                json={'numero_cnj': '0001234-56.2023.8.26.0100'},
            )

        data = response.get_json()
        assert len(data['partes']) == 2
        assert data['partes'][0]['nome'] == "João da Silva"
        assert data['partes'][0]['tipo'] == "AUTOR"
        assert data['partes'][0]['polo'] == "ativo"
        assert data['partes'][0]['advogados'] == ["Maria Advogada"]
        assert data['partes'][1]['nome'] == "Empresa XYZ"
        assert data['partes'][1]['polo'] == "passivo"

    @patch('app.routes.consulta.ProcessoService')
    def test_consulta_retorna_movimentacoes(self, MockService, client, app):
        """Retorna lista de movimentações com data, nome e complemento."""
        with app.app_context():
            mock_instance = MockService.return_value
            mock_instance.consulta_avulsa.return_value = _make_processo_dto()

            response = client.post(
                '/api/consulta-avulsa',
                json={'numero_cnj': '0001234-56.2023.8.26.0100'},
            )

        data = response.get_json()
        assert len(data['movimentacoes']) == 2
        assert data['movimentacoes'][0]['data'] == "2024-01-10T14:30:00"
        assert data['movimentacoes'][0]['nome'] == "Juntada de Petição"
        assert data['movimentacoes'][0]['complemento'] == "Petição Inicial"
        assert data['movimentacoes'][1]['nome'] == "Despacho"
        assert data['movimentacoes'][1]['complemento'] is None

    def test_consulta_sem_body(self, client, app):
        """Retorna 400 quando body está vazio."""
        with app.app_context():
            response = client.post(
                '/api/consulta-avulsa',
                json={},
            )

        assert response.status_code == 400
        data = response.get_json()
        assert 'erro' in data
        assert 'obrigatório' in data['erro']

    def test_consulta_sem_numero_cnj(self, client, app):
        """Retorna 400 quando numero_cnj não está no body."""
        with app.app_context():
            response = client.post(
                '/api/consulta-avulsa',
                json={'outro_campo': 'valor'},
            )

        assert response.status_code == 400
        data = response.get_json()
        assert 'obrigatório' in data['erro']

    @patch('app.routes.consulta.ProcessoService')
    def test_consulta_cnj_invalido(self, MockService, client, app):
        """Retorna 400 quando CNJ é inválido."""
        with app.app_context():
            mock_instance = MockService.return_value
            mock_instance.consulta_avulsa.side_effect = CNJInvalidoError("invalido")

            response = client.post(
                '/api/consulta-avulsa',
                json={'numero_cnj': 'invalido'},
            )

        assert response.status_code == 400
        data = response.get_json()
        assert 'erro' in data

    @patch('app.routes.consulta.ProcessoService')
    def test_consulta_processo_nao_encontrado(self, MockService, client, app):
        """Retorna 404 quando processo não é encontrado na API."""
        with app.app_context():
            mock_instance = MockService.return_value
            mock_instance.consulta_avulsa.side_effect = DataJudNotFoundError(
                "0001234-56.2023.8.26.0100"
            )

            response = client.post(
                '/api/consulta-avulsa',
                json={'numero_cnj': '0001234-56.2023.8.26.0100'},
            )

        assert response.status_code == 404
        data = response.get_json()
        assert 'erro' in data

    @patch('app.routes.consulta.ProcessoService')
    def test_consulta_api_error(self, MockService, client, app):
        """Retorna 502 quando há erro de comunicação com a API."""
        with app.app_context():
            mock_instance = MockService.return_value
            mock_instance.consulta_avulsa.side_effect = DataJudAPIError(
                "Erro interno da DataJud API"
            )

            response = client.post(
                '/api/consulta-avulsa',
                json={'numero_cnj': '0001234-56.2023.8.26.0100'},
            )

        assert response.status_code == 502
        data = response.get_json()
        assert 'erro' in data

    @patch('app.routes.consulta.ProcessoService')
    def test_consulta_timeout_error(self, MockService, client, app):
        """Retorna 502 quando há timeout na comunicação com a API."""
        with app.app_context():
            mock_instance = MockService.return_value
            mock_instance.consulta_avulsa.side_effect = DataJudTimeoutError()

            response = client.post(
                '/api/consulta-avulsa',
                json={'numero_cnj': '0001234-56.2023.8.26.0100'},
            )

        assert response.status_code == 502
        data = response.get_json()
        assert 'erro' in data
