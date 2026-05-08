# Plano de Implementação: Busca de Processos por CPF (JusBrasil)

## Visão Geral

Implementação do scraper JusBrasil para busca de processos por CPF utilizando Playwright (headless browser) com autenticação. Este módulo se integra à infraestrutura compartilhada já implementada pela spec `busca-cpf-tjsp` (TribunalScraper ABC, ProcessoEncontrado, ScraperRegistry, RateLimiter, CPFValidator, Blueprint, Frontend).

O JusBrasil é adicionado como mais um scraper registrado no registry existente, sem alterações na API ou frontend (além de aparecer automaticamente no dropdown de tribunais).

## Tarefas

- [ ] 1. Configurar dependência Playwright e variáveis de ambiente
  - [ ] 1.1 Instalar Playwright no projeto
    - Adicionar `playwright` ao `backend/requirements.txt`
    - Executar instalação dos browsers Playwright (chromium)
    - _Requisitos: 3.1, 3.4_

  - [ ] 1.2 Criar arquivo .env.example com credenciais JusBrasil
    - Criar arquivo `backend/.env.example` (ou atualizar se existente)
    - Adicionar variáveis: `JUSBRASIL_EMAIL=seu_email@exemplo.com` e `JUSBRASIL_PASSWORD=sua_senha_aqui`
    - Incluir comentário explicando que são credenciais de login no JusBrasil
    - _Requisitos: 9.1, 9.2_

  - [ ] 1.3 Atualizar .gitignore para proteger credenciais
    - Garantir que `.env` está listado no `.gitignore` do projeto
    - Verificar que `backend/.env` também está coberto
    - _Requisitos: 9.3_

- [ ] 2. Implementar exceções específicas do JusBrasil
  - [ ] 2.1 Criar módulo de exceções do JusBrasil
    - Criar arquivo `backend/app/services/scraping/jusbrasil/__init__.py`
    - Criar arquivo `backend/app/services/scraping/jusbrasil/exceptions.py`
    - Implementar `AutenticacaoError(motivo: str)` — falha no login
    - Implementar `CredenciaisNaoConfiguradasError` — variáveis de ambiente ausentes
    - Implementar `SessaoExpiradaError` — sessão expirou durante operação
    - _Requisitos: 1.5, 1.6, 5.3_

- [ ] 3. Implementar SessionManager (gerenciamento de sessão autenticada)
  - [ ] 3.1 Criar SessionManager com login via Playwright
    - Criar arquivo `backend/app/services/scraping/jusbrasil/session_manager.py`
    - Implementar `__init__()` com atributos: `_browser`, `_context`, `_ultimo_login`, `_sessao_ativa`
    - Implementar `_carregar_credenciais()` que lê `JUSBRASIL_EMAIL` e `JUSBRASIL_PASSWORD` do `os.environ`
    - Lançar `CredenciaisNaoConfiguradasError` se variáveis ausentes
    - _Requisitos: 1.1, 1.5, 9.1_

  - [ ] 3.2 Implementar fluxo de login no JusBrasil
    - Implementar `_realizar_login()` usando Playwright:
      - Navegar para `https://www.jusbrasil.com.br/login`
      - Preencher campo email (`input[name="email"]`)
      - Preencher campo senha (`input[name="password"]`)
      - Submeter formulário (`button[type="submit"]`)
      - Aguardar redirect (indica sucesso)
      - Armazenar cookies no BrowserContext
    - Implementar `_inicializar_browser()` com modo headless e user-agent real
    - Configurar user-agent: `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...`
    - Lançar `AutenticacaoError` se login falhar após `MAX_LOGIN_ATTEMPTS` (2) tentativas
    - Logar email utilizado (para diagnóstico), NUNCA logar a senha
    - _Requisitos: 1.2, 1.6, 3.3, 3.4, 9.4_

  - [ ] 3.3 Implementar gerenciamento de sessão (reutilização e renovação)
    - Implementar `garantir_sessao_ativa()`:
      - Se sessão válida (cookies não expirados), reutilizar sem novo login
      - Se sessão expirada ou inexistente, realizar novo login
    - Implementar `_verificar_sessao_valida()`:
      - Fazer requisição leve ao JusBrasil
      - Verificar se não há redirect para login (indica expiração)
    - Implementar `_descartar_sessao()`:
      - Fechar BrowserContext atual
      - Marcar `_sessao_ativa = False`
    - Manter no máximo uma sessão ativa por vez
    - Implementar `fechar()` para liberar recursos do browser
    - _Requisitos: 1.3, 1.4, 4.1, 4.2, 4.3, 4.4_

  - [ ]* 3.4 Escrever testes unitários do SessionManager
    - Testar `_carregar_credenciais()` com variáveis presentes e ausentes
    - Testar `garantir_sessao_ativa()` com sessão válida (reutiliza)
    - Testar `garantir_sessao_ativa()` com sessão expirada (re-login)
    - Testar `_realizar_login()` com sucesso (mock Playwright)
    - Testar `_realizar_login()` com credenciais inválidas (AutenticacaoError)
    - Testar `_descartar_sessao()` fecha contexto corretamente
    - Testar que no máximo uma sessão ativa por vez
    - Testar que senha NUNCA aparece nos logs
    - _Requisitos: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 4.1, 4.2, 4.3, 4.4, 9.4_

