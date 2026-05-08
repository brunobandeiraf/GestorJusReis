"""Mapeamento de tribunais brasileiros para endpoints da API DataJud.

Este módulo fornece o mapeamento entre o código do tribunal extraído do número CNJ
(formato J.TR) e a sigla utilizada nos endpoints da API pública DataJud do CNJ.

Endpoint pattern: https://api-publica.datajud.cnj.jus.br/api_publica_{sigla_tribunal}/_search
"""

# URL base da API pública DataJud
DATAJUD_BASE_URL = "https://api-publica.datajud.cnj.jus.br"

# Mapeamento J.TR → sigla do tribunal usada no endpoint da API DataJud.
# J = ramo da justiça, TR = código do tribunal (2 dígitos)
TRIBUNAL_ENDPOINTS = {
    # Tribunais Superiores
    "1.00": "stf",       # Supremo Tribunal Federal
    "2.00": "cnj",       # Conselho Nacional de Justiça
    "3.00": "stj",       # Superior Tribunal de Justiça
    "5.00": "tst",       # Tribunal Superior do Trabalho
    "6.00": "tse",       # Tribunal Superior Eleitoral

    # Justiça Federal (4.XX) - Tribunais Regionais Federais
    "4.01": "trf1",      # TRF 1ª Região (DF, GO, MT, BA, PI, MA, PA, AM, AC, RR, RO, AP, TO, MG)
    "4.02": "trf2",      # TRF 2ª Região (RJ, ES)
    "4.03": "trf3",      # TRF 3ª Região (SP, MS)
    "4.04": "trf4",      # TRF 4ª Região (PR, SC, RS)
    "4.05": "trf5",      # TRF 5ª Região (PE, CE, AL, SE, RN, PB)

    # Justiça do Trabalho (5.XX) - Tribunais Regionais do Trabalho
    "5.01": "trt1",      # TRT 1ª Região (RJ)
    "5.02": "trt2",      # TRT 2ª Região (SP - Capital)
    "5.03": "trt3",      # TRT 3ª Região (MG)
    "5.04": "trt4",      # TRT 4ª Região (RS)
    "5.05": "trt5",      # TRT 5ª Região (BA)
    "5.06": "trt6",      # TRT 6ª Região (PE)
    "5.07": "trt7",      # TRT 7ª Região (CE)
    "5.08": "trt8",      # TRT 8ª Região (PA, AP)
    "5.09": "trt9",      # TRT 9ª Região (PR)
    "5.10": "trt10",     # TRT 10ª Região (DF, TO)
    "5.11": "trt11",     # TRT 11ª Região (AM, RR)
    "5.12": "trt12",     # TRT 12ª Região (SC)
    "5.13": "trt13",     # TRT 13ª Região (PB)
    "5.14": "trt14",     # TRT 14ª Região (RO, AC)
    "5.15": "trt15",     # TRT 15ª Região (SP - Interior/Campinas)
    "5.16": "trt16",     # TRT 16ª Região (MA)
    "5.17": "trt17",     # TRT 17ª Região (ES)
    "5.18": "trt18",     # TRT 18ª Região (GO)
    "5.19": "trt19",     # TRT 19ª Região (AL)
    "5.20": "trt20",     # TRT 20ª Região (SE)
    "5.21": "trt21",     # TRT 21ª Região (RN)
    "5.22": "trt22",     # TRT 22ª Região (PI)
    "5.23": "trt23",     # TRT 23ª Região (MT)
    "5.24": "trt24",     # TRT 24ª Região (MS)

    # Justiça Eleitoral (6.XX) - Tribunais Regionais Eleitorais
    "6.01": "tre-ac",    # TRE Acre
    "6.02": "tre-al",    # TRE Alagoas
    "6.03": "tre-ap",    # TRE Amapá
    "6.04": "tre-am",    # TRE Amazonas
    "6.05": "tre-ba",    # TRE Bahia
    "6.06": "tre-ce",    # TRE Ceará
    "6.07": "tre-df",    # TRE Distrito Federal
    "6.08": "tre-es",    # TRE Espírito Santo
    "6.09": "tre-go",    # TRE Goiás
    "6.10": "tre-ma",    # TRE Maranhão
    "6.11": "tre-mt",    # TRE Mato Grosso
    "6.12": "tre-ms",    # TRE Mato Grosso do Sul
    "6.13": "tre-mg",    # TRE Minas Gerais
    "6.14": "tre-pa",    # TRE Pará
    "6.15": "tre-pb",    # TRE Paraíba
    "6.16": "tre-pr",    # TRE Paraná
    "6.17": "tre-pe",    # TRE Pernambuco
    "6.18": "tre-pi",    # TRE Piauí
    "6.19": "tre-rj",    # TRE Rio de Janeiro
    "6.20": "tre-rn",    # TRE Rio Grande do Norte
    "6.21": "tre-rs",    # TRE Rio Grande do Sul
    "6.22": "tre-ro",    # TRE Rondônia
    "6.23": "tre-rr",    # TRE Roraima
    "6.24": "tre-sc",    # TRE Santa Catarina
    "6.25": "tre-sp",    # TRE São Paulo
    "6.26": "tre-se",    # TRE Sergipe
    "6.27": "tre-to",    # TRE Tocantins

    # Justiça Militar (7.XX)
    "7.00": "stm",       # Superior Tribunal Militar
    "7.13": "tjmmg",     # Tribunal de Justiça Militar de Minas Gerais
    "7.21": "tjmrs",     # Tribunal de Justiça Militar do Rio Grande do Sul
    "7.26": "tjmsp",     # Tribunal de Justiça Militar de São Paulo

    # Justiça Estadual (8.XX) - Tribunais de Justiça
    "8.01": "tjac",      # Tribunal de Justiça do Acre
    "8.02": "tjal",      # Tribunal de Justiça de Alagoas
    "8.03": "tjap",      # Tribunal de Justiça do Amapá
    "8.04": "tjam",      # Tribunal de Justiça do Amazonas
    "8.05": "tjba",      # Tribunal de Justiça da Bahia
    "8.06": "tjce",      # Tribunal de Justiça do Ceará
    "8.07": "tjdft",     # Tribunal de Justiça do Distrito Federal e Territórios
    "8.08": "tjes",      # Tribunal de Justiça do Espírito Santo
    "8.09": "tjgo",      # Tribunal de Justiça de Goiás
    "8.10": "tjma",      # Tribunal de Justiça do Maranhão
    "8.11": "tjmt",      # Tribunal de Justiça de Mato Grosso
    "8.12": "tjms",      # Tribunal de Justiça de Mato Grosso do Sul
    "8.13": "tjmg",      # Tribunal de Justiça de Minas Gerais
    "8.14": "tjpa",      # Tribunal de Justiça do Pará
    "8.15": "tjpb",      # Tribunal de Justiça da Paraíba
    "8.16": "tjpr",      # Tribunal de Justiça do Paraná
    "8.17": "tjpe",      # Tribunal de Justiça de Pernambuco
    "8.18": "tjpi",      # Tribunal de Justiça do Piauí
    "8.19": "tjrj",      # Tribunal de Justiça do Rio de Janeiro
    "8.20": "tjrn",      # Tribunal de Justiça do Rio Grande do Norte
    "8.21": "tjrs",      # Tribunal de Justiça do Rio Grande do Sul
    "8.22": "tjro",      # Tribunal de Justiça de Rondônia
    "8.23": "tjrr",      # Tribunal de Justiça de Roraima
    "8.24": "tjsc",      # Tribunal de Justiça de Santa Catarina
    "8.25": "tjse",      # Tribunal de Justiça de Sergipe
    "8.26": "tjsp",      # Tribunal de Justiça de São Paulo
    "8.27": "tjto",      # Tribunal de Justiça de Tocantins
}

