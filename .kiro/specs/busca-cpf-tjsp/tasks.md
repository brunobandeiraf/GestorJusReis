# Plano de Implementação: Busca de Processos por CPF (TJSP)

## Visão Geral

Implementação incremental da funcionalidade de busca de processos por CPF no TJSP via web scraping do ESAJ. A infraestrutura compartilhada (ABC, Registry, RateLimiter, Validador) é projetada para reutilização por outros scrapers (ex: JusBrasil) no futuro.

## Tarefas

- [x] 1. Criar infraestrutura compartilhada de scraping
  - [x] 1.1 Criar módulo de exceções customizadas
    - Criar arquivo `backend/app/services/scraping/exceptions.py`
    - Implementar: `TribunalIndisponivelError`, `CaptchaDetectadoError`, `ScrapingError`, `TribunalNaoSuportadoError`, `CPFInvalidoError`
    - Cada exceção com atributos específicos conforme design (tribunal, motivo, detalhes)
    - _Requisitos: 4.1, 4.2, 4.3, 4.4_

  - [x] 1.2 Criar dataclass ProcessoEncontrado
    - Criar arquivo `backend/app/services/scraping/models.py`
    - Implementar dataclass `ProcessoEncontrado` com campos: `numero_cnj`, `classe`, `assunto`, `partes`, `vara`, `data_distribuicao`
    - _Requisitos: 3.4, 1.4_

  - [x] 1.3 Criar Abstract Base Class TribunalScraper
    - Criar arquivo `backend/app/services/scraping/base.py`
    - Implementar ABC com propriedades abstratas `tribunal_id` e `tribunal_nome`
    - Implementar método abstrato `buscar_por_cpf(cpf) -> List[ProcessoEncontrado]`
    - _Requisitos: 7.1, 7.2_

  - [x] 1.4 Criar ScraperRegistry
    - Criar arquivo `backend/app/services/scraping/registry.py`
    - Implementar métodos: `registrar(scraper)`, `obter(tribunal_id)`, `listar_disponiveis()`
    - `obter()` deve lançar `TribunalNaoSuportadoError` se tribunal não registrado
    - _Requisitos: 7.3, 7.4_

  - [x] 1.5 Criar RateLimiter
    - Criar arquivo `backend/app/services/scraping/rate_limiter.py`
    - Implementar rate limiter thread-safe com `threading.Lock`
    - Métodos: `aguardar()` (intervalo padrão 2s), `aguardar_paginacao()` (intervalo 1s)
    - Propriedade `tempo_espera` para estimar tempo até próxima permissão
    - _Requisitos: 5.1, 5.2, 5.4_

  - [x] 1.6 Criar CPFValidator
    - Criar arquivo `backend/app/services/scraping/cpf_validator.py`
    - Implementar métodos estáticos: `validar(cpf)`, `normalizar(cpf)`, `formatar(cpf)`
    - Validação: formato (11 dígitos), dígitos verificadores (módulo 11), rejeição de dígitos repetidos
    - Aceitar CPF com ou sem formatação (pontos e traço)
    - _Requisitos: 2.1, 2.2, 2.3, 2.4_

  - [x] 1.7 Criar `__init__.py` do pacote scraping
    - Criar arquivo `backend/app/services/scraping/__init__.py`
    - Exportar: `TribunalScraper`, `ProcessoEncontrado`, `ScraperRegistry`, `RateLimiter`, `CPFValidator`
    - Exportar todas as exceções customizadas
    - _Requisitos: 7.1_

- [x] 2. Implementar ESAJ Scraper para TJSP
  - [x] 2.1 Implementar ESAJScraperTJSP
    - Criar arquivo `backend/app/services/scraping/esaj_scraper.py`
    - Herdar de `TribunalScraper`, implementar propriedades `tribunal_id` ("tjsp") e `tribunal_nome`
    - Implementar `buscar_por_cpf(cpf)` com requests + BeautifulSoup
    - Implementar `_fazer_requisicao_busca(cpf, pagina)` com parâmetros do ESAJ (cbPesquisa=DOCPARTE, etc.)
    - Implementar `_parsear_resultados(html)` para extrair processos do HTML
    - Implementar `_detectar_captcha(html)` para verificar presença de CAPTCHA
    - Implementar `_obter_total_paginas(html)` para suporte a paginação
    - Usar `RateLimiter` para controlar frequência de requisições
    - Timeout de 30 segundos por requisição
    - _Requisitos: 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3_

  - [ ]* 2.2 Escrever testes unitários do ESAJScraperTJSP
    - Testar parsing de HTML com resultados (1 processo, múltiplos processos)
    - Testar parsing de HTML sem resultados
    - Testar detecção de CAPTCHA
    - Testar tratamento de timeout e erro de conexão (mock requests)
    - Testar paginação com 1, 2 e 3 páginas
    - Testar HTML com estrutura inesperada (ScrapingError)
    - _Requisitos: 3.2, 3.3, 4.1, 4.2, 4.3_

