"""Modelo SQLAlchemy para Processo Judicial."""
from datetime import datetime

from app import db


class Processo(db.Model):
    """Processo judicial cadastrado para monitoramento."""

    __tablename__ = 'processos'

    id = db.Column(db.Integer, primary_key=True)
    numero_cnj = db.Column(db.String(25), unique=True, nullable=False, index=True)
    tribunal = db.Column(db.String(10))
    classe = db.Column(db.String(200))
    assunto = db.Column(db.String(500))
    valor_causa = db.Column(db.String(50))
    status = db.Column(db.String(50), default='ativo')
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    ultima_atualizacao = db.Column(db.DateTime)
    ultima_visualizacao = db.Column(db.DateTime)
    ativo = db.Column(db.Boolean, default=True)

    movimentacoes = db.relationship(
        'Movimentacao',
        backref='processo',
        lazy='dynamic',
        order_by='Movimentacao.data_movimentacao.desc()',
    )
    partes = db.relationship('Parte', backref='processo', lazy='select')

    def __repr__(self):
        return f'<Processo {self.numero_cnj}>'
