# -*- coding: utf-8 -*-
"""
Software de Gerenciamento v6.4
Módulos:
- CRUD Pessoas (com captura facial)
- CRUD Câmeras (com upload de mapa)
- CRUD Parâmetros (Configuração centralizada)
- Acompanhamento por Área (Funcional)
- Acompanhamento por Pessoa (com Grafo de Caminhamento)

(FIX V6.4)
- (CRÍTICO) Corrige o erro de "comentário não fechado" da V6.3.


(UPDATE V6.3)
- Rótulo do nó no grafo exibe timestamp (Dia/Mês HH:MM:SS).
- Lógica de ordenação e revisita de nós já usa o timestamp.

(FIX V6.2)
- Corrige 'TypeError: node_list' para 'nodelist'.

(FIX V6.1)
- Adiciona botão explícito "Gerar Grafo".

(UPDATE V6.0)
- Adiciona "andarCamera" e "nrsalaproximaCamera".
- Adiciona Acompanhamento por Pessoa.

Requisitos:
pip install opencv-python face_recognition pandas Pillow psycopg2-binary
pip install matplotlib networkx mplcursors
"""
import tkinter as tk
from tkinter import ttk 
from tkinter import messagebox, filedialog
import cv2
import face_recognition
import os
from PIL import Image, ImageTk
import re
import psycopg2
import shutil 
from datetime import datetime 

# (NOVO V6.0) Imports para o Grafo
import networkx as nx
import matplotlib
matplotlib.use("TkAgg") # Informa ao matplotlib para usar o backend do Tkinter
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import mplcursors # Para o tooltip do grafo

# --- Configuração do Banco de Dados ---
DB_NAME = "postgres"
DB_USER = "supervisorio"
DB_PASS = "supervisorio101"
DB_HOST = "localhost"
DB_PORT = 5432

