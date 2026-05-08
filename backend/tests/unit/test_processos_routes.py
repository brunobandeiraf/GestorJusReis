"""Testes unitários para o blueprint de processos."""
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


@pytest.fixture
def sample_processo(app):
    """Cria um processo de exemplo no banco."""
    with app.app_context():
        processo = Processo(
            numero_cnj="0001234-56.2023.8.26.0100",
            tribunal="TJSP",
            classe="Procedimento Comum Cível",
            assunto="Direito Civil",
            valor_causa="10000.00",
            status="ativo",
            ativo=True,
            data_cadastro=datetime(2024, 1, 1, 12, 0, 0),
            ultima_atualizacao=datetime(2024, 1, 15, 10, 0, 0),
        )
        db.session.add(processo)
        db.session.commit()

        # Add partes
        parte1 = Parte(
            processo_id=processo.id,
            nome="João da Silva",
            tipo="AUTOR",
            polo="ativo",
        )
        parte2 = Parte(
            processo_id=processo.id,
            nome="Maria Souza",
            tipo="REU",
            polo="passivo",
        )
        db.session.add_all([parte1, parte2])

        # Add movimentações
        mov1 = Movimentacao(
            processo_id=processo.id,
            data_movimentacao=datetime(2024, 1, 10, 14, 30, 0),
            nome="Juntada de Petição",
            complemento="Petição Inicial",
            nova=False,
            data_importacao=datetime(2024, 1, 10, 15, 0, 0),
        )
        mov2 = Movimentacao(
            processo_id=processo.id,
            data_movimentacao=datetime(2024, 1, 15, 9, 0, 0),
            nome="Despacho",
            complemento=None,
            nova=True,
            data_importacao=datetime(2024, 1, 15, 10, 0, 0),
        )
        db.session.add_all([mov1, mov2])
        db.session.commit()

        return processo.id


class TestListarProcessos:
    """Testes para GET /api/processos."""

    def test_lista_vazia(self, client, app):
        """Retorna lista vazia quando não há processos."""
        with app.app_context():
            response = client.get('/api/processos')

        assert response.status_code == 200
        data = response.get_json()
        assert data['processos'] == []
        assert data['total'] == 0
        assert data['page'] == 1
        assert data['per_page'] == 20

    def test_lista_com_processos(self, client, app, sample_processo):
        """Retorna processos cadastrados."""
        with app.app_context():
            response = client.get('/api/processos')

        data = response.get_json()
        assert response.status_code == 200
        assert data['total'] == 1
        assert len(data['processos']) == 1
        assert data['processos'][0]['numero_cnj'] == "0001234-56.2023.8.26.0100"
        assert data['processos'][0]['tribunal'] == "TJSP"

    def test_paginacao_default(self, client, app, sample_processo):
        """Usa paginação padrão (page=1, per_page=20)."""
        with app.app_context():
            response = client.get('/api/processos')

        data = response.get_json()
        assert data['page'] == 1
        assert data['per_page'] == 20

    def test_paginacao_custom(self, client, app):
        """Aceita parâmetros de paginação customizados."""
        with app.app_context():
            # Create 5 processos
            for i in range(5):
                p = Processo(
                    numero_cnj=f"000{i:04d}-56.2023.8.26.0100",
                    tribunal="TJSP",
                    status="ativo",
                    ativo=True,
                    data_cadastro=datetime(2024, 1, i + 1),
                )
                db.session.add(p)
            db.session.commit()

            response = client.get('/api/processos?page=1&per_page=2')

        data = response.get_json()
        assert response.status_code == 200
        assert len(data['processos']) == 2
        assert data['total'] == 5
        assert data['pages'] == 3

    def test_nao_lista_processos_inativos(self, client, app):
        """Não retorna processos com ativo=False."""
        with app.app_context():
            p = Processo(
                numero_cnj="0001234-56.2023.8.26.0100",
                tribunal="TJSP",
                status="ativo",
                ativo=False,
                data_cadastro=datetime(2024, 1, 1),
            )
            db.session.add(p)
            db.session.commit()

            response = client.get('/api/processos')

        data = response.get_json()
        assert data['total'] == 0
        assert data['processos'] == []


