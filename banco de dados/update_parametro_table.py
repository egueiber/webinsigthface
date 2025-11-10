# -*- coding: utf-8 -*-
"""
Módulo para criar e atualizar a tabela de Parâmetros no banco de dados.
"""
from services.database_service import get_db_connection, close_db_connection

def atualizar_tabela_parametro():
    """
    Verifica e adiciona a coluna 'nomeparametro' à tabela 'tb_parametro'
    se ela ainda não existir.
    """
    conn = get_db_connection()
    if conn is None:
        print("Não foi possível conectar ao banco de dados para atualizar a tabela de parâmetros.")
        return

    try:
        with conn.cursor() as cur:
            # Verifica se a coluna já existe
            cur.execute("""
                SELECT 1 FROM information_schema.columns 
                WHERE table_schema = 'sch_supervisorio' 
                AND table_name = 'tb_parametro' 
                AND column_name = 'nomeparametro';
            """)
            coluna_existe = cur.fetchone()

            if not coluna_existe:
                # Adiciona a coluna se ela não existir
                cur.execute("""
                    ALTER TABLE sch_supervisorio.tb_parametro
                    ADD COLUMN nomeparametro VARCHAR(100);
                """)
                print("Coluna 'nomeparametro' adicionada à tabela 'tb_parametro' com sucesso.")
                conn.commit()
            else:
                print("Coluna 'nomeparametro' já existe na tabela 'tb_parametro'.")

    except Exception as e:
        print(f"Erro ao atualizar a tabela de parâmetros: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            close_db_connection(conn)

if __name__ == '__main__':
    print("Executando script para atualizar a tabela de parâmetros...")
    atualizar_tabela_parametro()
    print("Script finalizado.")
