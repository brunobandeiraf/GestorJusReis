"""Testes unitários para o módulo de mapeamento de tribunais."""

import pytest

from app.utils.tribunal_mapper import (
    DATAJUD_BASE_URL,
    TRIBUNAL_ENDPOINTS,
    listar_tribunais_suportados,
    obter_endpoint_tribunal,
    obter_url_consulta_publica,
)


class TestTribunalEndpoints:
    """Testes para o dicionário TRIBUNAL_ENDPOINTS."""

    def test_contem_todos_tjs_estaduais(self):
        """Verifica que todos os 27 TJs estaduais estão mapeados."""
        tjs_esperados = [
            "tjac", "tjal", "tjap", "tjam", "tjba", "tjce", "tjdft",
            "tjes", "tjgo", "tjma", "tjmt", "tjms", "tjmg", "tjpa",
            "tjpb", "tjpr", "tjpe", "tjpi", "tjrj", "tjrn", "tjrs",
            "tjro", "tjrr", "tjsc", "tjse", "tjsp", "tjto",
        ]
        siglas_estaduais = [
            v for k, v in TRIBUNAL_ENDPOINTS.items() if k.startswith("8.")
        ]
        for tj in tjs_esperados:
            assert tj in siglas_estaduais, f"{tj} não encontrado nos TJs estaduais"
        assert len(siglas_estaduais) == 27

    def test_contem_todos_trfs(self):
        """Verifica que os 5 TRFs estão mapeados."""
        trfs_esperados = ["trf1", "trf2", "trf3", "trf4", "trf5"]
        siglas_federais = [
            v for k, v in TRIBUNAL_ENDPOINTS.items() if k.startswith("4.")
        ]
        for trf in trfs_esperados:
            assert trf in siglas_federais, f"{trf} não encontrado nos TRFs"
        assert len(siglas_federais) == 5

    def test_contem_todos_trts(self):
        """Verifica que os 24 TRTs estão mapeados."""
        trts_esperados = [f"trt{i}" for i in range(1, 25)]
        siglas_trabalho = [
            v for k, v in TRIBUNAL_ENDPOINTS.items()
            if k.startswith("5.") and k != "5.00"
        ]
        for trt in trts_esperados:
            assert trt in siglas_trabalho, f"{trt} não encontrado nos TRTs"
        assert len(siglas_trabalho) == 24

    def test_contem_todos_tres(self):
        """Verifica que os 27 TREs estão mapeados."""
        siglas_eleitorais = [
            v for k, v in TRIBUNAL_ENDPOINTS.items()
            if k.startswith("6.") and k != "6.00"
        ]
        assert len(siglas_eleitorais) == 27

    def test_contem_tribunais_superiores(self):
        """Verifica que os tribunais superiores estão mapeados."""
        assert TRIBUNAL_ENDPOINTS["1.00"] == "stf"
        assert TRIBUNAL_ENDPOINTS["2.00"] == "cnj"
        assert TRIBUNAL_ENDPOINTS["3.00"] == "stj"
        assert TRIBUNAL_ENDPOINTS["5.00"] == "tst"
        assert TRIBUNAL_ENDPOINTS["6.00"] == "tse"

    def test_contem_justica_militar(self):
        """Verifica que a justiça militar está mapeada."""
        assert TRIBUNAL_ENDPOINTS["7.00"] == "stm"

    def test_codigos_formato_correto(self):
        """Verifica que todos os códigos seguem o formato J.TR (dígito.dois_dígitos)."""
        import re
        pattern = re.compile(r"^\d\.\d{2}$")
        for codigo in TRIBUNAL_ENDPOINTS:
            assert pattern.match(codigo), f"Código '{codigo}' não segue formato J.TR"


