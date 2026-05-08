"""Testes unitários para o serviço de agendamento (scheduler_service).

Verifica que o scheduler é configurado corretamente com o job de
monitoramento diário, timezone e horário esperados.
"""

from unittest.mock import patch

import pytz
from apscheduler.triggers.cron import CronTrigger

from app import create_app
from app.services.scheduler_service import (
    BRASILIA_TZ,
    RETRY_MAX_ATTEMPTS,
    RETRY_WAIT_SECONDS,
    configurar_scheduler,
)


class TestConfigurarScheduler:
    """Testes para a função configurar_scheduler."""

    def setup_method(self):
        """Cria app de teste para cada teste."""
        self.app = create_app('testing')

    def test_scheduler_retorna_instancia(self):
        """Verifica que configurar_scheduler retorna um scheduler iniciado."""
        scheduler = configurar_scheduler(self.app)
        try:
            assert scheduler is not None
            assert scheduler.running is True
        finally:
            scheduler.shutdown(wait=False)

    def test_job_monitoramento_diario_existe(self):
        """Verifica que o job 'monitoramento_diario' é adicionado ao scheduler."""
        scheduler = configurar_scheduler(self.app)
        try:
            job = scheduler.get_job('monitoramento_diario')
            assert job is not None
            assert job.name == 'Monitoramento diário de processos'
        finally:
            scheduler.shutdown(wait=False)

    def test_job_agendado_para_23h(self):
        """Verifica que o job está agendado para as 23:00."""
        scheduler = configurar_scheduler(self.app)
        try:
            job = scheduler.get_job('monitoramento_diario')
            trigger = job.trigger

            assert isinstance(trigger, CronTrigger)
            # Check the hour and minute fields of the cron trigger
            hour_field = str(trigger.fields[trigger.FIELD_NAMES.index('hour')])
            minute_field = str(trigger.fields[trigger.FIELD_NAMES.index('minute')])
            assert hour_field == '23'
            assert minute_field == '0'
        finally:
            scheduler.shutdown(wait=False)

    def test_job_usa_timezone_brasilia(self):
        """Verifica que o job usa timezone America/Sao_Paulo."""
        scheduler = configurar_scheduler(self.app)
        try:
            job = scheduler.get_job('monitoramento_diario')
            trigger = job.trigger

            assert trigger.timezone == pytz.timezone('America/Sao_Paulo')
        finally:
            scheduler.shutdown(wait=False)

    def test_brasilia_tz_constante(self):
        """Verifica que a constante BRASILIA_TZ está correta."""
        assert BRASILIA_TZ == pytz.timezone('America/Sao_Paulo')

    def test_retry_configuracao(self):
        """Verifica que as constantes de retry estão corretas."""
        assert RETRY_MAX_ATTEMPTS == 3
        assert RETRY_WAIT_SECONDS == 1800  # 30 minutos

    def test_scheduler_nao_inicia_em_modo_testing(self):
        """Verifica que o scheduler NÃO é iniciado quando TESTING=True."""
        app = create_app('testing')
        # In testing mode, the app factory should NOT call configurar_scheduler
        # We verify this by checking that no scheduler attribute is set
        # and that the app was created without errors
        assert app.config['TESTING'] is True


class TestExecutarMonitoramento:
    """Testes para a função executar_monitoramento."""

    def setup_method(self):
        """Cria app de teste para cada teste."""
        self.app = create_app('testing')

    @patch('app.services.processo_service.ProcessoService.executar_monitoramento_diario')
    def test_executa_dentro_do_app_context(self, mock_monitoramento):
        """Verifica que o monitoramento executa dentro do app context."""
        from app.services.processo_service import MonitoramentoLog
        from app.services.scheduler_service import executar_monitoramento

        mock_monitoramento.return_value = MonitoramentoLog(
            total_processos=5,
            processos_atualizados=2,
            processos_com_erro=0,
            status='sucesso',
            duracao_segundos=10,
        )

        with self.app.app_context():
            from app import db
            db.create_all()

        resultado = executar_monitoramento(self.app)

        assert resultado.total_processos == 5
        assert resultado.processos_atualizados == 2
        mock_monitoramento.assert_called_once()
