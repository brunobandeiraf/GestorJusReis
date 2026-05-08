"""Blueprint para endpoint de consulta avulsa de processos judiciais."""
from flask import Blueprint, jsonify, request

from app.services.datajud_client import (
    DataJudAPIError,
    DataJudNotFoundError,
    DataJudTimeoutError,
)
from app.services.processo_service import CNJInvalidoError, ProcessoService

consulta_bp = Blueprint('consulta', __name__, url_prefix='/api')


# --- Serialization helpers ---


def serialize_processo_dto(dto):
    """Converte um ProcessoDTO (dataclass) para dicionário JSON.

    Args:
        dto: Instância de ProcessoDTO retornada pelo serviço.

    Returns:
        Dicionário com dados completos do processo.
    """
    return {
        'numero_cnj': dto.numero_cnj,
        'tribunal': dto.tribunal,
        'classe': dto.classe,
        'assunto': dto.assunto,
        'valor_causa': dto.valor_causa,
        'data_ajuizamento': dto.data_ajuizamento,
        'partes': [
            {
                'nome': parte.nome,
                'tipo': parte.tipo,
                'polo': parte.polo,
                'advogados': parte.advogados,
            }
            for parte in dto.partes
        ],
        'movimentacoes': [
            {
                'data': mov.data,
                'nome': mov.nome,
                'complemento': mov.complemento,
            }
            for mov in dto.movimentacoes
        ],
    }


# --- Endpoints ---


@consulta_bp.route('/consulta-avulsa', methods=['POST'])
def consulta_avulsa():
    """Realiza consulta avulsa de processo sem persistir dados.

    Body JSON:
        numero_cnj (str): Número CNJ no formato NNNNNNN-DD.AAAA.J.TR.OOOO

    Returns:
        200: Dados completos do processo (classe, assunto, partes, movimentações).
        400: Número CNJ inválido ou ausente.
        404: Processo não encontrado na DataJud API.
        502: Erro de comunicação com a DataJud API.
    """
    data = request.get_json()
    if not data or 'numero_cnj' not in data:
        return jsonify({'erro': 'Campo numero_cnj é obrigatório'}), 400

    numero_cnj = data['numero_cnj']

    try:
        service = ProcessoService()
        processo_dto = service.consulta_avulsa(numero_cnj)
        return jsonify(serialize_processo_dto(processo_dto)), 200
    except CNJInvalidoError as e:
        return jsonify({'erro': str(e)}), 400
    except DataJudNotFoundError as e:
        return jsonify({'erro': str(e)}), 404
    except (DataJudAPIError, DataJudTimeoutError) as e:
        return jsonify({'erro': str(e)}), 502
