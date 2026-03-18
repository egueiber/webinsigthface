# -*- coding: utf-8 -*-
"""
Módulo de Serviço de Evento (Backend)

Centraliza a lógica de negócio para o cadastro de eventos.
"""
from backend.services.database_service import get_db_connection


def list_events(name_filter: str = ""):
    sql = """
        SELECT idevento, nomeevento, eventoduracao
        FROM sch_supervisorio.tb_evento
        WHERE nomeevento ILIKE %s
        ORDER BY nomeevento
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


def get_event_by_id(event_id: int):
    sql = 'SELECT nomeevento, eventoduracao FROM sch_supervisorio.tb_evento WHERE idevento = %s'
    conn = get_db_connection()
    event = None
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (event_id,))
            result = cur.fetchone()
            if result:
                event = {"name": result[0], "duration": result[1]}
    finally:
        conn.close()
    return event


def save_event(name: str, duration: int, event_id: int = None):
    conn = get_db_connection()
    try:
        if event_id:
            sql = """
                UPDATE sch_supervisorio.tb_evento
                SET nomeevento = %s, eventoduracao = %s
                WHERE idevento = %s
            """
            params = (name, duration, event_id)
        else:
            sql = """
                INSERT INTO sch_supervisorio.tb_evento
                (nomeevento, eventoduracao)
                VALUES (%s, %s)
            """
            params = (name, duration)
        with conn.cursor() as cur:
            cur.execute(sql, params)
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        if "unique constraint" in str(e):
            raise Exception(f"O evento '{name}' já está cadastrado.")
        raise Exception(f"Não foi possível salvar os dados no banco: {e}")
    finally:
        conn.close()


def delete_event(event_id: int):
    conn = get_db_connection()
    sql = 'DELETE FROM sch_supervisorio.tb_evento WHERE idevento = %s'
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (event_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise Exception(f"Não foi possível excluir o evento: {e}")
    finally:
        conn.close()