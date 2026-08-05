# Health Track UEPG — Sistema Web

Sistema de acompanhamento de pessoas por reconhecimento facial, desenvolvido para a Unimed em parceria com a UEPG.

Esta é a **versão web** do sistema, que substitui a versão desktop original (Python/Tkinter), mantendo compatibilidade com o mesmo banco de dados.

---

## Sumário

- [Arquitetura](#arquitetura)
- [Requisitos](#requisitos)
- [Como rodar (passo a passo)](#como-rodar-passo-a-passo)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Funcionalidades](#funcionalidades)
- [Configuração](#configuração)
- [Fluxo de uso](#fluxo-de-uso)
- [Integração com a Biodoc](#integração-com-a-biodoc)
- [Autenticação e permissões](#autenticação-e-permissões)
- [Pendências conhecidas](#pendências-conhecidas)
- [Solução de problemas](#solução-de-problemas)
- [Notas sobre dados sensíveis](#notas-sobre-dados-sensíveis)

---

## Arquitetura

O sistema é composto por **três componentes independentes** que se comunicam **exclusivamente através do banco de dados**:

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│     MOTOR       │         │   PostgreSQL      │         │  SISTEMA WEB    │
│  (insightface)  │────────▶│                   │◀────────│                 │
│                 │  grava  │  sch_supervisorio │   lê    │ FastAPI+Next.js │
│  Roda no        │         │                   │  grava  │                 │
│  Windows        │         │  Roda no Docker   │         │ Roda no Docker  │
└─────────────────┘         └──────────────────┘         └─────────────────┘
        │                                                         │
        │ processa vídeos                                        │ interface
        ▼                                                         ▼
   arquivos .mp4                                              navegador
```

**Pontos importantes:**

- O **motor** e o **sistema web** não conversam diretamente. O motor processa vídeos e grava as detecções no banco; o sistema web lê essas detecções e as exibe.
- O banco é **compartilhado** com a versão desktop (que ainda existe e é mantida em paralelo). Qualquer alteração de estrutura precisa ser coordenada entre as duas versões.
- O motor roda **nativamente no Windows** hoje (precisa de GPU/CUDA, acesso às pastas de vídeo, e abre uma janela própria). Só o **banco de dados e o backend** rodam em Docker — o frontend roda separado, direto na máquina, com `npm run dev` (ver seção seguinte).
- Existe um plano para containerizar o motor também (documentado em `MIGRACAO_CAMINHOS.md`), mas isso **ainda não foi feito** — veja [Pendências conhecidas](#pendências-conhecidas).

---

## Requisitos

- **Docker Desktop** — para o backend e o banco de dados
- **Node.js 18+** — para rodar o frontend
- **Python 3.11** — apenas se for rodar o motor de reconhecimento localmente (não é necessário para o sistema web)

---

## Como rodar (passo a passo)

### 1. Configurar as variáveis de ambiente (só na primeira vez)

O projeto usa um arquivo `.env` na raiz para guardar segredos (senha do banco, chave de autenticação). Esse arquivo **não é versionado no Git** — copie o modelo e preencha:

```bash
cd C:\caminho\para\face_recognition
copy .env.example .env
```

Abra o `.env` criado e preencha:

```env
DB_PASSWORD=escolha-uma-senha
JWT_SECRET=gere-uma-chave-aleatoria-aqui
```

Para gerar uma chave forte para o `JWT_SECRET`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

> Se o `.env` já existir (ambiente já configurado por outra pessoa), pule este passo.

### 2. Subir o banco de dados e o backend (Docker)

Em um terminal, na raiz do projeto:

```bash
cd C:\caminho\para\face_recognition
docker compose up -d
```

Isso sobe dois containers: `healthtrack-db` (PostgreSQL) e `healthtrack-api` (FastAPI, porta `8000`). O banco já é inicializado com a estrutura de tabelas na primeira subida.

Para ver os logs (útil se algo não subir):

```bash
docker compose logs -f backend
```

Para parar tudo:

```bash
docker compose down
```

> Sempre que o **código do backend** mudar (arquivos `.py`) ou o **Dockerfile** mudar, é preciso reconstruir a imagem:
> ```bash
> docker compose down && docker compose up --build
> ```
> Se só uma variável do `.env` mudou, `docker compose down && docker compose up -d` já basta (não precisa `--build`).

### 3. Rodar o frontend

Em **outro terminal** (o backend precisa continuar rodando no primeiro):

```bash
cd C:\caminho\para\face_recognition\frontend
npm install        # apenas na primeira vez, ou quando dependências mudarem
npm run dev
```

O frontend roda direto na máquina (não é containerizado) e recarrega sozinho a cada alteração de arquivo — não precisa reiniciar depois de colar um arquivo novo, só recarregar a página no navegador.

### 4. Acessar o sistema

Abra **http://localhost:3000** no navegador.

> Na primeira execução, como ainda não existe nenhum usuário cadastrado, a tela de login oferece a criação do primeiro administrador.

### Resumo (depois da primeira configuração)

No dia a dia, são só dois comandos, um em cada terminal:

```bash
# Terminal 1
docker compose up -d

# Terminal 2
cd frontend && npm run dev
```

---

## Estrutura do projeto

```
face_recognition/
├── backend/
│   ├── main.py                   # ponto de entrada da API, registro das rotas
│   ├── routes/                   # endpoints HTTP
│   │   ├── auth_routes.py        # login, setup do primeiro admin
│   │   ├── user_routes.py        # CRUD de usuários (somente admin)
│   │   ├── person_routes.py      # pessoas + upload de fotos
│   │   ├── camera_routes.py
│   │   ├── location_routes.py
│   │   ├── event_routes.py
│   │   ├── scenario_routes.py
│   │   ├── person_event_routes.py
│   │   ├── config_routes.py      # parâmetros (somente admin)
│   │   ├── dashboard_routes.py
│   │   ├── tracking_routes.py    # acompanhamento
│   │   ├── media_routes.py       # serve imagens e frames (rota pública)
│   │   ├── upload_mapa_route.py
│   │   └── biodoc_routes.py
│   └── services/
│       ├── auth_service.py       # JWT, hash de senha, CRUD de usuários
│       ├── auth_dependency.py    # dependências de proteção de rota
│       ├── database_service.py   # acesso ao banco
│       ├── config_service.py     # parâmetros
│       ├── face_crop_service.py  # recorte automático de rosto (fotos da Biodoc)
│       └── biodoc_service.py     # integração com a API da Biodoc
├── frontend/
│   ├── app/                      # páginas (Next.js App Router)
│   │   ├── login/
│   │   ├── dashboard/
│   │   ├── pessoas/
│   │   ├── usuarios/
│   │   └── ...
│   ├── components/
│   │   ├── AppShell.tsx          # layout + proteção de rotas
│   │   ├── Sidebar.tsx
│   │   └── ui/                   # componentes shadcn/ui
│   └── lib/
│       └── api.ts                # camada de comunicação com o backend
├── database/
│   └── scriptBancoDados.sql      # estrutura do banco
├── .env                          # segredos reais (NÃO versionado)
├── .env.example                  # modelo do .env (esse sim vai pro Git)
├── docker-compose.yml
├── Dockerfile.backend
└── requirements.txt
```

---

## Funcionalidades

### Cadastros
- **Pessoas** — dados cadastrais, carteirinha Biodoc e fotos (upload de arquivo ou busca automática na Biodoc). Na listagem, ações rápidas por linha: registrar um novo evento para a pessoa (já pré-selecionada) e encerrar a entrada em andamento (com opção de horário atual ou manual).
- **Câmeras** — nome, localização, andar, sala, notas de identificação
- **Localizações** — com upload de imagem de mapa
- **Eventos** — nome e duração (usada para calcular a saída prevista automaticamente)
- **Cenários** — agrupam as câmeras que o motor deve processar
- **Pessoa–Eventos** — associa pessoas a eventos, com busca de pessoa por nome (em vez de lista longa) e cálculo automático da saída prevista
- **Parâmetros** — caminhos de pastas, configurações do motor e credenciais da Biodoc. **Acesso restrito a administradores.**
- **Usuários** — gerenciamento de acesso. **Acesso restrito a administradores.**

### Acompanhamento
- **Por Área** — todas as detecções numa localização em determinada data, com visualização do frame de cada detecção
- **Por Pessoa** — trajetória cronológica da pessoa entre as câmeras, com data/hora e frame da detecção

### Dashboard
Indicadores de atendimento e atrasos, alimentados pelos registros de Pessoa–Eventos.

---

## Configuração

### Variáveis de ambiente

A maior parte da configuração fica fixa no `docker-compose.yml`. Os dois valores sensíveis (senha do banco e chave de autenticação) vêm do arquivo `.env` — veja [Como rodar](#1-configurar-as-variáveis-de-ambiente-só-na-primeira-vez).

| Variável | Onde é definida | Descrição | Valor atual |
|---|---|---|---|
| `DB_PASSWORD` | `.env` | Senha do PostgreSQL (banco e backend) | — (ver `.env`) |
| `JWT_SECRET` | `.env` | Chave que assina os tokens de login | — (ver `.env`, chave aleatória) |
| `DB_HOST` | `docker-compose.yml` | Host do banco | `db` |
| `DB_PORT` | `docker-compose.yml` | Porta do banco | `5432` |
| `DB_NAME` | `docker-compose.yml` | Nome do banco (backend) | `health-track-oficial` |
| `DB_USER` | `docker-compose.yml` | Usuário do banco | `postgres` |
| `JWT_EXPIRE_HOURS` | `docker-compose.yml` | Validade do token (horas) | `8` |
| `LOGIN_MAX_TENTATIVAS` | `docker-compose.yml` | Tentativas antes do bloqueio | `5` |
| `LOGIN_JANELA_SEGUNDOS` | `docker-compose.yml` | Janela de contagem | `300` |
| `LOGIN_BLOQUEIO_SEGUNDOS` | `docker-compose.yml` | Duração do bloqueio | `300` |
| `FOTOS_DIR` | `docker-compose.yml` | Pasta de fotos no container | `/app/fotos` |
| `MAPAS_DIR` | `docker-compose.yml` | Pasta de mapas no container | `/app/mapas` |
| `VIDEOMARCACOES_DIR` | `docker-compose.yml` | Pasta de vídeos marcados no container | `/app/videomarcacoes` |

> ⚠️ **Nunca commite o `.env`** — ele já está no `.gitignore`. Para configurar um ambiente novo, copie sempre o `.env.example`.

### Parâmetros (cadastrados pela interface, tela restrita a admin)

Os caminhos de pastas ficam no banco, na tabela `tb_parametro`, e são lidos **pelo motor**. Como o motor roda no Windows hoje, os caminhos cadastrados lá usam o formato `C:\...` — **diferente** dos caminhos internos do container Docker (`/app/fotos`, etc.) usados pelo backend web. Essa diferença é justamente a origem da pendência descrita em [Pendências conhecidas](#pendências-conhecidas).

---

## Fluxo de uso

A ordem importa — cada etapa depende da anterior já existir:

1. **Parâmetros** — configure os caminhos das pastas, modelo de detecção e tolerância (tela de administrador)
2. **Localizações** — cadastre as áreas monitoradas
3. **Câmeras** — cadastre vinculando a uma localização
   > O **nome da câmera** deve ser idêntico ao nome da pasta de vídeos que o motor vai ler.
4. **Cenário** — crie e vincule as câmeras que devem ser monitoradas nele
5. **Eventos** — cadastre os tipos de atendimento (com duração esperada)
6. **Pessoas** — cadastre com foto (essencial: sem foto o motor não identifica ninguém)
7. **Pessoa–Eventos** — registre a entrada da pessoa, deixando a saída efetiva em branco
   > **Só pessoas com evento em andamento (sem saída registrada) são reconhecidas pelo motor.**
8. **Motor** — roda o processamento de vídeo, de forma independente (fora do sistema web)
9. **Acompanhamento / Dashboard** — visualize as detecções e os indicadores

Ao final do atendimento, encerre a entrada da pessoa (pela tela de Pessoas ou de Pessoa–Eventos) — isso tira a pessoa do reconhecimento ativo e a conta como atendida no Dashboard.

---

## Integração com a Biodoc

A Biodoc é o serviço de biometria facial usado pela Unimed. A integração permite **buscar a foto já cadastrada** de um beneficiário pela carteirinha, evitando cadastro duplicado.

**Como funciona:**
1. Configure a URL e o token da API em **Parâmetros → Integração Biodoc** (tela de administrador)
2. No cadastro da pessoa, informe o número da **Carteirinha (Biodoc)**
3. Na aba **Biodoc**, clique em "Buscar foto da Biodoc"
4. A foto é baixada, tem o **rosto recortado automaticamente** (corrige fotos onde a pessoa aparece de longe) e é salva na pasta de fotos da pessoa, pronta para o motor usar

**Ambientes:**
- Sandbox: `https://api.sandbox.biodoc.com.br/api`
- Produção: `https://api.biodoc.com.br/api`

O token é fornecido pela Biodoc à empresa contratante (Unimed). **Testado e funcionando** com carteirinha real no ambiente sandbox.

> Um erro de credencial da própria Biodoc (token inválido/expirado do lado deles) retorna código HTTP 502 do backend, não 401 — isso é proposital, para não ser confundido com uma sessão expirada do Health Track e deslogar o usuário à toa.

---

## Autenticação e permissões

- **Login próprio** com JWT (validade padrão: 8 horas)
- Senhas armazenadas com **hash bcrypt** (nunca em texto)
- **Rate limit** no login: bloqueia após 5 tentativas falhas (por IP e por usuário), com bloqueio de 5 minutos
- **Dois papéis:**
  - `admin` — acesso total, incluindo **Usuários** e **Parâmetros**
  - `user` — acesso às telas operacionais do dia a dia (Pessoas, Câmeras, Localizações, Eventos, Cenários, Pessoa–Eventos, Acompanhamento, Dashboard)
- O primeiro administrador é criado na tela de login, quando não há nenhum usuário cadastrado
- Proteção contra desativar/rebaixar o **último administrador ativo**
- A restrição de admin em **Usuários** e **Parâmetros** existe em três camadas: o backend recusa quem não é admin (a proteção que realmente importa), o menu lateral esconde o item pra quem não é admin, e a própria tela mostra um aviso se alguém acessar a URL direto sem ser admin

> As rotas de mídia (`/media/*`) **não exigem autenticação**, porque imagens carregadas via `<img>` não enviam o cabeçalho `Authorization`. É uma exceção deliberada, não uma falha — nenhum dado sensível é exposto por esse caminho além da própria imagem, que já exige conhecer o caminho exato do arquivo.

---

## Pendências conhecidas

### 🔴 Integração de pastas entre o backend web e o motor (parcialmente resolvida)
Os caminhos de pasta já foram **padronizados** (`/app/fotos`, `/app/mapas`, `/app/videomarcacoes`, etc. — ver `MIGRACAO_CAMINHOS.md`), preparando o terreno para o motor rodar em Docker também. **Mas isso ainda não aconteceu**: o motor hoje roda nativo no Windows, com interface gráfica própria (Tkinter), então ele não enxerga os volumes internos do Docker automaticamente. Enquanto isso não for resolvido, fotos enviadas pela web podem precisar ser copiadas manualmente para onde o motor lê:
```bash
docker cp <origem> healthtrack-api:/app/fotos/<pasta_pessoa>
```
**Para resolver de vez**, falta (documentado em `MIGRACAO_CAMINHOS.md`): reescrever o motor numa versão sem interface gráfica (headless), containerizá-lo com suporte a GPU (NVIDIA Container Toolkit), e então ele e o backend passam a compartilhar os mesmos volumes nomeados de verdade.

### 🟡 Nomes de banco divergentes no `docker-compose.yml`
O serviço `db` cria o Postgres com `POSTGRES_DB: health-track-supervisorio`, mas o `backend` se conecta em `DB_NAME: health-track-oficial` — nomes diferentes. Não quebra nada hoje porque o volume do banco já existe (criado uma vez, no passado, com o nome que o backend espera) e `POSTGRES_DB` só tem efeito na primeira inicialização de um volume vazio. **Risco:** se o volume for apagado (`docker compose down -v`) e recriado do zero, o backend não vai encontrar o banco `health-track-oficial`. Vale corrigir os dois nomes para o mesmo valor.

### 🟡 Encoding de acentos
Nomes com acento gravados diretamente via terminal (cmd/psql) podem ficar corrompidos e quebrar a leitura do motor. Cadastros feitos pela interface web aparentam estar corretos — pendente de confirmação com um teste dedicado.

### 🟡 Ambiente de deploy definitivo
A definir com a TI da Unimed:
- O banco será o PostgreSQL corporativo deles ou um dedicado?
- Docker é permitido nos servidores?
- Isso também define a solução final do problema de integração de pastas acima.

---

## Solução de problemas

### "Não foi possível conectar ao servidor"
O backend não está rodando. Suba com `docker compose up -d` e confira `docker compose logs backend`.

### Erro `ImportError: libGL.so.1: cannot open shared object file`
Faltam bibliotecas de sistema que o `opencv-python` precisa (usadas no recorte de rosto da Biodoc). Já corrigido no `Dockerfile.backend` atual — se aparecer de novo após atualizar dependências, reconstrua sem cache:
```bash
docker compose build --no-cache backend && docker compose up -d
```

### Motor não conecta no banco / erro de encoding estranho
Verifique se há um **PostgreSQL nativo instalado no Windows** disputando a porta 5432:
```bash
netstat -ano | findstr :5432
sc query | findstr -i postgres
```
Se houver, pare o serviço (como administrador):
```bash
net stop postgresql-x64-<versao>
```
> Este foi um problema real e demorado de diagnosticar: o erro aparecia como falha de encoding (`0xe7`), mas era a mensagem "autenticação falhou" em português vinda do PostgreSQL errado.

### Motor mostra "MEMORIA PRONTA: 0 rostos"
A pessoa não tem foto na pasta que o motor lê, ou não tem **evento em andamento** cadastrado em Pessoa–Eventos (sem saída registrada).

### Detecções não aparecem no Acompanhamento
- Confirme que o **nome da câmera** no cadastro é idêntico ao nome da pasta de vídeos
- Use um **período de datas amplo** no filtro
- Desmarque "Somente identificadas" para ver todos os registros

### Botão "Ver frame" não mostra a imagem
O arquivo do frame não existe no servidor para aquela data. Os frames ficam em:
```
<caminhoVideoMarcacoes>/<camera>/<data>/<pasta_pessoa>/<HH-MM-SS_mmm>.jpg
```

### Erro ao instalar dependências do motor
O motor exige **Python 3.11** (não funciona no 3.13). Use um ambiente virtual:
```bash
py -3.11 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

## Notas sobre dados sensíveis

Este sistema processa **dados biométricos e de saúde** de pacientes reais, protegidos pela LGPD. Ao trabalhar com backups ou fotos:

- Nunca versione dados reais no Git
- Nunca versione o arquivo `.env` (senhas e chaves reais) — só o `.env.example`
- Não compartilhe backups fora do ambiente autorizado
- Remova cópias locais após os testes
- Evite prints de tela com dados reais em documentação

---

## Créditos

Desenvolvido para a Unimed em parceria com a Universidade Estadual de Ponta Grossa (UEPG).
