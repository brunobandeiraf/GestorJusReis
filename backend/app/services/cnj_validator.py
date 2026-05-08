"""Validador de número CNJ (Conselho Nacional de Justiça).

O número CNJ segue o formato: NNNNNNN-DD.AAAA.J.TR.OOOO

Componentes:
- NNNNNNN: número sequencial (7 dígitos)
- DD: dígito verificador (2 dígitos)
- AAAA: ano de ajuizamento (4 dígitos)
- J: ramo da justiça (1 dígito)
- TR: tribunal (2 dígitos)
- OOOO: origem/vara (4 dígitos)
"""

import re

CNJ_PATTERN = re.compile(
    r'^(\d{7})-(\d{2})\.(\d{4})\.(\d)\.(\d{2})\.(\d{4})$'
)


def validar_numero_cnj(numero: str) -> bool:
    """Valida se o número está no formato CNJ: NNNNNNN-DD.AAAA.J.TR.OOOO.

    Args:
        numero: String com o número do processo a ser validado.

    Returns:
        True se o formato é válido, False caso contrário.
    """
    if not isinstance(numero, str):
        return False
    return bool(CNJ_PATTERN.match(numero))


def extrair_tribunal(numero_cnj: str) -> str:
    """Extrai o identificador do tribunal (J.TR) a partir do número CNJ.

    O identificador é composto pelo ramo da justiça (J) e código do tribunal (TR),
    separados por ponto. Exemplo: "8.26" para TJSP.

    Args:
        numero_cnj: Número do processo no formato CNJ válido.

    Returns:
        String no formato "J.TR" (ex: "8.26", "5.02").

    Raises:
        ValueError: Se o número CNJ fornecido não é válido.
    """
    match = CNJ_PATTERN.match(numero_cnj)
    if not match:
        raise ValueError(f"Número CNJ inválido: {numero_cnj}")
    justica = match.group(4)  # J
    tribunal = match.group(5)  # TR
    return f"{justica}.{tribunal}"


def formatar_numero_cnj(numero: str) -> str:
    """Formata um número CNJ para exibição com separadores corretos.

    Aceita tanto o número já formatado quanto apenas os dígitos (20 dígitos).
    Retorna no formato: NNNNNNN-DD.AAAA.J.TR.OOOO

    Args:
        numero: Número CNJ formatado ou apenas dígitos (20 caracteres numéricos).

    Returns:
        String formatada no padrão NNNNNNN-DD.AAAA.J.TR.OOOO.

    Raises:
        ValueError: Se o número não pode ser formatado (quantidade de dígitos incorreta
            ou formato inválido).
    """
    # Se já está no formato correto, retorna como está
    if CNJ_PATTERN.match(numero):
        return numero

    # Remove caracteres não numéricos para tentar formatar
    digits = re.sub(r'\D', '', numero)

    if len(digits) != 20:
        raise ValueError(
            f"Número CNJ deve conter 20 dígitos, recebido: {len(digits)} dígitos"
        )

    # NNNNNNN-DD.AAAA.J.TR.OOOO
    formatted = (
        f"{digits[0:7]}-{digits[7:9]}.{digits[9:13]}"
        f".{digits[13]}.{digits[14:16]}.{digits[16:20]}"
    )
    return formatted
