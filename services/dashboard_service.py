# -*- coding: utf-8 -*-
"""
Módulo de Serviço do Dashboard (Backend)

Centraliza a lógica de negócio para buscar e calcular
os dados exibidos no dashboard.
"""
from .database_service import get_db_connection
from .localizacao_service import listar_localizacoes_db
from tkinter import messagebox
from datetime import timedelta

def get_indicadores(data_inicio, data_fim, localizacao_id=None):
    """
    Busca os dados para os três principais indicadores do dashboard,
    com filtro opcional por localização.
    """
    conn = get_db_connection()
    if conn is None:
        return {'total_atendidos': 0, 'tempo_medio': timedelta(0), 'total_presentes': 0}

    indicadores = {}
    
    try:
        with conn.cursor() as cur:
            
            pessoas_filtradas_sql = ""
            params_pessoas = ()

            # Se um local foi especificado, primeiro buscamos as pessoas relevantes
            if localizacao_id:
                pessoas_filtradas_sql = """
                    WITH PessoasNaLocalizacao AS (
                        SELECT DISTINCT p."idPessoa"
                        FROM sch_supervisorio.tb_pessoa p
                        JOIN sch_supervisorio.tb_videos_processados v ON p."fotosPessoa" = v."nomePastaPessoa"
                        JOIN sch_supervisorio.tb_cameras c ON v."nomeCamera" = c."nomeCamera"
                        WHERE c.idlocalizacao = %s
                          AND v.datahoraprocessamento::date BETWEEN %s AND %s
                    )
                """
                params_pessoas = (localizacao_id, data_inicio, data_fim)

            # --- 1. Total de pessoas atendidas ---
            sql_atendidos = f"""
                {pessoas_filtradas_sql}
                SELECT COUNT(DISTINCT ev.idpessoa)
                FROM sch_supervisorio.tb_pessoa_evento ev
                WHERE ev.datahoraefetivasaida IS NOT NULL
                  AND ev.datahoraefetivasaida::date BETWEEN %s AND %s
            """
            params_atendidos = [data_inicio, data_fim]
            if localizacao_id:
                sql_atendidos += " AND ev.idpessoa IN (SELECT \"idPessoa\" FROM PessoasNaLocalizacao)"
                params_atendidos = list(params_pessoas) + params_atendidos
            
            cur.execute(sql_atendidos, tuple(params_atendidos))
            indicadores['total_atendidos'] = cur.fetchone()[0] or 0

            # --- 2. Tempo médio de atendimento ---
            sql_tempo_medio = f"""
                {pessoas_filtradas_sql}
                SELECT AVG(ev.datahoraefetivasaida - ev.datahoraentrada)
                FROM sch_supervisorio.tb_pessoa_evento ev
                WHERE ev.datahoraefetivasaida IS NOT NULL
                  AND ev.datahoraefetivasaida::date BETWEEN %s AND %s
            """
            params_tempo = [data_inicio, data_fim]
            if localizacao_id:
                sql_tempo_medio += " AND ev.idpessoa IN (SELECT \"idPessoa\" FROM PessoasNaLocalizacao)"
                params_tempo = list(params_pessoas) + params_tempo

            cur.execute(sql_tempo_medio, tuple(params_tempo))
            indicadores['tempo_medio'] = cur.fetchone()[0] or timedelta(0)

            # --- 3. Total de pessoas presentes ---
            sql_presentes = f"""
                {pessoas_filtradas_sql}
                SELECT COUNT(DISTINCT ev.idpessoa)
                FROM sch_supervisorio.tb_pessoa_evento ev
                WHERE ev.datahoraentrada::date BETWEEN %s AND %s
                  AND ev.datahoraefetivasaida IS NULL
                  AND (ev.eventocancelado IS NULL OR ev.eventocancelado = FALSE)
            """
            params_presentes = [data_inicio, data_fim]
            if localizacao_id:
                sql_presentes += " AND ev.idpessoa IN (SELECT \"idPessoa\" FROM PessoasNaLocalizacao)"
                params_presentes = list(params_pessoas) + params_presentes

            cur.execute(sql_presentes, tuple(params_presentes))
            indicadores['total_presentes'] = cur.fetchone()[0] or 0
            
    except Exception as e:
        messagebox.showerror("Erro de Consulta", f"Erro ao calcular indicadores do dashboard:\n{e}")
        return {'total_atendidos': 0, 'tempo_medio': timedelta(0), 'total_presentes': 0}
    finally:
        conn.close()
        
    return indicadores



