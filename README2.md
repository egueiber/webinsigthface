# Health Track - Sistema de Gerenciamento e Acompanhamento Facial v8.0

Sistema web para gerenciamento de pessoas e câmeras, focado em reconhecimento facial e acompanhamento de movimentação em tempo real e histórico.

## 🚀 Funcionalidades Principais

* **Gerenciamento de Pessoas:** CRUD completo de usuários, incluindo captura facial.
* **Gerenciamento de Localizações:** CRUD de localizações com upload de mapas (plantas baixas).
* **Gerenciamento de Câmeras:** CRUD de câmeras com associação a localizações e metadados (andar, sala).
* **Gerenciamento de Cenários:** Configuração de cenários com conjuntos de câmeras.
* **Gerenciamento de Eventos:** CRUD de eventos e associação com pessoas.
* **Dashboard:** Indicadores de atendimento, pessoas presentes e atrasos.
* **Acompanhamento por Área:** Visualização em mapa das pessoas detectadas por localização e data.
* **Acompanhamento por Pessoa:** Grafo de caminhamento mostrando a sequência de câmeras.
* **Configurações:** Parâmetros de caminhos de pastas e reconhecimento facial.

## 🛠️ Tecnologias Utilizadas

### Backend (API)
* **Framework:** FastAPI
* **Linguagem:** Python 3.x
* **Banco de Dados:** PostgreSQL
* **Driver do Banco:** psycopg2-binary
* **Visão Computacional:** opencv-python
* **Reconhecimento Facial:** face_recognition

### Frontend (Web)
* **Framework:** Next.js 14+
* **Linguagem:** TypeScript
* **Estilização:** Tailwind CSS

## 🏛️ Arquitetura do Projeto

O projeto segue uma arquitetura de monorepo com separação clara entre frontend e backend:
```
/health-track/
│
├── backend/
│   ├── main.py                    # Ponto de entrada da API FastAPI
│   ├── routes/                    # Controllers/Rotas HTTP
│   │   ├── person_routes.py
│   │   ├── camera_routes.py
│   │   ├── location_routes.py
│   │   ├── scenario_routes.py
│   │   ├── event_routes.py
│   │   ├── dashboard_routes.py
│   │   └── config_routes.py
│   └── services/                  # Lógica de negócio e acesso ao banco
│       ├── database_service.py
│       ├── config_service.py
│       ├── cenario_service.py
│       ├── evento_service.py
│       ├── localizacao_service.py
│       ├── dashboard_service.py
│       ├── facial_service.py
│       └── graph_service.py
│
├── frontend/                      # Aplicação Next.js
│   ├── src/
│   │   ├── app/                   # App Router (páginas)
│   │   ├── components/            # Componentes React
│   │   └── lib/                   # API clients, utils
│   ├── package.json
│   └── next.config.js
│
├── assets/                        # Ícones e imagens
├── banco de dados/                # Scripts SQL
├── requirements.txt
└── README.md
```

## ⚙️ Instalação e Execução

### Pré-requisitos

* [Python 3.8+](https://www.python.org/downloads/)
* [Node.js 18+](https://nodejs.org/)
* [PostgreSQL](https://www.postgresql.org/download/) (v14 ou superior)

### Passo 1: Configurar o Banco de Dados

1. Certifique-se de que o PostgreSQL está em execução.
2. Crie o banco de dados e usuário.
3. Execute o script SQL em `/banco de dados/` para criar o schema e tabelas.
4. Se necessário, ajuste as credenciais em `backend/services/database_service.py`.

### Passo 2: Configurar o Backend
```bash
# Na pasta raiz do projeto
python -m venv venv

# Ativar o ambiente virtual
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### Passo 3: Configurar o Frontend
```bash
cd frontend
npm install
```

### Passo 4: Executar a Aplicação

**Terminal 1 - Backend:**
```bash
# Na pasta raiz, com venv ativado
python -m uvicorn backend.main:app --reload
```
API disponível em: http://localhost:8000
Documentação: http://localhost:8000/docs

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```
Aplicação disponível em: http://localhost:3000

## 📡 Endpoints da API

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/persons` | Lista todas as pessoas |
| GET | `/persons/{id}` | Busca pessoa por ID |
| POST | `/persons` | Cria nova pessoa |
| DELETE | `/persons/{id}` | Remove pessoa |
| GET | `/locations` | Lista todas as localizações |
| GET | `/locations/{id}` | Busca localização por ID |
| POST | `/locations` | Cria nova localização |
| PUT | `/locations/{id}` | Atualiza localização |
| DELETE | `/locations/{id}` | Remove localização |
| GET | `/scenarios` | Lista todos os cenários |
| GET | `/scenarios/{id}` | Busca cenário por ID |
| POST | `/scenarios` | Cria novo cenário |
| PUT | `/scenarios/{id}` | Atualiza cenário |
| DELETE | `/scenarios/{id}` | Remove cenário |
| GET | `/events` | Lista todos os eventos |
| GET | `/events/{id}` | Busca evento por ID |
| POST | `/events` | Cria novo evento |
| PUT | `/events/{id}` | Atualiza evento |
| DELETE | `/events/{id}` | Remove evento |
| GET | `/dashboard/indicators` | Indicadores do dashboard |
| GET | `/dashboard/delayed-persons` | Pessoas com atraso |
| GET | `/config/parameters` | Lista parâmetros |
| POST | `/config/parameters` | Cria parâmetros |
| PUT | `/config/parameters/{id}` | Atualiza parâmetros |

Documentação completa disponível em http://localhost:8000/docs (Swagger UI).

## 🔧 Configuração Inicial

1. Acesse http://localhost:8000/docs
2. Use o endpoint `POST /config/initialize` para criar parâmetros padrão
3. Configure os caminhos de pastas via `PUT /config/parameters/{id}`
4. A aplicação está pronta para uso

## ⚠️ Observações

* **CORS:** O backend está configurado para aceitar requisições de `http://localhost:3000`.
* **Banco de Dados:** Certifique-se de que as tabelas estão atualizadas com todas as colunas necessárias.
* **Webcam:** Para captura facial, verifique permissões de acesso à câmera.

## 📝 Migração da Versão Desktop

Este projeto foi migrado de uma aplicação desktop (Tkinter) para web. As principais mudanças foram:

* `messagebox.showerror()` → `raise HTTPException()`
* Funções de service mantidas, apenas removido o Tkinter
* Adicionada camada de routes (controllers) para expor endpoints HTTP
* Frontend recriado em Next.js/React