- [ ] 4. Implementar JusBrasilPageParser (extração de dados do DOM)
  - [ ] 4.1 Criar parser de resultados do JusBrasil
    - Criar arquivo `backend/app/services/scraping/jusbrasil/page_parser.py`
    - Implementar classe `JusBrasilPageParser` com métodos estáticos
    - Definir seletores CSS primários (`[data-testid="process-list-item"]`, etc.)
    - Definir seletores CSS fallback (`.ProcessList-item`, `.search-result-item`)
    - Implementar `extrair_processos(page)`:
      - Tentar seletores primários, depois fallback
      - Para cada elemento de resultado, extrair: `numero_cnj`, `classe`, `tribunal`, `partes`
      - Retornar `List[ProcessoEncontrado]`
      - Lançar `ScrapingError` se estrutura HTML não reconhecida
    - Implementar `_extrair_numero_cnj(elemento)`, `_extrair_tribunal(elemento)`, `_extrair_partes(elemento)`
    - _Requisitos: 2.2, 2.4, 5.3_

  - [ ] 4.2 Implementar detecção de CAPTCHA, bloqueio e paginação
    - Implementar `detectar_captcha(page)`:
      - Verificar presença de `iframe[src*="captcha"]` ou `div.captcha-container`
    - Implementar `detectar_bloqueio(page)`:
      - Verificar presença de `[data-testid="blocked-message"]`
    - Implementar `tem_proxima_pagina(page)`:
      - Verificar se botão `[data-testid="pagination-next"]` existe e está habilitado
    - _Requisitos: 2.3, 5.2, 5.4_

  - [ ]* 4.3 Escrever testes unitários do JusBrasilPageParser
    - Testar extração com 1 processo (seletores primários)
    - Testar extração com múltiplos processos
    - Testar extração com seletores fallback
    - Testar `ScrapingError` quando HTML não tem estrutura esperada
    - Testar `detectar_captcha()` com e sem CAPTCHA
    - Testar `detectar_bloqueio()` com e sem bloqueio
    - Testar `tem_proxima_pagina()` com e sem próxima página
    - Testar página sem resultados (lista vazia)
    - _Requisitos: 2.2, 2.3, 2.4, 5.2, 5.3, 5.4_

- [ ] 5. Checkpoint — Verificar SessionManager e PageParser
  - Garantir que todos os testes passam, perguntar ao usuário se houver dúvidas.