# Mapeamento de sigla do tribunal → URL de consulta pública
# Cada tribunal tem seu próprio sistema de consulta processual
_CONSULTA_PUBLICA_URLS = {
    # Tribunais Superiores
    "stf": "https://portal.stf.jus.br/processos/listarProcessos.asp?classe=&numeroProcesso={numero_sequencial}",
    "cnj": "https://www.cnj.jus.br/pjecnj/ConsultaPublica/listView.seam",
    "stj": "https://processo.stj.jus.br/processo/pesquisa/",
    "tst": "https://pje.tst.jus.br/consultaprocessual/detalhe-processo/{numero_cnj}",
    "tse": "https://www.tse.jus.br/servicos-judiciais/processos",

    # Justiça Federal - TRFs (PJe)
    "trf1": "https://pje1g.trf1.jus.br/consultapublica/ConsultaPublica/listView.seam",
    "trf2": "https://eproc.trf2.jus.br/eproc/externo_controlador.php?acao=processo_consulta_publica",
    "trf3": "https://pje1g.trf3.jus.br/pje/ConsultaPublica/listView.seam",
    "trf4": "https://eproc.trf4.jus.br/eproc2trf4/externo_controlador.php?acao=processo_consulta_publica",
    "trf5": "https://pje.trf5.jus.br/pje/ConsultaPublica/listView.seam",

    # Justiça do Trabalho - TRTs (PJe)
    "trt1": "https://pje.trt1.jus.br/consultaprocessual/detalhe-processo/{numero_cnj}",
    "trt2": "https://pje.trt2.jus.br/consultaprocessual/detalhe-processo/{numero_cnj}",
    "trt3": "https://pje.trt3.jus.br/consultaprocessual/detalhe-processo/{numero_cnj}",
    "trt4": "https://pje.trt4.jus.br/consultaprocessual/detalhe-processo/{numero_cnj}",
    "trt5": "https://pje.trt5.jus.br/consultaprocessual/detalhe-processo/{numero_cnj}",
    "trt6": "https://pje.trt6.jus.br/consultaprocessual/detalhe-processo/{numero_cnj}",
    "trt7": "https://pje.trt7.jus.br/consultaprocessual/detalhe-processo/{numero_cnj}",
    "trt8": "https://pje.trt8.jus.br/consultaprocessual/detalhe-processo/{numero_cnj}",
    "trt9": "https://pje.trt9.jus.br/consultaprocessual/detalhe-processo/{numero_cnj}",
    "trt10": "https://pje.trt10.jus.br/consultaprocessual/detalhe-processo/{numero_cnj}",
    "trt11": "https://pje.trt11.jus.br/consultaprocessual/detalhe-processo/{numero_cnj}",
    "trt12": "https://pje.trt12.jus.br/consultaprocessual/detalhe-processo/{numero_cnj}",
    "trt13": "https://pje.trt13.jus.br/consultaprocessual/detalhe-processo/{numero_cnj}",
    "trt14": "https://pje.trt14.jus.br/consultaprocessual/detalhe-processo/{numero_cnj}",
    "trt15": "https://pje.trt15.jus.br/consultaprocessual/detalhe-processo/{numero_cnj}",
    "trt16": "https://pje.trt16.jus.br/consultaprocessual/detalhe-processo/{numero_cnj}",
    "trt17": "https://pje.trt17.jus.br/consultaprocessual/detalhe-processo/{numero_cnj}",
    "trt18": "https://pje.trt18.jus.br/consultaprocessual/detalhe-processo/{numero_cnj}",
    "trt19": "https://pje.trt19.jus.br/consultaprocessual/detalhe-processo/{numero_cnj}",
    "trt20": "https://pje.trt20.jus.br/consultaprocessual/detalhe-processo/{numero_cnj}",
    "trt21": "https://pje.trt21.jus.br/consultaprocessual/detalhe-processo/{numero_cnj}",
    "trt22": "https://pje.trt22.jus.br/consultaprocessual/detalhe-processo/{numero_cnj}",
    "trt23": "https://pje.trt23.jus.br/consultaprocessual/detalhe-processo/{numero_cnj}",
    "trt24": "https://pje.trt24.jus.br/consultaprocessual/detalhe-processo/{numero_cnj}",

    # Justiça Eleitoral - TREs
    "tre-ac": "https://www.tre-ac.jus.br/servicos-judiciais/processos",
    "tre-al": "https://www.tre-al.jus.br/servicos-judiciais/processos",
    "tre-ap": "https://www.tre-ap.jus.br/servicos-judiciais/processos",
    "tre-am": "https://www.tre-am.jus.br/servicos-judiciais/processos",
    "tre-ba": "https://www.tre-ba.jus.br/servicos-judiciais/processos",
    "tre-ce": "https://www.tre-ce.jus.br/servicos-judiciais/processos",
    "tre-df": "https://www.tre-df.jus.br/servicos-judiciais/processos",
    "tre-es": "https://www.tre-es.jus.br/servicos-judiciais/processos",
    "tre-go": "https://www.tre-go.jus.br/servicos-judiciais/processos",
    "tre-ma": "https://www.tre-ma.jus.br/servicos-judiciais/processos",
    "tre-mt": "https://www.tre-mt.jus.br/servicos-judiciais/processos",
    "tre-ms": "https://www.tre-ms.jus.br/servicos-judiciais/processos",
    "tre-mg": "https://www.tre-mg.jus.br/servicos-judiciais/processos",
    "tre-pa": "https://www.tre-pa.jus.br/servicos-judiciais/processos",
    "tre-pb": "https://www.tre-pb.jus.br/servicos-judiciais/processos",
    "tre-pr": "https://www.tre-pr.jus.br/servicos-judiciais/processos",
    "tre-pe": "https://www.tre-pe.jus.br/servicos-judiciais/processos",
    "tre-pi": "https://www.tre-pi.jus.br/servicos-judiciais/processos",
    "tre-rj": "https://www.tre-rj.jus.br/servicos-judiciais/processos",
    "tre-rn": "https://www.tre-rn.jus.br/servicos-judiciais/processos",
    "tre-rs": "https://www.tre-rs.jus.br/servicos-judiciais/processos",
    "tre-ro": "https://www.tre-ro.jus.br/servicos-judiciais/processos",
    "tre-rr": "https://www.tre-rr.jus.br/servicos-judiciais/processos",
    "tre-sc": "https://www.tre-sc.jus.br/servicos-judiciais/processos",
    "tre-sp": "https://www.tre-sp.jus.br/servicos-judiciais/processos",
    "tre-se": "https://www.tre-se.jus.br/servicos-judiciais/processos",
    "tre-to": "https://www.tre-to.jus.br/servicos-judiciais/processos",

    # Justiça Militar
    "stm": "https://www.stm.jus.br/servicos-stm/processos",
    "tjmmg": "https://www.tjmmg.jus.br/consulta-processual",
    "tjmrs": "https://www.tjmrs.jus.br/consulta-processual",
    "tjmsp": "https://www.tjmsp.jus.br/consulta-processual",

    # Justiça Estadual - TJs (ESAJ e PJe)
    "tjac": "https://esaj.tjac.jus.br/cpopg/open.do",
    "tjal": "https://pje.tjal.jus.br/pje/ConsultaPublica/listView.seam",
    "tjap": "https://tucujuris.tjap.jus.br/tucujuris/pages/consultar-processo/consultar-processo.html",
    "tjam": "https://consultasaj.tjam.jus.br/cpopg/open.do",
    "tjba": "https://esaj.tjba.jus.br/cpopg/open.do",
    "tjce": "https://esaj.tjce.jus.br/cpopg/open.do",
    "tjdft": "https://pje.tjdft.jus.br/consultapublica/ConsultaPublica/listView.seam",
    "tjes": "https://sistemas.tjes.jus.br/pje/ConsultaPublica/listView.seam",
    "tjgo": "https://pje.tjgo.jus.br/ConsultaPublica/listView.seam",
    "tjma": "https://pje.tjma.jus.br/pje/ConsultaPublica/listView.seam",
    "tjmt": "https://pje.tjmt.jus.br/pje/ConsultaPublica/listView.seam",
    "tjms": "https://esaj.tjms.jus.br/cpopg/open.do",
    "tjmg": "https://pje.tjmg.jus.br/pje/ConsultaPublica/listView.seam",
    "tjpa": "https://consultas.tjpa.jus.br/consultaprocessual",
    "tjpb": "https://pje.tjpb.jus.br/pje/ConsultaPublica/listView.seam",
    "tjpr": "https://projudi.tjpr.jus.br/projudi/",
    "tjpe": "https://pje.tjpe.jus.br/pje/ConsultaPublica/listView.seam",
    "tjpi": "https://pje.tjpi.jus.br/pje/ConsultaPublica/listView.seam",
    "tjrj": "https://www3.tjrj.jus.br/consultaprocessual/",
    "tjrn": "https://pje.tjrn.jus.br/pje/ConsultaPublica/listView.seam",
    "tjrs": "https://www.tjrs.jus.br/novo/busca/?return=proc",
    "tjro": "https://pje.tjro.jus.br/pje/ConsultaPublica/listView.seam",
    "tjrr": "https://pje.tjrr.jus.br/pje/ConsultaPublica/listView.seam",
    "tjsc": "https://esaj.tjsc.jus.br/cpopg/open.do",
    "tjse": "https://pje.tjse.jus.br/pje/ConsultaPublica/listView.seam",
    "tjsp": "https://esaj.tjsp.jus.br/cpopg/open.do",
    "tjto": "https://eproc1.tjto.jus.br/eprocV2_prod_1grau/externo_controlador.php?acao=processo_consulta_publica",
}


