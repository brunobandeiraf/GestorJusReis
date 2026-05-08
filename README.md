# Monitoramento de Processos Judiciais

Sistema para cadastro e monitoramento automatizado de processos judiciais brasileiros. Consulta a API pública DataJud do CNJ para buscar dados de processos em todos os tribunais do país.

## Funcionalidades

- **Cadastro de processos** — Registre processos pelo número CNJ para acompanhamento contínuo
- **Monitoramento diário** — Verificação automática de novas movimentações às 23h (horário de Brasília)
- **Consulta avulsa** — Busque dados de um processo sem salvá-lo no sistema
- **Visualização detalhada** — Veja movimentações, partes envolvidas e dados completos do processo
- **Cobertura nacional** — Consulta em todos os tribunais brasileiros (Estadual, Federal, Trabalho, Eleitoral, Militar)

## Tecnologias

### Backend
- **Python 3.10+**
- **Flask** — Framework web (API REST)
- **SQLAlchemy** — ORM para banco de dados
- **SQLite** — Banco de dados (desenvolvimento)
- **APScheduler** — Agendamento do monitoramento diário
- **Tenacity** — Retry com backoff para chamadas à API
- **Requests** — Cliente HTTP para a DataJud API

### Frontend
- **React 18** — Interface de usuário
- **Vite** — Build tool e dev server
- **Axios** — Cliente HTTP
- **React Router** — Navegação SPA

### Integração
- **DataJud API (CNJ)** — API pública do Conselho Nacional de Justiça com cobertura de todos os tribunais brasileiros

## Pré-requisitos

- Python 3.10 ou superior
- Node.js 18 ou superior
- npm

## Como executar

### 1. Clone o repositório

```bash
git clone <url-do-repositorio>
cd GestorJusReis
```

### 2. Backend

```bash
# Instalar dependências Python
pip install -r backend/requirements.txt

# Inicializar o banco de dados
cd backend
FLASK_APP=app python -m flask init-db

# Iniciar o servidor (porta 5001)
FLASK_APP=app python -m flask run --port 5001
```

O backend estará disponível em `http://localhost:5001`.

### 3. Frontend

Em outro terminal:

```bash
cd frontend

# Instalar dependências
npm install

# Iniciar o servidor de desenvolvimento
npm run dev
```

O frontend estará disponível em `http://localhost:3000`.

### 4. Acessar o sistema

Abra **http://localhost:3000** no navegador.

## Estrutura do Projeto

```
├── backend/
│   ├── app/
│   │   ├── __init__.py          # App factory Flask
│   │   ├── config.py            # Configurações (dev/test/prod)
│   │   ├── models/              # Modelos SQLAlchemy
│   │   ├── routes/              # Endpoints REST (Blueprints)
│   │   ├── services/            # Lógica de negócio
│   │   └── utils/               # Utilitários (mapeamento de tribunais)
│   ├── tests/                   # Testes (unit, integration, property)
│   ├── instance/                # Banco SQLite (gerado)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/          # Componentes React
│   │   ├── pages/               # Páginas (Dashboard, Processo, Consulta)
│   │   ├── services/            # Cliente HTTP (Axios)
│   │   ├── context/             # Estado global (Context API)
│   │   └── utils/               # Utilitários (formatação CNJ)
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## API Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/processos` | Lista processos cadastrados |
| POST | `/api/processos` | Cadastra novo processo |
| GET | `/api/processos/:id` | Detalhes de um processo |
| DELETE | `/api/processos/:id` | Remove processo do monitoramento |
| GET | `/api/processos/:id/movimentacoes` | Movimentações do processo |
| POST | `/api/consulta-avulsa` | Consulta sem salvar |
| GET | `/api/health` | Status da integração com DataJud |
| GET | `/api/monitoramento/status` | Status do último monitoramento |
| GET | `/api/tribunais` | Lista tribunais suportados |

## Testes

```bash
# Testes unitários do backend
cd backend
python -m pytest tests/unit/ -q

# Testes do frontend
cd frontend
npm test
```

## Limitações conhecidas (Onda 1)

- **Download de documentos** não disponível — a DataJud API não fornece peças processuais
- **Autenticação de usuários** não implementada — será adicionada em ondas futuras
- **Banco SQLite** — adequado para desenvolvimento, migrar para PostgreSQL em produção
- **Notificações** — não implementadas nesta versão

## Nota sobre a porta 5000 no macOS

No macOS, a porta 5000 é usada pelo AirPlay Receiver. Por isso o backend usa a porta **5001**. Se precisar alterar, edite também o proxy em `frontend/vite.config.js`.
