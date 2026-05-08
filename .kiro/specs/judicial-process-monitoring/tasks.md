# Plano de Implementação: Monitoramento de Processos Judiciais

## Visão Geral

Plano de implementação incremental para o sistema de monitoramento de processos judiciais, focado na Onda 1 (validação de viabilidade técnica). Cada tarefa constrói sobre as anteriores, garantindo progresso contínuo e integração sem código órfão.

## Tarefas

- [x] 1. Configurar estrutura do projeto e dependências
  - [x] 1.1 Criar estrutura de diretórios do backend Flask
    - Criar `backend/app/__init__.py` com Flask app factory (create_app)
    - Criar `backend/app/config.py` com configurações para dev/test/prod
    - Criar `backend/run.py` como ponto de entrada
    - Criar `backend/requirements.txt` com dependências: Flask, SQLAlchemy, Flask-SQLAlchemy, APScheduler, requests, tenacity, hypothesis, pytest
    - _Requisitos: 6.1_

  - [x] 1.2 Criar estrutura de diretórios do frontend React
    - Inicializar projeto com Vite + React
    - Configurar `frontend/package.json` com dependências: axios, react-router-dom
    - Criar estrutura base: `src/components/`, `src/pages/`, `src/services/`, `src/context/`, `src/utils/`
    - Criar `frontend/src/App.jsx` com roteamento básico
    - _Requisitos: 4.1_

  - [x] 1.3 Configurar banco de dados SQLite com SQLAlchemy
    - Configurar Flask-SQLAlchemy na app factory
    - Configurar SQLite como banco padrão em dev (`instance/app.db`)
    - Criar comando CLI para inicializar o banco (`flask init-db`)
    - _Requisitos: 1.5_

- [x] 2. Implementar modelos de dados (SQLAlchemy)
  - [x] 2.1 Criar modelo Processo
    - Implementar `backend/app/models/processo.py` com todos os campos: id, numero_cnj (unique, indexed), tribunal, classe, assunto, valor_causa, status, data_cadastro, ultima_atualizacao, ultima_visualizacao, ativo
    - Definir relationships com Movimentacao e Parte
    - _Requisitos: 1.5_

  - [x] 2.2 Criar modelo Movimentacao
    - Implementar `backend/app/models/movimentacao.py` com campos: id, processo_id (FK), data_movimentacao, nome, complemento, nova, data_importacao
    - Configurar ordering por data_movimentacao desc
    - _Requisitos: 2.3, 4.2_

  - [x] 2.3 Criar modelo Parte
    - Implementar `backend/app/models/parte.py` com campos: id, processo_id (FK), nome, tipo, polo
    - _Requisitos: 1.5, 4.1_

  - [x] 2.4 Criar modelo LogExecucao
    - Implementar `backend/app/models/log_execucao.py` com campos: id, data_execucao, total_processos, processos_atualizados, processos_com_erro, detalhes_erros, status, duracao_segundos
    - _Requisitos: 2.5_

- [ ] 3. Implementar módulo de validação CNJ
  - [x] 3.1 Criar validador de número CNJ
    - Implementar `backend/app/services/cnj_validator.py`
    - Implementar `validar_numero_cnj(numero: str) -> bool` com regex para formato NNNNNNN-DD.AAAA.J.TR.OOOO
    - Implementar `extrair_tribunal(numero_cnj: str) -> str` para extrair J.TR do número
    - Implementar `formatar_numero_cnj(numero: str) -> str` para formatação de exibição
    - _Requisitos: 1.2, 3.2_

  - [ ]* 3.2 Escrever testes de propriedade para validação CNJ
    - **Propriedade 1: Rejeição de números CNJ inválidos**
    - **Valida: Requisitos 1.2**
    - Usar Hypothesis para gerar strings aleatórias e verificar que formatos inválidos são rejeitados
    - Gerar números com formato correto e verificar aceitação

  - [ ]* 3.3 Escrever testes de propriedade para extração de tribunal
    - **Propriedade 6: Mapeamento correto de tribunal a partir do número CNJ**
    - **Valida: Requisitos 3.2**
    - Verificar que para qualquer CNJ válido, os dígitos J.TR são extraídos corretamente

