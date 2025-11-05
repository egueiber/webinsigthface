
import psycopg2

# --- Configuração do Banco de Dados ---
DB_NAME = "postgres"
DB_USER = "supervisorio"
DB_PASS = "supervisorio101"
DB_HOST = "localhost"
DB_PORT = 5432

def create_table():
    """Cria a tabela de eventos no banco de dados."""
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT
        )
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sch_supervisorio.tb_evento
                (
                    idevento integer NOT NULL DEFAULT nextval('sch_supervisorio.tb_evento_idevento_seq'::regclass),
                    nomeevento character varying(70) COLLATE pg_catalog."default" NOT NULL,
                    eventoduracao integer,
                    CONSTRAINT tb_evento_pkey PRIMARY KEY (idevento)
                )
            """)
        conn.commit()
        print("Tabela 'tb_evento' criada com sucesso ou já existente.")
    except Exception as e:
        print(f"Erro ao criar a tabela 'tb_evento': {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    create_table()
