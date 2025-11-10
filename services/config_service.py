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
                cur.execute("""
                    INSERT INTO sch_supervisorio.tb_parametro (nomeparametro) 
                    VALUES ('Padrão')
                """)
                conn.commit()
                print("[TEMP] Parâmetros inicializados.")
            else:
                print("[TEMP] Parâmetros já existem.")
                
    except Exception as e:
        conn.rollback()
        if "column" in str(e) and "does not exist" in str(e):
             messagebox.showerror("Erro de Banco de Dados", f"Erro: A estrutura da tabela 'tb_parametro' parece estar desatualizada.\n{e}")
        else:
            messagebox.showerror("Erro Crítico de DB", f"Não foi possível ler ou inicializar a 'tb_parametro'.\n{e}")
        return
    finally:
        conn.close()

def listar_parametros_db(filtro_nome=""):
    """Lista todos os conjuntos de parâmetros, com filtro opcional por nome."""
    sql = """
        SELECT "idParametro", nomeparametro
        FROM sch_supervisorio.tb_parametro
        WHERE nomeparametro ILIKE %s
        ORDER BY nomeparametro
    """
    conn = get_db_connection()
    if conn is None: return []
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (f"%{filtro_nome}%",))
            return cur.fetchall()
    except Exception as e:
        messagebox.showerror("Erro de Consulta", f"Erro ao listar parâmetros:\n{e}")
        return []
    finally:
        conn.close()

def get_parametro_por_id_db(param_id):
    """Busca um conjunto de parâmetros específico pelo seu ID."""
    sql = """
        SELECT "idParametro", nomeparametro, "caminhoFotosClientes", "caminhoMapas",
               "caminhoVideoAProcessar", "caminhoVideoProcessados",
               "caminhoVideoMarcoes", "intevalorFrames", "escalaImagem",
               "modeloDeteccao", "toleranciaReconhecimento", "gerarvideomarcacoes"
        FROM sch_supervisorio.tb_parametro WHERE "idParametro" = %s
    """
    conn = get_db_connection()
    if conn is None: return None
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (param_id,))
            result = cur.fetchone()
            if result:
                return {
                    "id": result[0],
                    "nome": result[1],
                    "fotos": result[2],
                    "mapas": result[3],
                    "videos_a_processar": result[4],
                    "videos_processados": result[5],
                    "video_marcoes": result[6],
                    "intervalo_frames": result[7],
                    "escala_imagem": float(result[8]) if result[8] is not None else 1.0,
                    "modelo_deteccao": result[9],
                    "tolerancia": result[10],
                    "gerar_marcoes": result[11]
                }
            return None
    except Exception as e:
        messagebox.showerror("Erro de Consulta", f"Erro ao buscar parâmetro ID {param_id}:\n{e}")
        return None
    finally:
        conn.close()

def salvar_parametros_db(param_data, param_id=None):
    """Salva um novo conjunto de parâmetros ou atualiza um existente."""
    conn = get_db_connection()
    if conn is None: return None

    try:
        with conn.cursor() as cur:
            if param_id:
                sql = """
                    UPDATE sch_supervisorio.tb_parametro
                    SET nomeparametro = %s, "caminhoFotosClientes" = %s, "caminhoMapas" = %s,
                        "caminhoVideoAProcessar" = %s, "caminhoVideoProcessados" = %s,
                        "caminhoVideoMarcoes" = %s, "intevalorFrames" = %s, "escalaImagem" = %s,
                        "modeloDeteccao" = %s, "toleranciaReconhecimento" = %s,
                        "gerarvideomarcacoes" = %s
                    WHERE "idParametro" = %s
                """
                params = (
                    param_data['nome'], param_data['fotos'], param_data['mapas'],
                    param_data['videos_a_processar'], param_data['videos_processados'],
                    param_data['video_marcoes'], param_data['intervalo_frames'],
                    param_data['escala_imagem'], param_data['modelo_deteccao'],
                    param_data['tolerancia'], param_data['gerar_marcoes'], param_id
                )
            else:
                sql = """
                    INSERT INTO sch_supervisorio.tb_parametro (
                        nomeparametro, "caminhoFotosClientes", "caminhoMapas",
                        "caminhoVideoAProcessar", "caminhoVideoProcessados",
                        "caminhoVideoMarcoes", "intevalorFrames", "escalaImagem",
                        "modeloDeteccao", "toleranciaReconhecimento", "gerarvideomarcacoes"
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING "idParametro"
                """
                params = (
                    param_data['nome'], param_data['fotos'], param_data['mapas'],
                    param_data['videos_a_processar'], param_data['videos_processados'],
                    param_data['video_marcoes'], param_data['intervalo_frames'],
                    param_data['escala_imagem'], param_data['modelo_deteccao'],
                    param_data['tolerancia'], param_data['gerar_marcoes']
                )
            
            cur.execute(sql, params)
            if not param_id:
                param_id = cur.fetchone()[0]
        
        conn.commit()
        return param_id
    except Exception as e:
        conn.rollback()
        if "unique constraint" in str(e):
            messagebox.showerror("Erro ao Salvar", f"O nome de parâmetro '{param_data['nome']}' já existe.")
        else:
            messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar os parâmetros:\n{e}")
        return None
    finally:
        conn.close()

def excluir_parametro_db(param_id):
    """Exclui um conjunto de parâmetros do banco de dados."""
    conn = get_db_connection()
    if conn is None: return False
    sql = 'DELETE FROM sch_supervisorio.tb_parametro WHERE "idParametro" = %s'
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (param_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        if "violates foreign key constraint" in str(e):
            messagebox.showerror("Erro ao Excluir", "Não é possível excluir este parâmetro, pois ele está sendo usado por um ou mais cenários.")
        else:
            messagebox.showerror("Erro ao Excluir", f"Não foi possível excluir o parâmetro:\n{e}")
        return False
    finally:
        conn.close()
        
def carregar_parametros_db():
    """Carrega a primeira linha de parâmetros do banco de dados (usado na inicialização)."""
    sql = """
        SELECT "idParametro", nomeparametro, "caminhoFotosClientes", "caminhoMapas",
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
                    "nome": result[1],
                    "fotos": result[2],
                    "mapas": result[3],
                    "videos_a_processar": result[4],
                    "videos_processados": result[5],
                    "video_marcoes": result[6],
                    "intervalo_frames": result[7],
                    "escala_imagem": float(result[8]) if result[8] is not None else 1.0,
                    "modelo_deteccao": result[9],
                    "tolerancia": result[10],
                    "gerar_marcoes": result[11]
                }
    except Exception as e:
        messagebox.showerror("Erro de Consulta", f"Erro ao carregar parâmetros:\n{e}\n\nCertifique-se que a 'tb_parametro' foi atualizada com TODOS os campos.")
    finally:
        conn.close()
    
    if parametros is None:
        messagebox.showerror("Erro Crítico", "Não foi possível carregar os parâmetros de configuração do banco.")
        
    return parametros