- [ ] 4. Implementar módulo de mapeamento de tribunais
  - [x] 4.1 Criar mapeador tribunal → endpoint
    - Implementar `backend/app/utils/tribunal_mapper.py`
    - Criar dicionário TRIBUNAL_ENDPOINTS com mapeamento J.TR → sigla do tribunal
    - Implementar `obter_endpoint_tribunal(codigo_tribunal: str) -> str` que retorna a URL completa da API
    - Implementar `obter_url_consulta_publica(tribunal: str, numero_cnj: str) -> str` para link direto ao site do tribunal
    - Implementar `listar_tribunais_suportados() -> list` para endpoint de listagem
    - _Requisitos: 3.1, 3.2, 3.3, 7.3_

  - [ ]* 4.2 Escrever testes de propriedade para mapeamento de tribunal
    - **Propriedade 11: Geração correta de URL do tribunal**
    - **Valida: Requisitos 7.3**
    - Verificar que para qualquer tribunal conhecido, a URL gerada é válida e aponta para o endpoint correto

- [ ] 5. Checkpoint — Validar módulos base
  - Garantir que todos os testes passam, perguntar ao usuário se há dúvidas.

- [x] 6. Implementar cliente DataJud API
  - [x] 6.1 Criar cliente HTTP para DataJud
    - Implementar `backend/app/services/datajud_client.py`
    - Implementar classe `DataJudClient` com BASE_URL e API_KEY
    - Implementar método `buscar_processo(numero_cnj: str) -> Optional[ProcessoDTO]`
    - Implementar método `health_check() -> HealthStatus`
    - Configurar headers de autenticação (ApiKey)
    - Montar query Elasticsearch DSL para busca por número de processo
    - Implementar parsing da resposta JSON para DTO interno
    - Configurar timeout de 30 segundos por requisição
    - _Requisitos: 6.1, 6.2_

  - [x] 6.2 Implementar tratamento de erros e retry
    - Usar `tenacity` para retry com backoff exponencial
    - Tratar erros HTTP: 401/403 (sem retry), 404 (não encontrado), 429 (rate limit), 5xx (retry)
    - Implementar exceções customizadas: `DataJudAPIError`, `DataJudTimeoutError`, `DataJudNotFoundError`
    - Implementar validação de estrutura da resposta (campos esperados)
    - _Requisitos: 2.4, 6.4_

  - [ ]* 6.3 Escrever testes de propriedade para detecção de respostas malformadas
    - **Propriedade 10: Detecção de respostas malformadas da API**
    - **Valida: Requisitos 6.4**
    - Usar Hypothesis para gerar respostas JSON com campos ausentes/tipos incorretos e verificar que erros são registrados sem exceções não tratadas

- [x] 7. Implementar serviço de processos (lógica de negócio)
  - [x] 7.1 Implementar cadastro de processo
    - Implementar `backend/app/services/processo_service.py`
    - Implementar `cadastrar_processo(numero_cnj: str) -> Processo`
    - Validar número CNJ, verificar duplicidade (409 Conflict)
    - Identificar tribunal e buscar dados na DataJud API
    - Persistir processo com movimentações e partes
    - Tratar cenário de API indisponível (cadastro sem dados iniciais)
    - _Requisitos: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [x] 7.2 Implementar atualização de processo
    - Implementar `atualizar_processo(processo_id: int) -> AtualizacaoResult`
    - Buscar dados atualizados na DataJud API
    - Implementar deduplicação de movimentações (comparar por data + nome)
    - Marcar novas movimentações com `nova=True`
    - Atualizar `ultima_atualizacao` do processo
    - _Requisitos: 2.3, 4.3_

  - [x] 7.3 Implementar consulta avulsa
    - Implementar `consulta_avulsa(numero_cnj: str) -> ProcessoDTO`
    - Validar número CNJ, buscar na DataJud API
    - Retornar dados sem persistir no banco de dados
    - _Requisitos: 5.1, 5.2, 5.3_

  - [x] 7.4 Implementar monitoramento diário
    - Implementar `executar_monitoramento_diario() -> MonitoramentoLog`
    - Iterar sobre todos os processos com `ativo=True`
    - Chamar `atualizar_processo` para cada um
    - Registrar LogExecucao com totais (verificados, atualizados, erros)
    - Calcular duração em segundos
    - _Requisitos: 2.1, 2.2, 2.5_

  - [ ]* 7.5 Escrever testes de propriedade para completude de dados no cadastro
    - **Propriedade 2: Completude de dados no cadastro**
    - **Valida: Requisitos 1.1, 1.5**
    - Verificar que após cadastro com API mockada, todos os campos obrigatórios estão preenchidos

  - [ ]* 7.6 Escrever testes de propriedade para monitoramento de processos ativos
    - **Propriedade 3: Monitoramento consulta todos os processos ativos**
    - **Valida: Requisitos 2.2**
    - Verificar que apenas processos ativos são consultados na API

  - [ ]* 7.7 Escrever testes de propriedade para deduplicação de movimentações
    - **Propriedade 4: Deduplicação de movimentações**
    - **Valida: Requisitos 2.3**
    - Verificar que movimentações duplicadas não são inseridas

  - [ ]* 7.8 Escrever testes de propriedade para precisão do log
    - **Propriedade 5: Precisão do log de monitoramento**
    - **Valida: Requisitos 2.5**
    - Verificar que N = K + E + sem_alteracao

  - [ ]* 7.9 Escrever testes de propriedade para classificação de movimentações novas
    - **Propriedade 8: Classificação correta de movimentações novas**
    - **Valida: Requisitos 4.3**
    - Verificar que movimentações com data_importacao > ultima_visualizacao são marcadas como novas

  - [ ]* 7.10 Escrever testes de propriedade para não-persistência da consulta avulsa
    - **Propriedade 9: Não-persistência da consulta avulsa**
    - **Valida: Requisitos 5.3**
    - Verificar que após consulta avulsa, nenhum registro novo existe no banco

