
import psycopg2

DB_NAME = "postgres"
DB_USER = "supervisorio"
DB_PASS = "supervisorio101"
DB_HOST = "localhost"
DB_PORT = 5432

create_table_query = """
CREATE TABLE IF NOT EXISTS sch_supervisorio.tb_motor
(
    idmotor bigserial NOT NULL,
    nomemotor character varying(40) COLLATE pg_catalog."default",
    numversao real,
    nomefuncaochamada character varying(100) COLLATE pg_catalog."default",
    nomemetodo character varying(30) COLLATE pg_catalog."default",
    nomearquivojsonerno json,
    nomearquivoexterno character varying(500) COLLATE pg_catalog."default",
    ativo boolean DEFAULT true,
    CONSTRAINT tb_motor_pkey PRIMARY KEY (idmotor)
)
"""

def create_table():
    """Tenta estabelecer uma conexão com o banco de dados."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT
        )
        with conn.cursor() as cur:
            cur.execute(create_table_query)
        conn.commit()
        print("Tabela 'sch_supervisorio.tb_motor' criada com sucesso ou já existente.")
    except Exception as e:
        print(f"Não foi possível conectar ao PostgreSQL ou criar a tabela: {e}")

if __name__ == "__main__":
    create_table()