- [ ] 3. Checkpoint — Verificar infraestrutura e scraper
  - Garantir que todos os testes passam, perguntar ao usuário se houver dúvidas.

- [x] 4. Criar Blueprint Flask /api/busca-cpf
  - [x] 4.1 Implementar rotas do blueprint busca_cpf
    - Criar arquivo `backend/app/routes/busca_cpf.py`
    - Implementar `POST /api/busca-cpf`: recebe `{cpf, tribunal}`, valida CPF, obtém scraper do registry, executa busca, retorna JSON com processos
    - Implementar `GET /api/busca-cpf/tribunais`: retorna lista de tribunais disponíveis
    - Tratamento de erros: 400 (CPF inválido, tribunal não informado), 502 (tribunal indisponível, scraping error), 503 (CAPTCHA)
    - Logging de erros com CPF mascarado (`***.***.XXX-XX`)
    - _Requisitos: 1.4, 1.5, 2.1, 2.2, 4.1, 4.2, 4.3, 4.4_

  - [x] 4.2 Registrar blueprint e inicializar registry na aplicação
    - Modificar `backend/app/__init__.py` para registrar `busca_cpf_bp`
    - Instanciar `RateLimiter`, `ESAJScraperTJSP` e `ScraperRegistry`
    - Registrar o scraper TJSP no registry
    - Disponibilizar registry para as rotas (app context ou injeção)
    - _Requisitos: 7.3, 7.4_

  - [ ]* 4.3 Escrever testes unitários das rotas busca_cpf
    - Testar POST /api/busca-cpf com CPF válido (mock scraper)
    - Testar POST /api/busca-cpf com CPF inválido (400)
    - Testar POST /api/busca-cpf sem tribunal (400)
    - Testar POST /api/busca-cpf com tribunal indisponível (502)
    - Testar POST /api/busca-cpf com CAPTCHA (503)
    - Testar GET /api/busca-cpf/tribunais
    - _Requisitos: 1.4, 1.5, 4.1, 4.2, 4.3, 4.4_

- [ ] 5. Checkpoint — Verificar backend completo
  - Garantir que todos os testes passam, perguntar ao usuário se houver dúvidas.

- [x] 6. Criar componentes frontend
  - [x] 6.1 Adicionar funções de API no api.js
    - Adicionar `buscarPorCPF(cpf, tribunal)` → POST /busca-cpf
    - Adicionar `getTribunaisBuscaCPF()` → GET /busca-cpf/tribunais
    - _Requisitos: 1.2, 7.4_

  - [x] 6.2 Criar componente BuscaCPF
    - Criar arquivo `frontend/src/components/BuscaCPF/index.jsx`
    - Implementar formulário com: campo CPF com máscara (XXX.XXX.XXX-XX), dropdown de tribunal, botão "Buscar"
    - Implementar validação de CPF no frontend (feedback imediato)
    - Implementar indicador de carregamento (spinner) durante busca
    - Implementar lista de resultados com: número CNJ, classe, assunto, partes
    - Implementar botão "Monitorar" por processo (usa `cadastrarProcesso` existente)
    - Implementar indicação "Já monitorado" para processos já cadastrados
    - Implementar mensagens de erro e estado vazio (nenhum processo encontrado)
    - _Requisitos: 1.1, 1.2, 1.3, 1.4, 1.5, 2.5, 6.1, 6.2, 6.3, 6.4_

  - [x] 6.3 Criar página BuscaCPFPage
    - Criar arquivo `frontend/src/pages/BuscaCPFPage.jsx`
    - Página wrapper que renderiza o componente BuscaCPF
    - Título "Busca por CPF"
    - _Requisitos: 1.1_

  - [x] 6.4 Atualizar App.jsx com rota e navegação
    - Adicionar import de `BuscaCPFPage`
    - Adicionar `<Route path="/busca-cpf" element={<BuscaCPFPage />} />` nas rotas
    - Adicionar NavLink "Busca por CPF" na navegação principal
    - _Requisitos: 1.1_

- [ ] 7. Checkpoint — Verificar integração frontend-backend
  - Garantir que todos os testes passam, perguntar ao usuário se houver dúvidas.