- [ ] 8. Checkpoint — Validar lógica de negócio
  - Garantir que todos os testes passam, perguntar ao usuário se há dúvidas.

- [x] 9. Implementar endpoints REST (Flask Blueprints)
  - [x] 9.1 Criar blueprint de processos
    - Implementar `backend/app/routes/processos.py`
    - `GET /api/processos` — listar processos cadastrados (com paginação simples)
    - `POST /api/processos` — cadastrar novo processo (body: {numero_cnj})
    - `GET /api/processos/<id>` — detalhes de um processo
    - `DELETE /api/processos/<id>` — remover processo do monitoramento
    - `GET /api/processos/<id>/movimentacoes` — listar movimentações
    - Implementar serialização JSON dos modelos
    - _Requisitos: 1.1, 1.2, 4.1, 4.2, 4.3, 4.4_

  - [x] 9.2 Criar blueprint de consulta avulsa
    - Implementar `backend/app/routes/consulta.py`
    - `POST /api/consulta-avulsa` — consulta sem persistir (body: {numero_cnj})
    - Retornar dados completos: classe, assunto, partes, movimentações
    - _Requisitos: 5.1, 5.2, 5.4_

  - [x] 9.3 Criar blueprint de health check e utilitários
    - Implementar `backend/app/routes/health.py`
    - `GET /api/health` — health check com status da DataJud API
    - `GET /api/monitoramento/status` — status do último monitoramento
    - `GET /api/tribunais` — lista de tribunais suportados
    - _Requisitos: 6.3, 3.3_

  - [ ]* 9.4 Escrever testes de propriedade para completude da resposta de detalhes
    - **Propriedade 7: Completude da resposta de detalhes do processo**
    - **Valida: Requisitos 4.1, 4.2**
    - Verificar que a resposta do endpoint de detalhes contém todos os campos obrigatórios

- [x] 10. Implementar scheduler para monitoramento diário
  - [x] 10.1 Criar serviço de agendamento
    - Implementar `backend/app/services/scheduler_service.py`
    - Configurar APScheduler com BackgroundScheduler
    - Agendar job diário às 23h (America/Sao_Paulo)
    - Implementar retry: 3 tentativas com intervalo de 30 minutos
    - Integrar com `processo_service.executar_monitoramento_diario()`
    - Registrar início/fim no log
    - _Requisitos: 2.1, 2.4_

  - [ ]* 10.2 Escrever testes unitários para configuração do scheduler
    - Verificar que o job é configurado com timezone correto
    - Verificar que retry está configurado com 3 tentativas e 30min de intervalo
    - _Requisitos: 2.1, 2.4_

- [ ] 11. Checkpoint — Validar backend completo
  - Garantir que todos os testes passam, perguntar ao usuário se há dúvidas.

