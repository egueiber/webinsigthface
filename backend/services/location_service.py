# -*- coding: utf-8 -*-
"""
Módulo de Serviço de Localização (Backend)

Centraliza a lógica de negócio para o cadastro de localizações.
"""
from backend.services.database_service import get_db_connection
import os


def list_locations(name_filter: str = ""):
    sql = """
        SELECT idlocalizacao, nomelocalizacao
        FROM sch_supervisorio.tb_localizacao
        WHERE nomelocalizacao ILIKE %s
        ORDER BY nomelocalizacao
    """
    conn = get_db_connection()
    results = []
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (f"%{name_filter}%",))
            results = cur.fetchall()
    finally:
        conn.close()
    return results


def get_location_by_id(location_id: int):
    sql = 'SELECT nomelocalizacao, mapacamera FROM sch_supervisorio.tb_localizacao WHERE idlocalizacao = %s'
    conn = get_db_connection()
    location = None
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (location_id,))
            result = cur.fetchone()
            if result:
                location = {"name": result[0], "map_path": result[1]}
    finally:
        conn.close()
    return location


def save_location(name: str, map_path: str, location_id: int = None):
    conn = get_db_connection()
    try:
        if location_id:
            sql = """
                UPDATE sch_supervisorio.tb_localizacao
                SET nomelocalizacao = %s, mapacamera = %s
                WHERE idlocalizacao = %s
            """
            params = (name, map_path, location_id)
            with conn.cursor() as cur:
                cur.execute(sql, params)
            conn.commit()
            return location_id
        else:
            sql = """
                INSERT INTO sch_supervisorio.tb_localizacao
                (nomelocalizacao, mapacamera)
                VALUES (%s, %s)
                RETURNING idlocalizacao
            """
            params = (name, map_path)
            with conn.cursor() as cur:
                cur.execute(sql, params)
                new_id = cur.fetchone()[0]
            conn.commit()
            return new_id
    except Exception as e:
        conn.rollback()
        if "unique constraint" in str(e):
            raise Exception(f"A localização '{name}' já está cadastrada.")
        raise Exception(f"Não foi possível salvar os dados no banco: {e}")
    finally:
        conn.close()


def delete_location(location_id: int, map_path: str = None):
    conn = get_db_connection()
    sql = 'DELETE FROM sch_supervisorio.tb_localizacao WHERE idlocalizacao = %s'
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (location_id,))
        conn.commit()
        if map_path and os.path.exists(map_path):
            try:
                os.remove(map_path)
            except Exception as e:
                print(f"[WARN] Localização excluída do banco, mas falha ao excluir arquivo de mapa: {e}")
        return True
    except Exception as e:
        conn.rollback()
        raise Exception(f"Não foi possível excluir a localização: {e}")
    finally:
        conn.close()