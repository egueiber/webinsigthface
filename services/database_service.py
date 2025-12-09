# -*- coding: utf-8 -*-
"""
Módulo de Serviço de Banco de Dados (Backend) V7.2

Centraliza toda a comunicação com o banco de dados PostgreSQL.
(FIX V7.2) Garante que a lógica de UPDATE em salvar_camera_no_banco
inclua todos os campos (andar, nrsala) e a validação de duplicidade.
"""
import psycopg2
from tkinter import messagebox
import os
import shutil

# --- Configuração do Banco de Dados ---
# Alterne para True para usar o banco de dados do Docker Compose
DOCKER_DB = True

if DOCKER_DB:
    # Configurações para o banco de dados no contêiner Docker
    DB_NAME = "postgres"
    DB_USER = "postgres"
    DB_PASS = "postgres"
    DB_HOST = "localhost"  # O Docker Compose mapeia a porta para localhost
    DB_PORT = 5433
else:
    # Configurações originais
    DB_NAME = "postgres"
    DB_USER = "supervisorio"
    DB_PASS = "supervisorio101"
    DB_HOST = "localhost"
    DB_PORT = 5432

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
        messagebox.showerror("Erro de Banco de Dados", f"Não foi possível conectar ao PostgreSQL:\n{e}")
        return None

# --- Funções de Pessoa ---
def listar_pessoas_db(filtro_nome=""):
    sql = """
        SELECT "idPessoa", "nomePessoa", "documentoPessoa" 
        FROM sch_supervisorio.tb_pessoa
        WHERE "nomePessoa" ILIKE %s
        ORDER BY "nomePessoa"
    """
    conn = get_db_connection()
    if conn is None: return []
    resultados = []
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (f"%{filtro_nome}%",))
            resultados = cur.fetchall()
    except Exception as e:
        messagebox.showerror("Erro de Consulta", f"Erro ao listar pessoas:\n{e}")
    finally:
        conn.close()
    return resultados

def get_pessoa_por_id_db(pessoa_id):
    sql = 'SELECT "nomePessoa", "documentoPessoa" FROM sch_supervisorio.tb_pessoa WHERE "idPessoa" = %s'
    conn = get_db_connection()
    if conn is None: return None
    pessoa = None
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (pessoa_id,))
            result = cur.fetchone()
            if result:
                pessoa = {"nome": result[0], "documento": result[1]}
    except Exception as e:
        messagebox.showerror("Erro de Consulta", f"Erro ao buscar pessoa ID {pessoa_id}:\n{e}")
    finally:
        conn.close()
    return pessoa

def salvar_pessoa_no_banco(nome, documento, nome_pasta_fotos, pessoa_id=None):
    conn = get_db_connection()
    if conn is None: return False
    try:
        if pessoa_id:
            sql = """
                UPDATE sch_supervisorio.tb_pessoa
                SET "nomePessoa" = %s, "documentoPessoa" = %s, "fotosPessoa" = %s
                WHERE "idPessoa" = %s
            """
            params = (nome, documento, nome_pasta_fotos, pessoa_id)
        else:
            sql = """
                INSERT INTO sch_supervisorio.tb_pessoa
                ("documentoPessoa", "nomePessoa", "fotosPessoa")
                VALUES (%s, %s, %s)
            """
            params = (documento, nome, nome_pasta_fotos)
        with conn.cursor() as cur:
            cur.execute(sql, params)
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        if "unique constraint" in str(e):
             messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar: O documento '{documento}' já está cadastrado.")
        else:
             messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar os dados no banco:\n{e}")
        return False
    finally:
        conn.close()

def excluir_pessoa_db(pessoa_id, pasta_fotos_completa):
    conn = get_db_connection()
    if conn is None: return False
    sql = 'DELETE FROM sch_supervisorio.tb_pessoa WHERE "idPessoa" = %s'
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (pessoa_id,))
        conn.commit()
        if pasta_fotos_completa and os.path.exists(pasta_fotos_completa):
            try:
                shutil.rmtree(pasta_fotos_completa)
                print(f"[TEMP] Pasta de fotos excluída: {pasta_fotos_completa}")
            except Exception as e_fs:
                messagebox.showwarning("Aviso", f"Pessoa excluída do banco, mas falha ao excluir pasta de fotos:\n{e_fs}")
        return True
    except Exception as e:
        conn.rollback()
        messagebox.showerror("Erro ao Excluir", f"Não foi possível excluir a pessoa:\n{e}")
        return False
    finally:
        conn.close()

