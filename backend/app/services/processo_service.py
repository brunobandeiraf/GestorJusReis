"""Serviço de lógica de negócio para processos judiciais.

Este módulo implementa as operações de cadastro, atualização, consulta avulsa
e monitoramento diário de processos judiciais.
"""

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from app import db
from app.models.log_execucao import LogExecucao
from app.models.movimentacao import Movimentacao
from app.models.parte import Parte
from app.models.processo import Processo
from app.services.cnj_validator import extrair_tribunal, validar_numero_cnj
from app.services.datajud_client import (
    DataJudAPIError,
    DataJudClient,
    DataJudNotFoundError,
    DataJudTimeoutError,
    ProcessoDTO,
)

logger = logging.getLogger(__name__)


# --- Resultado de atualização ---


@dataclass
class AtualizacaoResult:
    """Resultado da operação de atualização de um processo."""

    atualizado: bool
    novas_movimentacoes: int
    erro: Optional[str] = None


@dataclass
class MonitoramentoLog:
    """Resultado da execução do monitoramento diário."""

    total_processos: int
    processos_atualizados: int
    processos_com_erro: int
    detalhes_erros: List[str] = field(default_factory=list)
    status: str = "sucesso"  # "sucesso", "parcial", "falha"
    duracao_segundos: int = 0


# --- Exceções customizadas ---


class ProcessoJaExisteError(Exception):
    """Erro levantado ao tentar cadastrar um processo que já existe no banco."""

    def __init__(self, numero_cnj: str):
        super().__init__(f"Processo já cadastrado: {numero_cnj}")
        self.numero_cnj = numero_cnj


class CNJInvalidoError(Exception):
    """Erro levantado quando o número CNJ fornecido é inválido."""

    def __init__(self, numero_cnj: str):
        super().__init__(
            f"Número CNJ inválido: {numero_cnj}. "
            f"Formato esperado: NNNNNNN-DD.AAAA.J.TR.OOOO"
        )
        self.numero_cnj = numero_cnj


# --- Serviço ---