def obter_endpoint_tribunal(codigo_tribunal: str) -> str:
    """Retorna a URL completa do endpoint da API DataJud para um tribunal.

    Args:
        codigo_tribunal: Código do tribunal no formato "J.TR" (ex: "8.26" para TJSP).

    Returns:
        URL completa do endpoint da API DataJud para o tribunal.

    Raises:
        ValueError: Se o código do tribunal não é reconhecido.
    """
    sigla = TRIBUNAL_ENDPOINTS.get(codigo_tribunal)
    if sigla is None:
        raise ValueError(
            f"Tribunal não reconhecido: '{codigo_tribunal}'. "
            f"Use listar_tribunais_suportados() para ver os tribunais disponíveis."
        )
    return f"{DATAJUD_BASE_URL}/api_publica_{sigla}/_search"


def obter_url_consulta_publica(tribunal: str, numero_cnj: str) -> str:
    """Retorna a URL de consulta pública do tribunal para acesso direto ao processo.

    Gera um link para a página de consulta processual do tribunal de origem,
    permitindo ao usuário acessar manualmente os documentos e detalhes do processo.

    Args:
        tribunal: Sigla do tribunal (ex: "tjsp", "trt2") ou código J.TR (ex: "8.26").
        numero_cnj: Número CNJ completo do processo (ex: "0001234-56.2023.8.26.0100").

    Returns:
        URL da página de consulta pública do tribunal.

    Raises:
        ValueError: Se o tribunal não é reconhecido.
    """
    # Se recebeu código J.TR, converte para sigla
    sigla = tribunal
    if "." in tribunal and tribunal in TRIBUNAL_ENDPOINTS:
        sigla = TRIBUNAL_ENDPOINTS[tribunal]

    url_template = _CONSULTA_PUBLICA_URLS.get(sigla)
    if url_template is None:
        raise ValueError(
            f"URL de consulta pública não disponível para o tribunal: '{tribunal}'."
        )

    # Substitui placeholders na URL template
    return url_template.format(
        numero_cnj=numero_cnj,
        numero_sequencial=numero_cnj.split("-")[0] if "-" in numero_cnj else numero_cnj,
    )


def listar_tribunais_suportados() -> list:
    """Retorna a lista de todos os tribunais suportados pelo sistema.

    Returns:
        Lista de dicionários com informações de cada tribunal:
        - codigo: código J.TR usado no número CNJ
        - sigla: sigla do tribunal usada no endpoint da API
        - endpoint: URL completa do endpoint da API DataJud
    """
    tribunais = []
    for codigo, sigla in sorted(TRIBUNAL_ENDPOINTS.items()):
        tribunais.append({
            "codigo": codigo,
            "sigla": sigla,
            "endpoint": f"{DATAJUD_BASE_URL}/api_publica_{sigla}/_search",
        })
    return tribunais