- [ ] 6. Implementar JusBrasilScraper (implementa TribunalScraper)
  - [ ] 6.1 Criar classe JusBrasilScraper
    - Criar arquivo `backend/app/services/scraping/jusbrasil/scraper.py`
    - Herdar de `TribunalScraper` ABC
    - Implementar propriedades: `tribunal_id` → `"jusbrasil"`, `tribunal_nome` → `"JusBrasil - Todos os Tribunais"`
    - Receber `SessionManager` e `RateLimiter` no construtor
    - Implementar `_construir_url_busca(cpf)` → `https://www.jusbrasil.com.br/consulta-processual/busca?q={cpf}` (apenas dígitos)
    - _Requisitos: 10.1, 10.2, 10.3_

  - [ ] 6.2 Implementar método buscar_por_cpf com paginação
    - Implementar `buscar_por_cpf(cpf)`:
      1. Chamar `session_manager.garantir_sessao_ativa()` para obter contexto autenticado
      2. Chamar `rate_limiter.aguardar()` (intervalo 3s)
      3. Navegar para URL de busca com CPF
      4. Aguardar renderização dos elementos de resultado no DOM (timeout 30s)
      5. Verificar CAPTCHA (`_detectar_captcha`) → lançar `CaptchaDetectadoError`
      6. Verificar bloqueio (`_detectar_bloqueio`) → lançar `TribunalIndisponivelError`
      7. Extrair processos via `JusBrasilPageParser.extrair_processos(page)`
      8. Se há próxima página: `rate_limiter.aguardar_paginacao()` (2s), navegar, extrair, consolidar
      9. Retornar lista consolidada de `ProcessoEncontrado`
    - Implementar retry de sessão expirada: se receber 401/403 durante busca, descartar sessão, re-login e repetir (1 tentativa)
    - Tratar timeout como `TribunalIndisponivelError`
    - _Requisitos: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 5.1, 5.2, 5.4, 5.5, 6.1, 6.2, 6.4_

  - [ ] 6.3 Implementar health_check
    - Implementar `health_check()`:
      - Retornar `{"status": "ok"|"error", "sessao_ativa": bool, "detalhes": str}`
      - Verificar se sessão está ativa e se JusBrasil está acessível
    - _Requisitos: 10.4_

  - [ ]* 6.4 Escrever testes unitários do JusBrasilScraper
    - Testar `buscar_por_cpf()` com 1 página de resultados (mock Playwright + SessionManager)
    - Testar `buscar_por_cpf()` com múltiplas páginas (paginação)
    - Testar `buscar_por_cpf()` sem resultados (lista vazia)
    - Testar detecção de CAPTCHA durante busca (CaptchaDetectadoError)
    - Testar detecção de bloqueio anti-bot (TribunalIndisponivelError)
    - Testar timeout de navegação (TribunalIndisponivelError)
    - Testar retry de sessão expirada durante busca
    - Testar `_construir_url_busca()` com CPF formatado e sem formatação
    - Testar `health_check()` com sessão ativa e inativa
    - _Requisitos: 2.1, 2.2, 2.3, 5.1, 5.2, 5.4, 5.5, 6.1, 10.1, 10.4_

- [ ] 7. Registrar JusBrasil no ScraperRegistry
  - [ ] 7.1 Atualizar inicialização do registry para incluir JusBrasil
    - Modificar `backend/app/services/scraping/__init__.py` (ou local equivalente de inicialização)
    - Instanciar `SessionManager`
    - Instanciar `RateLimiter(intervalo_minimo=3.0)` para JusBrasil
    - Instanciar `JusBrasilScraper(session_manager, rate_limiter)`
    - Registrar no `ScraperRegistry` com identificador `"jusbrasil"`
    - Envolver em try/except `CredenciaisNaoConfiguradasError`: se credenciais ausentes, não registrar (JusBrasil fica indisponível no dropdown)
    - _Requisitos: 10.2, 10.3, 1.5, 7.1, 7.2_

- [ ] 8. Checkpoint — Verificar integração completa do scraper
  - Garantir que todos os testes passam, perguntar ao usuário se houver dúvidas.

