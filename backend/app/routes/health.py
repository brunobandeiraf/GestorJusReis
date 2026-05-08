"""Blueprint para endpoints de health check e utilitários."""
from flask import Blueprint, jsonify

from app import db
from app.models.log_execucao import LogExecucao
from app.services.datajud_client import DataJudClient
from app.utils.tribunal_mapper import listar_tribunais_suportados

health_bp = Blueprint('health', __name__, url_prefix='/api')


@health_bp.route('/health', methods=['GET'])
def health_check():
    """Health check com status da DataJud API.

    Verifica a conectividade com a API DataJud e retorna informações
    de disponibilidade e latência.

    Returns:
        200: Status de saúde com disponibilidade, latência e mensagem.
    """
    client = DataJudClient()
    status = client.health_check()

    return jsonify({
        'disponivel': status.disponivel,
        'latencia_ms': status.latencia_ms,
        'mensagem': status.mensagem,
    }), 200


@health_bp.route('/monitoramento/status', methods=['GET'])
def monitoramento_status():
    """Retorna o status do último monitoramento executado.

    Consulta o registro mais recente de LogExecucao no banco de dados
    e retorna seus dados.

    Returns:
        200: Dados do último monitoramento.
        404: Nenhum monitoramento executado ainda.
    """
    ultimo_log = LogExecucao.query.order_by(
        LogExecucao.data_execucao.desc()
    ).first()

    if not ultimo_log:
        return jsonify({'mensagem': 'Nenhum monitoramento executado ainda'}), 404

    return jsonify({
        'id': ultimo_log.id,
        'data_execucao': ultimo_log.data_execucao.isoformat() if ultimo_log.data_execucao else None,
        'total_processos': ultimo_log.total_processos,
        'processos_atualizados': ultimo_log.processos_atualizados,
        'processos_com_erro': ultimo_log.processos_com_erro,
        'detalhes_erros': ultimo_log.detalhes_erros,
        'status': ultimo_log.status,
        'duracao_segundos': ultimo_log.duracao_segundos,
    }), 200


@health_bp.route('/tribunais', methods=['GET'])
def listar_tribunais():
    """Lista todos os tribunais suportados pelo sistema.

    Returns:
        200: Lista de tribunais com código, sigla e endpoint.
    """
    tribunais = listar_tribunais_suportados()

    return jsonify({
        'tribunais': tribunais,
        'total': len(tribunais),
    }), 200
