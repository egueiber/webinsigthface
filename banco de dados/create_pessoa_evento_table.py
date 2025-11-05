
import psycopg2

# --- Configuração do Banco de Dados ---
DB_NAME = "postgres"
DB_USER = "supervisorio"
DB_PASS = "supervisorio101"
DB_HOST = "localhost"
DB_PORT = 5432

def create_table():
    """Cria a tabela de pessoa_evento no banco de dados."""
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
                CREATE TABLE IF NOT EXISTS sch_supervisorio.tb_pessoa_evento
                (
                    idpessoaevento bigint NOT NULL DEFAULT nextval('sch_supervisorio.tb_pessoa_evento_idpessoaevento_seq'::regclass),
                    idpessoa bigint NOT NULL,
                    idevento integer NOT NULL,
                    datahoraentrada time without time zone NOT NULL,
                    datahoraprevistasaida time without time zone,
                    datahoraefetivasaida time without time zone,
                    eventocancelado boolean DEFAULT false,
                    CONSTRAINT pkeventopessoa PRIMARY KEY (idpessoaevento),
                    CONSTRAINT fkpessoa_evento_evento FOREIGN KEY (idevento)
                        REFERENCES sch_supervisorio.tb_evento (idevento) MATCH SIMPLE
                        ON UPDATE NO ACTION
                        ON DELETE NO ACTION,
                    CONSTRAINT fkpessoa_evento_pessoa FOREIGN KEY (idpessoa)
                        REFERENCES sch_supervisorio.tb_pessoa ("idPessoa") MATCH SIMPLE
                        ON UPDATE NO ACTION
                        ON DELETE NO ACTION
                )
            """)
        conn.commit()
        print("Tabela 'tb_pessoa_evento' criada com sucesso ou já existente.")
    except Exception as e:
        print(f"Erro ao criar a tabela 'tb_pessoa_evento': {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    create_table()
