# -*- coding: utf-8 -*-
"""
Rotas de gerenciamento de usuarios.
Todas exigem papel de admin (ver dependencies no main.py / apenas_admin).
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from backend.services.auth_service import (
    listar_usuarios,
    criar_usuario,
    atualizar_usuario,
    redefinir_senha,
    get_usuario_por_id,
)
from backend.services.auth_dependency import apenas_admin

# Todas as rotas de usuarios exigem admin, inclusive as que forem criadas depois.
router = APIRouter(prefix="/users", tags=["Usuarios"], dependencies=[Depends(apenas_admin)])


class NovoUsuarioData(BaseModel):
    nome: str
    login: str
    senha: str
    papel: str = "user"


class AtualizarUsuarioData(BaseModel):
    nome: str
    login: str
    papel: str
    ativo: bool


class RedefinirSenhaData(BaseModel):
    nova_senha: str


@router.get("/")
def get_all_users(admin=Depends(apenas_admin)):
    """Lista todos os usuarios cadastrados."""
    return listar_usuarios()


@router.get("/{user_id}")
def get_user(user_id: int, admin=Depends(apenas_admin)):
    usuario = get_usuario_por_id(user_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado.")
    return usuario


@router.post("/")
def create_user(data: NovoUsuarioData, admin=Depends(apenas_admin)):
    try:
        novo_id = criar_usuario(data.nome.strip(), data.login.strip(), data.senha, data.papel)
        return {"message": "Usuario criado com sucesso.", "id": novo_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{user_id}")
def update_user(user_id: int, data: AtualizarUsuarioData, admin=Depends(apenas_admin)):
    try:
        atualizar_usuario(user_id, data.nome.strip(), data.login.strip(), data.papel, data.ativo)
        return {"message": "Usuario atualizado com sucesso."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{user_id}/reset-password")
def reset_password(user_id: int, data: RedefinirSenhaData, admin=Depends(apenas_admin)):
    try:
        redefinir_senha(user_id, data.nova_senha)
        return {"message": "Senha redefinida com sucesso."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
