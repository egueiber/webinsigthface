# -*- coding: utf-8 -*-
"""
Servico de autenticacao do sistema web.

Responsavel por:
  - hash e verificacao de senha (bcrypt via passlib)
  - geracao e validacao de JWT
  - CRUD de usuarios no banco

Variaveis de ambiente:
    JWT_SECRET       - chave secreta para assinar os tokens (OBRIGATORIA em producao)
    JWT_EXPIRE_HOURS - validade do token em horas (padrao: 8)
"""
import os
from datetime import datetime, timedelta

from jose import jwt, JWTError
from passlib.context import CryptContext

from backend.services.database_service import get_db_connection

# --- Configuracao ---
JWT_SECRET       = os.getenv("JWT_SECRET", "troque-esta-chave-em-producao")
JWT_ALGORITHM    = "HS256"
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "8"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# --- Senha ---
def gerar_hash_senha(senha: str) -> str:
    """Gera o hash bcrypt de uma senha em texto puro."""
    return pwd_context.hash(senha)


def verificar_senha(senha: str, senha_hash: str) -> bool:
    """Compara a senha digitada com o hash armazenado."""
    try:
        return pwd_context.verify(senha, senha_hash)
    except Exception:
        return False


# --- JWT ---
def criar_token(dados: dict) -> str:
    """Gera um JWT assinado com validade configurada."""
    payload = dados.copy()
    payload["exp"] = datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def validar_token(token: str):
    """
    Valida um JWT e retorna o payload.
    Retorna None se o token for invalido ou estiver expirado.
    """
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None


# --- Consultas ---
def get_usuario_por_login(login: str):
    """Busca um usuario pelo login. Retorna dict (com hash) ou None."""
    sql = """
        SELECT idusuario, nomeusuario, login, senhahash, papel, ativo
        FROM sch_supervisorio.tb_usuario
        WHERE login = %s
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (login,))
            row = cur.fetchone()
            if not row:
                return None
            return {
                "id": row[0],
                "nome": row[1],
                "login": row[2],
                "senha_hash": row[3],
                "papel": row[4],
                "ativo": row[5],
            }
    finally:
        conn.close()


def get_usuario_por_id(usuario_id: int):
    """Busca um usuario pelo id (sem o hash da senha)."""
    sql = """
        SELECT idusuario, nomeusuario, login, papel, ativo
        FROM sch_supervisorio.tb_usuario
        WHERE idusuario = %s
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (usuario_id,))
            row = cur.fetchone()
            if not row:
                return None
            return {
                "id": row[0],
                "nome": row[1],
                "login": row[2],
                "papel": row[3],
                "ativo": row[4],
            }
    finally:
        conn.close()


def contar_admins_ativos(excluir_id: int = None) -> int:
    """Conta quantos admins ativos existem, opcionalmente excluindo um id (para checar antes de salvar)."""
    sql = """
        SELECT COUNT(*) FROM sch_supervisorio.tb_usuario
        WHERE papel = 'admin' AND ativo = true
    """
    params = []
    if excluir_id is not None:
        sql += " AND idusuario != %s"
        params.append(excluir_id)

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()[0]
    finally:
        conn.close()


def listar_usuarios():
    """Lista todos os usuarios (sem hash de senha), do mais novo para o mais antigo."""
    sql = """
        SELECT idusuario, nomeusuario, login, papel, ativo, datacriacao
        FROM sch_supervisorio.tb_usuario
        ORDER BY datacriacao DESC
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
            return [
                {
                    "id": r[0], "nome": r[1], "login": r[2],
                    "papel": r[3], "ativo": r[4],
                    "data_criacao": r[5].isoformat() if r[5] else None,
                }
                for r in rows
            ]
    finally:
        conn.close()


def autenticar(login: str, senha: str):
    """
    Valida as credenciais.
    Retorna o usuario (sem hash) se OK, ou None se falhar.
    """
    usuario = get_usuario_por_login(login)
    if not usuario:
        return None
    if not usuario["ativo"]:
        return None
    if not verificar_senha(senha, usuario["senha_hash"]):
        return None
    return {
        "id": usuario["id"],
        "nome": usuario["nome"],
        "login": usuario["login"],
        "papel": usuario["papel"],
    }


def contar_usuarios() -> int:
    """Retorna quantos usuarios existem cadastrados."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM sch_supervisorio.tb_usuario")
            return cur.fetchone()[0]
    finally:
        conn.close()


def criar_usuario(nome: str, login: str, senha: str, papel: str = "user") -> int:
    """Cria um usuario e retorna o id gerado."""
    if papel not in ("admin", "user"):
        raise Exception("Papel invalido. Use 'admin' ou 'user'.")
    if len(senha) < 6:
        raise Exception("A senha deve ter pelo menos 6 caracteres.")

    sql = """
        INSERT INTO sch_supervisorio.tb_usuario (nomeusuario, login, senhahash, papel)
        VALUES (%s, %s, %s, %s)
        RETURNING idusuario
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (nome, login, gerar_hash_senha(senha), papel))
            novo_id = cur.fetchone()[0]
        conn.commit()
        return novo_id
    except Exception as e:
        conn.rollback()
        if "unique" in str(e).lower():
            raise Exception(f"O login '{login}' ja esta em uso.")
        raise Exception(f"Nao foi possivel criar o usuario: {e}")
    finally:
        conn.close()


def atualizar_usuario(usuario_id: int, nome: str, login: str, papel: str, ativo: bool):
    """Atualiza nome, login, papel e status ativo/inativo de um usuario."""
    if papel not in ("admin", "user"):
        raise Exception("Papel invalido. Use 'admin' ou 'user'.")

    # Protecao: nao permite desativar ou rebaixar o ultimo admin ativo
    usuario_atual = get_usuario_por_id(usuario_id)
    if usuario_atual and usuario_atual["papel"] == "admin":
        vai_deixar_de_ser_admin_ativo = (papel != "admin") or (not ativo)
        if vai_deixar_de_ser_admin_ativo:
            outros_admins = contar_admins_ativos(excluir_id=usuario_id)
            if outros_admins == 0:
                raise Exception(
                    "Nao e possivel desativar ou rebaixar este usuario: "
                    "ele e o unico administrador ativo do sistema. "
                    "Promova outro usuario a administrador antes de continuar."
                )

    sql = """
        UPDATE sch_supervisorio.tb_usuario
        SET nomeusuario = %s, login = %s, papel = %s, ativo = %s
        WHERE idusuario = %s
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (nome, login, papel, ativo, usuario_id))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        if "unique" in str(e).lower():
            raise Exception(f"O login '{login}' ja esta em uso.")
        raise Exception(f"Nao foi possivel atualizar o usuario: {e}")
    finally:
        conn.close()


def redefinir_senha(usuario_id: int, nova_senha: str):
    """Redefine a senha de um usuario (usado pelo admin)."""
    if len(nova_senha) < 6:
        raise Exception("A senha deve ter pelo menos 6 caracteres.")

    sql = "UPDATE sch_supervisorio.tb_usuario SET senhahash = %s WHERE idusuario = %s"
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (gerar_hash_senha(nova_senha), usuario_id))
            if cur.rowcount == 0:
                raise Exception("Usuario nao encontrado.")
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise Exception(f"Nao foi possivel redefinir a senha: {e}")
    finally:
        conn.close()
