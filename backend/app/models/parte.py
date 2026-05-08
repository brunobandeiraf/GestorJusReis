"""Modelo SQLAlchemy para Parte de um Processo Judicial."""
from app import db


class Parte(db.Model):
    """Parte envolvida em um processo judicial."""

    __tablename__ = 'partes'

    id = db.Column(db.Integer, primary_key=True)
    processo_id = db.Column(db.Integer, db.ForeignKey('processos.id'), nullable=False)
    nome = db.Column(db.String(300), nullable=False)
    tipo = db.Column(db.String(100))  # ex: "Advogado", "Autor", "Réu"
    polo = db.Column(db.String(20))   # "ativo", "passivo", "terceiro"

    def __repr__(self):
        return f'<Parte {self.nome} ({self.tipo})>'