- [ ] 9. Testes de propriedade (Property-Based Tests)
  - [ ]* 9.1 Escrever teste de propriedade — Reutilização de sessão válida
    - **Propriedade 1: Reutilização de sessão válida**
    - Usar Hypothesis com `st.integers(min_value=2, max_value=10)` para gerar N buscas
    - Mock do Playwright/browser para contar chamadas de login
    - Verificar que login é executado exatamente 1 vez para N buscas com sessão válida
    - **Valida: Requisitos 1.3, 4.1, 4.2**

  - [ ]* 9.2 Escrever teste de propriedade — Renovação de sessão expirada
    - **Propriedade 2: Renovação de sessão expirada**
    - Usar Hypothesis com `st.integers(min_value=1, max_value=5)` para posição de expiração
    - Simular sessão que expira na N-ésima busca
    - Verificar que re-login acontece e busca é repetida com sucesso
    - **Valida: Requisitos 1.4, 4.3**

  - [ ]* 9.3 Escrever teste de propriedade — Invariante de sessão única
    - **Propriedade 3: Invariante de sessão única**
    - Usar Hypothesis com `st.lists(st.sampled_from(['login', 'busca', 'expira']), min_size=3, max_size=15)`
    - Executar sequência aleatória de operações
    - Verificar que nunca há mais de 1 sessão ativa simultaneamente
    - **Valida: Requisitos 4.4**

  - [ ]* 9.4 Escrever teste de propriedade — Construção correta de URL de busca
    - **Propriedade 4: Construção correta de URL de busca**
    - Usar Hypothesis com `st.from_regex(r'[0-9]{11}', fullmatch=True)` filtrado para CPFs válidos
    - Verificar que URL gerada é `https://www.jusbrasil.com.br/consulta-processual/busca?q={cpf}`
    - Verificar que CPF na URL contém apenas dígitos (sem pontos ou traço)
    - **Valida: Requisitos 2.1**

  - [ ]* 9.5 Escrever teste de propriedade — Extração completa de dados do DOM
    - **Propriedade 5: Extração completa de dados do DOM**
    - Usar Hypothesis para gerar listas de 1 a 10 processos com dados aleatórios
    - Criar helper `gerar_pagina_mock_jusbrasil(dados)` que gera mock de Page com elementos DOM
    - Verificar que parser extrai exatamente N processos com `numero_cnj`, `classe` e `partes` não-vazios
    - **Valida: Requisitos 2.2, 2.4, 10.1**

  - [ ]* 9.6 Escrever teste de propriedade — Consolidação de paginação
    - **Propriedade 6: Consolidação de paginação**
    - Usar Hypothesis com `st.lists(st.integers(min_value=1, max_value=10), min_size=1, max_size=5)` para processos por página
    - Mock de navegação com P páginas
    - Verificar que total de processos retornados = soma dos processos de cada página
    - **Valida: Requisitos 2.3**

  - [ ]* 9.7 Escrever teste de propriedade — HTML inesperado gera ScrapingError
    - **Propriedade 7: HTML inesperado gera ScrapingError**
    - Usar Hypothesis com `st.text(min_size=10, max_size=500)` filtrado para excluir seletores válidos
    - Verificar que parser lança `ScrapingError` (não exceção genérica)
    - **Valida: Requisitos 5.3**

  - [ ]* 9.8 Escrever teste de propriedade — Rate limiter intervalo 3 segundos
    - **Propriedade 8: Rate limiter garante intervalo mínimo de 3 segundos**
    - Usar Hypothesis com `st.integers(min_value=2, max_value=5)` para número de requisições
    - Instanciar `RateLimiter(intervalo_minimo=3.0)`
    - Verificar que intervalo entre requisições consecutivas é ≥ 3.0 segundos
    - **Valida: Requisitos 6.1, 6.2**

  - [ ]* 9.9 Escrever teste de propriedade — Rate limiter paginação 2 segundos
    - **Propriedade 9: Rate limiter garante intervalo de paginação de 2 segundos**
    - Usar Hypothesis com `st.integers(min_value=2, max_value=5)` para número de páginas
    - Verificar que intervalo entre requisições de paginação é ≥ 2.0 segundos
    - **Valida: Requisitos 6.4**

  - [ ]* 9.10 Escrever teste de propriedade — Senha nunca aparece em logs
    - **Propriedade 10: Senha nunca aparece em logs**
    - Usar Hypothesis com `st.text(min_size=4, max_size=30)` para gerar senhas aleatórias
    - Capturar todos os logs durante operações de login (sucesso e falha)
    - Verificar que a senha NUNCA aparece no texto dos logs
    - **Valida: Requisitos 9.4**

- [ ] 10. Checkpoint final — Garantir que todos os testes passam
  - Garantir que todos os testes passam, perguntar ao usuário se houver dúvidas.

## Notas

- Tarefas marcadas com `*` são opcionais e podem ser puladas para um MVP mais rápido
- Cada tarefa referencia requisitos específicos para rastreabilidade
- Checkpoints garantem validação incremental
- Testes de propriedade validam propriedades universais de corretude
- Testes unitários validam cenários específicos e edge cases
- Este módulo **depende** da infraestrutura compartilhada implementada pela spec `busca-cpf-tjsp` (TribunalScraper ABC, ProcessoEncontrado, ScraperRegistry, RateLimiter, CPFValidator, Blueprint, Frontend)
- Dependências adicionais: `playwright`, `hypothesis` (dev)
- Todos os testes usam mocks do Playwright — nenhuma chamada real ao JusBrasil em testes automatizados
