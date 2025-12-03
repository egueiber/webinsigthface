# Sistema de Gerenciamento e Acompanhamento Facial v7.0

Este projeto é uma aplicação de desktop desenvolvida em Python e Tkinter para o gerenciamento de pessoas e câmeras, focada em reconhecimento facial e acompanhamento de movimentação em tempo real e histórico.

## 🚀 Funcionalidades Principais

* **Gerenciamento de Pessoas:** CRUD completo de usuários, incluindo um assistente de captura facial guiada por webcam.
* **Gerenciamento de Localizações:** CRUD de localizações, permitindo o upload de mapas (plantas baixas) para cada registro.
* **Gerenciamento de Câmeras:** CRUD de câmeras, permitindo a associação de câmeras a uma localização e a definição de metadados (andar, sala próxima).
* **Acompanhamento por Área:** Visualização em mapa (planta baixa) das pessoas detectadas em uma determinada localização e data.
* **Acompanhamento por Pessoa:** Geração de um grafo de caminhamento que mostra a sequência de câmeras pelas quais uma pessoa passou ao longo de um período.
* **Painel de Parâmetros:** Tela centralizada para configurar todos os caminhos de pastas (fotos, mapas, vídeos) e parâmetros de reconhecimento facial (tolerância, modelo).

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3.x
* **Interface Gráfica (GUI):** Tkinter
* **Tema da GUI:** [Sun Valley ttk Theme (sv-ttk)](https://github.com/rdbende/Sun-Valley-ttk-theme)
* **Banco de Dados:** PostgreSQL
* **Driver do Banco:** `psycopg2-binary`
* **Visão Computacional:** `opencv-python`
* **Reconhecimento Facial:** `face_recognition`
* **Visualização de Grafos:** `networkx` e `matplotlib`
* **Manipulação de Imagens:** `Pillow (PIL)`

## 🏛️ Arquitetura do Projeto

O projeto foi refatorado para seguir uma estrutura que separa a lógica de interface (Frontend) da lógica de negócios e dados (Backend):

```
/Supervisorio_Refatorado/
|
|-- main.py                 (Ponto de entrada da aplicação)
|
|-- /assets/                  (Ícones da interface, ex: pessoa.png)
|
|-- /banco de dados/          (Contém o script SQL para criar o schema e tabelas)
|
|-- /services/                (Lógica de "Backend")
|   |-- database_service.py   (Toda a conexão e queries com o PostgreSQL)
|   |-- config_service.py     (Leitura e escrita da tabela de parâmetros)
|   |-- facial_service.py     (Lógica de CV, ex: data augmentation)
|   |-- graph_service.py      (Criação do grafo com NetworkX e Matplotlib)
|
|-- /ui/                      (Interface de "Frontend" com Tkinter)
|   |-- app_principal.py      (Janela principal, menu e navegação)
|   |-- widgets.py            (Componentes reutilizáveis, ex: Tooltip)
|   |-- home_frame.py         (Tela inicial)
|   |-- pessoa_frames.py      (Telas de listar e cadastrar pessoa)
|   |-- camera_frames.py      (Telas de listar e cadastrar câmera)
|   |-- localizacao_frames.py (Telas de listar e cadastrar localização, com upload de mapa)
|   |-- parametros_frame.py   (Tela de parâmetros)
|   |-- acompanhamento_area.py(Tela do mapa de área)
|   |-- acompanhamento_pessoa.py(Tela do grafo de pessoa)
|
|-- requirements.txt          (Lista de dependências do Python)
|-- README.md                 (Este arquivo)
```

## ⚙️ Instalação e Execução

Siga os passos abaixo para configurar e executar o projeto em sua máquina local.

### Pré-requisitos

* [Python 3.8+](https://www.python.org/downloads/)
* [PostgreSQL](https://www.postgresql.org/download/) (Recomendado v14 ou superior)

### Passo 1: Configurar o Banco de Dados

1.  Certifique-se de que seu servidor PostgreSQL está em execução.
2.  Crie um banco de dados (ex: `postgres`) e um usuário (ex: `supervisorio` com senha `supervisorio101`).
3.  Execute o script SQL localizado na pasta `/banco de dados/` para criar o schema (`sch_supervisorio`) e todas as tabelas (`tb_pessoa`, `tb_cameras`, `tb_parametro`, etc.).
4.  **Importante:** Se suas credenciais do PostgreSQL forem diferentes, ajuste as constantes `DB_NAME`, `DB_USER`, `DB_PASS`, etc., no topo do arquivo `services/database_service.py`.

### Passo 2: Configurar o Ambiente Python

1.  Clone este repositório (ou baixe os arquivos) para sua máquina local.
2.  Abra um terminal na pasta raiz do projeto (`Supervisorio_Refatorado/`).
3.  Crie um ambiente virtual (virtualenv) para isolar as dependências:

    ```bash
    # Cria o ambiente virtual na pasta 'venv'
    python -m venv venv
    ```

4.  Ative o ambiente virtual:
    * **No Windows (cmd/PowerShell):**
        ```bash
        .\venv\Scripts\activate
        ```
    * **No macOS/Linux:**
        ```bash
        source venv/bin/activate
        ```
    *Seu terminal deve agora mostrar `(venv)` no início da linha.*

### Passo 3: Instalar as Dependências

1.  Certifique-se de que o `pip` está atualizado:
    ```bash
    python -m pip install --upgrade pip
    ```
2.  Instale todas as bibliotecas necessárias usando o `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```

### Passo 4: Executar a Aplicação

Com o ambiente virtual ativado e as dependências instaladas, execute o script `main.py`:

```bash
python main.py
```

### Passo 5: Configuração Inicial no App

1.  Ao abrir o aplicativo pela primeira vez, vá para a tela **"Parâmetros"**.
2.  Configure os caminhos de todas as pastas (ex: `Caminho Fotos Clientes`, `Caminho Mapas Câmeras`). O sistema precisa saber onde salvar e ler os arquivos.
3.  Clique em "Salvar Parâmetros".
4.  A aplicação está pronta para ser usada.

## ⚠️ Observações

* **Ícones:** Os ícones da interface (menu lateral) são carregados da pasta `/assets/`. Certifique-se de que os arquivos `.png` (`pessoa.png`, `camera.png`, etc.) estejam presentes nesta pasta.
* **Erros de Câmera:** Se a captura facial não funcionar, verifique se o OpenCV tem permissão para acessar sua webcam e se o ID da câmera (geralmente `0`) está correto em `ui/pessoa_frames.py` (na linha `cv2.VideoCapture(0)`).