# --- Funções de Câmera ---
def listar_cameras_db(filtro_nome=""):
    sql = """
        SELECT c."idCamera", c."nomeCamera", l.nomelocalizacao
        FROM sch_supervisorio.tb_cameras c
        JOIN sch_supervisorio.tb_localizacao l ON c.idlocalizacao = l.idlocalizacao
        WHERE c."nomeCamera" ILIKE %s
        ORDER BY c."nomeCamera"
    """
    conn = get_db_connection()
    if conn is None: return []
    resultados = []
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (f"%{filtro_nome}%",))
            resultados = cur.fetchall()
    except Exception as e:
        messagebox.showerror("Erro de Consulta", f"Erro ao listar câmeras:\n{e}")
    finally:
        conn.close()
    return resultados

def get_camera_por_id_db(camera_id):
    sql = """
        SELECT "nomeCamera", idlocalizacao, 
               "andarCamera", "nrsalaproximaCamera", notaparaignorar, notaidentificacao
        FROM sch_supervisorio.tb_cameras WHERE "idCamera" = %s
    """
    conn = get_db_connection()
    if conn is None: return None
    camera = None
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (camera_id,))
            result = cur.fetchone()
            if result:
                camera = {
                    "nome": result[0], 
                    "idlocalizacao": result[1],
                    "andar": result[2],
                    "nrsala": result[3],
                    "notaparaignorar": result[4],
                    "notaidentificacao": result[5]
                }
    except Exception as e:
        if "column" in str(e) and "does not exist" in str(e):
            messagebox.showerror("Erro de Banco de Dados", f"Erro: A tabela 'tb_cameras' está desatualizada.\n{e}\n\nPor favor, execute o script ALTER TABLE para adicionar as colunas 'andarCamera' e 'nrsalaproximaCamera'.")
        else:
            messagebox.showerror("Erro de Consulta", f"Erro ao buscar câmera ID {camera_id}:\n{e}")
    finally:
        conn.close()
    return camera

