import os
import time
import re
"""from fastapi import APIRouter, HTTPException
from backend.services.auth_dependency import apenas_admin, Depends
"""
from fastapi import APIRouter, Depends, HTTPException
from backend.services.auth_dependency import apenas_admin
from backend.services.biodoc_service import (
    buscar_imagem_principal,
    salvar_imagem_base64,
    STATUS_CARTAO,
)
from backend.services.database_service import get_person_by_id, save_person
from backend.services.face_crop_service import recortar_rosto

router = APIRouter(prefix="/biodoc", tags=["Biodoc"])

FOTOS_DIR = os.getenv("FOTOS_DIR", "/app/fotos")


def _normalizar_nome(nome: str) -> str:
    nome = nome.lower().strip()
    for a, b in [("[áàãâä]", "a"), ("[éèêë]", "e"), ("[íìîï]", "i"),
                 ("[óòõôö]", "o"), ("[úùûü]", "u"), ("[ç]", "c")]:
        nome = re.sub(a, b, nome)
    nome = re.sub(r"[^a-z0-9]", "_", nome)
    return re.sub(r"_+", "_", nome).strip("_")


@router.get("/consultar/{id_card}", dependencies=[Depends(apenas_admin)])
def consultar_carteirinha(id_card: str):
    """
    Consulta uma carteirinha na Biodoc e retorna os dados (sem salvar).
    Usado para o usuário pré-visualizar antes de vincular.
    """
    try:
        info = buscar_imagem_principal(id_card)
        return {
            "status": info["status"],
            "status_descricao": STATUS_CARTAO.get(info["status"], "Desconhecido"),
            "name": info["name"],
            "tem_imagem": bool(info["base64_image"]),
            "base64_preview": info["base64_image"],
            "release_biometric": info["release_biometric"],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        # 502, não 401: é a Biodoc recusando a credencial dela, não a sessão
        # do usuário no Health Track. Usar 401 aqui faria o frontend deslogar
        # o usuário à toa (request() trata qualquer 401 como sessão expirada).
        raise HTTPException(status_code=502, detail=f"Biodoc: {e}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erro ao consultar Biodoc: {e}")


@router.post("/vincular/{person_id}", dependencies=[Depends(apenas_admin)])
def vincular_foto_biodoc(person_id: int, id_card: str):
    """
    Busca a foto do beneficiário na Biodoc pela carteirinha e salva na
    pasta de fotos da pessoa (que o motor insightface lê).
    Também grava o número da carteirinha no cadastro da pessoa.
    """
    person = get_person_by_id(person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")

    try:
        info = buscar_imagem_principal(id_card)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        # Mesmo motivo do endpoint /consultar acima: 502, não 401.
        raise HTTPException(status_code=502, detail=f"Biodoc: {e}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erro ao consultar Biodoc: {e}")

    if not info["base64_image"]:
        status_desc = STATUS_CARTAO.get(info["status"], "Desconhecido")
        raise HTTPException(
            status_code=422,
            detail=f"A Biodoc não retornou imagem para esta carteirinha. Status: {status_desc}."
        )

    # Define a pasta de fotos da pessoa
    photos_folder = person.get("photos_folder") or _normalizar_nome(person.get("name", str(person_id)))
    nome_arquivo = f"biodoc_{int(time.time())}.jpg"
    destino = os.path.join(FOTOS_DIR, photos_folder, nome_arquivo)

    try:
        salvar_imagem_base64(info["base64_image"], destino)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar imagem: {e}")

    # Recorta o rosto: algumas fotos da Biodoc vêm de longe/corpo inteiro, o que
    # prejudica o reconhecimento. Se nenhum rosto for detectado, a imagem
    # original é mantida — e o vínculo NÃO falha por causa do recorte.
    try:
        resultado_crop = recortar_rosto(destino)
    except Exception as e:
        resultado_crop = {"recortado": False, "motivo": f"Erro no recorte: {e}"}

    # Atualiza o cadastro: pasta de fotos + carteirinha
    save_person(
        person["name"], person["document"], photos_folder,
        person_id=person_id, biodoc_card=id_card
    )

    if resultado_crop.get("recortado"):
        msg = "Foto da Biodoc vinculada e rosto recortado com sucesso."
    else:
        msg = f"Foto da Biodoc vinculada. Recorte não aplicado: {resultado_crop.get('motivo', '')}".strip()

    return {
        "message": msg,
        "filename": nome_arquivo,
        "biodoc_name": info["name"],
        "photos_folder": photos_folder,
        "rosto_recortado": resultado_crop.get("recortado", False),
        "crop_motivo": resultado_crop.get("motivo", ""),
    }