class TestCadastrarProcesso:
    """Testes para POST /api/processos."""

    @patch('app.routes.processos.ProcessoService')
    def test_cadastro_sucesso(self, MockService, client, app):
        """Cadastra processo com sucesso e retorna 201."""
        with app.app_context():
            mock_instance = MockService.return_value
            processo = Processo(
                id=1,
                numero_cnj="0001234-56.2023.8.26.0100",
                tribunal="TJSP",
                classe="Cível",
                assunto="Direito Civil",
                valor_causa="10000.00",
                status="ativo",
                ativo=True,
                data_cadastro=datetime(2024, 1, 1),
                ultima_atualizacao=datetime(2024, 1, 1),
            )
            # Need to add to session for relationship access
            db.session.add(processo)
            db.session.commit()
            mock_instance.cadastrar_processo.return_value = processo

            response = client.post(
                '/api/processos',
                json={'numero_cnj': '0001234-56.2023.8.26.0100'},
            )

        assert response.status_code == 201
        data = response.get_json()
        assert data['numero_cnj'] == "0001234-56.2023.8.26.0100"
        assert data['tribunal'] == "TJSP"

    def test_cadastro_sem_body(self, client, app):
        """Retorna 400 quando body está vazio."""
        with app.app_context():
            response = client.post(
                '/api/processos',
                json={},
            )

        assert response.status_code == 400
        data = response.get_json()
        assert 'erro' in data

    def test_cadastro_sem_numero_cnj(self, client, app):
        """Retorna 400 quando numero_cnj não está no body."""
        with app.app_context():
            response = client.post(
                '/api/processos',
                json={'outro_campo': 'valor'},
            )

        assert response.status_code == 400
        data = response.get_json()
        assert 'obrigatório' in data['erro']

    @patch('app.routes.processos.ProcessoService')
    def test_cadastro_cnj_invalido(self, MockService, client, app):
        """Retorna 400 quando CNJ é inválido."""
        from app.services.processo_service import CNJInvalidoError

        with app.app_context():
            mock_instance = MockService.return_value
            mock_instance.cadastrar_processo.side_effect = CNJInvalidoError("invalido")

            response = client.post(
                '/api/processos',
                json={'numero_cnj': 'invalido'},
            )

        assert response.status_code == 400
        data = response.get_json()
        assert 'erro' in data

    @patch('app.routes.processos.ProcessoService')
    def test_cadastro_duplicado(self, MockService, client, app):
        """Retorna 409 quando processo já existe."""
        from app.services.processo_service import ProcessoJaExisteError

        with app.app_context():
            mock_instance = MockService.return_value
            mock_instance.cadastrar_processo.side_effect = ProcessoJaExisteError(
                "0001234-56.2023.8.26.0100"
            )

            response = client.post(
                '/api/processos',
                json={'numero_cnj': '0001234-56.2023.8.26.0100'},
            )

        assert response.status_code == 409
        data = response.get_json()
        assert 'erro' in data


class TestDetalheProcesso:
    """Testes para GET /api/processos/<id>."""

    def test_detalhe_sucesso(self, client, app, sample_processo):
        """Retorna detalhes completos do processo com partes."""
        with app.app_context():
            response = client.get(f'/api/processos/{sample_processo}')

        assert response.status_code == 200
        data = response.get_json()
        assert data['numero_cnj'] == "0001234-56.2023.8.26.0100"
        assert data['tribunal'] == "TJSP"
        assert data['classe'] == "Procedimento Comum Cível"
        assert data['assunto'] == "Direito Civil"
        assert data['valor_causa'] == "10000.00"
        assert len(data['partes']) == 2
        assert data['partes'][0]['nome'] == "João da Silva"
        assert data['partes'][1]['nome'] == "Maria Souza"

    def test_detalhe_nao_encontrado(self, client, app):
        """Retorna 404 quando processo não existe."""
        with app.app_context():
            response = client.get('/api/processos/99999')

        assert response.status_code == 404
        data = response.get_json()
        assert 'erro' in data


class TestRemoverProcesso:
    """Testes para DELETE /api/processos/<id>."""

    def test_remover_sucesso(self, client, app, sample_processo):
        """Remove processo (soft delete) com sucesso."""
        with app.app_context():
            response = client.delete(f'/api/processos/{sample_processo}')

            assert response.status_code == 200
            data = response.get_json()
            assert 'mensagem' in data

            # Verifica que ativo=False
            processo = Processo.query.get(sample_processo)
            assert processo.ativo is False

    def test_remover_nao_encontrado(self, client, app):
        """Retorna 404 quando processo não existe."""
        with app.app_context():
            response = client.delete('/api/processos/99999')

        assert response.status_code == 404


class TestListarMovimentacoes:
    """Testes para GET /api/processos/<id>/movimentacoes."""

    def test_listar_movimentacoes_sucesso(self, client, app, sample_processo):
        """Retorna lista de movimentações do processo."""
        with app.app_context():
            response = client.get(f'/api/processos/{sample_processo}/movimentacoes')

        assert response.status_code == 200
        data = response.get_json()
        assert data['total'] == 2
        assert len(data['movimentacoes']) == 2

    def test_movimentacoes_contem_campos_esperados(self, client, app, sample_processo):
        """Cada movimentação contém todos os campos esperados."""
        with app.app_context():
            response = client.get(f'/api/processos/{sample_processo}/movimentacoes')

        data = response.get_json()
        mov = data['movimentacoes'][0]
        assert 'id' in mov
        assert 'processo_id' in mov
        assert 'data_movimentacao' in mov
        assert 'nome' in mov
        assert 'complemento' in mov
        assert 'nova' in mov
        assert 'data_importacao' in mov

    def test_movimentacoes_atualiza_ultima_visualizacao(self, client, app, sample_processo):
        """Acessar movimentações atualiza ultima_visualizacao do processo."""
        with app.app_context():
            processo_antes = Processo.query.get(sample_processo)
            vis_antes = processo_antes.ultima_visualizacao

            response = client.get(f'/api/processos/{sample_processo}/movimentacoes')

            assert response.status_code == 200
            processo_depois = Processo.query.get(sample_processo)
            assert processo_depois.ultima_visualizacao is not None
            if vis_antes:
                assert processo_depois.ultima_visualizacao >= vis_antes

    def test_movimentacoes_processo_nao_encontrado(self, client, app):
        """Retorna 404 quando processo não existe."""
        with app.app_context():
            response = client.get('/api/processos/99999/movimentacoes')

        assert response.status_code == 404
