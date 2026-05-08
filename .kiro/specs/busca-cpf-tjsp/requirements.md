# Documento de Requisitos — Busca de Processos por CPF (TJSP)

## Introdução

Funcionalidade para busca de processos judiciais a partir do CPF de uma pessoa física no Tribunal de Justiça de São Paulo (TJSP). A API DataJud do CNJ não suporta busca por CPF — apenas por número de processo (número CNJ). Para contornar essa limitação, o sistema realizará web scraping do sistema ESAJ do TJSP (https://esaj.tjsp.jus.br/cpopg/open.do), que permite consulta por documento da parte.

Esta funcionalidade é uma prova de conceito (POC) limitada ao TJSP. A arquitetura deve ser extensível para permitir a adição de outros tribunais no futuro, mas a implementação inicial cobre apenas o ESAJ/TJSP.

## Glossário

- **Sistema**: A aplicação de monitoramento de processos judiciais
- **Scraper_TJSP**: Módulo responsável por realizar web scraping no sistema ESAJ do TJSP
- **ESAJ**: Sistema de Automação da Justiça, utilizado pelo TJSP para consulta processual pública
- **CPF**: Cadastro de Pessoa Física, documento de identificação com 11 dígitos numéricos
- **Validador_CPF**: Módulo responsável por validar formato e dígitos verificadores do CPF
- **Processo_Encontrado**: Processo judicial retornado pela busca no ESAJ, contendo número, classe, assunto e partes
- **Usuário**: Pessoa que utiliza o sistema para buscar e acompanhar processos
- **Rate_Limiter**: Mecanismo de controle de frequência de requisições ao ESAJ
- **Tribunal_Scraper**: Interface abstrata que define o contrato para scrapers de diferentes tribunais

## Requisitos

### Requisito 1: Página de Busca por CPF

**User Story:** Como um Usuário, eu quero acessar uma página dedicada para buscar processos por CPF, para que eu possa encontrar todos os processos associados a uma pessoa no TJSP.

#### Critérios de Aceitação

1. THE Sistema SHALL disponibilizar uma página acessível via navegação principal com o título "Busca por CPF"
2. WHEN o Usuário acessa a página de busca por CPF, THE Sistema SHALL exibir um formulário com campo para entrada do CPF e seleção do tribunal (inicialmente apenas TJSP disponível)
3. WHEN o Usuário submete o formulário com um CPF válido, THE Sistema SHALL exibir um indicador de carregamento durante o processamento da busca
4. WHEN a busca é concluída com resultados, THE Sistema SHALL exibir a lista de processos encontrados com: número do processo (formato CNJ), classe processual, assunto e partes envolvidas
5. WHEN a busca é concluída sem resultados, THE Sistema SHALL exibir mensagem informando que nenhum processo foi encontrado para o CPF informado no tribunal selecionado

### Requisito 2: Validação de CPF

**User Story:** Como um Usuário, eu quero que o sistema valide o CPF antes de realizar a busca, para que eu não desperdice tempo com consultas inválidas.

#### Critérios de Aceitação

1. WHEN o Usuário informa um CPF com formato inválido (diferente de 11 dígitos numéricos), THE Validador_CPF SHALL rejeitar a entrada e o Sistema SHALL exibir mensagem indicando o formato correto
2. WHEN o Usuário informa um CPF com dígitos verificadores incorretos, THE Validador_CPF SHALL rejeitar a entrada e o Sistema SHALL exibir mensagem indicando que o CPF é inválido
3. WHEN o Usuário informa um CPF com todos os dígitos iguais (ex: 111.111.111-11), THE Validador_CPF SHALL rejeitar a entrada como CPF inválido
4. THE Validador_CPF SHALL aceitar CPF informado com ou sem formatação (pontos e traço), normalizando para 11 dígitos numéricos antes do processamento
5. THE Sistema SHALL aplicar máscara de formatação (XXX.XXX.XXX-XX) no campo de entrada conforme o Usuário digita

### Requisito 3: Web Scraping do ESAJ/TJSP

**User Story:** Como um Usuário, eu quero que o sistema consulte o ESAJ do TJSP automaticamente, para que eu obtenha a lista de processos associados a um CPF sem precisar navegar manualmente no site do tribunal.

#### Critérios de Aceitação

1. WHEN o Validador_CPF confirma que o CPF é válido, THE Scraper_TJSP SHALL enviar uma requisição ao ESAJ do TJSP (https://esaj.tjsp.jus.br/cpopg/open.do) com o CPF como parâmetro de busca por documento da parte
2. WHEN o ESAJ retorna a página de resultados, THE Scraper_TJSP SHALL extrair de cada processo listado: número do processo (formato CNJ), classe processual, assunto e nome das partes
3. WHEN o ESAJ retorna múltiplas páginas de resultados, THE Scraper_TJSP SHALL navegar por todas as páginas e consolidar todos os processos encontrados
4. THE Scraper_TJSP SHALL retornar os dados extraídos em formato estruturado (lista de objetos com campos padronizados)

### Requisito 4: Tratamento de Indisponibilidade do ESAJ

**User Story:** Como um Usuário, eu quero ser informado quando o ESAJ estiver indisponível, para que eu saiba que o problema não é do sistema e possa tentar novamente mais tarde.

#### Critérios de Aceitação

1. IF o ESAJ do TJSP estiver indisponível (timeout ou erro de conexão), THEN THE Sistema SHALL exibir mensagem informando que o tribunal está temporariamente indisponível e sugerindo nova tentativa em alguns minutos
2. IF o ESAJ retornar uma página de CAPTCHA, THEN THE Sistema SHALL informar ao Usuário que o tribunal está exigindo verificação humana e sugerir acesso direto ao site do ESAJ
3. IF o ESAJ retornar uma resposta com estrutura HTML inesperada (possível alteração no layout), THEN THE Scraper_TJSP SHALL registrar erro detalhado no log e o Sistema SHALL informar ao Usuário que ocorreu um erro na leitura dos dados
4. IF o ESAJ retornar erro HTTP (4xx ou 5xx), THEN THE Sistema SHALL exibir mensagem de erro apropriada ao Usuário sem expor detalhes técnicos internos

### Requisito 5: Rate Limiting

**User Story:** Como um Usuário, eu quero que o sistema controle a frequência de requisições ao ESAJ, para que o serviço do tribunal não seja sobrecarregado e o acesso não seja bloqueado.

#### Critérios de Aceitação

1. THE Rate_Limiter SHALL limitar as requisições ao ESAJ a no máximo 1 requisição a cada 2 segundos por instância do sistema
2. WHEN o Rate_Limiter detecta que o limite foi atingido, THE Sistema SHALL enfileirar a requisição e processá-la quando o intervalo mínimo for respeitado
3. WHILE uma requisição está aguardando na fila do Rate_Limiter, THE Sistema SHALL manter o indicador de carregamento visível para o Usuário
4. THE Rate_Limiter SHALL aplicar um intervalo mínimo de 1 segundo entre requisições consecutivas de paginação ao ESAJ

### Requisito 6: Cadastro de Processos Encontrados para Monitoramento

**User Story:** Como um Usuário, eu quero poder cadastrar processos encontrados na busca por CPF para monitoramento contínuo, para que eu possa acompanhar suas atualizações automaticamente.

#### Critérios de Aceitação

1. WHEN a lista de processos encontrados é exibida, THE Sistema SHALL apresentar um botão "Monitorar" ao lado de cada processo
2. WHEN o Usuário clica em "Monitorar" em um Processo_Encontrado, THE Sistema SHALL cadastrar o processo para monitoramento utilizando o fluxo de cadastro existente (via DataJud API com o número CNJ)
3. WHEN o processo já está cadastrado para monitoramento, THE Sistema SHALL exibir indicação visual de "Já monitorado" em vez do botão "Monitorar"
4. IF o cadastro para monitoramento falha (ex: processo não encontrado na DataJud), THEN THE Sistema SHALL informar o Usuário sobre a falha sem remover o processo da lista de resultados

### Requisito 7: Arquitetura Extensível para Outros Tribunais

**User Story:** Como um desenvolvedor, eu quero que a arquitetura de scraping seja extensível, para que eu possa adicionar suporte a outros tribunais no futuro sem refatoração significativa.

#### Critérios de Aceitação

1. THE Sistema SHALL definir uma interface Tribunal_Scraper com métodos padronizados: buscar_por_cpf(cpf) retornando lista de Processo_Encontrado
2. THE Scraper_TJSP SHALL implementar a interface Tribunal_Scraper como primeira implementação concreta
3. THE Sistema SHALL utilizar um registro (registry) de scrapers disponíveis, mapeando identificador do tribunal para a implementação correspondente
4. WHEN o Usuário seleciona um tribunal na página de busca, THE Sistema SHALL utilizar o scraper correspondente do registro para realizar a consulta

