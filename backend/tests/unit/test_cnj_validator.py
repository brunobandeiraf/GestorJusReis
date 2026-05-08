"""Testes unitários para o validador de número CNJ."""

import pytest

from app.services.cnj_validator import (
    extrair_tribunal,
    formatar_numero_cnj,
    validar_numero_cnj,
)


class TestValidarNumeroCnj:
    """Testes para validar_numero_cnj."""

    def test_numero_valido_tjsp(self):
        assert validar_numero_cnj("0001234-56.2023.8.26.0100") is True

    def test_numero_valido_trt2(self):
        assert validar_numero_cnj("0000123-45.2022.5.02.0001") is True

    def test_numero_valido_justica_federal(self):
        assert validar_numero_cnj("1234567-89.2024.4.01.3400") is True

    def test_formato_invalido_sem_hifen(self):
        assert validar_numero_cnj("000123456.2023.8.26.0100") is False

    def test_formato_invalido_sem_pontos(self):
        assert validar_numero_cnj("0001234-56-2023-8-26-0100") is False

    def test_formato_invalido_digitos_a_menos(self):
        assert validar_numero_cnj("001234-56.2023.8.26.0100") is False

    def test_formato_invalido_digitos_a_mais(self):
        assert validar_numero_cnj("00012345-56.2023.8.26.0100") is False

    def test_formato_invalido_letras(self):
        assert validar_numero_cnj("ABCDEFG-56.2023.8.26.0100") is False

    def test_string_vazia(self):
        assert validar_numero_cnj("") is False

    def test_string_aleatoria(self):
        assert validar_numero_cnj("nao-e-um-numero-cnj") is False

    def test_none_retorna_false(self):
        assert validar_numero_cnj(None) is False

    def test_numero_com_espacos(self):
        assert validar_numero_cnj(" 0001234-56.2023.8.26.0100 ") is False

    def test_numero_parcial(self):
        assert validar_numero_cnj("0001234-56.2023") is False


class TestExtrairTribunal:
    """Testes para extrair_tribunal."""

    def test_extrair_tjsp(self):
        assert extrair_tribunal("0001234-56.2023.8.26.0100") == "8.26"

    def test_extrair_trt2(self):
        assert extrair_tribunal("0000123-45.2022.5.02.0001") == "5.02"

    def test_extrair_justica_federal(self):
        assert extrair_tribunal("1234567-89.2024.4.01.3400") == "4.01"

    def test_extrair_stf(self):
        assert extrair_tribunal("0000001-00.2020.1.00.0000") == "1.00"

    def test_numero_invalido_levanta_erro(self):
        with pytest.raises(ValueError, match="Número CNJ inválido"):
            extrair_tribunal("invalido")

    def test_string_vazia_levanta_erro(self):
        with pytest.raises(ValueError, match="Número CNJ inválido"):
            extrair_tribunal("")


class TestFormatarNumeroCnj:
    """Testes para formatar_numero_cnj."""

    def test_formatar_apenas_digitos(self):
        result = formatar_numero_cnj("00012345620238260100")
        assert result == "0001234-56.2023.8.26.0100"

    def test_formatar_numero_ja_formatado(self):
        result = formatar_numero_cnj("0001234-56.2023.8.26.0100")
        assert result == "0001234-56.2023.8.26.0100"

    def test_formatar_digitos_com_espacos(self):
        result = formatar_numero_cnj("0001234 56 2023 8 26 0100")
        assert result == "0001234-56.2023.8.26.0100"

    def test_formatar_digitos_insuficientes(self):
        with pytest.raises(ValueError, match="20 dígitos"):
            formatar_numero_cnj("123456")

    def test_formatar_digitos_excedentes(self):
        with pytest.raises(ValueError, match="20 dígitos"):
            formatar_numero_cnj("123456789012345678901")

    def test_formatar_string_vazia(self):
        with pytest.raises(ValueError, match="20 dígitos"):
            formatar_numero_cnj("")

    def test_formatar_trt2(self):
        result = formatar_numero_cnj("00001234520225020001")
        assert result == "0000123-45.2022.5.02.0001"