- [ ] 8. Testes de propriedade (Property-Based Tests)
  - [ ]* 8.1 Escrever teste de propriedade para validação de CPF — formato inválido
    - **Propriedade 1: Rejeição de CPF com formato inválido**
    - Usar Hypothesis com strategy `st.text()` filtrado para strings sem exatamente 11 dígitos
    - Verificar que `CPFValidator.validar()` retorna False para todos os inputs gerados
    - **Valida: Requisito 2.1**

  - [ ]* 8.2 Escrever teste de propriedade para validação de CPF — dígitos verificadores incorretos
    - **Propriedade 2: Rejeição de CPF com dígitos verificadores incorretos**
    - Usar Hypothesis para gerar 9 dígitos + 2 dígitos que NÃO correspondem ao módulo 11
    - Incluir CPFs com todos os dígitos iguais (000...0 até 999...9)
    - Verificar que `CPFValidator.validar()` retorna False
    - **Valida: Requisitos 2.2, 2.3**

  - [ ]* 8.3 Escrever teste de propriedade para round-trip formatação/normalização de CPF
    - **Propriedade 3: Round-trip de formatação/normalização de CPF**
    - Usar Hypothesis para gerar CPFs válidos (11 dígitos com check digits corretos)
    - Verificar que `normalizar(formatar(cpf)) == cpf`
    - **Valida: Requisito 2.4**

  - [ ]* 8.4 Escrever teste de propriedade para extração de dados do HTML do ESAJ
    - **Propriedade 4: Extração completa de dados do HTML do ESAJ**
    - Criar helper `gerar_html_esaj(dados)` que gera HTML no formato ESAJ a partir de dados conhecidos
    - Usar Hypothesis para gerar listas de ProcessoEncontrado (1 a 10 itens)
    - Verificar que o parser extrai exatamente N processos com campos obrigatórios preenchidos
    - **Valida: Requisitos 3.2, 3.4**

  - [ ]* 8.5 Escrever teste de propriedade para HTML inesperado
    - **Propriedade 5: HTML inesperado gera erro de scraping**
    - Usar Hypothesis para gerar strings HTML que NÃO contêm a estrutura esperada do ESAJ
    - Verificar que o parser lança `ScrapingError`
    - **Valida: Requisito 4.3**

  - [ ]* 8.6 Escrever teste de propriedade para rate limiter — intervalo mínimo
    - **Propriedade 6: Rate limiter garante intervalo mínimo entre requisições**
    - Usar Hypothesis para gerar número de requisições (2 a 5)
    - Verificar que intervalo entre requisições consecutivas é ≥ 2 segundos
    - **Valida: Requisitos 5.1, 5.2**

  - [ ]* 8.7 Escrever teste de propriedade para rate limiter — intervalo de paginação
    - **Propriedade 7: Rate limiter garante intervalo de paginação**
    - Usar Hypothesis para gerar sequências de requisições de paginação
    - Verificar que intervalo entre requisições consecutivas é ≥ 1 segundo
    - **Valida: Requisito 5.4**

- [ ] 9. Testes unitários complementares
  - [ ]* 9.1 Escrever testes unitários do CPFValidator
    - Testar os 10 CPFs com dígitos repetidos (111...1, 222...2, etc.)
    - Testar CPFs válidos conhecidos
    - Testar CPF com formatação (pontos e traço)
    - Testar CPF sem formatação
    - Testar strings vazias e com caracteres não numéricos
    - _Requisitos: 2.1, 2.2, 2.3, 2.4_

  - [ ]* 9.2 Escrever testes unitários do ScraperRegistry
    - Testar registro e obtenção de scraper
    - Testar `TribunalNaoSuportadoError` para tribunal não registrado
    - Testar `listar_disponiveis()` com 0 e múltiplos scrapers
    - _Requisitos: 7.3, 7.4_

  - [ ]* 9.3 Escrever testes unitários do RateLimiter
    - Testar que primeira requisição não bloqueia
    - Testar que segunda requisição aguarda intervalo mínimo
    - Testar `aguardar_paginacao()` com intervalo de 1 segundo
    - _Requisitos: 5.1, 5.4_

- [ ] 10. Checkpoint final — Garantir que todos os testes passam
  - Garantir que todos os testes passam, perguntar ao usuário se houver dúvidas.

## Notas

- Tarefas marcadas com `*` são opcionais e podem ser puladas para um MVP mais rápido
- Cada tarefa referencia requisitos específicos para rastreabilidade
- Checkpoints garantem validação incremental
- Testes de propriedade validam propriedades universais de corretude
- Testes unitários validam cenários específicos e edge cases
- A infraestrutura compartilhada (pacote `scraping/`) será reutilizada pelo scraper JusBrasil
- Dependências necessárias: `requests`, `beautifulsoup4`, `hypothesis` (dev)
