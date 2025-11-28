# -*- coding: utf-8 -*-
"""
Módulo de Serviço do Dashboard (Backend)

Centraliza a lógica de negócio para buscar e calcular
os dados exibidos no dashboard.
"""
from .database_service import get_db_connection
from .cenario_service import listar_cenarios_db
from tkinter import messagebox
from datetime import timedelta

def get_indicadores(data_inicio, data_fim, cenario_id=None):
    """
    Busca os dados para os três principais indicadores do dashboard. 
    
    TODO: Implementar o filtro por cenario_id.
    """
    conn = get_db_connection()
    if conn is None:
        return {'total_atendidos': 0, 'tempo_medio': timedelta(0), 'total_presentes': 0}

    indicadores = {}
    
    try:
        with conn.cursor() as cur:
            # 1. Total de pessoas atendidas
            sql_atendidos = """
                SELECT COUNT(DISTINCT idpessoa)
                FROM sch_supervisorio.tb_pessoa_evento
                WHERE datahoraefetivasaida IS NOT NULL
                  AND datahoraefetivasaida::date BETWEEN %s AND %s
            """
            cur.execute(sql_atendidos, (data_inicio, data_fim))
            indicadores['total_atendidos'] = cur.fetchone()[0] or 0

            # 2. Tempo médio de atendimento
            sql_tempo_medio = """
                SELECT AVG(datahoraefetivasaida - datahoraentrada)
                FROM sch_supervisorio.tb_pessoa_evento
                WHERE datahoraefetivasaida IS NOT NULL
                  AND datahoraefetivasaida::date BETWEEN %s AND %s
            """
            cur.execute(sql_tempo_medio, (data_inicio, data_fim))
            indicadores['tempo_medio'] = cur.fetchone()[0] or timedelta(0)

            # 3. Total de pessoas presentes
            sql_presentes = """
                SELECT COUNT(DISTINCT idpessoa)
                FROM sch_supervisorio.tb_pessoa_evento
                WHERE datahoraentrada::date BETWEEN %s AND %s
                  AND datahoraefetivasaida IS NULL
                  AND (eventocancelado IS NULL OR eventocancelado = FALSE)
            """
            cur.execute(sql_presentes, (data_inicio, data_fim))
            indicadores['total_presentes'] = cur.fetchone()[0] or 0
            
    except Exception as e:
        messagebox.showerror("Erro de Consulta", f"Erro ao calcular indicadores do dashboard:\n{e}")
        return {'total_atendidos': 0, 'tempo_medio': timedelta(0), 'total_presentes': 0}
    finally:
        conn.close()
        
    return indicadores

def get_pessoas_com_atraso(data_inicio, data_fim, cenario_id=None):
    """
    Busca pessoas com atendimento em atraso.
    
    Retorna uma lista de tuplas com (idPessoa, nomePessoa, tempo_de_atraso_formatado, ultima_localizacao).
    
    TODO: Implementar o filtro por cenario_id e encontrar a última localização.
    """
    conn = get_db_connection()
    if conn is None: return []

    # A query para encontrar a última localização é complexa.
    # Por enquanto, vamos retornar um valor fixo.
    sql = """
        SELECT 
            p."idPessoa",
            p."nomePessoa",
            (CURRENT_TIMESTAMP - pe.datahoraprevistasaida) as tempo_atraso
        FROM sch_supervisorio.tb_pessoa p
        JOIN sch_supervisorio.tb_pessoa_evento pe ON p."idPessoa" = pe.idpessoa
        WHERE pe.datahoraentrada::date BETWEEN %s AND %s
          AND pe.datahoraefetivasaida IS NULL
          AND (pe.eventocancelado IS NULL OR pe.eventocancelado = FALSE)
          AND pe.datahoraprevistasaida < CURRENT_TIMESTAMP
        ORDER BY tempo_atraso DESC;
    """
    params = (data_inicio, data_fim)
    
    resultados_finais = []
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            resultados = cur.fetchall()
            for id_pessoa, nome, atraso_delta in resultados:
                # Formatando o tempo de atraso para HH:MM:SS
                total_seconds = int(atraso_delta.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                atraso_formatado = f"{hours:02}:{minutes:02}:{seconds:02}"
                
                # TODO: Buscar a última localização real da pessoa
                ultima_localizacao = "..."
                
                resultados_finais.append((id_pessoa, nome, atraso_formatado, ultima_localizacao))

    except Exception as e:
        messagebox.showerror("Erro de Consulta", f"Erro ao buscar pessoas com atraso:\n{e}")
    finally:
        conn.close()
        
    return resultados_finais

def get_localizacoes_para_filtro():
    """
    Busca os cenários para usar como filtro de localização.
    Retorna uma lista de tuplas (id, nome).
    """
    # A função listar_cenarios_db retorna uma lista de tuplas com mais campos do que o necessário.
    # Vamos extrair apenas o ID e a descrição.
    try:
        cenarios_raw = listar_cenarios_db()
        # Assumindo que o formato é (idcenario, descricaocenario, idparametro, ativo, padrao)
        return [(c[0], c[1]) for c in cenarios_raw]
    except Exception as e:
        messagebox.showerror("Erro de Consulta", f"Erro ao buscar localizações (cenários):\n{e}")
        return []
