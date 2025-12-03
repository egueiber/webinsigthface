# -*- coding: utf-8 -*-
"""
Módulo de Serviço de Localização (Backend)

Centraliza a lógica de negócio para o cadastro de localizações.
"""
from .database_service import get_db_connection
from tkinter import messagebox
import os
import shutil

def listar_localizacoes_db(filtro_nome=""):
    sql = """
        SELECT idlocalizacao, nomelocalizacao
        FROM sch_supervisorio.tb_localizacao
        WHERE nomelocalizacao ILIKE %s
        ORDER BY nomelocalizacao
    """
    conn = get_db_connection()
    if conn is None: return []
    resultados = []
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (f"%{filtro_nome}%",))
            resultados = cur.fetchall()
    except Exception as e:
        messagebox.showerror("Erro de Consulta", f"Erro ao listar localizações:\n{e}")
    finally:
        conn.close()
    return resultados

def get_localizacao_por_id_db(localizacao_id):
    sql = 'SELECT nomelocalizacao, mapacamera FROM sch_supervisorio.tb_localizacao WHERE idlocalizacao = %s'
    conn = get_db_connection()
    if conn is None: return None
    localizacao = None
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (localizacao_id,))
            result = cur.fetchone()
            if result:
                localizacao = {"nome": result[0], "mapa_path": result[1]}
    except Exception as e:
        messagebox.showerror("Erro de Consulta", f"Erro ao buscar localização ID {localizacao_id}:\n{e}")
    finally:
        conn.close()
    return localizacao

def salvar_localizacao_no_banco(nome, mapa_path, localizacao_id=None):
    conn = get_db_connection()
    if conn is None: return False
    try:
        if localizacao_id:
            sql = """
                UPDATE sch_supervisorio.tb_localizacao
                SET nomelocalizacao = %s, mapacamera = %s
                WHERE idlocalizacao = %s
            """
            params = (nome, mapa_path, localizacao_id)
        else:
            sql = """
                INSERT INTO sch_supervisorio.tb_localizacao
                (nomelocalizacao, mapacamera)
                VALUES (%s, %s)
            """
            params = (nome, mapa_path)
        with conn.cursor() as cur:
            cur.execute(sql, params)
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        if "unique constraint" in str(e):
             messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar: A localização '{nome}' já está cadastrada.")
        else:
             messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar os dados no banco:\n{e}")
        return False
    finally:
        conn.close()

def excluir_localizacao_db(localizacao_id, mapa_path):
    conn = get_db_connection()
    if conn is None: return False
    sql = 'DELETE FROM sch_supervisorio.tb_localizacao WHERE idlocalizacao = %s'
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (localizacao_id,))
        conn.commit()
        if mapa_path and os.path.exists(mapa_path):
            try:
                os.remove(mapa_path)
                print(f"[TEMP] Arquivo de mapa excluído: {mapa_path}")
            except Exception as e_fs:
                messagebox.showwarning("Aviso", f"Localização excluída do banco, mas falha ao excluir arquivo de mapa:\n{e_fs}")
        return True
    except Exception as e:
        conn.rollback()
        messagebox.showerror("Erro ao Excluir", f"Não foi possível excluir a localização:\n{e}")
        return False
    finally:
        conn.close()
