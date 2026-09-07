# -*- coding: utf-8 -*-
"""
Módulo de Serviço de Banco de Dados (Backend) V7.2

Centraliza toda a comunicação com o banco de dados PostgreSQL.
(FIX V7.2) Garante que a lógica de UPDATE em save_camera
inclua todos os campos (floor, room) e a validação de duplicidade.
"""
import psycopg2
import os
import shutil

# --- Configuração do Banco de Dados ---
# Alterne para True para usar o banco de dados do Docker Compose
import os

DB_NAME = os.getenv("DB_NAME", "health-track-supervisorio")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "123456")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT  = int(os.getenv("DB_PORT", "5432"))


# --- Conexão ---
def get_db_connection():
    """Tenta estabelecer uma conexão com o banco de dados."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except Exception as e:
        raise Exception(f"Não foi possível conectar ao PostgreSQL: {e}")


# --- Funções de Person ---
def list_persons(name_filter: str = ""):
    sql = """
        SELECT "idPessoa", "nomePessoa", "documentoPessoa" 
        FROM sch_supervisorio.tb_pessoa
        WHERE "nomePessoa" ILIKE %s
        ORDER BY "nomePessoa"
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


def get_person_by_id(person_id: int):
    sql = '''SELECT "nomePessoa", "documentoPessoa", "fotosPessoa", "carteirinhaBiodoc" FROM sch_supervisorio.tb_pessoa WHERE "idPessoa" = %s'''
    conn = get_db_connection()
    person = None
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (person_id,))
            result = cur.fetchone()
            if result:
                person = {
                    "name": result[0],
                    "document": result[1],
                    "photos_folder": result[2] or "",
                    "biodoc_card": result[3] or "",
                }
    finally:
        conn.close()
    return person


def save_person(name: str, document: str, photos_folder: str, person_id: int = None, biodoc_card: str = None):
    conn = get_db_connection()
    try:
        if person_id:
            sql = """
                UPDATE sch_supervisorio.tb_pessoa
                SET "nomePessoa" = %s, "documentoPessoa" = %s, "fotosPessoa" = %s, "carteirinhaBiodoc" = %s
                WHERE "idPessoa" = %s
            """
            params = (name, document, photos_folder, biodoc_card, person_id)
            with conn.cursor() as cur:
                cur.execute(sql, params)
            conn.commit()
            return person_id
        else:
            sql = """
                INSERT INTO sch_supervisorio.tb_pessoa
                ("documentoPessoa", "nomePessoa", "fotosPessoa", "carteirinhaBiodoc")
                VALUES (%s, %s, %s, %s)
                RETURNING "idPessoa"
            """
            params = (document, name, photos_folder, biodoc_card)
            with conn.cursor() as cur:
                cur.execute(sql, params)
                new_id = cur.fetchone()[0]
            conn.commit()
            return new_id
    except Exception as e:
        conn.rollback()
        if "unique constraint" in str(e):
            raise Exception(f"O documento '{document}' já está cadastrado.")
        raise Exception(f"Não foi possível salvar os dados no banco: {e}")
    finally:
        conn.close()


def delete_person(person_id: int, photos_folder_path: str = None):
    conn = get_db_connection()
    sql = 'DELETE FROM sch_supervisorio.tb_pessoa WHERE "idPessoa" = %s'
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (person_id,))
        conn.commit()
        if photos_folder_path and os.path.exists(photos_folder_path):
            try:
                shutil.rmtree(photos_folder_path)
            except Exception as e:
                print(f"[WARN] Pessoa excluída do banco, mas falha ao excluir pasta de fotos: {e}")
        return True
    except Exception as e:
        conn.rollback()
        raise Exception(f"Não foi possível excluir a pessoa: {e}")
    finally:
        conn.close()


