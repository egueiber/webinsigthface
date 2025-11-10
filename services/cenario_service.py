# -*- coding: utf-8 -*-
"""
Módulo de Serviço de Cenário (Backend)

Centraliza a lógica de negócio para o cadastro de cenários.
"""
from .database_service import get_db_connection
from tkinter import messagebox

def listar_cenarios_db(filtro_nome=""):
    """Lista todos os cenários, com um filtro opcional por nome."""
    sql = """
        SELECT idcenario, descricaocenario, idparametro, ativo, padrao
        FROM sch_supervisorio.tb_cenario
        WHERE descricaocenario ILIKE %s
        ORDER BY descricaocenario
    """
    conn = get_db_connection()
    if conn is None: return []
    resultados = []
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (f"%{filtro_nome}%",))
            resultados = cur.fetchall()
    except Exception as e:
        messagebox.showerror("Erro de Consulta", f"Erro ao listar cenários:\n{e}")
    finally:
        conn.close()
    return resultados

def get_cenario_por_id_db(cenario_id):
    """Busca um cenário específico pelo seu ID."""
    sql = 'SELECT descricaocenario, idparametro, ativo, padrao FROM sch_supervisorio.tb_cenario WHERE idcenario = %s'
    conn = get_db_connection()
    if conn is None: return None
    cenario = None
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (cenario_id,))
            result = cur.fetchone()
            if result:
                cenario = {
                    "descricao": result[0], 
                    "idparametro": result[1],
                    "ativo": result[2],
                    "padrao": result[3]
                }
    except Exception as e:
        messagebox.showerror("Erro de Consulta", f"Erro ao buscar cenário ID {cenario_id}:\n{e}")
    finally:
        conn.close()
    return cenario

def salvar_cenario_no_banco(descricao, idparametro, ativo, padrao, cenario_id=None):
    """Salva um novo cenário ou atualiza um existente."""
    conn = get_db_connection()
    if conn is None: return False
    try:
        if cenario_id:
            sql = """
                UPDATE sch_supervisorio.tb_cenario
                SET descricaocenario = %s, idparametro = %s, ativo = %s, padrao = %s
                WHERE idcenario = %s
            """
            params = (descricao, idparametro, ativo, padrao, cenario_id)
        else:
            sql = """
                INSERT INTO sch_supervisorio.tb_cenario
                (descricaocenario, idparametro, ativo, padrao)
                VALUES (%s, %s, %s, %s) RETURNING idcenario;
            """
            params = (descricao, idparametro, ativo, padrao)
        
        with conn.cursor() as cur:
            cur.execute(sql, params)
            if not cenario_id:
                cenario_id = cur.fetchone()[0]
        conn.commit()
        return cenario_id
    except Exception as e:
        conn.rollback()
        if "unique constraint" in str(e):
             messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar: O cenário '{descricao}' já está cadastrado.")
        else:
             messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar os dados do cenário no banco:\n{e}")
        return None
    finally:
        conn.close()

def excluir_cenario_db(cenario_id):
    """Exclui um cenário do banco de dados."""
    conn = get_db_connection()
    if conn is None: return False
    sql = 'DELETE FROM sch_supervisorio.tb_cenario WHERE idcenario = %s'
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (cenario_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        messagebox.showerror("Erro ao Excluir", f"Não foi possível excluir o cenário:\n{e}")
        return False
    finally:
        conn.close()

def get_cameras_para_cenario_db(cenario_id):
    """Lista as câmeras associadas a um cenário."""
    sql = """
        SELECT cc.idcenariocamera, c."idCamera", c."nomeCamera"
        FROM sch_supervisorio.tb_cenariocamera cc
        JOIN sch_supervisorio.tb_cameras c ON cc."idcamera" = c."idCamera"
        WHERE cc."idcenario" = %s
        ORDER BY c."nomeCamera"
    """
    conn = get_db_connection()
    if conn is None: return []
    resultados = []
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (cenario_id,))
            resultados = cur.fetchall()
    except Exception as e:
        messagebox.showerror("Erro de Consulta", f"Erro ao listar câmeras do cenário:\n{e}")
    finally:
        conn.close()
    return resultados

def adicionar_camera_cenario_db(cenario_id, camera_id):
    """Adiciona uma câmera a um cenário."""
    sql = "INSERT INTO sch_supervisorio.tb_cenariocamera (idcenario, idcamera) VALUES (%s, %s)"
    conn = get_db_connection()
    if conn is None: return False
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (cenario_id, camera_id))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        messagebox.showerror("Erro ao Adicionar", f"Não foi possível adicionar a câmera ao cenário:\n{e}")
        return False
    finally:
        conn.close()

def remover_camera_cenario_db(cenariocamera_id):
    """Remove uma câmera de um cenário."""
    sql = "DELETE FROM sch_supervisorio.tb_cenariocamera WHERE idcenariocamera = %s"
    conn = get_db_connection()
    if conn is None: return False
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (cenariocamera_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        messagebox.showerror("Erro ao Remover", f"Não foi possível remover a câmera do cenário:\n{e}")
        return False
    finally:
        conn.close()

def listar_cameras_disponiveis_db():
    """Lista todas as câmeras disponíveis para serem adicionadas a um cenário."""
    sql = """SELECT "idCamera", "nomeCamera" FROM sch_supervisorio.tb_cameras ORDER BY "nomeCamera" """
    conn = get_db_connection()
    if conn is None: return []
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()
    except Exception as e:
        messagebox.showerror("Erro de Consulta", f"Erro ao listar câmeras disponíveis:\n{e}")
        return []
    finally:
        conn.close()

def listar_parametros_disponiveis_db():
    """Lista todos os parâmetros disponíveis."""
    sql = """SELECT "idParametro", nomeparametro FROM sch_supervisorio.tb_parametro ORDER BY nomeparametro"""
    conn = get_db_connection()
    if conn is None: return []
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()
    except Exception as e:
        messagebox.showerror("Erro de Consulta", f"Erro ao listar parâmetros disponíveis:\n{e}")
        return []
    finally:
        conn.close()