def salvar_camera_no_banco(nome, idlocalizacao, andar, nrsala, notaparaignorar, notaidentificacao, camera_id=None):
    """
    Salva (INSERT ou UPDATE) uma câmera no banco.
    A lógica de "if camera_id:" é o que diferencia
    a criação da edição.
    """
    conn = get_db_connection()
    if conn is None: return False
    
    try:
        with conn.cursor() as cur:
            # Validação de duplicidade
            cur.execute(
                'SELECT "idCamera", "nomeCamera" FROM sch_supervisorio.tb_cameras WHERE "andarCamera" = %s AND "nrsalaproximaCamera" = %s',
                (andar, nrsala)
            )
            conflito = cur.fetchone()
            
            # Se encontrou um conflito, verifica se NÃO é o próprio registro sendo editado
            if conflito and (camera_id is None or conflito[0] != camera_id):
                messagebox.showerror("Erro de Validação", f"Duplicidade detectada.\nA câmera '{conflito[1]}' (ID: {conflito[0]}) já está registrada para o Andar {andar} e Sala {nrsala}.")
                return False

            if camera_id:
                # --- MODO DE EDIÇÃO (UPDATE) ---
                sql = """
                    UPDATE sch_supervisorio.tb_cameras
                    SET "nomeCamera" = %s, idlocalizacao = %s,
                        "andarCamera" = %s, "nrsalaproximaCamera" = %s, notaparaignorar = %s, notaidentificacao = %s
                    WHERE "idCamera" = %s
                """
                params = (nome, idlocalizacao, andar, nrsala, notaparaignorar, notaidentificacao, camera_id)
            else:
                # --- MODO DE CRIAÇÃO (INSERT) ---
                sql = """
                    INSERT INTO sch_supervisorio.tb_cameras
                    ("nomeCamera", idlocalizacao, "andarCamera", "nrsalaproximaCamera", notaparaignorar, notaidentificacao)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                params = (nome, idlocalizacao, andar, nrsala, notaparaignorar, notaidentificacao)
            
            cur.execute(sql, params)
        conn.commit() # Salva as alterações
        return True
    except Exception as e:
        conn.rollback() # Desfaz em caso de erro
        messagebox.showerror("Erro ao Salvar Câmera", f"Não foi possível salvar a câmera no banco:\n{e}")
        return False
    finally:
        conn.close()

def excluir_camera_db(camera_id):
    conn = get_db_connection()
    if conn is None: return False
    sql = 'DELETE FROM sch_supervisorio.tb_cameras WHERE "idCamera" = %s'
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (camera_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        messagebox.showerror("Erro ao Excluir", f"Não foi possível excluir a câmera:\n{e}")
        return False
    finally:
        conn.close()

# --- Funções de Acompanhamento ---


def get_dados_acompanhamento_db(localizacao_id, data_filtro):
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
    if conn is None: return []
    resultados = []
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (localizacao_id, data_filtro))
            resultados = cur.fetchall()
    except Exception as e:
        messagebox.showerror("Erro de Consulta", f"Erro ao buscar dados de acompanhamento:\n{e}")
    finally:
        conn.close()
    return resultados

def get_pessoas_por_periodo_db(data_inicio, data_fim, somente_com_atraso=False, localizacao_id=None):
    conn = get_db_connection()
    if conn is None: return []

    params = []
    
    if somente_com_atraso:
        sql = """
            SELECT DISTINCT p."nomePessoa"
            FROM sch_supervisorio.tb_pessoa p
            JOIN sch_supervisorio.tb_pessoa_evento pe ON p."idPessoa" = pe.idpessoa
            WHERE pe.datahoraentrada::date BETWEEN %s AND %s
              AND pe.datahoraefetivasaida IS NULL
              AND (pe.eventocancelado IS NULL OR pe.eventocancelado = FALSE)
              AND pe.datahoraprevistasaida < CURRENT_TIMESTAMP
        """
        params.extend([data_inicio, data_fim])
    else:
        sql = """
            SELECT DISTINCT p."nomePessoa"
            FROM sch_supervisorio.tb_videos_processados v
            JOIN sch_supervisorio.tb_pessoa p ON v."nomePastaPessoa" = p."fotosPessoa"
            JOIN sch_supervisorio.tb_cameras c ON v."nomeCamera" = c."nomeCamera"
            WHERE v.datahoraprocessamento::date BETWEEN %s AND %s
        """
        params.extend([data_inicio, data_fim])
        
        if localizacao_id:
            sql += ' AND c.idlocalizacao = %s'
            params.append(localizacao_id)

    sql += ' ORDER BY p."nomePessoa"'

    resultados = []
    try:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            resultados = [row[0] for row in cur.fetchall()]
    except Exception as e:
        messagebox.showerror("Erro de Consulta", f"Erro ao buscar pessoas por período:\n{e}")
    finally:
        conn.close()
    return resultados

def get_caminho_pessoa_db(nome_pessoa, data_inicio, data_fim, identificada=True):
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
    params = (nome_pessoa, data_inicio, data_fim)

    if identificada:
        sql_final = sql_base + " AND v.identificada = TRUE"
    else:
        sql_final = sql_base
    
    sql_final += " ORDER BY v.datahoraprocessamento;"

    conn = get_db_connection()
    if conn is None: return []
    resultados = []
    try:
        with conn.cursor() as cur:
            cur.execute(sql_final, params)
            resultados = cur.fetchall()
    except Exception as e:
        messagebox.showerror("Erro de Consulta", f"Erro ao buscar caminhamento da pessoa:\n{e}")
    finally:
        conn.close()
    return resultados


def get_all_localizacoes_db():
    """Retorna uma lista com os nomes de todas as localizações."""
    conn = get_db_connection()
    if conn is None:
        return []
    
    localizacoes = []
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT idlocalizacao, nomelocalizacao FROM sch_supervisorio.tb_localizacao ORDER BY nomelocalizacao')
            localizacoes = cur.fetchall()
    except Exception as e:
        messagebox.showerror("Erro de Consulta", f"Erro ao buscar todas as localizações:\n{e}")
    finally:
        conn.close()
    
    return localizacoes

def get_localizacoes_db():
    """
    Retorna um dicionário {nome_localizacao: {'id': id, 'mapa': caminho_do_mapa_ou_None}}.
    Procura a pasta de mapas na tabela de parâmetros e tenta casar arquivos
    com o nome da localização. Se não encontrar um mapa, o valor será None.
    """
    conn = get_db_connection()
    if conn is None:
        return {}

    mapas_dir = None
    localizacoes = []
    try:
        with conn.cursor() as cur:
            # tenta ler o caminho configurado de mapas
            try:
                cur.execute('SELECT "caminhoMapas" FROM sch_supervisorio.tb_parametro LIMIT 1')
                res = cur.fetchone()
                if res:
                    mapas_dir = res[0]
            except Exception:
                # não é crítico — apenas prosseguir sem pasta de mapas
                mapas_dir = None

            # busca todas as localizações cadastradas
            cur.execute('SELECT idlocalizacao, nomelocalizacao FROM sch_supervisorio.tb_localizacao ORDER BY nomelocalizacao')
            localizacoes = cur.fetchall()
    except Exception as e:
        messagebox.showerror("Erro de Consulta", f"Erro ao buscar localizações:\n{e}")
        conn.close()
        return {}
    finally:
        conn.close()

    result = {}
    candidate_files = []
    if mapas_dir and os.path.isdir(mapas_dir):
        try:
            candidate_files = os.listdir(mapas_dir)
        except Exception:
            candidate_files = []

    for loc_id, nome in localizacoes:
        mapa_encontrado = None
        if candidate_files:
            nome_base = nome.strip().lower()
            for fname in candidate_files:
                base, ext = os.path.splitext(fname)
                if base.strip().lower() == nome_base and ext.lower() in ('.png', '.jpg', '.jpeg', '.bmp'):
                    mapa_encontrado = os.path.join(mapas_dir, fname)
                    break
        result[nome] = {'id': loc_id, 'mapa': mapa_encontrado}

    return result

# --- Funções de Motor ---
def listar_motores_db(filtro_nome=""):
    sql = """
        SELECT idmotor, nomemotor, numversao, ativo, padrao
        FROM sch_supervisorio.tb_motor
        WHERE nomemotor ILIKE %s
        ORDER BY nomemotor
    """
    conn = get_db_connection()
    if conn is None: return []
    resultados = []
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (f"%{filtro_nome}%",))
            resultados = cur.fetchall()
    except Exception as e:
        messagebox.showerror("Erro de Consulta", f"Erro ao listar motores:\n{e}")
    finally:
        conn.close()
    return resultados

def get_motor_por_id_db(motor_id):
    sql = """
        SELECT nomemotor, numversao, nomefuncaochamada, nomemetodo, nomearquivojsonerno, nomearquivoexterno, ativo, padrao
        FROM sch_supervisorio.tb_motor WHERE idmotor = %s
    """
    conn = get_db_connection()
    if conn is None: return None
    motor = None
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (motor_id,))
            result = cur.fetchone()
            if result:
                motor = {
                    "nomemotor": result[0],
                    "numversao": result[1],
                    "nomefuncaochamada": result[2],
                    "nomemetodo": result[3],
                    "nomearquivojsonerno": result[4],
                    "nomearquivoexterno": result[5],
                    "ativo": result[6]
                }
    except Exception as e:
        messagebox.showerror("Erro de Consulta", f"Erro ao buscar motor ID {motor_id}:\n{e}")
    finally:
        conn.close()
    return motor

def salvar_motor_no_banco(nomemotor, numversao, nomefuncaochamada, nomemetodo, nomearquivojsonerno, nomearquivoexterno, ativo, padrao=False, motor_id=None):
    conn = get_db_connection()
    if conn is None: return False
    
    try:
        with conn.cursor() as cur:
            # Se este registro estiver sendo marcado como padrão, desmarca todos os outros primeiro
            if padrao:
                try:
                    cur.execute('UPDATE sch_supervisorio.tb_motor SET padrao = FALSE WHERE padrao = TRUE')
                except Exception:
                    # continue mesmo se a atualização de padrao falhar; o erro será tratado adiante
                    pass

            if motor_id:
                sql = """
                    UPDATE sch_supervisorio.tb_motor
                    SET nomemotor = %s, numversao = %s, nomefuncaochamada = %s, nomemetodo = %s, nomearquivojsonerno = %s, nomearquivoexterno = %s, ativo = %s, padrao = %s
                    WHERE idmotor = %s
                """
                params = (nomemotor, numversao, nomefuncaochamada, nomemetodo, nomearquivojsonerno, nomearquivoexterno, ativo, padrao, motor_id)
            else:
                sql = """
                    INSERT INTO sch_supervisorio.tb_motor
                    (nomemotor, numversao, nomefuncaochamada, nomemetodo, nomearquivojsonerno, nomearquivoexterno, ativo, padrao)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                params = (nomemotor, numversao, nomefuncaochamada, nomemetodo, nomearquivojsonerno, nomearquivoexterno, ativo, padrao)
            
            cur.execute(sql, params)
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        messagebox.showerror("Erro ao Salvar Motor", f"Não foi possível salvar o motor no banco:\n{e}")
        return False
    finally:
        conn.close()

