# Documento de Requisitos — Busca de Processos por CPF (JusBrasil)

## Introdução

Funcionalidade para busca de processos judiciais a partir do CPF de uma pessoa física utilizando a plataforma JusBrasil (jusbrasil.com.br). Diferentemente da busca via ESAJ/TJSP (que cobre apenas o Tribunal de Justiça de São Paulo), o JusBrasil agrega processos de todos os tribunais brasileiros em uma única interface.

O JusBrasil exige autenticação (login) para visualizar processos associados a um CPF. O sistema utilizará as credenciais do usuário (armazenadas em variáveis de ambiente) para realizar login automatizado, navegar até a página de resultados e extrair os dados dos processos encontrados.

O padrão de URL para busca por CPF no JusBrasil é: `https://www.jusbrasil.com.br/consulta-processual/busca?q={cpf}`.

**Nota:** Esta funcionalidade realiza web scraping autenticado no JusBrasil. O usuário reconhece que isso pode violar os termos de uso da plataforma e optou por prosseguir.

## Glossário

- **Sistema**: A aplicação de monitoramento de processos judiciais
- **Scraper_JusBrasil**: Módulo responsável por realizar web scraping autenticado no JusBrasil
- **JusBrasil**: Plataforma web brasileira que agrega informações processuais de todos os tribunais
- **CPF**: Cadastro de Pessoa Física, documento de identificação com 11 dígitos numéricos
- **Validador_CPF**: Módulo responsável por validar formato e dígitos verificadores do CPF (compartilhado com busca-cpf-tjsp)
- **Processo_Encontrado**: Processo judicial retornado pela busca no JusBrasil, contendo número, tribunal, classe e partes
- **Usuário**: Pessoa que utiliza o sistema para buscar e acompanhar processos
- **Sessão_JusBrasil**: Sessão HTTP autenticada com cookies válidos para acesso ao JusBrasil
- **Gerenciador_Sessão**: Módulo responsável por criar, manter e renovar a Sessão_JusBrasil
- **Credenciais_JusBrasil**: Email e senha para login no JusBrasil, armazenados nas variáveis de ambiente JUSBRASIL_EMAIL e JUSBRASIL_PASSWORD
- **Tribunal_Scraper**: Interface abstrata que define o contrato para scrapers de diferentes tribunais (definida na spec busca-cpf-tjsp)
- **Rate_Limiter**: Mecanismo de controle de frequência de requisições ao JusBrasil
- **Headless_Browser**: Navegador sem interface gráfica (Playwright/Selenium) utilizado para renderizar páginas JavaScript

## Requisitos

### Requisito 1: Autenticação no JusBrasil

**User Story:** Como um Usuário, eu quero que o sistema faça login automaticamente no JusBrasil usando minhas credenciais, para que eu possa acessar dados de processos que exigem autenticação.

#### Critérios de Aceitação

1. THE Gerenciador_Sessão SHALL carregar as Credenciais_JusBrasil exclusivamente a partir das variáveis de ambiente JUSBRASIL_EMAIL e JUSBRASIL_PASSWORD
2. WHEN o Gerenciador_Sessão inicia uma nova sessão, THE Scraper_JusBrasil SHALL realizar login no JusBrasil utilizando as Credenciais_JusBrasil e obter cookies de autenticação válidos
3. WHILE a Sessão_JusBrasil possui cookies válidos (não expirados), THE Gerenciador_Sessão SHALL reutilizar a sessão existente sem realizar novo login
4. WHEN a Sessão_JusBrasil expira ou recebe resposta HTTP 401/403, THE Gerenciador_Sessão SHALL descartar a sessão atual e realizar novo login automaticamente
5. IF as Credenciais_JusBrasil não estiverem configuradas nas variáveis de ambiente, THEN THE Sistema SHALL exibir mensagem informando que as credenciais do JusBrasil não estão configuradas e desabilitar a opção de busca via JusBrasil
6. IF o login no JusBrasil falhar (credenciais inválidas ou erro de autenticação), THEN THE Sistema SHALL informar ao Usuário que não foi possível autenticar no JusBrasil e sugerir verificação das credenciais

### Requisito 2: Busca de Processos por CPF via JusBrasil

**User Story:** Como um Usuário, eu quero buscar processos associados a um CPF no JusBrasil, para que eu possa encontrar processos em todos os tribunais brasileiros de uma só vez.

#### Critérios de Aceitação

