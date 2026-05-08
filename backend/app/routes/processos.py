"""Blueprint para endpoints REST de processos judiciais."""
from datetime import datetime

from flask import Blueprint, jsonify, request

from app import db
from app.models.movimentacao import Movimentacao
from app.models.parte import Parte
from app.models.processo import Processo
from app.services.processo_service import (
    CNJInvalidoError,
    ProcessoJaExisteError,
    ProcessoService,
)

processos_bp = Blueprint('processos', __name__, url_prefix='/api')


# --- Serialization helpers ---


def serialize_processo(processo):
    """Serializa um Processo para dicionário JSON."""
    return {
        'id': processo.id,
        'numero_cnj': processo.numero_cnj,
        'tribunal': processo.tribunal,
        'classe': processo.classe,
        'assunto': processo.assunto,
        'valor_causa': processo.valor_causa,
        'status': processo.status,
        'data_cadastro': processo.data_cadastro.isoformat() if processo.data_cadastro else None,
        'ultima_atualizacao': processo.ultima_atualizacao.isoformat() if processo.ultima_atualizacao else None,
        'ultima_visualizacao': processo.ultima_visualizacao.isoformat() if processo.ultima_visualizacao else None,
        'ativo': processo.ativo,
    }


def serialize_processo_detail(processo):
    """Serializa um Processo com partes para dicionário JSON (detalhes)."""
    data = serialize_processo(processo)
    data['partes'] = [serialize_parte(p) for p in processo.partes]
    return data


def serialize_movimentacao(movimentacao):
    """Serializa uma Movimentacao para dicionário JSON."""
    return {
        'id': movimentacao.id,
        'processo_id': movimentacao.processo_id,
        'data_movimentacao': movimentacao.data_movimentacao.isoformat() if movimentacao.data_movimentacao else None,
        'nome': movimentacao.nome,
        'complemento': movimentacao.complemento,
        'nova': movimentacao.nova,
        'data_importacao': movimentacao.data_importacao.isoformat() if movimentacao.data_importacao else None,
    }


def serialize_parte(parte):
    """Serializa uma Parte para dicionário JSON."""
    return {
        'id': parte.id,
        'processo_id': parte.processo_id,
        'nome': parte.nome,
        'tipo': parte.tipo,
        'polo': parte.polo,
    }


# --- Endpoints ---


@processos_bp.route('/processos', methods=['GET'])
def listar_processos():
    """Lista processos cadastrados com paginação simples.

    Query params:
        page (int): Número da página (default: 1)
        per_page (int): Itens por página (default: 20)

    Returns:
        JSON com lista de processos e metadados de paginação.
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    pagination = Processo.query.filter_by(ativo=True).order_by(
        Processo.data_cadastro.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'processos': [serialize_processo(p) for p in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages,
    }), 200


@processos_bp.route('/processos', methods=['POST'])
def cadastrar_processo():
    """Cadastra um novo processo para monitoramento.

    Body JSON:
        numero_cnj (str): Número CNJ no formato NNNNNNN-DD.AAAA.J.TR.OOOO

    Returns:
        201: Processo cadastrado com sucesso.
        400: Número CNJ inválido.
        409: Processo já cadastrado.
    """
    data = request.get_json()
    if not data or 'numero_cnj' not in data:
        return jsonify({'erro': 'Campo numero_cnj é obrigatório'}), 400

    numero_cnj = data['numero_cnj']

    try:
        service = ProcessoService()
        processo = service.cadastrar_processo(numero_cnj)
        return jsonify(serialize_processo_detail(processo)), 201
    except CNJInvalidoError as e:
        return jsonify({'erro': str(e)}), 400
    except ProcessoJaExisteError as e:
        return jsonify({'erro': str(e)}), 409


@processos_bp.route('/processos/<int:id>', methods=['GET'])
def detalhe_processo(id):
    """Retorna detalhes completos de um processo com partes.

    Args:
        id: ID do processo.

    Returns:
        200: Dados completos do processo.
        404: Processo não encontrado.
    """
    processo = Processo.query.get(id)
    if not processo:
        return jsonify({'erro': 'Processo não encontrado'}), 404

    return jsonify(serialize_processo_detail(processo)), 200


@processos_bp.route('/processos/<int:id>', methods=['DELETE'])
def remover_processo(id):
    """Remove processo do monitoramento (soft delete: ativo=False).

    Args:
        id: ID do processo.

    Returns:
        200: Processo removido com sucesso.
        404: Processo não encontrado.
    """
    processo = Processo.query.get(id)
    if not processo:
        return jsonify({'erro': 'Processo não encontrado'}), 404

    processo.ativo = False
    db.session.commit()

    return jsonify({'mensagem': 'Processo removido do monitoramento'}), 200


@processos_bp.route('/processos/<int:id>/movimentacoes', methods=['GET'])
def listar_movimentacoes(id):
    """Lista movimentações de um processo e atualiza ultima_visualizacao.

    Ao acessar este endpoint, o campo ultima_visualizacao do processo é
    atualizado para o momento atual, marcando que o usuário visualizou
    as movimentações.

    Args:
        id: ID do processo.

    Returns:
        200: Lista de movimentações.
        404: Processo não encontrado.
    """
    processo = Processo.query.get(id)
    if not processo:
        return jsonify({'erro': 'Processo não encontrado'}), 404

    # Atualizar ultima_visualizacao
    processo.ultima_visualizacao = datetime.utcnow()
    db.session.commit()

    movimentacoes = processo.movimentacoes.all()

    return jsonify({
        'movimentacoes': [serialize_movimentacao(m) for m in movimentacoes],
        'total': len(movimentacoes),
    }), 200