def excluir_motor_db(motor_id):
    conn = get_db_connection()
    if conn is None: return False
    sql = 'DELETE FROM sch_supervisorio.tb_motor WHERE idmotor = %s'
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (motor_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        messagebox.showerror("Erro ao Excluir", f"Não foi possível excluir o motor:\n{e}")
        return False
    finally:
        conn.close()

# --- Funções de Evento ---
def listar_eventos_db(filtro_nome=""):
    sql = """
        SELECT idevento, nomeevento
        FROM sch_supervisorio.tb_evento
        WHERE nomeevento ILIKE %s
        ORDER BY nomeevento
    """
    conn = get_db_connection()
    if conn is None: return []
    resultados = []
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (f"%{filtro_nome}%",))
            resultados = cur.fetchall()
    except Exception as e:
        messagebox.showerror("Erro de Consulta", f"Erro ao listar eventos:\n{e}")
    finally:
        conn.close()
    return resultados

# --- Funções de Pessoa-Evento ---
def listar_eventos_por_pessoa_db(pessoa_id):
    sql = """
        SELECT pe.idpessoaevento, e.nomeevento, pe.datahoraentrada, pe.datahoraprevistasaida, pe.datahoraefetivasaida, pe.eventocancelado
        FROM sch_supervisorio.tb_pessoa_evento pe
        JOIN sch_supervisorio.tb_evento e ON pe.idevento = e.idevento
        WHERE pe.idpessoa = %s
        ORDER BY e.nomeevento
    """
    conn = get_db_connection()
    if conn is None: return []
    resultados = []
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (pessoa_id,))
            resultados = cur.fetchall()
    except Exception as e:
        messagebox.showerror("Erro de Consulta", f"Erro ao listar eventos da pessoa:\n{e}")
    finally:
        conn.close()
    return resultados

