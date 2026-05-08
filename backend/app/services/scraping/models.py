"""Modelos de dados para o módulo de scraping de tribunais."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ProcessoEncontrado:
    """Processo retornado pela busca por CPF em um tribunal."""

    numero_cnj: str
    classe: str
    assunto: str
    partes: List[str] = field(default_factory=list)
    vara: Optional[str] = None
    data_distribuicao: Optional[str] = None
