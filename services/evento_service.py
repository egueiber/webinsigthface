# -*- coding: utf-8 -*-
"""
Módulo de Serviço de Evento (Backend)

Centraliza a lógica de negócio para o cadastro de eventos.
"""
from .database_service import get_db_connection
from tkinter import messagebox

def listar_eventos_db(filtro_nome=""):
    sql = """
        SELECT idevento, nomeevento, eventoduracao
        FROM sch_supervisorio.tb_evento
        WHERE nomeevento ILIKE %s
        ORDER BY nomeevento
    """
    conn = get_db_connection()
    if conn is None: return []
    resultados = []
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (f"%{filtro_nome}%",))
            resultados = cur.fetchall()
    except Exception as e:
        messagebox.showerror("Erro de Consulta", f"Erro ao listar eventos:\n{e}")
    finally:
        conn.close()
    return resultados

def get_evento_por_id_db(evento_id):
    sql = 'SELECT nomeevento, eventoduracao FROM sch_supervisorio.tb_evento WHERE idevento = %s'
    conn = get_db_connection()
    if conn is None: return None
    evento = None
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (evento_id,))
            result = cur.fetchone()
            if result:
                evento = {"nome": result[0], "duracao": result[1]}
    except Exception as e:
        messagebox.showerror("Erro de Consulta", f"Erro ao buscar evento ID {evento_id}:\n{e}")
    finally:
        conn.close()
    return evento

def salvar_evento_no_banco(nome, duracao, evento_id=None):
    conn = get_db_connection()
    if conn is None: return False
    try:
        if evento_id:
            sql = """
                UPDATE sch_supervisorio.tb_evento
                SET nomeevento = %s, eventoduracao = %s
                WHERE idevento = %s
            """
            params = (nome, duracao, evento_id)
        else:
            sql = """
                INSERT INTO sch_supervisorio.tb_evento
                (nomeevento, eventoduracao)
                VALUES (%s, %s)
            """
            params = (nome, duracao)
        with conn.cursor() as cur:
            cur.execute(sql, params)
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        if "unique constraint" in str(e):
             messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar: O evento '{nome}' já está cadastrado.")
        else:
             messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar os dados no banco:\n{e}")
        return False
    finally:
        conn.close()

def excluir_evento_db(evento_id):
    conn = get_db_connection()
    if conn is None: return False
    sql = 'DELETE FROM sch_supervisorio.tb_evento WHERE idevento = %s'
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (evento_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        messagebox.showerror("Erro ao Excluir", f"Não foi possível excluir o evento:\n{e}")
        return False
    finally:
        conn.close()