1. WHEN o Validador_CPF confirma que o CPF é válido e o Usuário seleciona JusBrasil como fonte, THE Scraper_JusBrasil SHALL navegar até a página de busca por CPF no JusBrasil utilizando a Sessão_JusBrasil autenticada
2. WHEN o JusBrasil retorna a página de resultados, THE Scraper_JusBrasil SHALL extrair de cada processo listado: número do processo (formato CNJ), tribunal de origem, classe processual e nomes das partes
3. WHEN o JusBrasil retorna múltiplas páginas de resultados, THE Scraper_JusBrasil SHALL navegar por todas as páginas e consolidar todos os processos encontrados
4. THE Scraper_JusBrasil SHALL retornar os dados extraídos em formato estruturado compatível com a interface Tribunal_Scraper (lista de Processo_Encontrado)
5. WHEN a busca é concluída com resultados, THE Sistema SHALL exibir a lista de processos encontrados com: número do processo (formato CNJ), tribunal de origem, classe processual e partes envolvidas
6. WHEN a busca é concluída sem resultados, THE Sistema SHALL exibir mensagem informando que nenhum processo foi encontrado para o CPF informado no JusBrasil

### Requisito 3: Renderização de Páginas JavaScript

**User Story:** Como um Usuário, eu quero que o sistema consiga extrair dados mesmo de páginas que dependem de JavaScript para renderização, para que a busca funcione corretamente independentemente da tecnologia usada pelo JusBrasil.

#### Critérios de Aceitação

1. THE Scraper_JusBrasil SHALL utilizar um Headless_Browser (Playwright) para renderizar as páginas do JusBrasil que dependem de JavaScript para exibir conteúdo
2. WHEN o Headless_Browser carrega uma página, THE Scraper_JusBrasil SHALL aguardar até que os elementos de resultado estejam presentes no DOM antes de extrair dados
3. THE Scraper_JusBrasil SHALL configurar o Headless_Browser com user-agent de navegador real para reduzir detecção de automação
4. WHEN o Headless_Browser é iniciado, THE Scraper_JusBrasil SHALL executá-lo em modo headless sem interface gráfica visível

### Requisito 4: Gerenciamento de Sessão e Cookies

**User Story:** Como um Usuário, eu quero que o sistema gerencie sessões de forma eficiente, para que as buscas sejam rápidas sem necessidade de login a cada consulta.

#### Critérios de Aceitação

1. WHEN o Gerenciador_Sessão realiza login com sucesso, THE Gerenciador_Sessão SHALL armazenar os cookies de sessão em memória para reutilização em requisições subsequentes
2. THE Gerenciador_Sessão SHALL verificar a validade da sessão antes de cada busca, realizando novo login apenas quando necessário
3. WHEN o Gerenciador_Sessão detecta que a sessão expirou durante uma busca em andamento, THE Gerenciador_Sessão SHALL realizar novo login e repetir a requisição que falhou
4. THE Gerenciador_Sessão SHALL manter no máximo uma sessão ativa por vez, descartando sessões anteriores ao criar uma nova

### Requisito 5: Tratamento de Indisponibilidade e Proteções Anti-Bot

**User Story:** Como um Usuário, eu quero ser informado quando o JusBrasil estiver indisponível ou bloquear o acesso, para que eu saiba que o problema não é do sistema e possa tomar ação apropriada.

#### Critérios de Aceitação

1. IF o JusBrasil estiver indisponível (timeout ou erro de conexão), THEN THE Sistema SHALL exibir mensagem informando que o JusBrasil está temporariamente indisponível e sugerindo nova tentativa em alguns minutos
2. IF o JusBrasil apresentar um CAPTCHA durante a navegação, THEN THE Sistema SHALL informar ao Usuário que o JusBrasil está exigindo verificação humana e sugerir aguardar alguns minutos antes de tentar novamente
3. IF o JusBrasil retornar uma página com estrutura HTML inesperada (possível alteração no layout), THEN THE Scraper_JusBrasil SHALL registrar erro detalhado no log e o Sistema SHALL informar ao Usuário que ocorreu um erro na leitura dos dados
4. IF o JusBrasil bloquear o acesso por detecção de automação (HTTP 429 ou página de bloqueio), THEN THE Sistema SHALL informar ao Usuário que o acesso foi temporariamente bloqueado e sugerir aguardar antes de nova tentativa
5. IF o JusBrasil retornar erro HTTP (4xx ou 5xx) não relacionado a autenticação, THEN THE Sistema SHALL exibir mensagem de erro apropriada ao Usuário sem expor detalhes técnicos internos

### Requisito 6: Rate Limiting para JusBrasil

**User Story:** Como um Usuário, eu quero que o sistema controle a frequência de requisições ao JusBrasil, para que o acesso não seja bloqueado por excesso de requisições.

