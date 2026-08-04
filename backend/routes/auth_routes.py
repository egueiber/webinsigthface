# -*- coding: utf-8 -*-
"""
Rotas de autenticacao.

Inclui rate limit no login para mitigar ataques de forca bruta:
  - por login (usuario): bloqueia apos N tentativas falhas
  - por IP: bloqueia apos N tentativas falhas
O contador zera quando o login tem sucesso ou apos a janela de tempo.
"""
import os
import time
import threading
from collections import defaultdict
from typing import Optional

from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel

from backend.services.auth_service import (
    autenticar,
    criar_token,
    validar_token,
    get_usuario_por_id,
    contar_usuarios,
    criar_usuario,
)

router = APIRouter(prefix="/auth", tags=["Auth"])

# ── Rate limit ────────────────────────────────────────────────────────────────
# Configuravel por variavel de ambiente.
MAX_TENTATIVAS   = int(os.getenv("LOGIN_MAX_TENTATIVAS", "5"))     # falhas permitidas
JANELA_SEGUNDOS  = int(os.getenv("LOGIN_JANELA_SEGUNDOS", "300"))  # janela de contagem (5 min)
BLOQUEIO_SEGUNDOS = int(os.getenv("LOGIN_BLOQUEIO_SEGUNDOS", "300"))  # tempo bloqueado (5 min)

_lock = threading.Lock()
# chave -> {"falhas": int, "primeira": timestamp, "bloqueado_ate": timestamp}
_tentativas = defaultdict(lambda: {"falhas": 0, "primeira": 0.0, "bloqueado_ate": 0.0})


def _limpar_expirados(agora: float):
    """Remove entradas antigas para o dicionario nao crescer indefinidamente."""
    expirados = [
        k for k, v in _tentativas.items()
        if v["bloqueado_ate"] < agora and (agora - v["primeira"]) > JANELA_SEGUNDOS
    ]
    for k in expirados:
        del _tentativas[k]


def _checar_bloqueio(chave: str):
    """Levanta 429 se a chave estiver bloqueada."""
    agora = time.time()
    with _lock:
        reg = _tentativas[chave]
        if reg["bloqueado_ate"] > agora:
            faltam = int(reg["bloqueado_ate"] - agora)
            raise HTTPException(
                status_code=429,
                detail=f"Muitas tentativas. Tente novamente em {faltam} segundos."
            )


def _registrar_falha(chave: str):
    """Conta uma falha e bloqueia se passar do limite."""
    agora = time.time()
    with _lock:
        _limpar_expirados(agora)
        reg = _tentativas[chave]

        # Reinicia a contagem se a janela expirou
        if reg["primeira"] == 0.0 or (agora - reg["primeira"]) > JANELA_SEGUNDOS:
            reg["primeira"] = agora
            reg["falhas"] = 0

        reg["falhas"] += 1
        if reg["falhas"] >= MAX_TENTATIVAS:
            reg["bloqueado_ate"] = agora + BLOQUEIO_SEGUNDOS
            reg["falhas"] = 0
            reg["primeira"] = 0.0


def _limpar_falhas(chave: str):
    """Zera o contador apos um login bem-sucedido."""
    with _lock:
        if chave in _tentativas:
            del _tentativas[chave]


# ── Modelos ───────────────────────────────────────────────────────────────────
class LoginData(BaseModel):
    login: str
    senha: str


class PrimeiroAdminData(BaseModel):
    nome: str
    login: str
    senha: str


# ── Rotas ─────────────────────────────────────────────────────────────────────
@router.post("/login")
def login(data: LoginData, request: Request):
    """Valida credenciais e devolve o token JWT. Protegido por rate limit."""
    ip = request.client.host if request.client else "desconhecido"
    login_norm = data.login.strip().lower()

    chave_ip    = f"ip:{ip}"
    chave_login = f"login:{login_norm}"

    # Bloqueia antes de tentar autenticar
    _checar_bloqueio(chave_ip)
    _checar_bloqueio(chave_login)

    usuario = autenticar(data.login.strip(), data.senha)

    if not usuario:
        _registrar_falha(chave_ip)
        _registrar_falha(chave_login)
        # Mensagem generica: nao revela se o usuario existe
        raise HTTPException(status_code=401, detail="Login ou senha invalidos.")

    _limpar_falhas(chave_ip)
    _limpar_falhas(chave_login)

    token = criar_token({
        "sub": str(usuario["id"]),
        "login": usuario["login"],
        "papel": usuario["papel"],
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "usuario": usuario,
    }


@router.get("/me")
def me(authorization: Optional[str] = Header(None)):
    """Retorna os dados do usuario dono do token enviado."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Token nao informado.")

    token = authorization.split(" ", 1)[1].strip()
    payload = validar_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token invalido ou expirado.")

    usuario = get_usuario_por_id(int(payload.get("sub", 0)))
    if not usuario or not usuario["ativo"]:
        raise HTTPException(status_code=401, detail="Usuario nao encontrado ou inativo.")

    return usuario


@router.get("/setup-needed")
def setup_needed():
    """Informa se ainda nao existe nenhum usuario cadastrado."""
    return {"setup_needed": contar_usuarios() == 0}


@router.post("/setup")
def setup(data: PrimeiroAdminData):
    """
    Cria o primeiro usuario admin do sistema.
    So funciona enquanto nao houver nenhum usuario cadastrado.
    """
    if contar_usuarios() > 0:
        raise HTTPException(
            status_code=403,
            detail="Ja existem usuarios cadastrados. Use a tela de usuarios para criar novos."
        )
    try:
        novo_id = criar_usuario(data.nome, data.login.strip(), data.senha, papel="admin")
        return {"message": "Administrador criado com sucesso.", "id": novo_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