# --- Funções de Camera ---
def list_cameras(name_filter: str = ""):
    sql = """
        SELECT c."idCamera", c."nomeCamera", l.nomelocalizacao
        FROM sch_supervisorio.tb_cameras c
        JOIN sch_supervisorio.tb_localizacao l ON c.idlocalizacao = l.idlocalizacao
        WHERE c."nomeCamera" ILIKE %s
        ORDER BY c."nomeCamera"
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


def get_camera_by_id(camera_id: int):
    sql = """
        SELECT "nomeCamera", idlocalizacao, 
               "andarCamera", "nrsalaproximaCamera", notaparaignorar, notaidentificacao,
               url_rtsp, processar_tempo_real
        FROM sch_supervisorio.tb_cameras WHERE "idCamera" = %s
    """
    conn = get_db_connection()
    camera = None
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (camera_id,))
            result = cur.fetchone()
            if result:
                camera = {
                    "name": result[0],
                    "location_id": result[1],
                    "floor": result[2],
                    "room_number": result[3],
                    "ignore_threshold": result[4],
                    "identification_threshold": result[5],
                    "url_rtsp": result[6] if len(result) > 6 else None,
                    "processar_tempo_real": result[7] if len(result) > 7 else False
                }
    finally:
        conn.close()
    return camera


def save_camera(name: str, location_id: int, floor: int, room_number: int, 
                ignore_threshold: float, identification_threshold: float, camera_id: int = None,
                url_rtsp: str = None, processar_tempo_real: bool = False):
    """
    Salva (INSERT ou UPDATE) uma câmera no banco.
    A lógica de "if camera_id:" é o que diferencia a criação da edição.
    """
    conn = get_db_connection()
    
    try:
        with conn.cursor() as cur:
            # Validação de duplicidade
            cur.execute(
                'SELECT "idCamera", "nomeCamera" FROM sch_supervisorio.tb_cameras WHERE "andarCamera" = %s AND "nrsalaproximaCamera" = %s',
                (floor, room_number)
            )
            conflict = cur.fetchone()
            
            # Se encontrou um conflito, verifica se NÃO é o próprio registro sendo editado
            if conflict and (camera_id is None or conflict[0] != camera_id):
                raise Exception(f"Duplicidade detectada. A câmera '{conflict[1]}' (ID: {conflict[0]}) já está registrada para o Andar {floor} e Sala {room_number}.")

            if camera_id:
                # --- MODO DE EDIÇÃO (UPDATE) ---
                sql = """
                    UPDATE sch_supervisorio.tb_cameras
                    SET "nomeCamera" = %s, idlocalizacao = %s,
                        "andarCamera" = %s, "nrsalaproximaCamera" = %s, notaparaignorar = %s, notaidentificacao = %s,
                        url_rtsp = %s, processar_tempo_real = %s
                    WHERE "idCamera" = %s
                """
                params = (name, location_id, floor, room_number, ignore_threshold, identification_threshold, url_rtsp, processar_tempo_real, camera_id)
            else:
                # --- MODO DE CRIAÇÃO (INSERT) ---
                sql = """
                    INSERT INTO sch_supervisorio.tb_cameras
                    ("nomeCamera", idlocalizacao, "andarCamera", "nrsalaproximaCamera", notaparaignorar, notaidentificacao, url_rtsp, processar_tempo_real)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                params = (name, location_id, floor, room_number, ignore_threshold, identification_threshold, url_rtsp, processar_tempo_real)
            
            cur.execute(sql, params)
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise Exception(f"Não foi possível salvar a câmera no banco: {e}")
    finally:
        conn.close()


def delete_camera(camera_id: int):
    conn = get_db_connection()
    sql = 'DELETE FROM sch_supervisorio.tb_cameras WHERE "idCamera" = %s'
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (camera_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise Exception(f"Não foi possível excluir a câmera: {e}")
    finally:
        conn.close()


# --- Funções de Tracking (Acompanhamento) ---
def get_tracking_data(location_id: int, date_filter: str):
    sql = """
        SELECT 
            p."nomePessoa", 
            v.datahoraprocessamento, 
            TO_CHAR((v."tempoMarcacaoSegundos" || ' second')::interval, 'HH24:MI:SS'),
            v.notacomparacao,
            c.notaparaignorar,
            c.notaidentificacao,
            v.nomearquivovideomarcacao,
            v.segundomarcacao
        FROM sch_supervisorio.tb_videos_processados v
        JOIN sch_supervisorio.tb_cameras c ON v."nomeCamera" = c."nomeCamera"
        JOIN sch_supervisorio.tb_pessoa p ON p."fotosPessoa" = v."nomePastaPessoa"
        WHERE c.idlocalizacao = %s 
        AND v.datahoraprocessamento::date = %s
        ORDER BY v.datahoraprocessamento;
    """
    conn = get_db_connection()
    results = []
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (location_id, date_filter))
            results = cur.fetchall()
    finally:
        conn.close()
    return results


