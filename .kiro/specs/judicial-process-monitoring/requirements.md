# Documento de Requisitos — Monitoramento de Processos Judiciais

## Introdução

Sistema para cadastro e monitoramento de processos judiciais brasileiros. O sistema permite cadastrar processos para acompanhamento contínuo, realiza monitoramento diário automatizado (por volta das 23h) buscando atualizações em todos os tribunais brasileiros, e oferece a possibilidade de consulta avulsa (sem salvar). O desenvolvimento será feito em ondas (iterações), sendo a primeira onda focada na validação da viabilidade técnica.

### Pesquisa de Viabilidade Técnica — APIs Disponíveis

Com base na pesquisa realizada, as seguintes opções de API foram identificadas:

1. **DataJud (CNJ)** — API pública mantida pelo Conselho Nacional de Justiça. Permite consulta de processos judiciais utilizando o número CNJ. Possui chave de acesso pública e cobre todos os tribunais brasileiros. Disponível em: https://www.jus.br/servico/datajud/. Existem bibliotecas open-source que consomem esta API (ex: gem Ruby `datajud`, projeto Go `DataJUD_API_CALLER`).

2. **ESAJ / PJe (Tribunais Estaduais)** — Sistemas como ESAJ (usado pelo TJSP e outros) e PJe (Processo Judicial Eletrônico) possuem interfaces web públicas para consulta, mas não oferecem APIs REST oficiais abertas. A consulta programática geralmente requer web scraping.

3. **Serviços Pagos** — Plataformas como Judit, Codilo e JusBrasil oferecem APIs pagas com cobertura ampla de tribunais.

**Conclusão da pesquisa:** A API DataJud do CNJ é a principal opção gratuita e oficial para consulta processual em todos os tribunais brasileiros. Ela retorna metadados do processo (movimentações, partes, classe, assunto), mas **não oferece download direto de documentos/peças processuais**. Para download de documentos, seria necessário integração com os sistemas individuais dos tribunais (ESAJ, PJe) via scraping ou APIs específicas quando disponíveis.

## Glossário

- **Sistema**: A aplicação de monitoramento de processos judiciais
- **Processo_Judicial**: Ação judicial identificada por um número CNJ único
- **Número_CNJ**: Número unificado de identificação de processo no formato NNNNNNN-DD.AAAA.J.TR.OOOO
- **Monitorador**: Módulo responsável pelo agendamento e execução das consultas diárias
- **Consultor**: Módulo responsável por realizar as buscas nos tribunais via API
- **DataJud_API**: API pública do CNJ para consulta de dados processuais
- **Movimentação**: Evento ou andamento registrado no processo judicial
- **Consulta_Avulsa**: Busca de processo sem persistência dos dados no sistema
- **Usuário**: Pessoa que utiliza o sistema para cadastrar e acompanhar processos
- **Tribunal**: Órgão do Poder Judiciário brasileiro (ex: TJSP, TRF1, TST)

## Requisitos

### Requisito 1: Cadastro de Processos Judiciais

**User Story:** Como um Usuário, eu quero cadastrar processos judiciais no sistema, para que eu possa acompanhar suas atualizações de forma automatizada.

#### Critérios de Aceitação

1. WHEN o Usuário fornece um Número_CNJ válido, THE Sistema SHALL registrar o Processo_Judicial e associá-lo ao Usuário
2. WHEN o Usuário fornece um Número_CNJ com formato inválido, THE Sistema SHALL rejeitar o cadastro e exibir mensagem indicando o formato correto (NNNNNNN-DD.AAAA.J.TR.OOOO)
3. WHEN o Usuário cadastra um Processo_Judicial, THE Consultor SHALL realizar uma busca inicial na DataJud_API para preencher os dados públicos do processo (classe, assunto, partes, tribunal, última movimentação)
4. IF a DataJud_API retorna erro ou não encontra o processo durante o cadastro, THEN THE Sistema SHALL informar o Usuário e permitir que ele decida se deseja manter o cadastro mesmo sem dados iniciais
5. THE Sistema SHALL armazenar para cada Processo_Judicial: Número_CNJ, tribunal de origem, classe processual, assunto, lista de partes, data de cadastro e status atual

### Requisito 2: Monitoramento Diário Automatizado

**User Story:** Como um Usuário, eu quero que o sistema verifique automaticamente as atualizações dos meus processos uma vez por dia, para que eu seja informado sobre novas movimentações sem precisar consultar manualmente.

#### Critérios de Aceitação

1. THE Monitorador SHALL executar a verificação de todos os processos cadastrados uma vez por dia, com início programado para as 23h (horário de Brasília)
2. WHEN o Monitorador inicia a execução diária, THE Consultor SHALL consultar a DataJud_API para cada Processo_Judicial cadastrado e ativo
3. WHEN a DataJud_API retorna novas movimentações para um Processo_Judicial, THE Sistema SHALL armazenar as novas movimentações e atualizar o status do processo
4. IF a DataJud_API estiver indisponível durante o monitoramento, THEN THE Monitorador SHALL registrar o erro e tentar novamente após 30 minutos, com no máximo 3 tentativas
5. WHEN o monitoramento diário é concluído, THE Sistema SHALL registrar um log com: quantidade de processos verificados, quantidade de processos com atualizações, e eventuais erros

