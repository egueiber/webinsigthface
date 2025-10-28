# -*- coding: utf-8 -*-
"""
Módulo de Serviço de Banco de Dados (Backend)

Centraliza toda a comunicação com o banco de dados PostgreSQL.
"""
import psycopg2
from tkinter import messagebox
import os
import shutil

# --- Configuração do Banco de Dados ---
DB_NAME = "postgres"
DB_USER = "supervisorio"
DB_PASS = "supervisorio101"
DB_HOST = "localhost"
DB_PORT = 5432

# --- Conexão ---
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

# --- Funções de Pessoa ---
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

# --- Funções de Câmera ---
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
        if "column" in str(e) and "does not exist" in str(e):
            messagebox.showerror("Erro de Banco de Dados", f"Erro: A tabela 'tb_cameras' está desatualizada.\n{e}\n\nPor favor, execute o script ALTER TABLE para adicionar as colunas 'andarCamera' e 'nrsalaproximaCamera'.")
        else:
            messagebox.showerror("Erro de Consulta", f"Erro ao buscar câmera ID {camera_id}:\n{e}")
    finally:
        conn.close()
    return camera

def salvar_camera_no_banco(nome, localizacao, caminho_mapa, andar, nrsala, camera_id=None):
    conn = get_db_connection()
    if conn is None: return False
    
    try:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT "idCamera", "nomeCamera" FROM sch_supervisorio.tb_cameras WHERE "andarCamera" = %s AND "nrsalaproximaCamera" = %s',
                (andar, nrsala)
            )
            conflito = cur.fetchone()
            
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

# --- Funções de Acompanhamento ---
def get_localizacoes_db():
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

def get_pessoas_por_periodo_db(data_inicio, data_fim):
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
            resultados = [row[0] for row in cur.fetchall()]
    except Exception as e:
        messagebox.showerror("Erro de Consulta", f"Erro ao buscar pessoas por período:\n{e}")
    finally:
        conn.close()
    return resultados

def get_caminho_pessoa_db(nome_pessoa, data_inicio, data_fim):
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