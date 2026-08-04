import os
import shutil
import re
import time
from fastapi import APIRouter, HTTPException, UploadFile, File
from backend.services.database_service import (
    list_persons,
    get_person_by_id,
    save_person,
    delete_person,
)

router = APIRouter(prefix="/persons", tags=["Persons"])

FOTOS_DIR = os.getenv("FOTOS_DIR", "/app/fotos")


def _normalizar_nome(nome: str) -> str:
    """Converte 'João Silva' em 'joao_silva' para usar como nome de pasta."""
    nome = nome.lower().strip()
    nome = re.sub(r'[áàãâä]', 'a', nome)
    nome = re.sub(r'[éèêë]', 'e', nome)
    nome = re.sub(r'[íìîï]', 'i', nome)
    nome = re.sub(r'[óòõôö]', 'o', nome)
    nome = re.sub(r'[úùûü]', 'u', nome)
    nome = re.sub(r'[ç]', 'c', nome)
    nome = re.sub(r'[^a-z0-9]', '_', nome)
    nome = re.sub(r'_+', '_', nome).strip('_')
    return nome


@router.get("/")
def get_all_persons(filter: str = ""):
    return list_persons(filter)


@router.get("/{person_id}")
def get_person(person_id: int):
    person = get_person_by_id(person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person


@router.post("/")
def create_person(name: str, document: str, photos_folder: str = "", biodoc_card: str = ""):
    try:
        if not photos_folder:
            photos_folder = _normalizar_nome(name)
        new_id = save_person(name, document, photos_folder, biodoc_card=biodoc_card or None)
        pasta = os.path.join(FOTOS_DIR, photos_folder)
        os.makedirs(pasta, exist_ok=True)
        return {"message": "Person created successfully", "id": new_id, "photos_folder": photos_folder}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{person_id}")
def update_person(person_id: int, name: str, document: str, photos_folder: str = "", biodoc_card: str = ""):
    try:
        person = get_person_by_id(person_id)
        if not person:
            raise HTTPException(status_code=404, detail="Person not found")
        if not photos_folder:
            photos_folder = person.get("photos_folder") or _normalizar_nome(name)
        card = biodoc_card if biodoc_card != "" else person.get("biodoc_card")
        save_person(name, document, photos_folder, person_id, biodoc_card=card or None)
        pasta = os.path.join(FOTOS_DIR, photos_folder)
        os.makedirs(pasta, exist_ok=True)
        return {"message": "Person updated successfully", "id": person_id, "photos_folder": photos_folder}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{person_id}/photos")
async def upload_photo(person_id: int, file: UploadFile = File(...)):
    """Faz upload de uma foto para a pasta da pessoa."""
    person = get_person_by_id(person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    ext = os.path.splitext(file.filename or "foto.jpg")[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
        raise HTTPException(status_code=400, detail="Formato não suportado. Use jpg, png ou webp.")

    photos_folder = person.get("photos_folder") or _normalizar_nome(person.get("name", str(person_id)))
    pasta = os.path.join(FOTOS_DIR, photos_folder)
    os.makedirs(pasta, exist_ok=True)

    nome_arquivo = f"foto_{int(time.time())}{ext}"
    destino = os.path.join(pasta, nome_arquivo)

    try:
        with open(destino, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar foto: {e}")

    save_person(person["name"], person["document"], photos_folder, person_id,
                biodoc_card=person.get("biodoc_card") or None)

    return {"message": "Foto enviada com sucesso", "path": destino, "filename": nome_arquivo}


@router.get("/{person_id}/photos")
def list_photos(person_id: int):
    """Lista as fotos cadastradas de uma pessoa."""
    person = get_person_by_id(person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    photos_folder = person.get("photos_folder", "")
    if not photos_folder:
        return {"photos": []}

    pasta = os.path.join(FOTOS_DIR, photos_folder)
    if not os.path.isdir(pasta):
        return {"photos": []}

    fotos = [
        f for f in os.listdir(pasta)
        if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))
    ]
    return {"photos": fotos, "folder": photos_folder, "folder_path": pasta}


@router.delete("/{person_id}/photos/{filename}")
def delete_photo(person_id: int, filename: str):
    """Remove uma foto específica da pessoa."""
    person = get_person_by_id(person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    photos_folder = person.get("photos_folder", "")
    if not photos_folder:
        raise HTTPException(status_code=404, detail="Pasta de fotos não configurada")

    filename = os.path.basename(filename)
    caminho = os.path.join(FOTOS_DIR, photos_folder, filename)

    if not os.path.exists(caminho):
        raise HTTPException(status_code=404, detail="Foto não encontrada")

    os.remove(caminho)
    return {"message": "Foto removida com sucesso"}


@router.delete("/{person_id}")
def remove_person(person_id: int):
    try:
        delete_person(person_id)
        return {"message": "Person deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
