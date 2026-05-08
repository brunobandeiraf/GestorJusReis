"""Blueprint para endpoint de busca de processos por CPF."""

import logging

from flask import Blueprint, current_app, jsonify, request

from app.services.scraping.cpf_validator import CPFValidator
from app.services.scraping.exceptions import (
    CaptchaDetectadoError,
    CPFInvalidoError,
    ScrapingError,
    TribunalIndisponivelError,
    TribunalNaoSuportadoError,
)

logger = logging.getLogger(__name__)

busca_cpf_bp = Blueprint('busca_cpf', __name__, url_prefix='/api')


def _mascarar_cpf(cpf: str) -> str:
    """Mascara CPF para logging seguro: ***.***.XXX-XX."""
    digitos = cpf.replace('.', '').replace('-', '')
    if len(digitos) >= 11:
        return f"***.***{digitos[6:9]}-{digitos[9:11]}"
    return "***"


@busca_cpf_bp.route('/busca-cpf', methods=['POST'])
def buscar_por_cpf():
    """Busca processos por CPF em um tribunal.

    Body JSON:
        cpf (str): CPF com ou sem formatação
        tribunal (str): ID do tribunal (ex: "tjsp")

    Returns:
        200: {processos: [...], total: N, tribunal: "tjsp", tribunal_nome: "..."}
        400: CPF inválido ou tribunal não informado
        502: Tribunal indisponível ou erro de scraping
        503: CAPTCHA detectado
    """
    data = request.get_json()
    if not data:
        return jsonify({'erro': 'Corpo da requisição é obrigatório'}), 400

    cpf = data.get('cpf', '').strip()
    tribunal = data.get('tribunal', '').strip()

    # Validate tribunal
    if not tribunal:
        return jsonify({'erro': 'Selecione um tribunal para realizar a busca.'}), 400

    # Validate CPF
    if not cpf:
        return jsonify({'erro': 'CPF é obrigatório.'}), 400

    if not CPFValidator.validar(cpf):
        return jsonify({
            'erro': 'CPF inválido. Informe 11 dígitos numéricos (com ou sem formatação).'
        }), 400

    cpf_normalizado = CPFValidator.normalizar(cpf)

    # Get scraper from registry
    registry = current_app.config['SCRAPER_REGISTRY']

    try:
        scraper = registry.obter(tribunal)
    except TribunalNaoSuportadoError:
        return jsonify({
            'erro': 'Tribunal selecionado não suporta busca por CPF.'
        }), 400

    # Execute search
    try:
        processos = scraper.buscar_por_cpf(cpf_normalizado)
    except TribunalIndisponivelError as e:
        logger.error(
            "Tribunal indisponível ao buscar CPF %s no %s: %s",
            _mascarar_cpf(cpf_normalizado),
            tribunal,
            e.motivo,
        )
        return jsonify({
            'erro': f'O {tribunal.upper()} está temporariamente indisponível. '
                    'Tente novamente em alguns minutos.'
        }), 502
    except CaptchaDetectadoError:
        logger.error(
            "CAPTCHA detectado ao buscar CPF %s no %s",
            _mascarar_cpf(cpf_normalizado),
            tribunal,
        )
        return jsonify({
            'erro': f'O {tribunal.upper()} está exigindo verificação humana. '
                    'Acesse diretamente: https://esaj.tjsp.jus.br/cpopg/open.do'
        }), 503
    except ScrapingError as e:
        logger.error(
            "Erro de scraping ao buscar CPF %s no %s: %s",
            _mascarar_cpf(cpf_normalizado),
            tribunal,
            e.detalhes,
        )
        return jsonify({
            'erro': 'Ocorreu um erro ao ler os dados do tribunal. '
                    'Tente novamente mais tarde.'
        }), 502

    # Build response
    resultado = []
    for p in processos:
        resultado.append({
            'numero_cnj': p.numero_cnj,
            'classe': p.classe,
            'assunto': p.assunto,
            'partes': p.partes,
            'vara': p.vara,
            'data_distribuicao': p.data_distribuicao,
        })

    return jsonify({
        'processos': resultado,
        'total': len(resultado),
        'tribunal': scraper.tribunal_id,
        'tribunal_nome': scraper.tribunal_nome,
    }), 200


@busca_cpf_bp.route('/busca-cpf/tribunais', methods=['GET'])
def listar_tribunais_busca_cpf():
    """Lista tribunais disponíveis para busca por CPF.

    Returns:
        200: {tribunais: [{id, nome}]}
    """
    registry = current_app.config['SCRAPER_REGISTRY']
    return jsonify({
        'tribunais': registry.listar_disponiveis(),
    }), 200
