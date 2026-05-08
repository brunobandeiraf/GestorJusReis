"""Exceções customizadas para o módulo de scraping de tribunais."""


class TribunalIndisponivelError(Exception):
    """Tribunal offline, timeout ou erro de conexão."""

    def __init__(self, tribunal: str, motivo: str):
        self.tribunal = tribunal
        self.motivo = motivo
        super().__init__(f"Tribunal {tribunal} indisponível: {motivo}")


class CaptchaDetectadoError(Exception):
    """Tribunal exigindo verificação CAPTCHA."""

    def __init__(self, tribunal: str):
        self.tribunal = tribunal
        super().__init__(f"CAPTCHA detectado no tribunal {tribunal}")


class ScrapingError(Exception):
    """Erro ao interpretar resposta HTML do tribunal."""

    def __init__(self, tribunal: str, detalhes: str):
        self.tribunal = tribunal
        self.detalhes = detalhes
        super().__init__(f"Erro de scraping no {tribunal}: {detalhes}")


class TribunalNaoSuportadoError(Exception):
    """Tribunal não possui scraper registrado."""

    def __init__(self, tribunal_id: str):
        self.tribunal_id = tribunal_id
        super().__init__(
            f"Tribunal não suportado para busca por CPF: {tribunal_id}"
        )


class CPFInvalidoError(Exception):
    """CPF com formato ou dígitos verificadores inválidos."""

    def __init__(self, motivo: str):
        self.motivo = motivo
        super().__init__(f"CPF inválido: {motivo}")
