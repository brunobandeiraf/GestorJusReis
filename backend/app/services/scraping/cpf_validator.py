"""Validador de CPF com verificação de formato e dígitos verificadores."""

import re


class CPFValidator:
    """Validador de CPF com verificação de formato e dígitos verificadores.

    Regras:
    - Aceita com ou sem formatação (XXX.XXX.XXX-XX ou XXXXXXXXXXX)
    - Rejeita CPFs com todos os dígitos iguais
    - Valida dígitos verificadores (algoritmo módulo 11)
    """

    @staticmethod
    def validar(cpf: str) -> bool:
        """Valida formato e dígitos verificadores do CPF.

        Args:
            cpf: String com CPF (com ou sem formatação).

        Returns:
            True se CPF é válido, False caso contrário.
        """
        # Remove formatação
        digitos = re.sub(r'\D', '', cpf)

        # Verifica se tem exatamente 11 dígitos
        if len(digitos) != 11:
            return False

        # Rejeita CPFs com todos os dígitos iguais
        if len(set(digitos)) == 1:
            return False

        # Valida primeiro dígito verificador
        soma = 0
        for i in range(9):
            soma += int(digitos[i]) * (10 - i)
        resto = soma % 11
        primeiro_digito = 0 if resto < 2 else 11 - resto
        if int(digitos[9]) != primeiro_digito:
            return False

        # Valida segundo dígito verificador
        soma = 0
        for i in range(10):
            soma += int(digitos[i]) * (11 - i)
        resto = soma % 11
        segundo_digito = 0 if resto < 2 else 11 - resto
        if int(digitos[10]) != segundo_digito:
            return False

        return True

    @staticmethod
    def normalizar(cpf: str) -> str:
        """Remove formatação do CPF, retornando apenas 11 dígitos.

        Args:
            cpf: String com CPF (com ou sem formatação).

        Returns:
            String com 11 dígitos numéricos.

        Raises:
            ValueError: Se não é possível extrair 11 dígitos.
        """
        digitos = re.sub(r'\D', '', cpf)
        if len(digitos) != 11:
            raise ValueError(
                f"CPF deve conter 11 dígitos, recebido: {len(digitos)} dígitos"
            )
        return digitos

    @staticmethod
    def formatar(cpf: str) -> str:
        """Aplica formatação XXX.XXX.XXX-XX ao CPF.

        Args:
            cpf: String com 11 dígitos numéricos.

        Returns:
            String formatada como XXX.XXX.XXX-XX.

        Raises:
            ValueError: Se o CPF não contém exatamente 11 dígitos.
        """
        digitos = re.sub(r'\D', '', cpf)
        if len(digitos) != 11:
            raise ValueError(
                f"CPF deve conter 11 dígitos para formatação, "
                f"recebido: {len(digitos)} dígitos"
            )
        return f"{digitos[0:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:11]}"
