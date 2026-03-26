# Health Track — Sistema de Gerenciamento e Acompanhamento Facial

> Unimed · UEPG — v8.0

---

## Arquitetura

O sistema é composto por três serviços:

| Serviço | Tecnologia | Como roda |
|---|---|---|
| Banco de dados | PostgreSQL 15 | Docker |
| Backend / API | Python + FastAPI | Docker |
| Frontend | Next.js 15 | Local (`npm run dev`) |

> O Docker sobe o banco e o backend automaticamente. O frontend roda localmente com npm.

---

## Pré-requisitos

| Ferramenta | Versão | Download |
|---|---|---|
| Docker Desktop | Qualquer | https://docker.com/products/docker-desktop |
| Git | 2.x+ | https://git-scm.com/download/win |
| Node.js | 20+ (LTS) | https://nodejs.org |

---

## Instalação

### 1. Clonar o repositório

```bash
git clone <URL_DO_REPOSITORIO>
cd face_recognition
git checkout feature/api
git pull
```

### 2. Subir o backend com Docker

Na raiz do repositório:

```bash
docker compose up --build
```

> Na primeira execução o processo pode levar de 10 a 20 minutos. O banco de dados é criado e populado automaticamente.

Aguarde as seguintes mensagens para confirmar que tudo subiu:

```
healthtrack-db   | database system is ready to accept connections
healthtrack-api  | INFO:     Uvicorn running on http://0.0.0.0:8000
```

Confirme que a API está no ar: http://localhost:8000/docs

### 3. Rodar o frontend

Em um segundo terminal:

```bash
cd frontend
npm install
npm run dev
```

Acesse: http://localhost:3000

---

## Uso no dia a dia

Sempre que for trabalhar no projeto, abra dois terminais:

**Terminal 1 — Backend**
```bash
cd face_recognition
docker compose up
```

**Terminal 2 — Frontend**
```bash
cd face_recognition/frontend
npm run dev
```

**Encerrar o ambiente**
```bash
docker compose down
```

---

## Módulos do sistema

| Módulo | URL | Descrição |
|---|---|---|
| Dashboard | `/dashboard` | Indicadores de atendimento e atrasos |
| Pessoas | `/pessoas` | Cadastro de pacientes/usuários |
| Câmeras | `/cameras` | Gerenciamento de câmeras |
| Localizações | `/localizacoes` | Áreas monitoradas e plantas baixas |
| Eventos | `/eventos` | Tipos de evento e duração esperada |
| Cenários | `/cenarios` | Grupos de câmeras para processamento |
| Parâmetros | `/parametros` | Configuração do motor de reconhecimento |
| Acomp. por Área | `/acompanhamento-area` | Mapa de presença por localização |
| Acomp. por Pessoa | `/acompanhamento-pessoa` | Grafo de caminhamento individual |

---

## Tecnologias

**Backend**
- Python 3.9 + FastAPI + Uvicorn
- PostgreSQL 15
- face_recognition + OpenCV
- NetworkX (grafos de caminhamento)

**Frontend**
- Next.js 15 + TypeScript
- Tailwind CSS v4
- shadcn/ui (Radix UI)
- Lucide React + Sonner

---

## Estrutura do projeto

```
face_recognition/
├── Dockerfile.backend        # imagem do FastAPI
├── docker-compose.yml        # backend + PostgreSQL
├── requirements.txt          # dependências Python
├── backend/
│   ├── main.py               # entrada da API + CORS
│   ├── routes/               # endpoints HTTP
│   └── services/             # lógica de negócio e banco
├── database/
│   └── scriptBancoDados.sql  # schema criado automaticamente
└── frontend/
    ├── app/                  # páginas Next.js
    ├── components/ui/        # componentes shadcn/ui
    ├── lib/api.ts            # cliente HTTP
    └── .env.local            # configuração de ambiente
```

---

## Observações

- **Captura facial:** realizada pelo aplicativo desktop legado (Python/Tkinter). O frontend web gerencia apenas os dados cadastrais.
- **Acompanhamento por Área e por Pessoa:** em desenvolvimento — aguardam endpoints adicionais no backend.
- **Reset do banco:** para apagar todos os dados e recriar do zero: `docker compose down -v`
