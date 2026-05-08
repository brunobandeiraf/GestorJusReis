"""Modelo SQLAlchemy para Log de Execução do Monitoramento."""
from datetime import datetime

from app import db


class LogExecucao(db.Model):
    """Log de execução do monitoramento diário."""

    __tablename__ = 'logs_execucao'

    id = db.Column(db.Integer, primary_key=True)
    data_execucao = db.Column(db.DateTime, default=datetime.utcnow)
    total_processos = db.Column(db.Integer, default=0)
    processos_atualizados = db.Column(db.Integer, default=0)
    processos_com_erro = db.Column(db.Integer, default=0)
    detalhes_erros = db.Column(db.Text)
    status = db.Column(db.String(20))  # "sucesso", "parcial", "falha"
    duracao_segundos = db.Column(db.Integer)

    def __repr__(self):
        return f'<LogExecucao {self.id} - {self.status} ({self.data_execucao})>'
