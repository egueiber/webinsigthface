# -*- coding: utf-8 -*-
"""
Módulo de Serviço de Cenário (Backend)

Centraliza a lógica de negócio para o cadastro de cenários.
"""
from backend.services.database_service import get_db_connection


def list_scenarios(name_filter: str = ""):
    """Lista todos os cenários, com um filtro opcional por nome."""
    sql = """
        SELECT idcenario, descricaocenario, idparametro, ativo, padrao
        FROM sch_supervisorio.tb_cenario
        WHERE descricaocenario ILIKE %s
        ORDER BY descricaocenario
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


def get_scenario_by_id(scenario_id: int):
    """Busca um cenário específico pelo seu ID."""
    sql = 'SELECT descricaocenario, idparametro, ativo, padrao FROM sch_supervisorio.tb_cenario WHERE idcenario = %s'
    conn = get_db_connection()
    scenario = None
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (scenario_id,))
            result = cur.fetchone()
            if result:
                scenario = {
                    "description": result[0],
                    "parameter_id": result[1],
                    "active": result[2],
                    "default": result[3]
                }
    finally:
        conn.close()
    return scenario


def save_scenario(description: str, parameter_id: int, active: bool, default: bool, scenario_id: int = None):
    """Salva um novo cenário ou atualiza um existente."""
    conn = get_db_connection()
    try:
        if scenario_id:
            sql = """
                UPDATE sch_supervisorio.tb_cenario
                SET descricaocenario = %s, idparametro = %s, ativo = %s, padrao = %s
                WHERE idcenario = %s
            """
            params = (description, parameter_id, active, default, scenario_id)
        else:
            sql = """
                INSERT INTO sch_supervisorio.tb_cenario
                (descricaocenario, idparametro, ativo, padrao)
                VALUES (%s, %s, %s, %s) RETURNING idcenario;
            """
            params = (description, parameter_id, active, default)

        with conn.cursor() as cur:
            cur.execute(sql, params)
            if not scenario_id:
                scenario_id = cur.fetchone()[0]
        conn.commit()
        return scenario_id
    except Exception as e:
        conn.rollback()
        if "unique constraint" in str(e):
            raise Exception(f"O cenário '{description}' já está cadastrado.")
        raise Exception(f"Não foi possível salvar os dados do cenário no banco: {e}")
    finally:
        conn.close()


def delete_scenario(scenario_id: int):
    """Exclui um cenário do banco de dados."""
    conn = get_db_connection()
    sql = 'DELETE FROM sch_supervisorio.tb_cenario WHERE idcenario = %s'
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (scenario_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise Exception(f"Não foi possível excluir o cenário: {e}")
    finally:
        conn.close()


def get_cameras_for_scenario(scenario_id: int):
    """Lista as câmeras associadas a um cenário."""
    sql = """
        SELECT cc.idcenariocamera, c."idCamera", c."nomeCamera"
        FROM sch_supervisorio.tb_cenariocamera cc
        JOIN sch_supervisorio.tb_cameras c ON cc."idcamera" = c."idCamera"
        WHERE cc."idcenario" = %s
        ORDER BY c."nomeCamera"
    """
    conn = get_db_connection()
    results = []
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (scenario_id,))
            results = cur.fetchall()
    finally:
        conn.close()
    return results


def add_camera_to_scenario(scenario_id: int, camera_id: int):
    """Adiciona uma câmera a um cenário."""
    sql = "INSERT INTO sch_supervisorio.tb_cenariocamera (idcenario, idcamera) VALUES (%s, %s)"
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (scenario_id, camera_id))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise Exception(f"Não foi possível adicionar a câmera ao cenário: {e}")
    finally:
        conn.close()


def remove_camera_from_scenario(scenario_camera_id: int):
    """Remove uma câmera de um cenário."""
    sql = "DELETE FROM sch_supervisorio.tb_cenariocamera WHERE idcenariocamera = %s"
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (scenario_camera_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise Exception(f"Não foi possível remover a câmera do cenário: {e}")
    finally:
        conn.close()


def list_available_cameras():
    """Lista todas as câmeras disponíveis para serem adicionadas a um cenário."""
    sql = """SELECT "idCamera", "nomeCamera" FROM sch_supervisorio.tb_cameras ORDER BY "nomeCamera" """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()
    finally:
        conn.close()


def list_available_parameters():
    """Lista todos os parâmetros disponíveis."""
    sql = """SELECT "idParametro", nomeparametro FROM sch_supervisorio.tb_parametro ORDER BY nomeparametro"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()
    finally:
        conn.close()