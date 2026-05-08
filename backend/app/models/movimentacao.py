"""Modelo SQLAlchemy para Movimentação de Processo Judicial."""
from datetime import datetime

from app import db


class Movimentacao(db.Model):
    """Movimentação/andamento de um processo judicial."""

    __tablename__ = 'movimentacoes'

    id = db.Column(db.Integer, primary_key=True)
    processo_id = db.Column(db.Integer, db.ForeignKey('processos.id'), nullable=False)
    data_movimentacao = db.Column(db.DateTime, nullable=False)
    nome = db.Column(db.String(500), nullable=False)
    complemento = db.Column(db.Text)
    nova = db.Column(db.Boolean, default=True)
    data_importacao = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Movimentacao {self.nome} ({self.data_movimentacao})>'
