# -*- coding: utf-8 -*-
"""
Módulo de Serviço de Configuração (Backend)

Centraliza a lógica de inicialização, leitura e escrita
da tabela de parâmetros do sistema.
"""
from tkinter import messagebox
from services.database_service import get_db_connection

def inicializar_db_parametros():
    """Garante que a tabela de parâmetros tenha pelo menos uma linha de configuração."""
    print("Verificando parâmetros...")
    conn = get_db_connection()
    if conn is None:
        return

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM sch_supervisorio.tb_parametro")
            count = cur.fetchone()[0]
            
            if count == 0:
                print("Inicializando parâmetros padrão no banco de dados...")
                cur.execute('INSERT INTO sch_supervisorio.tb_parametro ("idParametro") VALUES (DEFAULT)')
                conn.commit()
                print("Parâmetros inicializados.")
            else:
                print("Parâmetros já existem.")
                
    except Exception as e:
        conn.rollback()
        if "column" in str(e) and "does not exist" in str(e):
             messagebox.showerror("Erro de Banco de Dados", f"Erro: A estrutura da tabela 'tb_parametro' parece estar desatualizada.\n{e}")
        else:
            messagebox.showerror("Erro Crítico de DB", f"Não foi possível ler ou inicializar a 'tb_parametro'.\n{e}")
        return
    finally:
        conn.close()
        
def carregar_parametros_db():
    """Carrega a primeira linha de parâmetros do banco de dados."""
    sql = """
        SELECT "idParametro", "caminhoFotosClientes", "caminhoMapas",
               "caminhoVideoAProcessar", "caminhoVideoProcessados",
               "caminhoVideoMarcoes", "intevalorFrames", "escalaImagem",
               "modeloDeteccao", "toleranciaReconhecimento", "gerarvideomarcacoes"
        FROM sch_supervisorio.tb_parametro LIMIT 1
    """
    conn = get_db_connection()
    if conn is None: 
        return None
    
    parametros = None
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            result = cur.fetchone()
            if result:
                parametros = {
                    "id": result[0],
                    "fotos": result[1],
                    "mapas": result[2],
                    "videos_a_processar": result[3],
                    "videos_processados": result[4],
                    "video_marcoes": result[5],
                    "intervalo_frames": result[6],
                    "escala_imagem": result[7],
                    "modelo_deteccao": result[8],
                    "tolerancia": result[9],
                    "gerar_marcoes": result[10] 
                }
    except Exception as e:
        messagebox.showerror("Erro de Consulta", f"Erro ao carregar parâmetros:\n{e}\n\nCertifique-se que a 'tb_parametro' foi atualizada com TODOS os campos.")
    finally:
        conn.close()
    
    if parametros is None:
        messagebox.showerror("Erro Crítico", "Não foi possível carregar os parâmetros de configuração do banco.")
        
    return parametros

def salvar_parametros_db(param_id, caminho_fotos, caminho_mapas, 
                         videos_a_processar, videos_processados, 
                         video_marcoes, intervalo_frames, escala_imagem, 
                         modelo_deteccao, tolerancia, gerar_marcoes):
    """Atualiza a linha de parâmetros no banco de dados."""
    sql = """
        UPDATE sch_supervisorio.tb_parametro
        SET "caminhoFotosClientes" = %s, "caminhoMapas" = %s,
            "caminhoVideoAProcessar" = %s, "caminhoVideoProcessados" = %s,
            "caminhoVideoMarcoes" = %s, "intevalorFrames" = %s, "escalaImagem" = %s,
            "modeloDeteccao" = %s, "toleranciaReconhecimento" = %s,
            "gerarvideomarcacoes" = %s
        WHERE "idParametro" = %s
    """
    conn = get_db_connection()
    if conn is None:
        return False
    
    success = False
    try:
        with conn.cursor() as cur:
            params = (caminho_fotos, caminho_mapas, videos_a_processar, videos_processados,
                      video_marcoes, intervalo_frames, escala_imagem, modelo_deteccao, 
                      tolerancia, gerar_marcoes, param_id)
            cur.execute(sql, params)
        conn.commit()
        success = True
        print("Parâmetros salvos no banco com sucesso.")
    except Exception as e:
        conn.rollback()
        messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar os parâmetros:\n{e}")
    finally:
        conn.close()
    return success