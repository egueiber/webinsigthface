# -*- coding: utf-8 -*-
"""
Módulo de Serviço do Dashboard (Backend)

Centraliza a lógica de negócio para buscar e calcular
os dados exibidos no dashboard.
"""
from backend.services.database_service import get_db_connection
from backend.services.location_service import list_locations
from datetime import timedelta


def get_indicators(start_date: str, end_date: str, location_id: int = None):
    """
    Busca os dados para os três principais indicadores do dashboard,
    com filtro opcional por localização.
    """
    conn = get_db_connection()
    indicators = {}

    try:
        with conn.cursor() as cur:

            filtered_persons_sql = ""
            params_persons = ()

            # Se um local foi especificado, primeiro buscamos as pessoas relevantes
            if location_id:
                filtered_persons_sql = """
                    WITH PersonsInLocation AS (
                        SELECT DISTINCT p."idPessoa"
                        FROM sch_supervisorio.tb_pessoa p
                        JOIN sch_supervisorio.tb_videos_processados v ON p."fotosPessoa" = v."nomePastaPessoa"
                        JOIN sch_supervisorio.tb_cameras c ON v."nomeCamera" = c."nomeCamera"
                        WHERE c.idlocalizacao = %s
                          AND v.datahoraprocessamento::date BETWEEN %s AND %s
                    )
                """
                params_persons = (location_id, start_date, end_date)

            # --- 1. Total de pessoas atendidas ---
            sql_served = f"""
                {filtered_persons_sql}
                SELECT COUNT(DISTINCT ev.idpessoa)
                FROM sch_supervisorio.tb_pessoa_evento ev
                WHERE ev.datahoraefetivasaida IS NOT NULL
                  AND ev.datahoraefetivasaida::date BETWEEN %s AND %s
            """
            params_served = [start_date, end_date]
            if location_id:
                sql_served += " AND ev.idpessoa IN (SELECT \"idPessoa\" FROM PersonsInLocation)"
                params_served = list(params_persons) + params_served

            cur.execute(sql_served, tuple(params_served))
            indicators['total_served'] = cur.fetchone()[0] or 0

            # --- 2. Tempo médio de atendimento ---
            sql_avg_time = f"""
                {filtered_persons_sql}
                SELECT AVG(ev.datahoraefetivasaida - ev.datahoraentrada)
                FROM sch_supervisorio.tb_pessoa_evento ev
                WHERE ev.datahoraefetivasaida IS NOT NULL
                  AND ev.datahoraefetivasaida::date BETWEEN %s AND %s
            """
            params_time = [start_date, end_date]
            if location_id:
                sql_avg_time += " AND ev.idpessoa IN (SELECT \"idPessoa\" FROM PersonsInLocation)"
                params_time = list(params_persons) + params_time

            cur.execute(sql_avg_time, tuple(params_time))
            avg_time = cur.fetchone()[0]
            indicators['average_time'] = str(avg_time) if avg_time else "00:00:00"

            # --- 3. Total de pessoas presentes ---
            sql_present = f"""
                {filtered_persons_sql}
                SELECT COUNT(DISTINCT ev.idpessoa)
                FROM sch_supervisorio.tb_pessoa_evento ev
                WHERE ev.datahoraentrada::date BETWEEN %s AND %s
                  AND ev.datahoraefetivasaida IS NULL
                  AND (ev.eventocancelado IS NULL OR ev.eventocancelado = FALSE)
            """
            params_present = [start_date, end_date]
            if location_id:
                sql_present += " AND ev.idpessoa IN (SELECT \"idPessoa\" FROM PersonsInLocation)"
                params_present = list(params_persons) + params_present

            cur.execute(sql_present, tuple(params_present))
            indicators['total_present'] = cur.fetchone()[0] or 0

    except Exception as e:
        raise Exception(f"Erro ao calcular indicadores do dashboard: {e}")
    finally:
        conn.close()

    return indicators


def get_delayed_persons(start_date: str, end_date: str, location_id: int = None):
    """
    Busca pessoas com atendimento em atraso, com filtro opcional por localização.
    Retorna uma lista de dicts com id, name, delay_time, last_location.
    """
    conn = get_db_connection()

    sql = """
        WITH LastLocation AS (
            SELECT 
                p."idPessoa",
                l.nomelocalizacao,
                l.idlocalizacao,
                ROW_NUMBER() OVER(PARTITION BY p."idPessoa" ORDER BY v.datahoraprocessamento DESC) as rn
            FROM sch_supervisorio.tb_pessoa p
            JOIN sch_supervisorio.tb_videos_processados v ON p."fotosPessoa" = v."nomePastaPessoa"
            JOIN sch_supervisorio.tb_cameras c ON v."nomeCamera" = c."nomeCamera"
            JOIN sch_supervisorio.tb_localizacao l ON c.idlocalizacao = l.idlocalizacao
            WHERE v.datahoraprocessamento::date <= %s
        )
        SELECT 
            p."idPessoa",
            p."nomePessoa",
            (CURRENT_TIMESTAMP - pe.datahoraprevistasaida) as delay_time,
            COALESCE(ul.nomelocalizacao, 'Unknown') as last_location
        FROM sch_supervisorio.tb_pessoa p
        JOIN sch_supervisorio.tb_pessoa_evento pe ON p."idPessoa" = pe.idpessoa
        LEFT JOIN LastLocation ul ON p."idPessoa" = ul."idPessoa" AND ul.rn = 1
        WHERE pe.datahoraentrada::date BETWEEN %s AND %s
          AND pe.datahoraefetivasaida IS NULL
          AND (pe.eventocancelado IS NULL OR pe.eventocancelado = FALSE)
          AND pe.datahoraprevistasaida < CURRENT_TIMESTAMP
    """

    params = [end_date, start_date, end_date]

    if location_id:
        sql += " AND ul.idlocalizacao = %s"
        params.append(location_id)

    sql += " ORDER BY delay_time DESC;"

    results = []
    try:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            rows = cur.fetchall()
            for person_id, name, delay_delta, last_location in rows:
                total_seconds = int(delay_delta.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                delay_formatted = f"{hours:02}:{minutes:02}:{seconds:02}"
                results.append({
                    "id": person_id,
                    "name": name,
                    "delay_time": delay_formatted,
                    "last_location": last_location
                })

    except Exception as e:
        raise Exception(f"Erro ao buscar pessoas com atraso: {e}")
    finally:
        conn.close()

    return results


def get_locations_for_filter():
    """
    Busca as localizações para usar como filtro.
    Retorna uma lista de tuplas (id, nome).
    """
    return list_locations()