- [x] 12. Implementar frontend React — Componentes base
  - [x] 12.1 Criar cliente HTTP (Axios) e contexto global
    - Implementar `frontend/src/services/api.js` com instância Axios configurada (baseURL, interceptors de erro)
    - Implementar `frontend/src/context/ProcessoContext.jsx` com Context API para estado global (lista de processos, loading, errors)
    - _Requisitos: 4.1_

  - [x] 12.2 Criar utilitário de formatação CNJ no frontend
    - Implementar `frontend/src/utils/cnjFormatter.js`
    - Função `formatarCNJ(numero)` para exibição formatada
    - Função `validarCNJ(numero)` para validação client-side
    - Função `mascararInput(valor)` para aplicar máscara durante digitação
    - _Requisitos: 1.2_

  - [x] 12.3 Implementar componente ProcessoForm (cadastro)
    - Criar `frontend/src/components/ProcessoForm/`
    - Input com máscara para número CNJ
    - Validação client-side antes de enviar
    - Feedback visual de sucesso/erro
    - Mensagem sobre indisponibilidade de download de documentos
    - _Requisitos: 1.1, 1.2, 1.4, 7.1_

  - [x] 12.4 Implementar componente ProcessoList (lista)
    - Criar `frontend/src/components/ProcessoList/`
    - Exibir lista de processos cadastrados com: número CNJ, tribunal, classe, status
    - Indicador visual de processos com novas movimentações
    - Botão para remover processo do monitoramento
    - _Requisitos: 4.1, 4.3_

  - [x] 12.5 Implementar componente ProcessoDetail (detalhes)
    - Criar `frontend/src/components/ProcessoDetail/`
    - Exibir dados completos: número CNJ, tribunal, classe, assunto, partes, valor da causa
    - Exibir data/hora da última atualização
    - Link direto para página do processo no site do tribunal
    - _Requisitos: 4.1, 4.4, 7.3_

  - [x] 12.6 Implementar componente MovimentacaoList
    - Criar `frontend/src/components/MovimentacaoList/`
    - Listar movimentações ordenadas por data (mais recente primeiro)
    - Exibir data, nome e complemento de cada movimentação
    - Destacar visualmente movimentações novas (badge ou cor diferente)
    - _Requisitos: 4.2, 4.3_

  - [x] 12.7 Implementar componente ConsultaAvulsa
    - Criar `frontend/src/components/ConsultaAvulsa/`
    - Input com máscara para número CNJ
    - Exibir resultados no mesmo formato do ProcessoDetail
    - Botão "Cadastrar para monitoramento" após consulta bem-sucedida
    - Mensagem clara de erro quando API falha
    - _Requisitos: 5.1, 5.2, 5.4, 5.5_

- [x] 13. Implementar páginas e roteamento do frontend
  - [x] 13.1 Criar página Dashboard
    - Implementar `frontend/src/pages/Dashboard.jsx`
    - Integrar ProcessoList e ProcessoForm
    - Exibir status do último monitoramento
    - _Requisitos: 4.1, 2.5_

  - [x] 13.2 Criar página ProcessoPage (detalhe)
    - Implementar `frontend/src/pages/ProcessoPage.jsx`
    - Integrar ProcessoDetail e MovimentacaoList
    - Atualizar `ultima_visualizacao` ao acessar
    - _Requisitos: 4.1, 4.2, 4.3, 4.4_

  - [x] 13.3 Criar página ConsultaPage
    - Implementar `frontend/src/pages/ConsultaPage.jsx`
    - Integrar componente ConsultaAvulsa
    - _Requisitos: 5.1, 5.2_

  - [x] 13.4 Configurar roteamento e navegação
    - Configurar React Router em `App.jsx`
    - Criar layout com navegação entre Dashboard, Consulta Avulsa
    - Implementar navegação para detalhe do processo
    - _Requisitos: 4.1, 5.1_

- [ ] 14. Checkpoint — Validar frontend e integração
  - Garantir que todos os testes passam, perguntar ao usuário se há dúvidas.

- [ ] 15. Testes de integração
  - [ ]* 15.1 Escrever teste de integração com DataJud API
    - Testar comunicação real com DataJud API usando 1-2 números CNJ conhecidos
    - Verificar que a resposta é parseada corretamente
    - _Requisitos: 6.1, 6.2_

  - [ ]* 15.2 Escrever testes de integração dos endpoints REST
    - Testar fluxo completo: cadastro → listagem → detalhes → remoção
    - Testar consulta avulsa end-to-end
    - Testar health check
    - Testar respostas de erro (CNJ inválido, processo não encontrado, duplicado)
    - _Requisitos: 1.1, 1.2, 4.1, 5.1, 6.3_

  - [ ]* 15.3 Escrever teste de integração do scheduler
    - Verificar que o scheduler executa o monitoramento corretamente
    - Verificar que o log é registrado com dados corretos
    - _Requisitos: 2.1, 2.5_

- [ ] 16. Checkpoint final — Validação completa da Onda 1
  - Garantir que todos os testes passam, perguntar ao usuário se há dúvidas.

## Notas

- Tarefas marcadas com `*` são opcionais e podem ser puladas para um MVP mais rápido
- Cada tarefa referencia requisitos específicos para rastreabilidade
- Checkpoints garantem validação incremental
- Testes de propriedade validam propriedades universais de corretude (Hypothesis)
- Testes unitários validam cenários específicos e edge cases
- O foco é na Onda 1 (viabilidade técnica): integração com DataJud API funcionando end-to-end
- A linguagem do backend é Python (Flask) e do frontend é JavaScript (React + Vite)
