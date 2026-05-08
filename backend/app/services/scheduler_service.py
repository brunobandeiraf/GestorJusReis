"""Serviço de agendamento para monitoramento diário de processos.

Este módulo configura o APScheduler para executar o monitoramento diário
de processos judiciais às 23h (horário de Brasília), com retry automático
em caso de falha.
"""

import logging

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
)

from app.services.datajud_client import DataJudAPIError, DataJudTimeoutError

logger = logging.getLogger(__name__)

BRASILIA_TZ = pytz.timezone('America/Sao_Paulo')

# Retry configuration: 3 attempts, 30 minutes between each
RETRY_MAX_ATTEMPTS = 3
RETRY_WAIT_SECONDS = 1800  # 30 minutes


def configurar_scheduler(app):
    """Configura o scheduler para monitoramento diário às 23h (Brasília).

    Cria um BackgroundScheduler com um job cron agendado para executar
    o monitoramento diário de processos judiciais.

    Args:
        app: Instância da aplicação Flask.

    Returns:
        Instância do BackgroundScheduler configurado e iniciado.
    """
    scheduler = BackgroundScheduler()

    scheduler.add_job(
        func=executar_monitoramento,
        trigger=CronTrigger(hour=23, minute=0, timezone=BRASILIA_TZ),
        id='monitoramento_diario',
        name='Monitoramento diário de processos',
        replace_existing=True,
        args=[app],
    )

    scheduler.start()
    logger.info("Scheduler configurado: monitoramento diário às 23h (America/Sao_Paulo)")
    return scheduler


@retry(
    stop=stop_after_attempt(RETRY_MAX_ATTEMPTS),
    wait=wait_fixed(RETRY_WAIT_SECONDS),
    retry=retry_if_exception_type((DataJudAPIError, DataJudTimeoutError)),
    reraise=True,
)
def executar_monitoramento(app):
    """Executa o monitoramento diário dentro do contexto da aplicação Flask.

    Esta função é chamada pelo scheduler e executa o monitoramento com
    retry automático: até 3 tentativas com intervalo de 30 minutos entre elas.

    Args:
        app: Instância da aplicação Flask (necessária para app context).
    """
    logger.info("Iniciando monitoramento diário de processos")

    with app.app_context():
        from app.services.processo_service import ProcessoService

        service = ProcessoService()
        resultado = service.executar_monitoramento_diario()

        logger.info(
            "Monitoramento diário finalizado: total=%d, atualizados=%d, "
            "erros=%d, status=%s, duração=%ds",
            resultado.total_processos,
            resultado.processos_atualizados,
            resultado.processos_com_erro,
            resultado.status,
            resultado.duracao_segundos,
        )

    return resultado