def get_persons_by_period(start_date: str, end_date: str, only_delayed: bool = False, location_id: int = None):
    conn = get_db_connection()
    params = []
    
    if only_delayed:
        sql = """
            SELECT DISTINCT p."nomePessoa"
            FROM sch_supervisorio.tb_pessoa p
            JOIN sch_supervisorio.tb_pessoa_evento pe ON p."idPessoa" = pe.idpessoa
            WHERE pe.datahoraentrada::date BETWEEN %s AND %s
              AND pe.datahoraefetivasaida IS NULL
              AND (pe.eventocancelado IS NULL OR pe.eventocancelado = FALSE)
              AND pe.datahoraprevistasaida < CURRENT_TIMESTAMP
        """
        params.extend([start_date, end_date])
    else:
        sql = """
            SELECT DISTINCT p."nomePessoa"
            FROM sch_supervisorio.tb_videos_processados v
            JOIN sch_supervisorio.tb_pessoa p ON v."nomePastaPessoa" = p."fotosPessoa"
            JOIN sch_supervisorio.tb_cameras c ON v."nomeCamera" = c."nomeCamera"
            WHERE v.datahoraprocessamento::date BETWEEN %s AND %s
        """
        params.extend([start_date, end_date])
        
        if location_id:
            sql += ' AND c.idlocalizacao = %s'
            params.append(location_id)

    sql += ' ORDER BY p."nomePessoa"'

    results = []
    try:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            results = [row[0] for row in cur.fetchall()]
    finally:
        conn.close()
    return results


def get_person_path(person_name: str, start_date: str, end_date: str, identified: bool = True):
    sql_base = """
        SELECT 
            v.datahoraprocessamento, 
            c."nomeCamera", 
            c."andarCamera", 
            c."nrsalaproximaCamera",
            v.nomearquivovideomarcacao,
            v.segundomarcacao
        FROM sch_supervisorio.tb_videos_processados v
        JOIN sch_supervisorio.tb_pessoa p ON v."nomePastaPessoa" = p."fotosPessoa"
        JOIN sch_supervisorio.tb_cameras c ON v."nomeCamera" = c."nomeCamera"
        WHERE p."nomePessoa" = %s
        AND v.datahoraprocessamento::date BETWEEN %s AND %s
    """
    params = (person_name, start_date, end_date)

    if identified:
        sql_final = sql_base + " AND v.identificada = TRUE"
    else:
        sql_final = sql_base
    
    sql_final += " ORDER BY v.datahoraprocessamento;"

    conn = get_db_connection()
    results = []
    try:
        with conn.cursor() as cur:
            cur.execute(sql_final, params)
            results = cur.fetchall()
    finally:
        conn.close()
    return results


# --- Funções de Location ---
def get_all_locations():
    """Retorna uma lista com os nomes de todas as localizações."""
    conn = get_db_connection()
    locations = []
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT idlocalizacao, nomelocalizacao FROM sch_supervisorio.tb_localizacao ORDER BY nomelocalizacao')
            locations = cur.fetchall()
    finally:
        conn.close()
    return locations


def get_locations_with_maps():
    """
    Retorna um dicionário {nome_localizacao: {'id': id, 'map': caminho_do_mapa_ou_None}}.
    Procura a pasta de mapas na tabela de parâmetros e tenta casar arquivos
    com o nome da localização. Se não encontrar um mapa, o valor será None.
    """
    conn = get_db_connection()
    maps_dir = None
    locations = []
    
    try:
        with conn.cursor() as cur:
            # tenta ler o caminho configurado de mapas
            try:
                cur.execute('SELECT "caminhoMapas" FROM sch_supervisorio.tb_parametro LIMIT 1')
                res = cur.fetchone()
                if res:
                    maps_dir = res[0]
            except Exception:
                # não é crítico — apenas prosseguir sem pasta de mapas
                maps_dir = None

            # busca todas as localizações cadastradas
            cur.execute('SELECT idlocalizacao, nomelocalizacao FROM sch_supervisorio.tb_localizacao ORDER BY nomelocalizacao')
            locations = cur.fetchall()
    finally:
        conn.close()

    result = {}
    candidate_files = []
    if maps_dir and os.path.isdir(maps_dir):
        try:
            candidate_files = os.listdir(maps_dir)
        except Exception:
            candidate_files = []

    for loc_id, name in locations:
        found_map = None
        if candidate_files:
            name_base = name.strip().lower()
            for fname in candidate_files:
                base, ext = os.path.splitext(fname)
                if base.strip().lower() == name_base and ext.lower() in ('.png', '.jpg', '.jpeg', '.bmp'):
                    found_map = os.path.join(maps_dir, fname)
                    break
        result[name] = {'id': loc_id, 'map': found_map}

    return result


