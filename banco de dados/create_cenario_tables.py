# -*- coding: utf-8 -*-
"""
Módulo para criar as tabelas de Cenario e CenarioCamera no banco de dados.
"""
from services.database_service import get_db_connection, close_db_connection

def criar_tabelas_cenario():
    """
    Cria as tabelas 'tb_cenario' e 'tb_cenariocamera' no esquema 'sch_supervisorio'
    se elas ainda não existirem.
    """
    conn = get_db_connection()
    if conn is None:
        print("Não foi possível conectar ao banco de dados para criar as tabelas de cenário.")
        return

    try:
        with conn.cursor() as cur:
            # Cria a tabela de Cenários
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sch_supervisorio.tb_cenario
                (
                    idcenario SERIAL PRIMARY KEY,
                    descricaocenario VARCHAR(100) NOT NULL,
                    idparametro BIGINT,
                    ativo BOOLEAN NOT NULL DEFAULT true,
                    padrao BOOLEAN NOT NULL DEFAULT false,
                    CONSTRAINT fk_parametro
                        FOREIGN KEY("idParametro") 
                        REFERENCES sch_supervisorio.tb_parametro("idParametro")
                );
            """)
            print("Tabela 'tb_cenario' verificada/criada com sucesso.")

            # Cria a tabela de Itens do Cenário (CenarioCamera)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sch_supervisorio.tb_cenariocamera
                (
                    idcenariocamera SERIAL PRIMARY KEY,
                    idcenario INTEGER NOT NULL,
                    idcamera INTEGER,
                    CONSTRAINT fk_cenario
                        FOREIGN KEY(idcenario) 
                        REFERENCES sch_supervisorio.tb_cenario(idcenario)
                        ON DELETE CASCADE,
                    CONSTRAINT fk_camera
                        FOREIGN KEY("idCamera") 
                        REFERENCES sch_supervisorio.tb_cameras("idCamera")
                );
            """)
            print("Tabela 'tb_cenariocamera' verificada/criada com sucesso.")
            
            conn.commit()

    except Exception as e:
        print(f"Erro ao criar as tabelas de cenário: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            close_db_connection(conn)

if __name__ == '__main__':
    print("Executando script para criar tabelas de cenário...")
    criar_tabelas_cenario()
    print("Script finalizado.")
