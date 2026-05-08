"""Testes unitários para o blueprint de health check e utilitários."""
import sys
from datetime import datetime
from pathlib import Path

# Add backend to path so 'app' module can be resolved
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from unittest.mock import patch

import pytest

from app import create_app, db
from app.models.log_execucao import LogExecucao
from app.services.datajud_client import HealthStatus


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


class TestHealthCheck:
    """Testes para GET /api/health."""

    @patch('app.routes.health.DataJudClient')
    def test_health_api_disponivel(self, MockClient, client, app):
        """Retorna status disponível quando API está acessível."""
        with app.app_context():
            mock_instance = MockClient.return_value
            mock_instance.health_check.return_value = HealthStatus(
                disponivel=True,
                latencia_ms=150,
                mensagem="DataJud API disponível",
            )

            response = client.get('/api/health')

        assert response.status_code == 200
        data = response.get_json()
        assert data['disponivel'] is True
        assert data['latencia_ms'] == 150
        assert data['mensagem'] == "DataJud API disponível"

    @patch('app.routes.health.DataJudClient')
    def test_health_api_indisponivel(self, MockClient, client, app):
        """Retorna status indisponível quando API não responde."""
        with app.app_context():
            mock_instance = MockClient.return_value
            mock_instance.health_check.return_value = HealthStatus(
                disponivel=False,
                latencia_ms=30000,
                mensagem="Timeout na conexão com DataJud API",
            )

            response = client.get('/api/health')

        assert response.status_code == 200
        data = response.get_json()
        assert data['disponivel'] is False
        assert data['latencia_ms'] == 30000
        assert data['mensagem'] == "Timeout na conexão com DataJud API"

    @patch('app.routes.health.DataJudClient')
    def test_health_api_erro_http(self, MockClient, client, app):
        """Retorna status indisponível quando API retorna erro HTTP."""
        with app.app_context():
            mock_instance = MockClient.return_value
            mock_instance.health_check.return_value = HealthStatus(
                disponivel=False,
                latencia_ms=200,
                mensagem="DataJud API retornou HTTP 500",
            )

            response = client.get('/api/health')

        assert response.status_code == 200
        data = response.get_json()
        assert data['disponivel'] is False
        assert 'HTTP 500' in data['mensagem']


class TestMonitoramentoStatus:
    """Testes para GET /api/monitoramento/status."""

    def test_monitoramento_sem_execucao(self, client, app):
        """Retorna 404 quando nenhum monitoramento foi executado."""
        with app.app_context():
            response = client.get('/api/monitoramento/status')

        assert response.status_code == 404
        data = response.get_json()
        assert 'mensagem' in data
        assert 'Nenhum monitoramento' in data['mensagem']

    def test_monitoramento_com_execucao(self, client, app):
        """Retorna dados do último monitoramento executado."""
        with app.app_context():
            log = LogExecucao(
                data_execucao=datetime(2024, 1, 15, 23, 0, 0),
                total_processos=10,
                processos_atualizados=7,
                processos_com_erro=1,
                detalhes_erros="Timeout no processo X",
                status="parcial",
                duracao_segundos=120,
            )
            db.session.add(log)
            db.session.commit()

            response = client.get('/api/monitoramento/status')

        assert response.status_code == 200
        data = response.get_json()
        assert data['total_processos'] == 10
        assert data['processos_atualizados'] == 7
        assert data['processos_com_erro'] == 1
        assert data['detalhes_erros'] == "Timeout no processo X"
        assert data['status'] == "parcial"
        assert data['duracao_segundos'] == 120

    def test_monitoramento_retorna_mais_recente(self, client, app):
        """Retorna o monitoramento mais recente quando há múltiplos."""
        with app.app_context():
            log_antigo = LogExecucao(
                data_execucao=datetime(2024, 1, 14, 23, 0, 0),
                total_processos=5,
                processos_atualizados=3,
                processos_com_erro=0,
                status="sucesso",
                duracao_segundos=60,
            )
            log_recente = LogExecucao(
                data_execucao=datetime(2024, 1, 15, 23, 0, 0),
                total_processos=10,
                processos_atualizados=8,
                processos_com_erro=2,
                status="parcial",
                duracao_segundos=180,
            )
            db.session.add(log_antigo)
            db.session.add(log_recente)
            db.session.commit()

            response = client.get('/api/monitoramento/status')

        assert response.status_code == 200
        data = response.get_json()
        assert data['total_processos'] == 10
        assert data['processos_atualizados'] == 8
        assert data['status'] == "parcial"


class TestListarTribunais:
    """Testes para GET /api/tribunais."""

    def test_listar_tribunais_retorna_lista(self, client, app):
        """Retorna lista de tribunais suportados."""
        with app.app_context():
            response = client.get('/api/tribunais')

        assert response.status_code == 200
        data = response.get_json()
        assert 'tribunais' in data
        assert 'total' in data
        assert isinstance(data['tribunais'], list)
        assert data['total'] > 0
        assert data['total'] == len(data['tribunais'])

    def test_listar_tribunais_formato_correto(self, client, app):
        """Cada tribunal tem código, sigla e endpoint."""
        with app.app_context():
            response = client.get('/api/tribunais')

        data = response.get_json()
        tribunal = data['tribunais'][0]
        assert 'codigo' in tribunal
        assert 'sigla' in tribunal
        assert 'endpoint' in tribunal

    def test_listar_tribunais_contem_tjsp(self, client, app):
        """Lista contém o TJSP (8.26) como tribunal suportado."""
        with app.app_context():
            response = client.get('/api/tribunais')

        data = response.get_json()
        codigos = [t['codigo'] for t in data['tribunais']]
        assert '8.26' in codigos

        tjsp = next(t for t in data['tribunais'] if t['codigo'] == '8.26')
        assert tjsp['sigla'] == 'tjsp'
        assert 'api_publica_tjsp' in tjsp['endpoint']
