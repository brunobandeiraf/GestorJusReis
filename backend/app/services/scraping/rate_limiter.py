"""Rate limiter para controle de frequência de requisições a tribunais."""

import time
import threading


class RateLimiter:
    """Rate limiter baseado em intervalo mínimo entre requisições.

    Implementa controle de frequência thread-safe para evitar
    sobrecarga no servidor do tribunal.

    Configuração padrão:
    - Busca inicial: 1 requisição a cada 2 segundos
    - Paginação: 1 requisição a cada 1 segundo
    """

    def __init__(self, intervalo_minimo: float = 2.0):
        """
        Args:
            intervalo_minimo: Segundos mínimos entre requisições.
        """
        self._intervalo = intervalo_minimo
        self._ultimo_request: float = 0.0
        self._lock = threading.Lock()

    def aguardar(self) -> None:
        """Bloqueia até que o intervalo mínimo seja respeitado.

        Thread-safe: múltiplas threads podem chamar simultaneamente.
        """
        with self._lock:
            agora = time.time()
            tempo_desde_ultimo = agora - self._ultimo_request
            if tempo_desde_ultimo < self._intervalo:
                espera = self._intervalo - tempo_desde_ultimo
                time.sleep(espera)
            self._ultimo_request = time.time()

    def aguardar_paginacao(self) -> None:
        """Aguarda intervalo reduzido para requisições de paginação (1s)."""
        with self._lock:
            agora = time.time()
            intervalo_paginacao = 1.0
            tempo_desde_ultimo = agora - self._ultimo_request
            if tempo_desde_ultimo < intervalo_paginacao:
                espera = intervalo_paginacao - tempo_desde_ultimo
                time.sleep(espera)
            self._ultimo_request = time.time()

    @property
    def tempo_espera(self) -> float:
        """Retorna tempo de espera estimado (em segundos) até próxima permissão."""
        agora = time.time()
        tempo_desde_ultimo = agora - self._ultimo_request
        if tempo_desde_ultimo >= self._intervalo:
            return 0.0
        return self._intervalo - tempo_desde_ultimo