def get_pessoa_evento_por_id_db(pessoa_evento_id):
    sql = 'SELECT idpessoa, idevento, datahoraentrada, datahoraprevistasaida, datahoraefetivasaida, eventocancelado FROM sch_supervisorio.tb_pessoa_evento WHERE idpessoaevento = %s'
    conn = get_db_connection()
    if conn is None: return None
    pessoa_evento = None
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (pessoa_evento_id,))
            result = cur.fetchone()
            if result:
                pessoa_evento = {
                    "idpessoa": result[0],
                    "idevento": result[1],
                    "datahoraentrada": result[2],
                    "datahoraprevistasaida": result[3],
                    "datahoraefetivasaida": result[4],
                    "eventocancelado": result[5]
                }
    except Exception as e:
        messagebox.showerror("Erro de Consulta", f"Erro ao buscar evento da pessoa ID {pessoa_evento_id}:\n{e}")
    finally:
        conn.close()
    return pessoa_evento

def salvar_pessoa_evento_no_banco(idpessoa, idevento, datahoraentrada, datahoraprevistasaida, datahoraefetivasaida, eventocancelado, pessoa_evento_id=None):
    conn = get_db_connection()
    if conn is None: return False
    try:
        if pessoa_evento_id:
            sql = """
                UPDATE sch_supervisorio.tb_pessoa_evento
                SET idpessoa = %s, idevento = %s, datahoraentrada = %s, datahoraprevistasaida = %s, datahoraefetivasaida = %s, eventocancelado = %s
                WHERE idpessoaevento = %s
            """
            params = (idpessoa, idevento, datahoraentrada, datahoraprevistasaida, datahoraefetivasaida, eventocancelado, pessoa_evento_id)
        else:
            sql = """
                INSERT INTO sch_supervisorio.tb_pessoa_evento
                (idpessoa, idevento, datahoraentrada, datahoraprevistasaida, datahoraefetivasaida, eventocancelado)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            params = (idpessoa, idevento, datahoraentrada, datahoraprevistasaida, datahoraefetivasaida, eventocancelado)
        with conn.cursor() as cur:
            cur.execute(sql, params)
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar o evento da pessoa no banco:\n{e}")
        return False
    finally:
        conn.close()

def excluir_pessoa_evento_db(pessoa_evento_id):

    conn = get_db_connection()

    if conn is None: return False

    sql = 'DELETE FROM sch_supervisorio.tb_pessoa_evento WHERE idpessoaevento = %s'

    try:

        with conn.cursor() as cur:

            cur.execute(sql, (pessoa_evento_id,))

        conn.commit()

        return True

    except Exception as e:

        conn.rollback()

        messagebox.showerror("Erro ao Excluir", f"Não foi possível excluir o evento da pessoa:\n{e}")

        return False

    finally:

        conn.close()