# --- Funções de Engine (Motor) ---
def list_engines(name_filter: str = ""):
    sql = """
        SELECT idmotor, nomemotor, numversao, ativo, padrao
        FROM sch_supervisorio.tb_motor
        WHERE nomemotor ILIKE %s
        ORDER BY nomemotor
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


def get_engine_by_id(engine_id: int):
    sql = """
        SELECT nomemotor, numversao, nomefuncaochamada, nomemetodo, nomearquivojsonerno, nomearquivoexterno, ativo, padrao
        FROM sch_supervisorio.tb_motor WHERE idmotor = %s
    """
    conn = get_db_connection()
    engine = None
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (engine_id,))
            result = cur.fetchone()
            if result:
                engine = {
                    "name": result[0],
                    "version": result[1],
                    "function_name": result[2],
                    "method_name": result[3],
                    "json_file": result[4],
                    "external_file": result[5],
                    "active": result[6],
                    "default": result[7]
                }
    finally:
        conn.close()
    return engine


def save_engine(name: str, version: str, function_name: str, method_name: str, 
                json_file: str, external_file: str, active: bool, default: bool = False, engine_id: int = None):
    conn = get_db_connection()
    
    try:
        with conn.cursor() as cur:
            # Se este registro estiver sendo marcado como padrão, desmarca todos os outros primeiro
            if default:
                try:
                    cur.execute('UPDATE sch_supervisorio.tb_motor SET padrao = FALSE WHERE padrao = TRUE')
                except Exception:
                    pass

            if engine_id:
                sql = """
                    UPDATE sch_supervisorio.tb_motor
                    SET nomemotor = %s, numversao = %s, nomefuncaochamada = %s, nomemetodo = %s, 
                        nomearquivojsonerno = %s, nomearquivoexterno = %s, ativo = %s, padrao = %s
                    WHERE idmotor = %s
                """
                params = (name, version, function_name, method_name, json_file, external_file, active, default, engine_id)
            else:
                sql = """
                    INSERT INTO sch_supervisorio.tb_motor
                    (nomemotor, numversao, nomefuncaochamada, nomemetodo, nomearquivojsonerno, nomearquivoexterno, ativo, padrao)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                params = (name, version, function_name, method_name, json_file, external_file, active, default)
            
            cur.execute(sql, params)
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise Exception(f"Não foi possível salvar o motor no banco: {e}")
    finally:
        conn.close()


