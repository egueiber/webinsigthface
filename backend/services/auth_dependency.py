# -*- coding: utf-8 -*-
"""
Dependencias de autenticacao para proteger as rotas.

Uso numa rota:
    from backend.services.auth_dependency import usuario_logado, apenas_admin

    @router.get("/algo")
    def algo(usuario = Depends(usuario_logado)):
        ...

    @router.post("/users")
    def criar(usuario = Depends(apenas_admin)):
        ...
"""
from fastapi import HTTPException, Header
from typing import Optional

from backend.services.auth_service import validar_token, get_usuario_por_id


def usuario_logado(authorization: Optional[str] = Header(None)):
    """
    Valida o token do header Authorization e retorna o usuario.
    Levanta 401 se nao houver token valido.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Nao autenticado.")

    token = authorization.split(" ", 1)[1].strip()
    payload = validar_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Sessao expirada. Faca login novamente.")

    usuario = get_usuario_por_id(int(payload.get("sub", 0)))
    if not usuario or not usuario.get("ativo"):
        raise HTTPException(status_code=401, detail="Usuario nao encontrado ou inativo.")

    return usuario


def apenas_admin(authorization: Optional[str] = Header(None)):
    """Igual ao usuario_logado, mas exige papel de admin."""
    usuario = usuario_logado(authorization)
    if usuario.get("papel") != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores.")
    return usuario