class ProcessoService:
    """Serviço de lógica de negócio para processos judiciais."""

    def __init__(self, datajud_client: Optional[DataJudClient] = None):
        """Inicializa o serviço com um cliente DataJud.

        Args:
            datajud_client: Instância do DataJudClient. Se não fornecido,
                            cria uma instância padrão.
        """
        self.datajud_client = datajud_client or DataJudClient()

    def cadastrar_processo(self, numero_cnj: str) -> Processo:
        """Cadastra um processo judicial e realiza busca inicial na DataJud.

        Fluxo:
        1. Valida o formato do número CNJ
        2. Verifica se o processo já existe no banco (duplicidade)
        3. Extrai o código do tribunal a partir do número CNJ
        4. Busca dados iniciais na DataJud API
        5. Persiste o processo com movimentações e partes
        6. Se a API estiver indisponível, cadastra apenas com número CNJ e tribunal

        Args:
            numero_cnj: Número do processo no formato NNNNNNN-DD.AAAA.J.TR.OOOO

        Returns:
            Instância do modelo Processo persistida no banco.

        Raises:
            CNJInvalidoError: Se o número CNJ é inválido.
            ProcessoJaExisteError: Se o processo já está cadastrado (409 Conflict).
        """
        # 1. Validar formato CNJ
        if not validar_numero_cnj(numero_cnj):
            raise CNJInvalidoError(numero_cnj)

        # 2. Verificar duplicidade
        processo_existente = Processo.query.filter_by(numero_cnj=numero_cnj).first()
        if processo_existente:
            raise ProcessoJaExisteError(numero_cnj)

        # 3. Extrair tribunal
        codigo_tribunal = extrair_tribunal(numero_cnj)

        # 4. Buscar dados na DataJud API
        processo_dto = self._buscar_dados_datajud(numero_cnj)

        # 5. Criar e persistir processo
        processo = self._criar_processo(numero_cnj, codigo_tribunal, processo_dto)

        db.session.add(processo)
        db.session.commit()

        logger.info("Processo cadastrado com sucesso: %s", numero_cnj)
        return processo

    def atualizar_processo(self, processo_id: int) -> AtualizacaoResult:
        """Atualiza dados de um processo via DataJud API.

        Busca dados atualizados na API e compara movimentações retornadas
        com as existentes no banco. Adiciona apenas movimentações novas
        (deduplicação por data_movimentacao + nome).

        Args:
            processo_id: ID do processo no banco de dados.

        Returns:
            AtualizacaoResult com status da atualização.
        """
        # 1. Buscar processo no banco
        processo = Processo.query.get(processo_id)
        if not processo:
            return AtualizacaoResult(
                atualizado=False,
                novas_movimentacoes=0,
                erro=f"Processo não encontrado: id={processo_id}",
            )

        # 2. Buscar dados atualizados na DataJud API
        try:
            processo_dto = self.datajud_client.buscar_processo(processo.numero_cnj)
        except (DataJudAPIError, DataJudTimeoutError, DataJudNotFoundError) as e:
            logger.warning(
                "Erro ao atualizar processo %s (id=%d): %s",
                processo.numero_cnj,
                processo_id,
                str(e),
            )
            return AtualizacaoResult(
                atualizado=False,
                novas_movimentacoes=0,
                erro=str(e),
            )

        if not processo_dto:
            # API retornou None (processo não encontrado na API)
            processo.ultima_atualizacao = datetime.utcnow()
            db.session.commit()
            return AtualizacaoResult(atualizado=False, novas_movimentacoes=0)

        # 3. Deduplicar movimentações
        movimentacoes_existentes = set()
        for mov in processo.movimentacoes.all():
            chave = (mov.data_movimentacao, mov.nome)
            movimentacoes_existentes.add(chave)

        # 4. Adicionar apenas movimentações novas
        novas_count = 0
        for mov_dto in processo_dto.movimentacoes:
            data_mov = self._parse_data(mov_dto.data)
            chave = (data_mov, mov_dto.nome)

            if chave not in movimentacoes_existentes:
                nova_movimentacao = Movimentacao(
                    processo_id=processo.id,
                    data_movimentacao=data_mov,
                    nome=mov_dto.nome,
                    complemento=mov_dto.complemento,
                    nova=True,
                    data_importacao=datetime.utcnow(),
                )
                db.session.add(nova_movimentacao)
                novas_count += 1

        # 5. Atualizar ultima_atualizacao
        processo.ultima_atualizacao = datetime.utcnow()
        db.session.commit()

        logger.info(
            "Processo %s atualizado: %d novas movimentações",
            processo.numero_cnj,
            novas_count,
        )

        return AtualizacaoResult(
            atualizado=novas_count > 0,
            novas_movimentacoes=novas_count,
        )

    def consulta_avulsa(self, numero_cnj: str) -> ProcessoDTO:
        """Realiza consulta avulsa de um processo sem persistir dados.

        Busca dados do processo na DataJud API e retorna diretamente,
        sem salvar nenhuma informação no banco de dados.

        Args:
            numero_cnj: Número do processo no formato NNNNNNN-DD.AAAA.J.TR.OOOO

        Returns:
            ProcessoDTO com dados completos do processo.

        Raises:
            CNJInvalidoError: Se o número CNJ é inválido.
            DataJudAPIError: Em caso de erro de comunicação com a API.
            DataJudTimeoutError: Em caso de timeout na comunicação.
            DataJudNotFoundError: Se o processo não é encontrado na API.
        """
        # 1. Validar formato CNJ
        if not validar_numero_cnj(numero_cnj):
            raise CNJInvalidoError(numero_cnj)

        # 2. Buscar dados na DataJud API (sem tratar exceções — re-raises)
        resultado = self.datajud_client.buscar_processo(numero_cnj)

        # 3. Se API retornou None, processo não encontrado
        if resultado is None:
            raise DataJudNotFoundError(numero_cnj)

        return resultado

    def executar_monitoramento_diario(self) -> MonitoramentoLog:
        """Executa verificação de todos os processos ativos.

        Itera sobre todos os processos com ativo=True, chama atualizar_processo
        para cada um, e registra um LogExecucao com os totais.

        Returns:
            MonitoramentoLog com estatísticas da execução.
        """
        inicio = time.time()

        # 1. Buscar todos os processos ativos
        processos_ativos = Processo.query.filter_by(ativo=True).all()

        total = len(processos_ativos)
        atualizados = 0
        erros = 0
        detalhes_erros: List[str] = []

        # 2. Atualizar cada processo
        for processo in processos_ativos:
            try:
                resultado = self.atualizar_processo(processo.id)
                if resultado.erro:
                    erros += 1
                    detalhes_erros.append(
                        f"Processo {processo.numero_cnj}: {resultado.erro}"
                    )
                elif resultado.atualizado:
                    atualizados += 1
            except Exception as e:
                erros += 1
                detalhes_erros.append(
                    f"Processo {processo.numero_cnj}: {str(e)}"
                )

        # 3. Calcular duração
        duracao = int(time.time() - inicio)

        # 4. Determinar status
        if erros == 0:
            status = "sucesso"
        elif erros < total:
            status = "parcial"
        else:
            status = "falha"

        # 5. Persistir LogExecucao
        log = LogExecucao(
            data_execucao=datetime.utcnow(),
            total_processos=total,
            processos_atualizados=atualizados,
            processos_com_erro=erros,
            detalhes_erros=json.dumps(detalhes_erros) if detalhes_erros else None,
            status=status,
            duracao_segundos=duracao,
        )
        db.session.add(log)
        db.session.commit()

        logger.info(
            "Monitoramento diário concluído: total=%d, atualizados=%d, erros=%d, "
            "status=%s, duração=%ds",
            total,
            atualizados,
            erros,
            status,
            duracao,
        )

        return MonitoramentoLog(
            total_processos=total,
            processos_atualizados=atualizados,
            processos_com_erro=erros,
            detalhes_erros=detalhes_erros,
            status=status,
            duracao_segundos=duracao,
        )

    def _buscar_dados_datajud(self, numero_cnj: str) -> Optional[ProcessoDTO]:
        """Busca dados do processo na DataJud API, tratando indisponibilidade.

        Args:
            numero_cnj: Número CNJ do processo.

        Returns:
            ProcessoDTO com dados da API ou None se API indisponível.
        """
        try:
            return self.datajud_client.buscar_processo(numero_cnj)
        except (DataJudAPIError, DataJudTimeoutError) as e:
            logger.warning(
                "DataJud API indisponível ao cadastrar processo %s: %s. "
                "Cadastrando sem dados iniciais.",
                numero_cnj,
                str(e),
            )
            return None

    def _criar_processo(
        self,
        numero_cnj: str,
        codigo_tribunal: str,
        processo_dto: Optional[ProcessoDTO],
    ) -> Processo:
        """Cria instância do modelo Processo a partir dos dados disponíveis.

        Args:
            numero_cnj: Número CNJ do processo.
            codigo_tribunal: Código do tribunal no formato J.TR.
            processo_dto: Dados retornados pela API ou None.

        Returns:
            Instância do modelo Processo (não commitada).
        """
        if processo_dto:
            processo = Processo(
                numero_cnj=numero_cnj,
                tribunal=processo_dto.tribunal or codigo_tribunal,
                classe=processo_dto.classe or "",
                assunto=processo_dto.assunto or "",
                valor_causa=processo_dto.valor_causa,
                status="ativo",
                ativo=True,
                data_cadastro=datetime.utcnow(),
                ultima_atualizacao=datetime.utcnow(),
            )

            # Criar movimentações
            for mov_dto in processo_dto.movimentacoes:
                movimentacao = Movimentacao(
                    data_movimentacao=self._parse_data(mov_dto.data),
                    nome=mov_dto.nome,
                    complemento=mov_dto.complemento,
                    nova=True,
                    data_importacao=datetime.utcnow(),
                )
                processo.movimentacoes.append(movimentacao)

            # Criar partes
            for parte_dto in processo_dto.partes:
                parte = Parte(
                    nome=parte_dto.nome,
                    tipo=parte_dto.tipo,
                    polo=parte_dto.polo,
                )
                processo.partes.append(parte)
        else:
            # API indisponível: cadastro mínimo
            processo = Processo(
                numero_cnj=numero_cnj,
                tribunal=codigo_tribunal,
                status="ativo",
                ativo=True,
                data_cadastro=datetime.utcnow(),
            )

        return processo

    @staticmethod
    def _parse_data(data_str: str) -> datetime:
        """Converte string de data da API para datetime.

        Tenta múltiplos formatos comuns retornados pela DataJud API.

        Args:
            data_str: String com a data (ex: "2024-01-10T14:30:00", "2024-01-10").

        Returns:
            Objeto datetime correspondente.
        """
        formatos = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%d",
            "%d/%m/%Y",
        ]
        for fmt in formatos:
            try:
                return datetime.strptime(data_str, fmt)
            except (ValueError, TypeError):
                continue

        # Fallback: retorna data atual se não conseguir parsear
        logger.warning("Não foi possível parsear data: %s", data_str)
        return datetime.utcnow()