def delete_engine(engine_id: int):
    conn = get_db_connection()
    sql = 'DELETE FROM sch_supervisorio.tb_motor WHERE idmotor = %s'
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (engine_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise Exception(f"Não foi possível excluir o motor: {e}")
    finally:
        conn.close()


# --- Funções de Event ---
def list_events(name_filter: str = ""):
    sql = """
        SELECT idevento, nomeevento
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


# --- Funções de PersonEvent ---
def list_events_by_person(person_id: int):
    sql = """
        SELECT pe.idpessoaevento, e.nomeevento, pe.datahoraentrada, pe.datahoraprevistasaida, pe.datahoraefetivasaida, pe.eventocancelado
        FROM sch_supervisorio.tb_pessoa_evento pe
        JOIN sch_supervisorio.tb_evento e ON pe.idevento = e.idevento
        WHERE pe.idpessoa = %s
        ORDER BY e.nomeevento
    """
    conn = get_db_connection()
    results = []
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (person_id,))
            results = cur.fetchall()
    finally:
        conn.close()
    return results


def get_person_event_by_id(person_event_id: int):
    sql = 'SELECT idpessoa, idevento, datahoraentrada, datahoraprevistasaida, datahoraefetivasaida, eventocancelado FROM sch_supervisorio.tb_pessoa_evento WHERE idpessoaevento = %s'
    conn = get_db_connection()
    person_event = None
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (person_event_id,))
            result = cur.fetchone()
            if result:
                person_event = {
                    "person_id": result[0],
                    "event_id": result[1],
                    "entry_datetime": result[2],
                    "expected_exit_datetime": result[3],
                    "actual_exit_datetime": result[4],
                    "event_cancelled": result[5]
                }
    finally:
        conn.close()
    return person_event


def save_person_event(person_id: int, event_id: int, entry_datetime, expected_exit_datetime, 
                      actual_exit_datetime, event_cancelled: bool, person_event_id: int = None):
    conn = get_db_connection()
    try:
        if person_event_id:
            sql = """
                UPDATE sch_supervisorio.tb_pessoa_evento
                SET idpessoa = %s, idevento = %s, datahoraentrada = %s, datahoraprevistasaida = %s, 
                    datahoraefetivasaida = %s, eventocancelado = %s
                WHERE idpessoaevento = %s
            """
            params = (person_id, event_id, entry_datetime, expected_exit_datetime, actual_exit_datetime, event_cancelled, person_event_id)
        else:
            sql = """
                INSERT INTO sch_supervisorio.tb_pessoa_evento
                (idpessoa, idevento, datahoraentrada, datahoraprevistasaida, datahoraefetivasaida, eventocancelado)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            params = (person_id, event_id, entry_datetime, expected_exit_datetime, actual_exit_datetime, event_cancelled)
        with conn.cursor() as cur:
            cur.execute(sql, params)
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise Exception(f"Não foi possível salvar o evento da pessoa no banco: {e}")
    finally:
        conn.close()


def delete_person_event(person_event_id: int):
    conn = get_db_connection()
    sql = 'DELETE FROM sch_supervisorio.tb_pessoa_evento WHERE idpessoaevento = %s'
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (person_event_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise Exception(f"Não foi possível excluir o evento da pessoa: {e}")
    finally:
        conn.close()


def get_area_tracking_data(location_id: int, date_filter: str):
    """
    Retorna detecções de pessoas em uma localização numa data.
    Usado pela tela de Acompanhamento por Área.
    """
    sql = """
        SELECT
            p."nomePessoa",
            v.datahoraprocessamento,
            TO_CHAR((v."tempoMarcacaoSegundos" || ' second')::interval, 'HH24:MI:SS'),
            v.notacomparacao,
            c.notaparaignorar,
            c.notaidentificacao,
            v.nomearquivovideomarcacao,
            v.segundomarcacao,
            v."nomePastaPessoa",
            v.datahora_ao_vivo
        FROM sch_supervisorio.tb_videos_processados v
        JOIN sch_supervisorio.tb_cameras c ON v."nomeCamera" = c."nomeCamera"
        JOIN sch_supervisorio.tb_pessoa p ON p."fotosPessoa" = v."nomePastaPessoa"
        WHERE c.idlocalizacao = %s
        AND v.datahoraprocessamento::date = %s
        ORDER BY v.datahoraprocessamento;
    """
    conn = get_db_connection()
    results = []
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (location_id, date_filter))
            rows = cur.fetchall()
            for row in rows:
                results.append({
                    "nome": row[0],
                    "horario": row[1].strftime("%H:%M:%S") if row[1] else "",
                    "data": row[1].strftime("%d/%m/%Y") if row[1] else "",
                    "data_hora": row[1].strftime("%d/%m/%Y %H:%M:%S") if row[1] else "",
                    "tempo_marcacao": row[2] or "",
                    "nota_comparacao": float(row[3]) if row[3] else 0.0,
                    "nota_ignorar": float(row[4]) if row[4] else 0.0,
                    "nota_identificacao": float(row[5]) if row[5] else 0.0,
                    "video_path": row[6] or "",
                    "segundo_marcacao": int(row[7]) if row[7] else 0,
                    "pasta_pessoa": row[8] or "",
                    "datahora_ao_vivo": row[9].isoformat() if row[9] else "",
                })
    finally:
        conn.close()
    return results


def get_persons_in_period(start_date: str, end_date: str, location_id: int = None):
    """
    Retorna lista de pessoas com detecções no período.
    Usado para popular o select da tela de Acompanhamento por Pessoa.
    """
    sql = """
        SELECT DISTINCT p."idPessoa", p."nomePessoa"
        FROM sch_supervisorio.tb_videos_processados v
        JOIN sch_supervisorio.tb_pessoa p ON v."nomePastaPessoa" = p."fotosPessoa"
        JOIN sch_supervisorio.tb_cameras c ON v."nomeCamera" = c."nomeCamera"
        WHERE v.datahoraprocessamento::date BETWEEN %s AND %s
    """
    params = [start_date, end_date]

    if location_id:
        sql += " AND c.idlocalizacao = %s"
        params.append(location_id)

    sql += ' ORDER BY p."nomePessoa";'

    conn = get_db_connection()
    results = []
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            results = [{"id": row[0], "nome": row[1]} for row in rows]
    finally:
        conn.close()
    return results


def get_person_path_data(person_id: int, start_date: str, end_date: str, identified_only: bool = True):
    """
    Retorna a sequência de câmeras que uma pessoa passou.
    Usado pela tela de Acompanhamento por Pessoa.
    """
    sql = """
        SELECT
            v.datahoraprocessamento,
            c."nomeCamera",
            c."andarCamera",
            c."nrsalaproximaCamera",
            v.nomearquivovideomarcacao,
            v.segundomarcacao,
            v."nomePastaPessoa",
            v.datahora_ao_vivo
        FROM sch_supervisorio.tb_videos_processados v
        JOIN sch_supervisorio.tb_pessoa p ON v."nomePastaPessoa" = p."fotosPessoa"
        JOIN sch_supervisorio.tb_cameras c ON v."nomeCamera" = c."nomeCamera"
        WHERE p."idPessoa" = %s
        AND v.datahoraprocessamento::date BETWEEN %s AND %s
    """
    params = [person_id, start_date, end_date]

    if identified_only:
        sql += " AND v.identificada = TRUE"

    sql += " ORDER BY v.datahoraprocessamento;"

    conn = get_db_connection()
    results = []
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            for i, row in enumerate(rows):
                results.append({
                    "ordem": i + 1,
                    "horario": row[0].strftime("%H:%M:%S") if row[0] else "",
                    "data": row[0].strftime("%d/%m/%Y") if row[0] else "",
                    "data_hora": row[0].strftime("%d/%m/%Y %H:%M:%S") if row[0] else "",
                    "camera": row[1] or "",
                    "andar": row[2] if row[2] is not None else 0,
                    "sala": row[3] if row[3] is not None else 0,
                    "video_path": row[4] or "",
                    "segundo_marcacao": int(row[5]) if row[5] else 0,
                    "pasta_pessoa": row[6] or "",
                    "datahora_ao_vivo": row[7].isoformat() if row[7] else "",
                })
    finally:
        conn.close()
    return results

def list_person_events(person_id: int = None):
    """Lista eventos de pessoas. Se person_id informado, filtra por pessoa."""
    sql = """
        SELECT
            pe.idpessoaevento,
            p."nomePessoa",
            e.nomeevento,
            pe.datahoraentrada,
            pe.datahoraprevistasaida,
            pe.datahoraefetivasaida,
            pe.eventocancelado,
            pe.idpessoa,
            pe.idevento
        FROM sch_supervisorio.tb_pessoa_evento pe
        JOIN sch_supervisorio.tb_pessoa p ON pe.idpessoa = p."idPessoa"
        JOIN sch_supervisorio.tb_evento e ON pe.idevento = e.idevento
    """
    params = []
    if person_id:
        sql += " WHERE pe.idpessoa = %s"
        params.append(person_id)
    sql += " ORDER BY pe.datahoraentrada DESC"
    conn = get_db_connection()
    results = []
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            for row in rows:
                results.append({
                    "id": row[0],
                    "nome_pessoa": row[1],
                    "nome_evento": row[2],
                    "entrada": row[3].isoformat() if row[3] else None,
                    "saida_prevista": row[4].isoformat() if row[4] else None,
                    "saida_efetiva": row[5].isoformat() if row[5] else None,
                    "cancelado": row[6],
                    "pessoa_id": row[7],
                    "evento_id": row[8],
                })
    finally:
        conn.close()
    return results


# --- Configuração da Biodoc (lida do parâmetro padrão) ---
def get_biodoc_config():
    """
    Retorna a URL e o token da Biodoc a partir do parâmetro marcado como padrão
    (tb_parametro.padrao = true). Se não houver parâmetro padrão, retorna o
    primeiro parâmetro disponível. Campos: biodocapiurl, biodocapitoken.
    Retorna dict {"url": str, "token": str} — valores podem ser "" se não configurados.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT biodocapiurl, biodocapitoken
                FROM sch_supervisorio.tb_parametro
                ORDER BY padrao DESC NULLS LAST, "idParametro" ASC
                LIMIT 1
            """)
            row = cur.fetchone()
            if not row:
                return {"url": "", "token": ""}
            return {"url": row[0] or "", "token": row[1] or ""}
    finally:
        conn.close()