# --- Funções de Inicialização e Parâmetros ---
PADDING_PIXELS = 60 
def get_db_connection():
    """Tenta estabelecer uma conexão com o banco de dados."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except Exception as e:
        messagebox.showerror("Erro de Banco de Dados", f"Não foi possível conectar ao PostgreSQL:\n{e}")
        return None

def inicializar_db_parametros():
    """Garante que a tabela de parâmetros tenha pelo menos uma linha de configuração."""
    print("Verificando parâmetros...")
    conn = get_db_connection()
    if conn is None:
        return

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM sch_supervisorio.tb_parametro")
            count = cur.fetchone()[0]
            
            if count == 0:
                print("Inicializando parâmetros padrão no banco de dados...")
                cur.execute('INSERT INTO sch_supervisorio.tb_parametro ("idParametro") VALUES (DEFAULT)')
                conn.commit()
                print("Parâmetros inicializados.")
            else:
                print("Parâmetros já existem.")
                
    except Exception as e:
        conn.rollback()
        # (MODIFICADO V6.0) Verifica se o erro é de colunas faltando (erro comum)
        if "column" in str(e) and "does not exist" in str(e):
             messagebox.showerror("Erro de Banco de Dados", f"Erro: A estrutura da tabela 'tb_parametro' parece estar desatualizada.\n{e}")
        else:
            messagebox.showerror("Erro Crítico de DB", f"Não foi possível ler ou inicializar a 'tb_parametro'.\n{e}")
        return
    finally:
        conn.close()
        
def carregar_parametros_db():
    """Carrega a primeira linha de parâmetros do banco de dados."""
    sql = """
        SELECT "idParametro", "caminhoFotosClientes", "caminhoMapas",
               "caminhoVideoAProcessar", "caminhoVideoProcessados",
               "caminhoVideoMarcoes", "intevalorFrames", "escalaImagem",
               "modeloDeteccao", "toleranciaReconhecimento", "gerarvideomarcacoes"
        FROM sch_supervisorio.tb_parametro LIMIT 1
    """
    conn = get_db_connection()
    if conn is None: 
        return None
    
    parametros = None
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            result = cur.fetchone()
            if result:
                parametros = {
                    "id": result[0],
                    "fotos": result[1],
                    "mapas": result[2],
                    "videos_a_processar": result[3],
                    "videos_processados": result[4],
                    "video_marcoes": result[5],
                    "intervalo_frames": result[6],
                    "escala_imagem": result[7],
                    "modelo_deteccao": result[8],
                    "tolerancia": result[9],
                    "gerar_marcoes": result[10] 
                }
    except Exception as e:
        messagebox.showerror("Erro de Consulta", f"Erro ao carregar parâmetros:\n{e}\n\nCertifique-se que a 'tb_parametro' foi atualizada com TODOS os campos.")
    finally:
        conn.close()
    
    if parametros is None:
        messagebox.showerror("Erro Crítico", "Não foi possível carregar os parâmetros de configuração do banco.")
        
    return parametros

def salvar_parametros_db(param_id, caminho_fotos, caminho_mapas, 
                         videos_a_processar, videos_processados, 
                         video_marcoes, intervalo_frames, escala_imagem, 
                         modelo_deteccao, tolerancia, gerar_marcoes):
    """Atualiza a linha de parâmetros no banco de dados."""
    sql = """
        UPDATE sch_supervisorio.tb_parametro
        SET "caminhoFotosClientes" = %s, "caminhoMapas" = %s,
            "caminhoVideoAProcessar" = %s, "caminhoVideoProcessados" = %s,
            "caminhoVideoMarcoes" = %s, "intevalorFrames" = %s, "escalaImagem" = %s,
            "modeloDeteccao" = %s, "toleranciaReconhecimento" = %s,
            "gerarvideomarcacoes" = %s
        WHERE "idParametro" = %s
    """
    conn = get_db_connection()
    if conn is None:
        return False
    
    success = False
    try:
        with conn.cursor() as cur:
            params = (caminho_fotos, caminho_mapas, videos_a_processar, videos_processados,
                      video_marcoes, intervalo_frames, escala_imagem, modelo_deteccao, 
                      tolerancia, gerar_marcoes, param_id)
            cur.execute(sql, params)
        conn.commit()
        success = True
        print("Parâmetros salvos no banco com sucesso.")
    except Exception as e:
        conn.rollback()
        messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar os parâmetros:\n{e}")
    finally:
        conn.close()
    return success

# --- Funções Auxiliares do Banco de Dados (Pessoa) ---
def listar_pessoas_db(filtro_nome=""):
    sql = """
        SELECT "idPessoa", "nomePessoa", "documentoPessoa" 
        FROM sch_supervisorio.tb_pessoa
        WHERE "nomePessoa" ILIKE %s
        ORDER BY "nomePessoa"
    """
    conn = get_db_connection()
    if conn is None: return []
    resultados = []
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (f"%{filtro_nome}%",))
            resultados = cur.fetchall()
    except Exception as e:
        messagebox.showerror("Erro de Consulta", f"Erro ao listar pessoas:\n{e}")
    finally:
        conn.close()
    return resultados

def get_pessoa_por_id_db(pessoa_id):
    sql = 'SELECT "nomePessoa", "documentoPessoa" FROM sch_supervisorio.tb_pessoa WHERE "idPessoa" = %s'
    conn = get_db_connection()
    if conn is None: return None
    pessoa = None
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (pessoa_id,))
            result = cur.fetchone()
            if result:
                pessoa = {"nome": result[0], "documento": result[1]}
    except Exception as e:
        messagebox.showerror("Erro de Consulta", f"Erro ao buscar pessoa ID {pessoa_id}:\n{e}")
    finally:
        conn.close()
    return pessoa

def salvar_pessoa_no_banco(nome, documento, nome_pasta_fotos, pessoa_id=None):
    """
    (V4.4) Salva apenas o NOME DA PASTA (ex: "Joao_Silva_123")
    na coluna "fotosPessoa", e não o caminho completo.
    """
    conn = get_db_connection()
    if conn is None: return False
    try:
        if pessoa_id:
            sql = """
                UPDATE sch_supervisorio.tb_pessoa
                SET "nomePessoa" = %s, "documentoPessoa" = %s, "fotosPessoa" = %s
                WHERE "idPessoa" = %s
            """
            params = (nome, documento, nome_pasta_fotos, pessoa_id)
        else:
            sql = """
                INSERT INTO sch_supervisorio.tb_pessoa
                ("documentoPessoa", "nomePessoa", "fotosPessoa")
                VALUES (%s, %s, %s)
            """
            params = (documento, nome, nome_pasta_fotos)
        with conn.cursor() as cur:
            cur.execute(sql, params)
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        if "unique constraint" in str(e):
             messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar: O documento '{documento}' já está cadastrado.")
        else:
             messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar os dados no banco:\n{e}")
        return False
    finally:
        conn.close()

def excluir_pessoa_db(pessoa_id, pasta_fotos_completa):
    """
    (V4.4) Recebe o caminho COMPLETO para a pasta de fotos,
    pois o banco não armazena mais o caminho.
    """
    conn = get_db_connection()
    if conn is None: return False
    sql = 'DELETE FROM sch_supervisorio.tb_pessoa WHERE "idPessoa" = %s'
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (pessoa_id,))
        conn.commit()
        if pasta_fotos_completa and os.path.exists(pasta_fotos_completa):
            try:
                shutil.rmtree(pasta_fotos_completa)
                print(f"Pasta de fotos excluída: {pasta_fotos_completa}")
            except Exception as e_fs:
                messagebox.showwarning("Aviso", f"Pessoa excluída do banco, mas falha ao excluir pasta de fotos:\n{e_fs}")
        return True
    except Exception as e:
        conn.rollback()
        messagebox.showerror("Erro ao Excluir", f"Não foi possível excluir a pessoa:\n{e}")
        return False
    finally:
        conn.close()

# --- (MODIFICADO V6.0) Funções Auxiliares do Banco de Dados (Câmera) ---
def listar_cameras_db(filtro_nome=""):
    sql = """
        SELECT "idCamera", "nomeCamera", "localizacaoCamera" 
        FROM sch_supervisorio.tb_cameras
        WHERE "nomeCamera" ILIKE %s
        ORDER BY "nomeCamera"
    """
    conn = get_db_connection()
    if conn is None: return []
    resultados = []
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (f"%{filtro_nome}%",))
            resultados = cur.fetchall()
    except Exception as e:
        messagebox.showerror("Erro de Consulta", f"Erro ao listar câmeras:\n{e}")
    finally:
        conn.close()
    return resultados

def get_camera_por_id_db(camera_id):
    # (MODIFICADO V6.0) Adiciona as novas colunas
    sql = """
        SELECT "nomeCamera", "localizacaoCamera", "mapaCamera", 
               "andarCamera", "nrsalaproximaCamera"
        FROM sch_supervisorio.tb_cameras WHERE "idCamera" = %s
    """
    conn = get_db_connection()
    if conn is None: return None
    camera = None
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (camera_id,))
            result = cur.fetchone()
            if result:
                camera = {
                    "nome": result[0], 
                    "localizacao": result[1], 
                    "mapa_path": result[2],
                    "andar": result[3],
                    "nrsala": result[4]
                }
    except Exception as e:
        # (MODIFICADO V6.0) Erro comum se o PASSO 2 (ALTER TABLE) falhou
        if "column" in str(e) and "does not exist" in str(e):
            messagebox.showerror("Erro de Banco de Dados", f"Erro: A tabela 'tb_cameras' está desatualizada.\n{e}\n\nPor favor, execute o script ALTER TABLE para adicionar as colunas 'andarCamera' e 'nrsalaproximaCamera'.")
        else:
            messagebox.showerror("Erro de Consulta", f"Erro ao buscar câmera ID {camera_id}:\n{e}")
    finally:
        conn.close()
    return camera

def salvar_camera_no_banco(nome, localizacao, caminho_mapa, andar, nrsala, camera_id=None):
    """
    (MODIFICADO V6.0) Adiciona 'andar' e 'nrsala' e a validação de duplicidade.
    """
    conn = get_db_connection()
    if conn is None: return False
    
    try:
        with conn.cursor() as cur:
            # (NOVO V6.0) Validação de duplicidade
            cur.execute(
                'SELECT "idCamera", "nomeCamera" FROM sch_supervisorio.tb_cameras WHERE "andarCamera" = %s AND "nrsalaproximaCamera" = %s',
                (andar, nrsala)
            )
            conflito = cur.fetchone()
            
            # Se encontrou um conflito, verifica se NÃO é o próprio registro sendo editado
            if conflito and (camera_id is None or conflito[0] != camera_id):
                messagebox.showerror("Erro de Validação", f"Duplicidade detectada.\nA câmera '{conflito[1]}' (ID: {conflito[0]}) já está registrada para o Andar {andar} e Sala {nrsala}.")
                return False

            if camera_id:
                sql = """
                    UPDATE sch_supervisorio.tb_cameras
                    SET "nomeCamera" = %s, "localizacaoCamera" = %s, "mapaCamera" = %s,
                        "andarCamera" = %s, "nrsalaproximaCamera" = %s
                    WHERE "idCamera" = %s
                """
                params = (nome, localizacao, caminho_mapa, andar, nrsala, camera_id)
            else:
                sql = """
                    INSERT INTO sch_supervisorio.tb_cameras
                    ("nomeCamera", "localizacaoCamera", "mapaCamera", "andarCamera", "nrsalaproximaCamera")
                    VALUES (%s, %s, %s, %s, %s)
                """
                params = (nome, localizacao, caminho_mapa, andar, nrsala)
            
            cur.execute(sql, params)
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        messagebox.showerror("Erro ao Salvar Câmera", f"Não foi possível salvar a câmera no banco:\n{e}")
        return False
    finally:
        conn.close()

def excluir_camera_db(camera_id, caminho_mapa):
    conn = get_db_connection()
    if conn is None: return False
    sql = 'DELETE FROM sch_supervisorio.tb_cameras WHERE "idCamera" = %s'
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (camera_id,))
        conn.commit()
        if caminho_mapa and os.path.exists(caminho_mapa):
            try:
                os.remove(caminho_mapa)
                print(f"Arquivo de mapa excluído: {caminho_mapa}")
            except Exception as e_fs:
                messagebox.showwarning("Aviso", f"Câmera excluída do banco, but falha ao excluir arquivo de mapa:\n{e_fs}")
        return True
    except Exception as e:
        conn.rollback()
        messagebox.showerror("Erro ao Excluir", f"Não foi possível excluir a câmera:\n{e}")
        return False
    finally:
        conn.close()

# --- Funções de BD para Acompanhamento ---
def get_localizacoes_db():
    """Busca localizações únicas e seus mapas para o dropdown."""
    sql = """
        SELECT DISTINCT "localizacaoCamera", "mapaCamera" 
        FROM sch_supervisorio.tb_cameras
        ORDER BY "localizacaoCamera"
    """
    conn = get_db_connection()
    if conn is None: return {}
    localizacoes = {}
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            resultados = cur.fetchall()
            localizacoes = {loc: mapa for loc, mapa in resultados}
    except Exception as e:
        messagebox.showerror("Erro de Consulta", f"Erro ao listar localizações:\n{e}")
    finally:
        conn.close()
    return localizacoes

def get_dados_acompanhamento_db(localizacao, data_filtro):
    """
    (V4.9) SQL simplificado para Acompanhamento por Área.
    """
    sql = """
        SELECT 
            p."nomePessoa", 
            v.datahoraprocessamento, 
            v."tempoMarcacaoSegundos"
        FROM sch_supervisorio.tb_videos_processados v
        JOIN sch_supervisorio.tb_cameras c ON v."nomeCamera" = c."nomeCamera"
        JOIN sch_supervisorio.tb_pessoa p ON p."fotosPessoa" = v."nomePastaPessoa"
        WHERE c."localizacaoCamera" = %s 
        AND v.datahoraprocessamento::date = %s
        ORDER BY v.datahoraprocessamento;
    """
    conn = get_db_connection()
    if conn is None: return []
    resultados = []
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (localizacao, data_filtro))
            resultados = cur.fetchall()
    except Exception as e:
        messagebox.showerror("Erro de Consulta", f"Erro ao buscar dados de acompanhamento:\n{e}")
    finally:
        conn.close()
    return resultados

# (NOVO V6.0) Funções de BD para Grafo de Caminhamento
def get_pessoas_por_periodo_db(data_inicio, data_fim):
    """
    (NOVO V6.0) Busca pessoas únicas que apareceram no intervalo de datas.
    """
    sql = """
        SELECT DISTINCT p."nomePessoa"
        FROM sch_supervisorio.tb_videos_processados v
        JOIN sch_supervisorio.tb_pessoa p ON v."nomePastaPessoa" = p."fotosPessoa"
        WHERE v.datahoraprocessamento::date BETWEEN %s AND %s
        ORDER BY p."nomePessoa";
    """
    conn = get_db_connection()
    if conn is None: return []
    resultados = []
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (data_inicio, data_fim))
            # Converte lista de tuplas [('Nome1',), ('Nome2',)] para lista de strings ['Nome1', 'Nome2']
            resultados = [row[0] for row in cur.fetchall()]
    except Exception as e:
        messagebox.showerror("Erro de Consulta", f"Erro ao buscar pessoas por período:\n{e}")
    finally:
        conn.close()
    return resultados

def get_caminho_pessoa_db(nome_pessoa, data_inicio, data_fim):
    """
    (NOVO V6.0) Busca a sequência de câmeras por onde uma pessoa passou.
    (MODIFICADO V6.3) A consulta já ordena pelo timestamp completo,
    o que define a sequência de eventos corretamente.
    """
    sql = """
        SELECT 
            v.datahoraprocessamento, 
            c."nomeCamera", 
            c."andarCamera", 
            c."nrsalaproximaCamera"
        FROM sch_supervisorio.tb_videos_processados v
        JOIN sch_supervisorio.tb_pessoa p ON v."nomePastaPessoa" = p."fotosPessoa"
        JOIN sch_supervisorio.tb_cameras c ON v."nomeCamera" = c."nomeCamera"
        WHERE p."nomePessoa" = %s
        AND v.datahoraprocessamento::date BETWEEN %s AND %s
        ORDER BY v.datahoraprocessamento;
    """
    conn = get_db_connection()
    if conn is None: return []
    resultados = []
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (nome_pessoa, data_inicio, data_fim))
            resultados = cur.fetchall()
    except Exception as e:
        messagebox.showerror("Erro de Consulta", f"Erro ao buscar caminhamento da pessoa:\n{e}")
    finally:
        conn.close()
    return resultados

# --- Função de Data Augmentation ---
def gerar_aumentos_de_dados(caminho_pasta):
    print(f"Iniciando aumento de dados para a pasta: {caminho_pasta}")
    arquivos_originais = [f for f in os.listdir(caminho_pasta) if f.endswith(('.jpg', '.png'))]
    
    for nome_arquivo in arquivos_originais:
        caminho_imagem = os.path.join(caminho_pasta, nome_arquivo)
        imagem = cv2.imread(caminho_imagem)
        
        if imagem is None: 
            continue

        nome_base, extensao = os.path.splitext(nome_arquivo)

        imagem_distante_75 = cv2.resize(imagem, (0, 0), fx=0.75, fy=0.75)
        novo_nome_75 = f"{nome_base}_distante_75{extensao}"
        cv2.imwrite(os.path.join(caminho_pasta, novo_nome_75), imagem_distante_75)

        imagem_distante_50 = cv2.resize(imagem, (0, 0), fx=0.5, fy=0.5)
        novo_nome_50 = f"{nome_base}_distante_50{extensao}"
        cv2.imwrite(os.path.join(caminho_pasta, novo_nome_50), imagem_distante_50)

        imagem_desfocada = cv2.GaussianBlur(imagem, (3, 3), 0)
        novo_nome_desfocado = f"{nome_base}_desfocado{extensao}"
        cv2.imwrite(os.path.join(caminho_pasta, novo_nome_desfocado), imagem_desfocada)
        
    print("Aumento de dados concluído.")
    
    
# --- Módulo 0: Tela Home (Padrão) ---
class HomeFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="Health Track Unimed - UEPG", font=("Arial", 24, "bold"))
        label.pack(pady=100)
        label2 = tk.Label(self, text="Selecione um módulo no menu lateral para começar.", font=("Arial", 16))
        label2.pack(pady=10)


# --- Módulo de Parâmetros (CRUD) (V4.3) ---
class ParametrosFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        
        self.var_gerar_marcoes = tk.BooleanVar()
        
        titulo_label = tk.Label(self, text="Parâmetros do Sistema", font=("Arial", 18, "bold"))
        titulo_label.pack(pady=20)
        
        form_frame = tk.Frame(self)
        form_frame.pack(pady=10, padx=20, fill="x")

        tk.Label(form_frame, text="Caminho Fotos Clientes:", font=("Arial", 12)).grid(row=0, column=0, padx=5, pady=8, sticky='e')
        self.fotos_entry = tk.Entry(form_frame, width=80, font=("Arial", 12))
        self.fotos_entry.grid(row=0, column=1, padx=5, pady=8)
        
        tk.Label(form_frame, text="Caminho Mapas Câmeras:", font=("Arial", 12)).grid(row=1, column=0, padx=5, pady=8, sticky='e')
        self.mapas_entry = tk.Entry(form_frame, width=80, font=("Arial", 12))
        self.mapas_entry.grid(row=1, column=1, padx=5, pady=8)
        
        tk.Label(form_frame, text="Caminho Vídeos a Processar:", font=("Arial", 12)).grid(row=2, column=0, padx=5, pady=8, sticky='e')
        self.videos_a_processar_entry = tk.Entry(form_frame, width=80, font=("Arial", 12))
        self.videos_a_processar_entry.grid(row=2, column=1, padx=5, pady=8)
        
        tk.Label(form_frame, text="Caminho Vídeos Processados:", font=("Arial", 12)).grid(row=3, column=0, padx=5, pady=8, sticky='e')
        self.videos_processados_entry = tk.Entry(form_frame, width=80, font=("Arial", 12))
        self.videos_processados_entry.grid(row=3, column=1, padx=5, pady=8)
        
        tk.Label(form_frame, text="Caminho Vídeo Marcações:", font=("Arial", 12)).grid(row=4, column=0, padx=5, pady=8, sticky='e')
        self.video_marcoes_entry = tk.Entry(form_frame, width=80, font=("Arial", 12))
        self.video_marcoes_entry.grid(row=4, column=1, padx=5, pady=8)

        tk.Label(form_frame, text="Configurações:", font=("Arial", 12)).grid(row=5, column=0, padx=5, pady=15, sticky='ne')
        
        config_frame = tk.Frame(form_frame)
        config_frame.grid(row=5, column=1, sticky='w', padx=5, pady=10)

        tk.Label(config_frame, text="Intervalo Frames:", font=("Arial", 12)).grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.intervalo_frames_entry = tk.Entry(config_frame, width=10, font=("Arial", 12))
        self.intervalo_frames_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(config_frame, text="Escala Imagem (ex: 1):", font=("Arial", 12)).grid(row=0, column=2, padx=10, pady=5, sticky='e')
        self.escala_imagem_entry = tk.Entry(config_frame, width=10, font=("Arial", 12))
        self.escala_imagem_entry.grid(row=0, column=3, padx=5, pady=5)
        
        tk.Label(config_frame, text="Tolerância (ex: 0.6):", font=("Arial", 12)).grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.tolerancia_entry = tk.Entry(config_frame, width=10, font=("Arial", 12))
        self.tolerancia_entry.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(config_frame, text="Modelo Detecção (hog/cnn):", font=("Arial", 12)).grid(row=1, column=2, padx=10, pady=5, sticky='e')
        self.modelo_deteccao_entry = tk.Entry(config_frame, width=10, font=("Arial", 12))
        self.modelo_deteccao_entry.grid(row=1, column=3, padx=5, pady=5)
        
        tk.Label(config_frame, text="Processamento:", font=("Arial", 12)).grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.gerar_marcoes_check = tk.Checkbutton(config_frame, text="Gerar Vídeo com Marcações", font=("Arial", 12),
                                                  variable=self.var_gerar_marcoes)
        self.gerar_marcoes_check.grid(row=2, column=1, columnspan=3, padx=5, pady=5, sticky='w')

        
        self.btn_salvar = tk.Button(self, text="Salvar Parâmetros", font=("Arial", 12, "bold"), bg="#007bff", fg="white", command=self.salvar_parametros)
        self.btn_salvar.pack(pady=20, ipadx=10, ipady=5)
        
        self.carregar_dados()
        
    def carregar_dados(self):
        """Carrega os parâmetros atuais do controlador."""
        params = self.controller.parametros
        
        self.fotos_entry.delete(0, tk.END)
        self.mapas_entry.delete(0, tk.END)
        self.videos_a_processar_entry.delete(0, tk.END)
        self.videos_processados_entry.delete(0, tk.END)
        self.video_marcoes_entry.delete(0, tk.END)
        self.intervalo_frames_entry.delete(0, tk.END)
        self.escala_imagem_entry.delete(0, tk.END)
        self.tolerancia_entry.delete(0, tk.END)
        self.modelo_deteccao_entry.delete(0, tk.END)
        
        if params:
            self.fotos_entry.insert(0, params.get("fotos", ""))
            self.mapas_entry.insert(0, params.get("mapas", ""))
            self.videos_a_processar_entry.insert(0, params.get("videos_a_processar", ""))
            self.videos_processados_entry.insert(0, params.get("videos_processados", ""))
            self.video_marcoes_entry.insert(0, params.get("video_marcoes", ""))
            self.intervalo_frames_entry.insert(0, params.get("intervalo_frames", 15))
            self.escala_imagem_entry.insert(0, params.get("escala_imagem", 1))
            self.tolerancia_entry.insert(0, params.get("tolerancia", 0.6))
            self.modelo_deteccao_entry.insert(0, params.get("modelo_deteccao", "hog"))
            self.var_gerar_marcoes.set(params.get("gerar_marcoes", False))
        
    def salvar_parametros(self):
        param_id = self.controller.parametros.get("id")
        if not param_id:
            messagebox.showerror("Erro", "Não foi possível identificar o ID dos parâmetros.")
            return
            
        fotos = self.fotos_entry.get().strip()
        mapas = self.mapas_entry.get().strip()
        videos_a_processar = self.videos_a_processar_entry.get().strip()
        videos_processados = self.videos_processados_entry.get().strip()
        video_marcoes = self.video_marcoes_entry.get().strip()
        modelo_deteccao = self.modelo_deteccao_entry.get().strip()

        if not all([fotos, mapas, videos_a_processar, videos_processados, video_marcoes, modelo_deteccao]):
            messagebox.showwarning("Dados Incompletos", "Todos os campos de texto/caminho são obrigatórios.")
            return

        try:
            intervalo_frames = int(self.intervalo_frames_entry.get().strip())
            escala_imagem = int(self.escala_imagem_entry.get().strip())
            tolerancia = float(self.tolerancia_entry.get().strip())
        except ValueError as e:
            messagebox.showerror("Erro de Validação", 
                                 f"Erro ao converter valores numéricos:\n{e}\n\n"
                                 "Verifique 'Intervalo Frames', 'Escala Imagem' (inteiros) e 'Tolerância' (float).")
            return
            
        gerar_marcoes = self.var_gerar_marcoes.get()

        success = salvar_parametros_db(
            param_id, fotos, mapas, videos_a_processar, videos_processados,
            video_marcoes, intervalo_frames, escala_imagem, 
            modelo_deteccao, tolerancia, gerar_marcoes
        )
        
        if success:
            self.controller.recarregar_parametros()
            messagebox.showinfo("Sucesso", "Parâmetros atualizados com sucesso!")
        
    def on_show(self):
        """Chamado pelo show_frame para garantir que os dados estejam atualizados."""
        self.carregar_dados()


# --- Módulo 1A: Lista de Pessoas ---
class ListarPessoasFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        
        top_frame = tk.Frame(self)
        top_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Label(top_frame, text="Gerenciar Pessoas", font=("Arial", 18, "bold")).pack(side="left")
        tk.Button(top_frame, text="Novo Cadastro +", font=("Arial", 12, "bold"), bg="#28a745", fg="white", 
                  command=self.abrir_novo).pack(side="right")

        search_frame = tk.Frame(self)
        search_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(search_frame, text="Buscar por Nome:", font=("Arial", 12)).pack(side="left", padx=(0, 5))
        self.search_entry = tk.Entry(search_frame, width=40, font=("Arial", 12))
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.search_entry.bind("<Return>", lambda event: self.popular_lista())
        tk.Button(search_frame, text="Buscar", command=self.popular_lista).pack(side="left", padx=5)
        
        tree_frame = tk.Frame(self)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        cols = ("id", "nome", "documento")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        self.tree.column("id", width=50, anchor="center")
        self.tree.column("nome", width=300)
        self.tree.column("documento", width=150, anchor="center")
        
        self.tree.heading("id", text="ID")
        self.tree.heading("nome", text="Nome Completo")
        self.tree.heading("documento", text="Documento")
        
        self.tree.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        action_frame = tk.Frame(self)
        action_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Button(action_frame, text="Editar Selecionado", font=("Arial", 12), bg="#ffc107", 
                  command=self.abrir_edicao).pack(side="left", padx=5)
        tk.Button(action_frame, text="Excluir Selecionado", font=("Arial", 12), bg="#dc3545", fg="white", 
                  command=self.excluir).pack(side="right", padx=5)

    def popular_lista(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        filtro = self.search_entry.get()
        pessoas = listar_pessoas_db(filtro)
        for pessoa in pessoas:
            self.tree.insert("", "end", values=pessoa)

    def abrir_novo(self):
        self.controller.abrir_edicao_pessoa(None) 

    def abrir_edicao(self):
        selecionado = self.tree.focus() 
        if not selecionado:
            messagebox.showwarning("Seleção", "Por favor, selecione uma pessoa na lista para editar.")
            return
        dados_pessoa = self.tree.item(selecionado)
        pessoa_id = dados_pessoa["values"][0] 
        self.controller.abrir_edicao_pessoa(pessoa_id)
        
    def excluir(self):
        selecionado = self.tree.focus()
        if not selecionado:
            messagebox.showwarning("Seleção", "Por favor, selecione uma pessoa na lista para excluir.")
            return
        dados_pessoa = self.tree.item(selecionado)
        pessoa_id = dados_pessoa["values"][0]
        nome = dados_pessoa["values"][1]
        if not messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir '{nome}' (ID: {pessoa_id})?\n\nTODOS OS DADOS E FOTOS SERÃO APAGADOS PERMANENTEMENTE."):
            return
        
        # (V4.4) Reconstrói o caminho completo da pasta para exclusão
        nome_pasta_fotos = None
        conn = get_db_connection()
        if conn is None: return
        try:
            with conn.cursor() as cur:
                cur.execute('SELECT "fotosPessoa" FROM sch_supervisorio.tb_pessoa WHERE "idPessoa" = %s', (pessoa_id,))
                result = cur.fetchone()
                if result:
                    nome_pasta_fotos = result[0]
        finally:
            conn.close()
        
        caminho_completo_para_excluir = None
        if nome_pasta_fotos:
            base_path_fotos = self.controller.parametros.get("fotos")
            if base_path_fotos:
                 caminho_completo_para_excluir = os.path.join(base_path_fotos, nome_pasta_fotos)
            
        success = excluir_pessoa_db(pessoa_id, caminho_completo_para_excluir)
        
        if success:
            messagebox.showinfo("Sucesso", f"'{nome}' foi excluído com sucesso.")
            self.popular_lista() 
        
    def on_show(self):
        self.popular_lista()


# --- Módulo 1B: Cadastro/Edição de Pessoa ---
class CadastroFacialFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        
        self.poses = ["Frente", "Direita", "Esquerda", "Sorrindo", "Cima", "Baixo"]
        self.current_pose_index = 0
        self.capturando = False
        self.video_capture = None
        self.pessoa_id_atual = None 

        top_frame = tk.Frame(self)
        top_frame.pack(fill="x", padx=10, pady=10)
        
        self.titulo_label = tk.Label(top_frame, text="Nova Pessoa", font=("Arial", 18, "bold"))
        self.titulo_label.pack(side="left")
        tk.Button(top_frame, text="< Voltar para Lista", font=("Arial", 12), 
                  command=lambda: controller.show_frame("ListarPessoasFrame")).pack(side="right")
        
        self.video_label = tk.Label(self)
        self.instrucao_label = tk.Label(self, text="Preencha os dados e inicie o cadastro.", font=("Arial", 16))
        self.instrucao_label.pack(pady=10)
        
        form_frame = tk.Frame(self)
        form_frame.pack(pady=5)

        tk.Label(form_frame, text="Nome Completo:").grid(row=0, column=0, padx=5, sticky='w')
        self.nome_entry = tk.Entry(form_frame, width=30)
        self.nome_entry.grid(row=0, column=1, padx=5)

        tk.Label(form_frame, text="Nº da Carteira de ID:").grid(row=1, column=0, padx=5, sticky='w')
        self.id_entry = tk.Entry(form_frame, width=30)
        self.id_entry.grid(row=1, column=1, padx=5)

        self.btn_acao = tk.Button(self, text="Iniciar Cadastro", font=("Arial", 12, "bold"), bg="#28a745", fg="white", command=self.iniciar_cadastro)
        self.btn_acao.pack(pady=15, ipadx=10, ipady=5)
        
        self.camera_off_label = tk.Label(self, text="Câmera desligada.\nO cadastro facial ativará a câmera.", font=("Arial", 14), bg="lightgrey", width=80, height=27)

    def carregar_dados(self, pessoa_id):
        self.pessoa_id_atual = pessoa_id
        self.nome_entry.config(state=tk.NORMAL)
        self.id_entry.config(state=tk.NORMAL)
        self.nome_entry.delete(0, tk.END)
        self.id_entry.delete(0, tk.END)
        if pessoa_id is None:
            self.titulo_label.config(text="Nova Pessoa")
            self.instrucao_label.config(text="Preencha os dados e inicie o cadastro.")
            self.btn_acao.config(text="Iniciar Cadastro", command=self.iniciar_cadastro, bg="#28a745")
            self.capturando = False
        else:
            self.titulo_label.config(text="Editar Pessoa")
            pessoa_data = get_pessoa_por_id_db(pessoa_id)
            if pessoa_data:
                self.nome_entry.insert(0, pessoa_data["nome"])
                self.id_entry.insert(0, pessoa_data["documento"])
            self.instrucao_label.config(text="Para RE-CAPTURAR fotos, clique em 'Iniciar Captura'.\nPara salvar apenas os dados (Nome/ID), clique em 'Salvar Dados'.")
            self.btn_acao.config(text="Iniciar RE-Captura", command=self.iniciar_cadastro, bg="#007bff")

    def iniciar_camera(self):
        if self.video_capture is None:
            self.video_capture = cv2.VideoCapture(0)
            if not self.video_capture.isOpened():
                messagebox.showerror("Erro de Câmera", "Não foi possível acessar a câmera.")
                self.video_capture = None
                self.camera_off_label.pack(pady=5, fill="both", expand=True) 
                return
        self.camera_off_label.pack_forget()
        self.video_label.pack(pady=5)
        self.update_frame()

    def release_camera(self):
        if self.video_capture:
            self.video_capture.release()
            self.video_capture = None
            self.video_label.config(image='')
            self.video_label.imgtk = None
            self.video_label.pack_forget()
            self.camera_off_label.pack(pady=5, fill="both", expand=True)

    def update_frame(self):
        if self.video_capture is None or not self.video_capture.isOpened():
            self.release_camera() 
            return
        ret, frame = self.video_capture.read()
        if ret:
            frame = cv2.flip(frame, 1)
            face_locations = face_recognition.face_locations(frame, model='hog')
            for (top, right, bottom, left) in face_locations:
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(cv2image)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)
        self.after(15, self.update_frame)

    def sanitizar_nome(self, nome):
        return re.sub(r'[^a-zA-Z0-9_]', '', nome.replace(" ", "_"))

    def iniciar_cadastro(self):
        nome = self.nome_entry.get().strip()
        id_carteira = self.id_entry.get().strip()
        if not nome or not id_carteira:
            messagebox.showwarning("Dados Incompletos", "Por favor, preencha o Nome e o Número da Carteira.")
            return
        base_path_fotos = self.controller.parametros.get("fotos")
        if not base_path_fotos or not os.path.isdir(base_path_fotos):
             messagebox.showerror("Erro de Parâmetro", f"O caminho de fotos não está configurado ou é inválido:\n{base_path_fotos}\n\nVá ao menu 'Parâmetros' para corrigir.")
             return
        nome_sanitizado = self.sanitizar_nome(nome)
        id_sanitizado = self.sanitizar_nome(id_carteira)
        self.nome_pasta = f"{nome_sanitizado}_{id_sanitizado}"
        self.caminho_pasta = os.path.join(base_path_fotos, self.nome_pasta)
        if os.path.exists(self.caminho_pasta):
            if not messagebox.askyesno("Pasta Existente", f"A pasta de fotos '{self.nome_pasta}' já existe.\nDeseja sobrescrever as fotos existentes?"):
                return
        else:
            os.makedirs(self.caminho_pasta)
        self.capturando = True
        self.current_pose_index = 0
        self.nome_entry.config(state=tk.DISABLED)
        self.id_entry.config(state=tk.DISABLED)
        self.atualizar_passo_gui()
        self.btn_acao.config(command=self.processar_passo, text="Capturar e Prosseguir", bg="#007bff")

    def processar_passo(self):
        if not self.capturando or self.video_capture is None:
            return
        ret, frame = self.video_capture.read()
        if not ret:
            messagebox.showerror("Erro de Câmera", "Não foi possível ler a imagem da câmera.")
            return
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame, model='hog')
        if len(face_locations) != 1:
            messagebox.showwarning("Aviso de Captura", "Não foi possível detectar um único rosto.")
            return
        top, right, bottom, left = face_locations[0]
        h, w, _ = frame.shape
        top_padded = max(0, top - PADDING_PIXELS)
        left_padded = max(0, left - PADDING_PIXELS)
        bottom_padded = min(h, bottom + PADDING_PIXELS)
        right_padded = min(w, right + PADDING_PIXELS)
        rosto_recortado = frame[top_padded:bottom_padded, left_padded:right_padded]
        pose_atual = self.poses[self.current_pose_index]
        nome_arquivo = f"{pose_atual}.jpg"
        caminho_arquivo = os.path.join(self.caminho_pasta, nome_arquivo)
        cv2.imwrite(caminho_arquivo, rosto_recortado)
        print(f"Rosto recortado e salvo em: {caminho_arquivo}")
        self.current_pose_index += 1
        if self.current_pose_index < len(self.poses):
            self.atualizar_passo_gui()
        else:
            self.finalizar_cadastro()

    def atualizar_passo_gui(self):
        pose_instrucao = self.poses[self.current_pose_index]
        self.instrucao_label.config(text=f"Passo {self.current_pose_index + 1}/{len(self.poses)}: Peça para a pessoa estar na pose '{pose_instrucao.upper()}'")

    def finalizar_cadastro(self):
        gerar_aumentos_de_dados(self.caminho_pasta)
        nome_final = self.nome_entry.get().strip()
        id_final = self.id_entry.get().strip()
        
        # (MODIFICADO V4.4) Salva apenas o nome da pasta
        success = salvar_pessoa_no_banco(nome_final, id_final, self.nome_pasta, self.pessoa_id_atual)
        
        if success:
            messagebox.showinfo("Cadastro Concluído", f"Cadastro de '{nome_final}' salvo com sucesso!\n\nDados salvos no banco e fotos salvas em:\n{self.caminho_pasta}")
            self.controller.show_frame("ListarPessoasFrame")
        self.capturando = False
        self.nome_entry.config(state=tk.NORMAL)
        self.id_entry.config(state=tk.NORMAL)
        self.carregar_dados(self.pessoa_id_atual)


# --- Módulo 2A: Lista de Câmeras ---
class ListarCamerasFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        
        top_frame = tk.Frame(self)
        top_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Label(top_frame, text="Gerenciar Câmeras", font=("Arial", 18, "bold")).pack(side="left")
        tk.Button(top_frame, text="Nova Câmera +", font=("Arial", 12, "bold"), bg="#28a745", fg="white", 
                  command=self.abrir_novo).pack(side="right")

        search_frame = tk.Frame(self)
        search_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(search_frame, text="Buscar por Nome:", font=("Arial", 12)).pack(side="left", padx=(0, 5))
        self.search_entry = tk.Entry(search_frame, width=40, font=("Arial", 12))
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.search_entry.bind("<Return>", lambda event: self.popular_lista())
        tk.Button(search_frame, text="Buscar", command=self.popular_lista).pack(side="left", padx=5)
        
        tree_frame = tk.Frame(self)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        cols = ("id", "nome", "localizacao")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        self.tree.column("id", width=50, anchor="center")
        self.tree.column("nome", width=250)
        self.tree.column("localizacao", width=300)
        
        self.tree.heading("id", text="ID")
        self.tree.heading("nome", text="Nome Câmera")
        self.tree.heading("localizacao", text="Localização") 
        
        self.tree.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        action_frame = tk.Frame(self)
        action_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Button(action_frame, text="Editar Selecionado", font=("Arial", 12), bg="#ffc107", 
                  command=self.abrir_edicao).pack(side="left", padx=5)
        tk.Button(action_frame, text="Excluir Selecionado", font=("Arial", 12), bg="#dc3545", fg="white", 
                  command=self.excluir).pack(side="right", padx=5)

    def popular_lista(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        filtro = self.search_entry.get()
        cameras = listar_cameras_db(filtro)
        for camera in cameras:
            self.tree.insert("", "end", values=camera)

    def abrir_novo(self):
        self.controller.abrir_edicao_camera(None) 

    def abrir_edicao(self):
        selecionado = self.tree.focus()
        if not selecionado:
            messagebox.showwarning("Seleção", "Por favor, selecione uma câmera na lista para editar.")
            return
        dados_camera = self.tree.item(selecionado)
        camera_id = dados_camera["values"][0] 
        self.controller.abrir_edicao_camera(camera_id)
        
    def excluir(self):
        selecionado = self.tree.focus()
        if not selecionado:
            messagebox.showwarning("Seleção", "Por favor, selecione uma câmera na lista para excluir.")
            return
        dados_camera = self.tree.item(selecionado)
        camera_id = dados_camera["values"][0]
        nome = dados_camera["values"][1]
        if not messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir a câmera '{nome}' (ID: {camera_id})?\n\nO MAPA ASSOCIADO SERÁ APAGADO PERMANENTEMENTE."):
            return
        camera_data = get_camera_por_id_db(camera_id)
        caminho_mapa = camera_data.get("mapa_path") if camera_data else None
        success = excluir_camera_db(camera_id, caminho_mapa)
        if success:
            messagebox.showinfo("Sucesso", f"Câmera '{nome}' foi excluída com sucesso.")
            self.popular_lista() 
        
    def on_show(self):
        self.popular_lista()


# --- (MODIFICADO V6.0) Módulo 2B: Cadastro/Edição de Câmera ---
class CadastroCamerasFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.filepath_original_selecionado = None 
        self.camera_id_atual = None
        
        top_frame = tk.Frame(self)
        top_frame.pack(fill="x", padx=10, pady=10)
        
        self.titulo_label = tk.Label(top_frame, text="Nova Câmera", font=("Arial", 18, "bold"))
        self.titulo_label.pack(side="left")
        tk.Button(top_frame, text="< Voltar para Lista", font=("Arial", 12), 
                  command=lambda: controller.show_frame("ListarCamerasFrame")).pack(side="right")

        
        form_frame = tk.Frame(self)
        form_frame.pack(pady=10, padx=20)

        tk.Label(form_frame, text="Nome da Câmera:", font=("Arial", 12)).grid(row=0, column=0, padx=5, pady=8, sticky='e')
        self.nome_entry = tk.Entry(form_frame, width=40, font=("Arial", 12))
        self.nome_entry.grid(row=0, column=1, padx=5, pady=8)
        
        tk.Label(form_frame, text="Localização:", font=("Arial", 12)).grid(row=1, column=0, padx=5, pady=8, sticky='e')
        self.loc_entry = tk.Entry(form_frame, width=40, font=("Arial", 12))
        self.loc_entry.grid(row=1, column=1, padx=5, pady=8)

        # (NOVO V6.0) Novos campos
        tk.Label(form_frame, text="Andar (ex: 0, 1, -1):", font=("Arial", 12)).grid(row=2, column=0, padx=5, pady=8, sticky='e')
        self.andar_entry = tk.Entry(form_frame, width=10, font=("Arial", 12))
        self.andar_entry.grid(row=2, column=1, padx=5, pady=8, sticky='w')
        
        tk.Label(form_frame, text="Nº Sala Próxima:", font=("Arial", 12)).grid(row=3, column=0, padx=5, pady=8, sticky='e')
        self.nrsala_entry = tk.Entry(form_frame, width=10, font=("Arial", 12))
        self.nrsala_entry.grid(row=3, column=1, padx=5, pady=8, sticky='w')

        tk.Label(form_frame, text="Imagem (Mapa):", font=("Arial", 12)).grid(row=4, column=0, padx=5, pady=8, sticky='e')
        self.btn_selecionar = tk.Button(form_frame, text="Selecionar Nova Imagem...", command=self.selecionar_imagem)
        self.btn_selecionar.grid(row=4, column=1, padx=5, pady=8, sticky='w')
        
        self.path_label = tk.Label(form_frame, text="Nenhum arquivo selecionado.", font=("Arial", 9, "italic"), fg="grey")
        self.path_label.grid(row=5, column=1, padx=5, sticky='w')

        self.thumbnail_label = tk.Label(self, bg="lightgrey", width=40, height=15)
        self.thumbnail_label.pack(pady=10)
        
        self.btn_salvar = tk.Button(self, text="Salvar Cadastro", font=("Arial", 12, "bold"), bg="#007bff", fg="white", command=self.salvar_camera)
        self.btn_salvar.pack(pady=20, ipadx=10, ipady=5)

    def carregar_dados(self, camera_id):
        self.camera_id_atual = camera_id
        self.filepath_original_selecionado = None 
        self.nome_entry.delete(0, tk.END)
        self.loc_entry.delete(0, tk.END)
        # (NOVO V6.0) Limpa novos campos
        self.andar_entry.delete(0, tk.END)
        self.nrsala_entry.delete(0, tk.END)
        
        self.thumbnail_label.config(image='', width=40, height=15, text="")
        self.thumbnail_label.image = None
        self.path_label.config(text="Nenhum arquivo selecionado.", font=("Arial", 9, "italic"), fg="grey")
        
        if camera_id is None:
            self.titulo_label.config(text="Nova Câmera")
            self.btn_salvar.config(text="Salvar Nova Câmera")
            # (NOVO V6.0) Valores padrão para nova câmera
            self.andar_entry.insert(0, "0")
            self.nrsala_entry.insert(0, "0")
        else:
            self.titulo_label.config(text="Editar Câmera")
            self.btn_salvar.config(text="Salvar Alterações")
            camera_data = get_camera_por_id_db(self.camera_id_atual)
            
            if camera_data:
                self.nome_entry.insert(0, camera_data["nome"])
                self.loc_entry.insert(0, camera_data["localizacao"])
                
                # (NOVO V6.0) Carrega dados de andar/sala
                self.andar_entry.insert(0, str(camera_data.get("andar", 0)))
                self.nrsala_entry.insert(0, str(camera_data.get("nrsala", 0)))
                
                mapa_path = camera_data.get("mapa_path")
                if mapa_path and os.path.exists(mapa_path):
                    self.filepath_original_selecionado = mapa_path
                    self.exibir_thumbnail(mapa_path)
                    self.path_label.config(text=f"(Atual) {os.path.basename(mapa_path)}", fg="black", font=("Arial", 9, "normal"))
                else:
                    self.path_label.config(text="(Imagem do mapa não encontrada)", fg="red")
            else:
                # Erro ao carregar dados (ex: colunas não existem)
                self.controller.show_frame("ListarCamerasFrame")


    def selecionar_imagem(self):
        filetypes = (('Imagens', '*.jpg *.jpeg *.png *.bmp'), ('Todos os arquivos', '*.*'))
        filepath = filedialog.askopenfilename(title='Selecione uma imagem de mapa', filetypes=filetypes)
        if filepath:
            self.filepath_original_selecionado = filepath
            self.path_label.config(text=os.path.basename(filepath), fg="black", font=("Arial", 9, "normal"))
            self.exibir_thumbnail(filepath)

    def exibir_thumbnail(self, filepath):
        try:
            img = Image.open(filepath)
            max_size = (300, 300)
            img.thumbnail(max_size)
            imgtk = ImageTk.PhotoImage(image=img)
            self.thumbnail_label.config(image=imgtk, width=img.width, height=img.height)
            self.thumbnail_label.image = imgtk 
        except Exception as e:
            messagebox.showerror("Erro de Imagem", f"Não foi possível carregar a imagem: {e}")
            self.thumbnail_label.config(image='', text="Erro ao carregar imagem")
            self.thumbnail_label.image = None
            self.path_label.config(text="Arquivo inválido.", fg="red")
            self.filepath_original_selecionado = None

    def salvar_camera(self):
        nome = self.nome_entry.get().strip()
        localizacao = self.loc_entry.get().strip()
        
        if not nome or not localizacao:
            messagebox.showwarning("Dados Incompletos", "Por favor, preencha Nome e Localização.")
            return
            
        # (NOVO V6.0) Validação dos campos numéricos
        try:
            andar = int(self.andar_entry.get().strip())
            nrsala = int(self.nrsala_entry.get().strip())
        except ValueError:
            messagebox.showerror("Erro de Validação", "Os campos 'Andar' e 'Nº Sala Próxima' devem ser números inteiros.")
            return

        if self.filepath_original_selecionado is None:
             messagebox.showwarning("Dados Incompletos", "Por favor, selecione uma imagem para o mapa.")
             return
             
        base_path_mapas = self.controller.parametros.get("mapas")
        
        try:
            os.makedirs(base_path_mapas, exist_ok=True)
        except Exception as e:
             messagebox.showerror("Erro de Parâmetro", f"Não foi possível criar a pasta de destino dos mapas:\n{base_path_mapas}\n\nErro: {e}")
             return
        
        nome_arquivo = os.path.basename(self.filepath_original_selecionado)
        caminho_destino_mapa = os.path.join(base_path_mapas, nome_arquivo)
        
        try:
            if os.path.exists(caminho_destino_mapa):
                if os.path.samefile(self.filepath_original_selecionado, caminho_destino_mapa):
                    print("Arquivo de mapa já está no destino. Nenhuma cópia necessária.")
                    pass 
                else:
                    shutil.copy(self.filepath_original_selecionado, caminho_destino_mapa)
                    print(f"Arquivo de mapa sobrescrito em: {caminho_destino_mapa}")
            else:
                shutil.copy(self.filepath_original_selecionado, caminho_destino_mapa)
                print(f"Arquivo de mapa copiado para: {caminho_destino_mapa}")
        except Exception as e:
            messagebox.showerror("Erro de Cópia", f"Não foi possível copiar o arquivo de mapa para o destino:\n{e}")
            return
            
        # (MODIFICADO V6.0) Passa os novos valores
        success = salvar_camera_no_banco(
            nome, localizacao, caminho_destino_mapa, 
            andar, nrsala, self.camera_id_atual
        )
        
        if success:
            messagebox.showinfo("Cadastro Salvo", f"Câmera '{nome}' salva com sucesso no banco de dados!")
            self.controller.show_frame("ListarCamerasFrame")
        

# --- (MODIFICADO V6.0) Módulo 3: Acompanhamento por ÁREA ---
# (Renomeado de AcompanhamentoFrame para AcompanhamentoAreaFrame)
class AcompanhamentoAreaFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.map_image_tk = None 
        self.localizacoes_mapas = {} 
        self.icones_canvas = [] 
        self.tooltip_window_mapa = None 
        
        self.cores_icones = [
            "#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", "#00FFFF",
            "#FF4500", "#ADFF2F", "#DA70D6", "#B0C4DE"
        ]

        # --- Layout Principal ---
        filtro_frame = tk.Frame(self)
        filtro_frame.pack(fill="x", padx=10, pady=10)

        tk.Label(filtro_frame, text="Localização:", font=("Arial", 12)).pack(side="left", padx=(0, 5))
        self.loc_combobox = ttk.Combobox(filtro_frame, state="readonly", width=30, font=("Arial", 12))
        self.loc_combobox.pack(side="left", padx=5)

        tk.Label(filtro_frame, text="Data (AAAA-MM-DD):", font=("Arial", 12)).pack(side="left", padx=(15, 5))
        self.data_entry = tk.Entry(filtro_frame, width=12, font=("Arial", 12))
        self.data_entry.pack(side="left", padx=5)
        self.data_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        tk.Button(filtro_frame, text="Buscar", font=("Arial", 12, "bold"), bg="#007bff", fg="white",
                  command=self.buscar_dados).pack(side="left", padx=10)

        content_frame = tk.Frame(self)
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)

        map_frame = tk.Frame(content_frame, relief=tk.SUNKEN, borderwidth=1)
        map_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        self.map_canvas = tk.Canvas(map_frame, bg="gray", relief=tk.SUNKEN, borderwidth=1)
        self.map_canvas.pack(fill="both", expand=True)

        list_frame = tk.Frame(content_frame, width=400, relief=tk.SUNKEN, borderwidth=1)
        list_frame.pack(side="right", fill="y", expand=False, padx=(5, 0))
        list_frame.pack_propagate(False) 

        tk.Label(list_frame, text="Pessoas Identificadas", font=("Arial", 12, "bold")).pack(pady=5)
        
        tree_container = tk.Frame(list_frame)
        tree_container.pack(fill="both", expand=True, padx=5, pady=(0, 5))

        cols = ("nome", "horario", "segundo")
        self.tree = ttk.Treeview(tree_container, columns=cols, show="headings", height=10)
        self.tree.column("nome", width=180)
        self.tree.column("horario", width=100, anchor="center")
        self.tree.column("segundo", width=70, anchor="e")
        
        self.tree.heading("nome", text="Nome")
        self.tree.heading("horario", text="Horário")
        self.tree.heading("segundo", text="Seg. (Vídeo)")
        
        scrollbar = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

    def on_show(self):
        """Chamado ao exibir o frame. Carrega as localizações."""
        self.carregar_localizacoes()
        self.limpar_tela()

    def carregar_localizacoes(self):
        """Busca localizações do DB e preenche o combobox."""
        self.localizacoes_mapas = get_localizacoes_db()
        loc_nomes = list(self.localizacoes_mapas.keys())
        self.loc_combobox['values'] = loc_nomes
        if loc_nomes:
            self.loc_combobox.current(0)

    def limpar_tela(self):
        """Limpa o mapa e a lista."""
        self.map_canvas.delete("all")
        self.map_image_tk = None
        self.icones_canvas = []
        for i in self.tree.get_children():
            self.tree.delete(i)

    def buscar_dados(self):
        """Função principal que busca dados e atualiza a tela."""
        self.limpar_tela()
        
        localizacao = self.loc_combobox.get()
        data_str = self.data_entry.get()

        if not localizacao:
            messagebox.showwarning("Filtro Incompleto", "Por favor, selecione uma localização.")
            return
        
        try:
            datetime.strptime(data_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("Data Inválida", "Por favor, insira a data no formato AAAA-MM-DD.")
            return

        # 1. Carregar o Mapa no Canvas
        mapa_path = self.localizacoes_mapas.get(localizacao)
        
        map_x_pos, map_y_pos = 0, 0
        map_width, map_height = 100, 100
        
        if mapa_path and os.path.exists(mapa_path):
            try:
                self.map_canvas.update_idletasks()
                canvas_width = self.map_canvas.winfo_width()
                canvas_height = self.map_canvas.winfo_height()
                if canvas_width <= 1: canvas_width = 500
                if canvas_height <= 1: canvas_height = 500

                img = Image.open(mapa_path)
                img_ratio = img.width / img.height
                canvas_ratio = canvas_width / canvas_height

                if img_ratio > canvas_ratio: 
                    new_width = canvas_width
                    new_height = int(new_width / img_ratio)
                else: 
                    new_height = canvas_height
                    new_width = int(new_height * img_ratio)

                if new_width <= 0: new_width = 500
                if new_height <= 0: new_height = 500
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                self.map_image_tk = ImageTk.PhotoImage(img)
                
                x_pos = (canvas_width - new_width) / 2
                y_pos = (canvas_height - new_height) / 2
                self.map_canvas.create_image(x_pos, y_pos, anchor='nw', image=self.map_image_tk)
                
                map_x_pos, map_y_pos = x_pos, y_pos
                map_width, map_height = new_width, new_height

            except Exception as e:
                print(f"Erro ao carregar imagem: {e}")
                self.map_canvas.create_text(10, 10, anchor='nw', text=f"Erro ao carregar mapa:\n{e}", fill="red")
        else:
            self.map_canvas.create_text(10, 10, anchor='nw', text=f"Mapa não encontrado para '{localizacao}'\nCaminho: {mapa_path}", fill="red")

        # 2. Buscar Dados de Acompanhamento
        dados = get_dados_acompanhamento_db(localizacao, data_str)
        if not dados:
            if mapa_path and os.path.exists(mapa_path): 
                messagebox.showinfo("Sem Resultados", f"Nenhum registro encontrado para '{localizacao}' na data '{data_str}'.")
            return

        # 3. Preencher a Lista (Treeview)
        pessoas_unicas = {}
        for nome_pessoa, data_hora, segundo in dados:
            if nome_pessoa not in pessoas_unicas:
                pessoas_unicas[nome_pessoa] = []
            pessoas_unicas[nome_pessoa].append(data_hora)
            # (MODIFICADO V6.3) Apenas para clareza, a lógica aqui está correta
            # A view é por dia, então mostrar só a hora é o ideal.
            horario_str = data_hora.strftime("%H:%M:%S")
            self.tree.insert("", "end", values=(nome_pessoa, horario_str, f"{segundo:.1f}s"))

        # 4. Desenhar os ícones no mapa (centralizados e coloridos)
        centro_x = map_x_pos + (map_width / 2)
        centro_y = map_y_pos + (map_height / 2)
        
        offsets = [
            (0, 0), (-40, -40), (40, 40), (0, -60), (0, 60), (-70, 0),
            (70, 0), (-50, 50), (50, -50), (80, -20), (-80, 20)
        ]
        
        raio = 8 
        
        for i, nome_pessoa in enumerate(pessoas_unicas.keys()):
            cor_icone = self.cores_icones[i % len(self.cores_icones)]
            offset_x, offset_y = offsets[i % len(offsets)]
            x = centro_x + offset_x
            y = centro_y + offset_y
            
            x = max(map_x_pos + raio, min(map_x_pos + map_width - raio, x))
            y = max(map_y_pos + raio, min(map_y_pos + map_height - raio, y))
            
            icone = self.map_canvas.create_oval(x-raio, y-raio, x+raio, y+raio, 
                                                fill=cor_icone, outline="black", width=1,
                                                tags=(f"icone_{i}")) 
            self.icones_canvas.append(icone) 

            primeira_vez = min(pessoas_unicas[nome_pessoa]).strftime("%H:%M:%S")
            ultima_vez = max(pessoas_unicas[nome_pessoa]).strftime("%H:%M:%S")
            contagem = len(pessoas_unicas[nome_pessoa])
            
            tooltip_text = f"Pessoa: {nome_pessoa}\n" \
                           f"Detecções: {contagem}\n" \
                           f"Primeira vez: {primeira_vez}\n" \
                           f"Última vez: {ultima_vez}"
                           
            self.map_canvas.tag_bind(f"icone_{i}", "<Enter>", lambda e, txt=tooltip_text: self.mostrar_tooltip_icone(e, txt))
            self.map_canvas.tag_bind(f"icone_{i}", "<Leave>", lambda e: self.esconder_tooltip_icone())

    def mostrar_tooltip_icone(self, event, texto):
        if self.tooltip_window_mapa:
            self.tooltip_window_mapa.destroy()
        x = event.x_root + 15
        y = event.y_root + 10
        self.tooltip_window_mapa = tk.Toplevel(self.map_canvas)
        self.tooltip_window_mapa.wm_overrideredirect(True)
        self.tooltip_window_mapa.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tooltip_window_mapa, text=texto, justify='left',
                         background="#ffffe0", relief='solid', borderwidth=1,
                         font=("Arial", 9, "normal"))
        label.pack(ipadx=4, ipady=2)

    def esconder_tooltip_icone(self, event=None): 
        if self.tooltip_window_mapa:
            self.tooltip_window_mapa.destroy()
        self.tooltip_window_mapa = None


# --- (MODIFICADO V6.3) Módulo 4: Acompanhamento por Pessoa (Grafo) ---
class AcompanhamentoPessoaFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.graph_canvas_widget = None
        self.graph_figure = None
        self.tooltip_cursor = None

        # --- Frame de Filtros ---
        filtro_frame = tk.Frame(self)
        filtro_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Label(filtro_frame, text="Data Inicial:", font=("Arial", 12)).pack(side="left", padx=(0, 5))
        self.data_inicio_entry = tk.Entry(filtro_frame, width=12, font=("Arial", 12))
        self.data_inicio_entry.pack(side="left", padx=5)
        self.data_inicio_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        tk.Label(filtro_frame, text="Data Final:", font=("Arial", 12)).pack(side="left", padx=(15, 5))
        self.data_final_entry = tk.Entry(filtro_frame, width=12, font=("Arial", 12))
        self.data_final_entry.pack(side="left", padx=5)
        self.data_final_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        tk.Button(filtro_frame, text="Buscar Pessoas", font=("Arial", 12, "bold"), bg="#007bff", fg="white",
                  command=self.buscar_pessoas).pack(side="left", padx=10)
        
        # --- Frame de Seleção ---
        selecao_frame = tk.Frame(self)
        selecao_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(selecao_frame, text="Pessoa:", font=("Arial", 12)).pack(side="left", padx=(0, 5))
        self.pessoa_combobox = ttk.Combobox(selecao_frame, state="readonly", width=40, font=("Arial", 12))
        self.pessoa_combobox.pack(side="left", padx=5)
        
        # (NOVO V6.1) Botão explícito para gerar o grafo
        tk.Button(selecao_frame, text="Gerar Grafo", font=("Arial", 12, "bold"), bg="#28a745", fg="white",
                  command=self.gerar_grafo).pack(side="left", padx=10)

        # --- Frame do Grafo ---
        self.graph_frame = tk.Frame(self, relief=tk.SUNKEN, borderwidth=1, bg="white")
        self.graph_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def on_show(self):
        """Limpa a tela ao ser exibida."""
        self.limpar_grafo()
        self.pessoa_combobox['values'] = []
        self.pessoa_combobox.set("")

    def limpar_grafo(self):
        """Remove o widget do grafo anterior."""
        if self.graph_canvas_widget:
            self.graph_canvas_widget.destroy()
            self.graph_canvas_widget = None
        if self.graph_figure:
            plt.close(self.graph_figure) # Fecha a figura do matplotlib
            self.graph_figure = None
        self.tooltip_cursor = None

    def validar_datas(self):
        """Valida as datas de início e fim. Retorna (data_inicio, data_fim) ou None."""
        data_inicio_str = self.data_inicio_entry.get()
        data_fim_str = self.data_final_entry.get()
        try:
            data_inicio = datetime.strptime(data_inicio_str, "%Y-%m-%d").date()
            data_fim = datetime.strptime(data_fim_str, "%Y-%m-%d").date()
            return data_inicio, data_fim
        except ValueError:
            messagebox.showwarning("Data Inválida", "Por favor, insira as datas no formato AAAA-MM-DD.")
            return None, None

    def buscar_pessoas(self):
        """Busca pessoas com registros no período selecionado."""
        self.limpar_grafo()
        self.pessoa_combobox.set("")
        
        data_inicio, data_fim = self.validar_datas()
        if data_inicio is None:
            return

        pessoas = get_pessoas_por_periodo_db(data_inicio, data_fim)
        if not pessoas:
            messagebox.showinfo("Sem Resultados", "Nenhuma pessoa encontrada no período selecionado.")
            self.pessoa_combobox['values'] = []
        else:
            self.pessoa_combobox['values'] = pessoas
            if pessoas:
                self.pessoa_combobox.current(0)
            # (REMOVIDO V6.1) Não gera mais o grafo automaticamente
            # self.gerar_grafo() 

    def gerar_grafo(self, event=None):
        """Gera e exibe o grafo de caminhamento para a pessoa selecionada."""
        self.limpar_grafo()
        
        nome_pessoa = self.pessoa_combobox.get()
        if not nome_pessoa:
            messagebox.showwarning("Seleção Vazia", "Por favor, busque e selecione uma pessoa primeiro.")
            return
            
        data_inicio, data_fim = self.validar_datas()
        if data_inicio is None:
            return
            
        # (MODIFICADO V6.1) Pega as datas dos campos de entrada
        data_inicio_str = self.data_inicio_entry.get()
        data_fim_str = self.data_final_entry.get()
            
        caminho_data = get_caminho_pessoa_db(nome_pessoa, data_inicio, data_fim)
        
        if not caminho_data:
            messagebox.showinfo("Sem Dados", f"Nenhum dado de caminhamento encontrado para '{nome_pessoa}' neste período.")
            return
            
        # Verifica se as colunas de andar/sala estão preenchidas
        if any(r[2] is None or r[3] is None for r in caminho_data):
            messagebox.showwarning("Dados Incompletos", 
                                   "Alguns registros de câmera não possuem dados de 'Andar' ou 'Sala'.\n"
                                   "O grafo pode ficar incompleto ou posicionado incorretamente (usando Andar 0).\n"
                                   "Atualize os dados em 'Gerenciar Câmeras'.")
            
        G = nx.DiGraph()
        pos = {}
        node_labels = {}
        node_colors = []
        node_ids_ordenados = [] # Para garantir a ordem de desenho

        # Nós anteriores para criar as arestas
        node_anterior = None
        
        # 1. Construir o grafo (Nós, Posições, Arestas, Metadados)
        # (MODIFICADO V6.3) A lógica aqui já está correta, pois 'caminho_data'
        # já vem ordenado pelo timestamp completo do banco.
        for i, (datahora, nome_camera, andar, nrsala) in enumerate(caminho_data):
            # O 'i' garante um ID de nó único para cada evento de timestamp,
            # permitindo revisitas à mesma câmera.
            node_id = f"{i}_{nome_camera}"
            
            # Garante que dados nulos sejam tratados
            andar_val = andar if andar is not None else 0
            nrsala_val = nrsala if nrsala is not None else -1 # -1 para "Desconhecido"
            
            # Posição: X = sequência (i), Y = andar
            pos[node_id] = (i, andar_val) 
            
            # (MODIFICADO V6.3) Rótulo do Nó
            # Mostra Dia/Mês e Hora:Min:Seg para economizar espaço
            node_labels[node_id] = f"Sala {nrsala_val}\n{nome_camera}\n{datahora.strftime('%d/%m %H:%M:%S')}"
            
            # Cor do Nó (Verde para Sala 0, Azul para outros)
            cor = "skyblue"
            if nrsala_val == 0:
                cor = "#90EE90" # Verde claro
            node_colors.append(cor)

            # Adiciona o nó com seus metadados para o tooltip
            G.add_node(node_id,
                       pessoa=nome_pessoa,
                       camera=nome_camera,
                       andar=andar_val,
                       sala=nrsala_val,
                       horario=datahora.strftime('%Y-%m-%d %H:%M:%S')) # Tooltip com data completa
            
            node_ids_ordenados.append(node_id)
            
            # Adiciona a aresta do nó anterior para o atual
            if node_anterior:
                G.add_edge(node_anterior, node_id)
            node_anterior = node_id

        # 2. Configurar a Figura Matplotlib
        self.graph_figure, ax = plt.subplots(figsize=(10, 6))
        plt.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.1)
        
        # 3. Desenhar os componentes do Grafo
        
        # (FIX V6.2) Altera 'node_list' para 'nodelist'
        # Desenha os nós (e guarda o artista 'nodes' para o tooltip)
        nodes = nx.draw_networkx_nodes(G, pos, ax=ax, nodelist=node_ids_ordenados,
                                       node_color=node_colors, node_size=3500,
                                       edgecolors="black")
        
        # Desenha as arestas
        nx.draw_networkx_edges(G, pos, ax=ax, node_size=3500,
                               arrowstyle='->', arrowsize=20,
                               connectionstyle='arc3,rad=0.1')
        
        # Desenha os rótulos
        nx.draw_networkx_labels(G, pos, labels=node_labels, ax=ax, font_size=8)

        # 4. Configurar Eixos e Título
        ax.set_title(f"Caminhamento de {nome_pessoa} ({data_inicio_str} a {data_fim_str})", fontsize=14)
        ax.set_xticks([]) # Remove o eixo X (sequência)
        
        # Configura o eixo Y para mostrar os andares
        y_andares = sorted(list(set(andar for _, andar in pos.values())))
        # Garante que pelo menos um eixo Y apareça se houver dados
        if not y_andares:
             y_andares = [0]
             
        ax.set_yticks(y_andares)
        ax.set_yticklabels([f"Andar {andar}" for andar in y_andares], fontsize=10)
        ax.tick_params(axis='y', left=True, right=False)
        ax.spines['left'].set_visible(True)
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.spines['bottom'].set_visible(False)

        # 5. Embutir o Grafo no Canvas do Tkinter
        canvas = FigureCanvasTkAgg(self.graph_figure, master=self.graph_frame)
        self.graph_canvas_widget = canvas.get_tk_widget()
        self.graph_canvas_widget.pack(fill="both", expand=True)
        canvas.draw()
        
        # 6. Configurar o Tooltip (Hover)
        # Aponta o mplcursors para o artista 'nodes' que desenhamos
        self.tooltip_cursor = mplcursors.cursor(nodes, hover=True)
        
        @self.tooltip_cursor.connect("add")
        def on_hover(sel):
            # Pega o índice do nó que o mouse está sobre
            node_index = sel.target.ind[0]
            # Pega o ID do nó correspondente da nossa lista ordenada
            node_id = node_ids_ordenados[node_index]
            # Pega os metadados que guardamos no nó
            metadata = G.nodes[node_id]
            
            # Formata o texto do tooltip
            texto_tooltip = (
                f"Pessoa: {metadata['pessoa']}\n"
                f"Câmera: {metadata['camera']}\n"
                f"Andar: {metadata['andar']}\n"
                f"Sala: {metadata['sala']}\n"
                f"Horário: {metadata['horario']}"
            )
            sel.annotation.set_text(texto_tooltip)
            sel.annotation.get_bbox_patch().set(facecolor='white', alpha=0.9)


# --- Classe Principal da Aplicação (Controlador) ---
class AppPrincipal(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        
        self.parametros = carregar_parametros_db()
        if self.parametros is None:
            messagebox.showerror("Erro Fatal", "Aplicação não pode iniciar sem parâmetros válidos.")
            self.destroy()
            return

        self.title(f"Health Track Unimed - UEPG (Fotos: {self.parametros.get('fotos')})")
        self.geometry("950x700") # (MODIFICADO V6.0) Aumentei a largura
        
        style = ttk.Style(self)
        style.theme_use("default") 
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"))
        style.configure("Treeview", rowheight=25, font=("Arial", 10))

        # --- Menu Lateral ---
        menu_frame = tk.Frame(self, bg="#f0f0f0", width=200, relief=tk.RAISED, borderwidth=1)
        menu_frame.pack(side="left", fill="y", padx=(5,0), pady=5)
        menu_frame.pack_propagate(False) 

        tk.Label(menu_frame, text="MENU", font=("Arial", 16, "bold"), bg="#f0f0f0").pack(pady=15)
        
        # --- Conteúdo Principal ---
        content_frame = tk.Frame(self, bg="white")
        content_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)

        # (MODIFICADO V6.0) Botões do Menu
        botoes_menu = [
            ("Gerenciar Pessoas", "ListarPessoasFrame"),  
            ("Gerenciar Câmeras", "ListarCamerasFrame"), 
            ("Acompanhamento por Área", "AcompanhamentoAreaFrame"), # Renomeado
            ("Acompanhamento por Pessoa", "AcompanhamentoPessoaFrame"), # Novo
            ("Parâmetros", "ParametrosFrame")          
        ]
        
        for texto, frame_nome in botoes_menu:
            btn = tk.Button(menu_frame, text=texto, font=("Arial", 12),
                            command=lambda nome=frame_nome: self.show_frame(nome),
                            anchor="w", justify="left",
                            padx=10)
            btn.pack(fill="x", pady=5, padx=10)

        # (MODIFICADO V6.0) Lista de Frames
        self.frames = {}
        for F in (HomeFrame, 
                  ListarPessoasFrame, CadastroFacialFrame, 
                  ListarCamerasFrame, CadastroCamerasFrame, 
                  AcompanhamentoAreaFrame, AcompanhamentoPessoaFrame, # Atualizado
                  ParametrosFrame):
            page_name = F.__name__
            frame = F(parent=content_frame, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.current_frame_name = None
        self.show_frame("HomeFrame")

    def recarregar_parametros(self):
        """Recarrega os parâmetros do DB e atualiza o estado global."""
        self.parametros = carregar_parametros_db()
        self.title(f"Health Track Unimed - UEPG (Fotos: {self.parametros.get('fotos')})")
        print("Parâmetros globais recarregados.")
        
    def show_frame(self, page_name):
        if self.current_frame_name == page_name:
            return
            
        # (MODIFICADO V6.0) Limpa o grafo ao sair da tela de pessoa
        if self.current_frame_name == "AcompanhamentoPessoaFrame":
            self.frames["AcompanhamentoPessoaFrame"].limpar_grafo()
            
        if self.current_frame_name == "CadastroFacialFrame":
            self.frames["CadastroFacialFrame"].release_camera()
        
        if page_name == "CadastroFacialFrame":
            self.frames["CadastroFacialFrame"].iniciar_camera()
            
        frame = self.frames[page_name]
        
        if hasattr(frame, "on_show"):
            frame.on_show()
            
        frame.tkraise()
        self.current_frame_name = page_name

    def abrir_edicao_pessoa(self, pessoa_id):
        """Prepara o frame de cadastro para edição e o exibe."""
        frame = self.frames["CadastroFacialFrame"]
        frame.carregar_dados(pessoa_id)
        self.show_frame("CadastroFacialFrame")

    def abrir_edicao_camera(self, camera_id):
        """Prepara o frame de câmeras para edição e o exibe."""
        frame = self.frames["CadastroCamerasFrame"]
        frame.carregar_dados(camera_id)
        self.show_frame("CadastroCamerasFrame")

    def on_closing(self):
        print("Fechando aplicação...")
        # (MODIFICADO V6.0) Garante que a câmera seja liberada
        if "CadastroFacialFrame" in self.frames:
            self.frames["CadastroFacialFrame"].release_camera()
        # (MODIFICADO V6.0) Garante que as figuras do matplotlib sejam fechadas
        if "AcompanhamentoPessoaFrame" in self.frames:
            self.frames["AcompanhamentoPessoaFrame"].limpar_grafo()
        plt.close('all')
        self.destroy()

# --- Ponto de Entrada da Aplicação ---
if __name__ == "__main__":
    
    # (MODIFICADO V6.0) Verifica a tabela de parâmetros ANTES de iniciar o app
    # Isso é crucial caso o DB não esteja pronto
    try:
        inicializar_db_parametros()
    except Exception as e:
        messagebox.showerror("Erro Crítico de Inicialização", f"Não foi possível inicializar os parâmetros do banco.\nVerifique a conexão e a estrutura das tabelas.\n\nErro: {e}")
        # Sai se não puder inicializar
        exit() 
        
    app = AppPrincipal()
    app.mainloop()