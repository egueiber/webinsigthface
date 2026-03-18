# -*- coding: utf-8 -*-
"""
Módulo de Serviço de Configuração (Backend)

Centraliza a lógica de inicialização, leitura e escrita
da tabela de parâmetros do sistema.
"""
from backend.services.database_service import get_db_connection


def initialize_db_parameters():
    """Garante que a tabela de parâmetros tenha pelo menos uma linha de configuração."""
    print("Verificando parâmetros...")
    conn = get_db_connection()

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
                print("[INFO] Parâmetros inicializados.")
            else:
                print("[INFO] Parâmetros já existem.")

    except Exception as e:
        conn.rollback()
        raise Exception(f"Não foi possível ler ou inicializar a 'tb_parametro': {e}")
    finally:
        conn.close()


def list_parameters(name_filter: str = ""):
    """Lista todos os conjuntos de parâmetros, com filtro opcional por nome."""
    sql = """
        SELECT "idParametro", nomeparametro
        FROM sch_supervisorio.tb_parametro
        WHERE nomeparametro ILIKE %s
        ORDER BY nomeparametro
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (f"%{name_filter}%",))
            return cur.fetchall()
    finally:
        conn.close()


def get_parameter_by_id(param_id: int):
    """Busca um conjunto de parâmetros específico pelo seu ID."""
    sql = """
        SELECT "idParametro", nomeparametro, "caminhoFotosClientes", "caminhoMapas",
               "caminhoVideoAProcessar", "caminhoVideoProcessados",
               "caminhoVideoMarcacoes", "intevalorFrames", "escalaImagem",
               "modeloDeteccao", "toleranciaReconhecimento", "gerarvideomarcacoes",
               "finalizaraoidentificartodos"
        FROM sch_supervisorio.tb_parametro WHERE "idParametro" = %s
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (param_id,))
            result = cur.fetchone()
            if result:
                return {
                    "id": result[0],
                    "name": result[1],
                    "photos_path": result[2],
                    "maps_path": result[3],
                    "videos_to_process_path": result[4],
                    "processed_videos_path": result[5],
                    "video_markers_path": result[6],
                    "frame_interval": result[7],
                    "image_scale": float(result[8]) if result[8] is not None else 1.0,
                    "detection_model": result[9],
                    "recognition_tolerance": result[10],
                    "generate_markers": result[11],
                    "finish_when_all_identified": result[12]
                }
            return None
    finally:
        conn.close()


def save_parameters(param_data: dict, param_id: int = None):
    """Salva um novo conjunto de parâmetros ou atualiza um existente."""
    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            if param_id:
                sql = """
                    UPDATE sch_supervisorio.tb_parametro
                    SET nomeparametro = %s, "caminhoFotosClientes" = %s, "caminhoMapas" = %s,
                        "caminhoVideoAProcessar" = %s, "caminhoVideoProcessados" = %s,
                        "caminhoVideoMarcacoes" = %s, "intevalorFrames" = %s, "escalaImagem" = %s,
                        "modeloDeteccao" = %s, "toleranciaReconhecimento" = %s,
                        "gerarvideomarcacoes" = %s, "finalizaraoidentificartodos" = %s
                    WHERE "idParametro" = %s
                """
                params = (
                    param_data['name'], param_data['photos_path'], param_data['maps_path'],
                    param_data['videos_to_process_path'], param_data['processed_videos_path'],
                    param_data['video_markers_path'], param_data['frame_interval'],
                    param_data['image_scale'], param_data['detection_model'],
                    param_data['recognition_tolerance'], param_data['generate_markers'],
                    param_data['finish_when_all_identified'], param_id
                )
            else:
                sql = """
                    INSERT INTO sch_supervisorio.tb_parametro (
                        nomeparametro, "caminhoFotosClientes", "caminhoMapas",
                        "caminhoVideoAProcessar", "caminhoVideoProcessados",
                        "caminhoVideoMarcacoes", "intevalorFrames", "escalaImagem",
                        "modeloDeteccao", "toleranciaReconhecimento", "gerarvideomarcacoes",
                        "finalizaraoidentificartodos"
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING "idParametro"
                """
                params = (
                    param_data['name'], param_data['photos_path'], param_data['maps_path'],
                    param_data['videos_to_process_path'], param_data['processed_videos_path'],
                    param_data['video_markers_path'], param_data['frame_interval'],
                    param_data['image_scale'], param_data['detection_model'],
                    param_data['recognition_tolerance'], param_data['generate_markers'],
                    param_data['finish_when_all_identified']
                )

            cur.execute(sql, params)
            if not param_id:
                param_id = cur.fetchone()[0]

        conn.commit()
        return param_id
    except Exception as e:
        conn.rollback()
        if "unique constraint" in str(e):
            raise Exception(f"O nome de parâmetro '{param_data['name']}' já existe.")
        raise Exception(f"Não foi possível salvar os parâmetros: {e}")
    finally:
        conn.close()


def delete_parameter(param_id: int):
    """Exclui um conjunto de parâmetros do banco de dados."""
    conn = get_db_connection()
    sql = 'DELETE FROM sch_supervisorio.tb_parametro WHERE "idParametro" = %s'
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (param_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        if "violates foreign key constraint" in str(e):
            raise Exception("Não é possível excluir este parâmetro, pois ele está sendo usado por um ou mais cenários.")
        raise Exception(f"Não foi possível excluir o parâmetro: {e}")
    finally:
        conn.close()


def load_parameters():
    """Carrega a primeira linha de parâmetros do banco de dados (usado na inicialização)."""
    sql = """
        SELECT "idParametro", nomeparametro, "caminhoFotosClientes", "caminhoMapas",
               "caminhoVideoAProcessar", "caminhoVideoProcessados",
               "caminhoVideoMarcacoes", "intevalorFrames", "escalaImagem",
               "modeloDeteccao", "toleranciaReconhecimento", "gerarvideomarcacoes",
               "finalizaraoidentificartodos"
        FROM sch_supervisorio.tb_parametro LIMIT 1
    """
    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            result = cur.fetchone()
            if result:
                return {
                    "id": result[0],
                    "name": result[1],
                    "photos_path": result[2],
                    "maps_path": result[3],
                    "videos_to_process_path": result[4],
                    "processed_videos_path": result[5],
                    "video_markers_path": result[6],
                    "frame_interval": result[7],
                    "image_scale": float(result[8]) if result[8] is not None else 1.0,
                    "detection_model": result[9],
                    "recognition_tolerance": result[10],
                    "generate_markers": result[11],
                    "finish_when_all_identified": result[12]
                }
            return None
    except Exception as e:
        raise Exception(f"Erro ao carregar parâmetros: {e}")
    finally:
        conn.close()