def get_pessoas_com_atraso(data_inicio, data_fim, localizacao_id=None):
    """
    Busca pessoas com atendimento em atraso, com filtro opcional por localização.
    Retorna uma lista de tuplas com (idPessoa, nomePessoa, tempo_de_atraso_formatado, ultima_localizacao).
    """
    conn = get_db_connection()
    if conn is None: return []

    # Subquery para encontrar a última localização de cada pessoa
    sql = """
        WITH UltimaLocalizacao AS (
            SELECT 
                p."idPessoa",
                l.nomelocalizacao,
                l.idlocalizacao,
                ROW_NUMBER() OVER(PARTITION BY p."idPessoa" ORDER BY v.datahoraprocessamento DESC) as rn
            FROM sch_supervisorio.tb_pessoa p
            JOIN sch_supervisorio.tb_videos_processados v ON p."fotosPessoa" = v."nomePastaPessoa"
            JOIN sch_supervisorio.tb_cameras c ON v."nomeCamera" = c."nomeCamera"
            JOIN sch_supervisorio.tb_localizacao l ON c.idlocalizacao = l.idlocalizacao
            WHERE v.datahoraprocessamento::date <= %s -- Considera histórico até a data fim
        )
        SELECT 
            p."idPessoa",
            p."nomePessoa",
            (CURRENT_TIMESTAMP - pe.datahoraprevistasaida) as tempo_atraso,
            COALESCE(ul.nomelocalizacao, 'Desconhecida') as ultima_localizacao
        FROM sch_supervisorio.tb_pessoa p
        JOIN sch_supervisorio.tb_pessoa_evento pe ON p."idPessoa" = pe.idpessoa
        LEFT JOIN UltimaLocalizacao ul ON p."idPessoa" = ul."idPessoa" AND ul.rn = 1
        WHERE pe.datahoraentrada::date BETWEEN %s AND %s
          AND pe.datahoraefetivasaida IS NULL
          AND (pe.eventocancelado IS NULL OR pe.eventocancelado = FALSE)
          AND pe.datahoraprevistasaida < CURRENT_TIMESTAMP
    """

    params = [data_fim, data_inicio, data_fim]

    # Adiciona o filtro de localização se um ID for fornecido
    if localizacao_id:
        sql += " AND ul.idlocalizacao = %s"
        params.append(localizacao_id)

    sql += " ORDER BY tempo_atraso DESC;"

    resultados_finais = []
    try:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            resultados = cur.fetchall()
            for id_pessoa, nome, atraso_delta, ultima_localizacao in resultados:
                total_seconds = int(atraso_delta.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                atraso_formatado = f"{hours:02}:{minutes:02}:{seconds:02}"
                resultados_finais.append((id_pessoa, nome, atraso_formatado, ultima_localizacao))

    except Exception as e:
        messagebox.showerror("Erro de Consulta", f"Erro ao buscar pessoas com atraso:\n{e}")
    finally:
        conn.close()
        
    return resultados_finais

    



def get_localizacoes_para_filtro():
    """
    Busca as localizações para usar como filtro.
    Retorna uma lista de tuplas (id, nome).
    """
    try:
        return listar_localizacoes_db()
    except Exception as e:
        messagebox.showerror("Erro de Consulta", f"Erro ao buscar localizações:\n{e}")
        return []