#### Critérios de Aceitação

1. THE Rate_Limiter SHALL limitar as requisições ao JusBrasil a no máximo 1 requisição a cada 3 segundos por instância do sistema
2. WHEN o Rate_Limiter detecta que o limite foi atingido, THE Sistema SHALL enfileirar a requisição e processá-la quando o intervalo mínimo for respeitado
3. WHILE uma requisição está aguardando na fila do Rate_Limiter, THE Sistema SHALL manter o indicador de carregamento visível para o Usuário
4. THE Rate_Limiter SHALL aplicar um intervalo mínimo de 2 segundos entre requisições consecutivas de paginação ao JusBrasil

### Requisito 7: Integração com a Página de Busca por CPF

**User Story:** Como um Usuário, eu quero selecionar JusBrasil como fonte de busca na mesma página de busca por CPF, para que eu tenha uma experiência unificada ao buscar processos em diferentes fontes.

#### Critérios de Aceitação

1. WHEN o Usuário acessa a página de busca por CPF, THE Sistema SHALL exibir JusBrasil como opção no seletor de tribunal/fonte (ao lado de TJSP e futuras fontes)
2. WHEN o JusBrasil está selecionado como fonte e as Credenciais_JusBrasil não estão configuradas, THE Sistema SHALL exibir aviso informando que as credenciais precisam ser configuradas para utilizar esta fonte
3. WHEN o JusBrasil está selecionado como fonte e as credenciais estão configuradas, THE Sistema SHALL habilitar o botão de busca normalmente
4. THE Sistema SHALL exibir ao lado da opção JusBrasil uma indicação de que esta fonte cobre todos os tribunais brasileiros

### Requisito 8: Cadastro de Processos Encontrados para Monitoramento

**User Story:** Como um Usuário, eu quero poder cadastrar processos encontrados via JusBrasil para monitoramento contínuo, para que eu possa acompanhar suas atualizações automaticamente.

#### Critérios de Aceitação

1. WHEN a lista de processos encontrados via JusBrasil é exibida, THE Sistema SHALL apresentar um botão "Monitorar" ao lado de cada processo
2. WHEN o Usuário clica em "Monitorar" em um Processo_Encontrado, THE Sistema SHALL cadastrar o processo para monitoramento utilizando o fluxo de cadastro existente (via DataJud API com o número CNJ)
3. WHEN o processo já está cadastrado para monitoramento, THE Sistema SHALL exibir indicação visual de "Já monitorado" em vez do botão "Monitorar"
4. IF o cadastro para monitoramento falha (ex: processo não encontrado na DataJud), THEN THE Sistema SHALL informar o Usuário sobre a falha sem remover o processo da lista de resultados

### Requisito 9: Segurança das Credenciais

**User Story:** Como um Usuário, eu quero que minhas credenciais do JusBrasil sejam armazenadas de forma segura, para que não haja risco de exposição acidental.

#### Critérios de Aceitação

1. THE Sistema SHALL carregar as credenciais do JusBrasil exclusivamente a partir de variáveis de ambiente (JUSBRASIL_EMAIL e JUSBRASIL_PASSWORD), sem armazená-las em código-fonte, banco de dados ou arquivos de configuração versionados
2. THE Sistema SHALL incluir JUSBRASIL_EMAIL e JUSBRASIL_PASSWORD no arquivo .env.example como referência, com valores placeholder (sem credenciais reais)
3. IF o arquivo .env contiver credenciais reais, THEN THE Sistema SHALL garantir que o .gitignore inclua o arquivo .env para evitar commit acidental
4. THE Sistema SHALL registrar nos logs apenas o email utilizado para login (para diagnóstico), sem registrar a senha em nenhuma circunstância

### Requisito 10: Implementação da Interface Tribunal_Scraper

**User Story:** Como um desenvolvedor, eu quero que o scraper do JusBrasil implemente a mesma interface dos outros scrapers, para que a arquitetura permaneça consistente e extensível.

#### Critérios de Aceitação

1. THE Scraper_JusBrasil SHALL implementar a interface Tribunal_Scraper com o método buscar_por_cpf(cpf) retornando lista de Processo_Encontrado
2. THE Scraper_JusBrasil SHALL ser registrado no registry de scrapers com o identificador "jusbrasil"
3. WHEN o Scraper_JusBrasil é instanciado, THE Scraper_JusBrasil SHALL verificar se as Credenciais_JusBrasil estão disponíveis e lançar exceção configurável caso não estejam
4. THE Scraper_JusBrasil SHALL expor um método de health check que verifica se a sessão está ativa e se o JusBrasil está acessível