### Requisito 3: Consulta em Todos os Tribunais Brasileiros

**User Story:** Como um Usuário, eu quero que as buscas sejam realizadas em todos os tribunais brasileiros, para que eu tenha cobertura completa independentemente de onde o processo tramita.

#### Critérios de Aceitação

1. THE Consultor SHALL utilizar a DataJud_API do CNJ como fonte primária de dados, garantindo cobertura de todos os tribunais brasileiros (Justiça Estadual, Federal, Trabalhista, Eleitoral e Militar)
2. WHEN o Consultor realiza uma busca por Número_CNJ, THE Consultor SHALL identificar o tribunal de origem a partir dos dígitos do Número_CNJ e direcionar a consulta ao endpoint correto da DataJud_API
3. THE Sistema SHALL manter uma lista atualizada dos tribunais suportados pela DataJud_API e seus respectivos identificadores

### Requisito 4: Visualização Detalhada do Processo

**User Story:** Como um Usuário, eu quero visualizar os detalhes completos de um processo cadastrado, para que eu possa acompanhar todas as informações e movimentações relevantes.

#### Critérios de Aceitação

1. WHEN o Usuário seleciona um Processo_Judicial cadastrado, THE Sistema SHALL exibir os dados completos: Número_CNJ, tribunal, classe, assunto, partes envolvidas, valor da causa (quando disponível) e lista de movimentações ordenadas por data
2. WHEN o Usuário visualiza as movimentações, THE Sistema SHALL apresentar cada Movimentação com: data, descrição e complemento (quando disponível)
3. THE Sistema SHALL indicar visualmente quais movimentações são novas desde a última visualização pelo Usuário
4. WHEN o Usuário acessa a visualização detalhada, THE Sistema SHALL exibir a data e hora da última atualização bem-sucedida do processo

### Requisito 5: Consulta Avulsa (Sem Salvar)

**User Story:** Como um Usuário, eu quero realizar uma busca de processo judicial sem salvá-lo no sistema, para que eu possa verificar informações pontuais sem poluir minha lista de processos monitorados.

#### Critérios de Aceitação

1. WHEN o Usuário solicita uma Consulta_Avulsa informando um Número_CNJ válido, THE Consultor SHALL buscar os dados na DataJud_API e apresentar os resultados ao Usuário
2. WHEN a Consulta_Avulsa é concluída, THE Sistema SHALL exibir os mesmos dados detalhados disponíveis na visualização de processos cadastrados (classe, assunto, partes, movimentações)
3. THE Sistema SHALL descartar os dados da Consulta_Avulsa após o Usuário encerrar a visualização, sem persistir informações no banco de dados
4. WHEN o Usuário visualiza o resultado de uma Consulta_Avulsa, THE Sistema SHALL oferecer a opção de cadastrar o processo para monitoramento contínuo
5. IF a DataJud_API retorna erro durante uma Consulta_Avulsa, THEN THE Sistema SHALL exibir mensagem de erro clara indicando o motivo da falha

### Requisito 6: Validação de Viabilidade Técnica (Onda 1)

**User Story:** Como um Usuário, eu quero validar que a integração com a API do CNJ funciona corretamente, para que eu tenha confiança de que o sistema é tecnicamente viável antes de investir em funcionalidades avançadas.

#### Critérios de Aceitação

1. THE Consultor SHALL estabelecer conexão com a DataJud_API utilizando a chave de acesso pública e autenticação via header HTTP
2. WHEN o Consultor envia uma requisição com um Número_CNJ válido, THE DataJud_API SHALL retornar os dados do processo em formato JSON contendo: classe, assunto, tribunal, partes e movimentações
3. THE Sistema SHALL implementar um endpoint de health-check que valide a conectividade com a DataJud_API e retorne o status da integração
4. WHEN a DataJud_API altera sua estrutura de resposta, THE Sistema SHALL registrar erro detalhado no log para facilitar a identificação da mudança
5. THE Sistema SHALL documentar as limitações conhecidas da DataJud_API, incluindo: rate limits, dados não disponíveis (documentos/peças processuais) e eventuais tribunais com cobertura parcial

### Requisito 7: Download de Documentos (Investigação)

**User Story:** Como um Usuário, eu quero saber se é possível baixar documentos e peças processuais, para que eu possa acessar o conteúdo completo dos autos.

#### Critérios de Aceitação

1. THE Sistema SHALL informar ao Usuário que o download de documentos processuais não está disponível via DataJud_API do CNJ
2. WHERE a funcionalidade de download de documentos for implementada em ondas futuras, THE Sistema SHALL integrar-se com os sistemas individuais dos tribunais (ESAJ, PJe) para obter peças processuais
3. WHEN o Usuário visualiza um processo, THE Sistema SHALL exibir links diretos para a página do processo no site do tribunal de origem, permitindo acesso manual aos documentos
4. THE Sistema SHALL registrar no roadmap a investigação de viabilidade de integração com ESAJ e PJe para download automatizado de documentos em ondas futuras