class TestObterEndpointTribunal:
    """Testes para a função obter_endpoint_tribunal."""

    def test_retorna_url_correta_tjsp(self):
        """Verifica URL para TJSP (8.26)."""
        url = obter_endpoint_tribunal("8.26")
        assert url == f"{DATAJUD_BASE_URL}/api_publica_tjsp/_search"

    def test_retorna_url_correta_trf1(self):
        """Verifica URL para TRF1 (4.01)."""
        url = obter_endpoint_tribunal("4.01")
        assert url == f"{DATAJUD_BASE_URL}/api_publica_trf1/_search"

    def test_retorna_url_correta_trt2(self):
        """Verifica URL para TRT2 (5.02)."""
        url = obter_endpoint_tribunal("5.02")
        assert url == f"{DATAJUD_BASE_URL}/api_publica_trt2/_search"

    def test_retorna_url_correta_stf(self):
        """Verifica URL para STF (1.00)."""
        url = obter_endpoint_tribunal("1.00")
        assert url == f"{DATAJUD_BASE_URL}/api_publica_stf/_search"

    def test_retorna_url_correta_tse(self):
        """Verifica URL para TSE (6.00)."""
        url = obter_endpoint_tribunal("6.00")
        assert url == f"{DATAJUD_BASE_URL}/api_publica_tse/_search"

    def test_retorna_url_correta_tre_sp(self):
        """Verifica URL para TRE-SP (6.25)."""
        url = obter_endpoint_tribunal("6.25")
        assert url == f"{DATAJUD_BASE_URL}/api_publica_tre-sp/_search"

    def test_retorna_url_correta_stm(self):
        """Verifica URL para STM (7.00)."""
        url = obter_endpoint_tribunal("7.00")
        assert url == f"{DATAJUD_BASE_URL}/api_publica_stm/_search"

    def test_url_segue_padrao_datajud(self):
        """Verifica que todas as URLs seguem o padrão da API DataJud."""
        for codigo in TRIBUNAL_ENDPOINTS:
            url = obter_endpoint_tribunal(codigo)
            assert url.startswith(DATAJUD_BASE_URL)
            assert url.endswith("/_search")
            assert "/api_publica_" in url

    def test_tribunal_nao_reconhecido_levanta_erro(self):
        """Verifica que código desconhecido levanta ValueError."""
        with pytest.raises(ValueError, match="Tribunal não reconhecido"):
            obter_endpoint_tribunal("9.99")

    def test_codigo_vazio_levanta_erro(self):
        """Verifica que string vazia levanta ValueError."""
        with pytest.raises(ValueError, match="Tribunal não reconhecido"):
            obter_endpoint_tribunal("")

    def test_codigo_formato_invalido_levanta_erro(self):
        """Verifica que formato inválido levanta ValueError."""
        with pytest.raises(ValueError):
            obter_endpoint_tribunal("826")


class TestObterUrlConsultaPublica:
    """Testes para a função obter_url_consulta_publica."""

    def test_url_tjsp_esaj(self):
        """Verifica URL de consulta pública do TJSP (ESAJ)."""
        url = obter_url_consulta_publica("tjsp", "0001234-56.2023.8.26.0100")
        assert "esaj.tjsp.jus.br" in url

    def test_url_trt2_pje(self):
        """Verifica URL de consulta pública do TRT2 (PJe)."""
        numero = "0001234-56.2023.5.02.0001"
        url = obter_url_consulta_publica("trt2", numero)
        assert "pje.trt2.jus.br" in url
        assert numero in url

    def test_aceita_codigo_jtr(self):
        """Verifica que aceita código J.TR como tribunal."""
        url = obter_url_consulta_publica("8.26", "0001234-56.2023.8.26.0100")
        assert "esaj.tjsp.jus.br" in url

    def test_tribunal_desconhecido_levanta_erro(self):
        """Verifica que tribunal desconhecido levanta ValueError."""
        with pytest.raises(ValueError, match="URL de consulta pública não disponível"):
            obter_url_consulta_publica("tribunal_inexistente", "0001234-56.2023.8.26.0100")

    def test_url_stf(self):
        """Verifica URL de consulta pública do STF."""
        url = obter_url_consulta_publica("stf", "0001234-56.2023.1.00.0000")
        assert "portal.stf.jus.br" in url

    def test_url_tre(self):
        """Verifica URL de consulta pública de um TRE."""
        url = obter_url_consulta_publica("tre-sp", "0001234-56.2023.6.25.0000")
        assert "tre-sp.jus.br" in url


class TestListarTribunaisSuportados:
    """Testes para a função listar_tribunais_suportados."""

    def test_retorna_lista_nao_vazia(self):
        """Verifica que a lista não está vazia."""
        tribunais = listar_tribunais_suportados()
        assert len(tribunais) > 0

    def test_quantidade_total_tribunais(self):
        """Verifica que a quantidade total corresponde ao dicionário."""
        tribunais = listar_tribunais_suportados()
        assert len(tribunais) == len(TRIBUNAL_ENDPOINTS)

    def test_estrutura_item(self):
        """Verifica que cada item tem as chaves esperadas."""
        tribunais = listar_tribunais_suportados()
        for tribunal in tribunais:
            assert "codigo" in tribunal
            assert "sigla" in tribunal
            assert "endpoint" in tribunal

    def test_endpoint_formato_correto(self):
        """Verifica que os endpoints seguem o padrão da API DataJud."""
        tribunais = listar_tribunais_suportados()
        for tribunal in tribunais:
            assert tribunal["endpoint"].startswith(DATAJUD_BASE_URL)
            assert tribunal["endpoint"].endswith("/_search")
            assert f"/api_publica_{tribunal['sigla']}/_search" in tribunal["endpoint"]

    def test_lista_ordenada_por_codigo(self):
        """Verifica que a lista está ordenada por código."""
        tribunais = listar_tribunais_suportados()
        codigos = [t["codigo"] for t in tribunais]
        assert codigos == sorted(codigos)

    def test_contem_tjsp(self):
        """Verifica que TJSP está na lista."""
        tribunais = listar_tribunais_suportados()
        siglas = [t["sigla"] for t in tribunais]
        assert "tjsp" in siglas

    def test_contem_stf(self):
        """Verifica que STF está na lista."""
        tribunais = listar_tribunais_suportados()
        siglas = [t["sigla"] for t in tribunais]
        assert "stf" in siglas
