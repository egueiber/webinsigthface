import os
import shutil
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from backend.services.database_service import get_db_connection

router = APIRouter(prefix="/locations", tags=["Locations - Mapa"])

MAPAS_DIR = os.getenv("MAPAS_DIR", "/app/data/mapas")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


@router.post("/{location_id}/mapa")
async def upload_mapa(location_id: int, file: UploadFile = File(...)):
    """Upload de imagem de mapa para uma localização."""
    ext = os.path.splitext(file.filename or "mapa.jpg")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Formato não suportado. Use jpg, png ou webp.")

    os.makedirs(MAPAS_DIR, exist_ok=True)
    destino = os.path.join(MAPAS_DIR, f"localizacao_{location_id}{ext}")

    try:
        with open(destino, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar arquivo: {e}")

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE sch_supervisorio.tb_localizacao SET mapacamera = %s WHERE idlocalizacao = %s",
                (destino, location_id)
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar banco: {e}")
    finally:
        conn.close()

    return {"message": "Mapa enviado com sucesso", "path": destino}


@router.get("/{location_id}/mapa")
def get_mapa(location_id: int):
    """Retorna a imagem de mapa de uma localização."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT mapacamera FROM sch_supervisorio.tb_localizacao WHERE idlocalizacao = %s",
                (location_id,)
            )
            row = cur.fetchone()
    finally:
        conn.close()

    if not row or not row[0]:
        raise HTTPException(status_code=404, detail="Mapa não cadastrado")
    path = row[0]
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado no servidor")
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    media_type = "image/jpeg" if ext in {"jpg", "jpeg"} else f"image/{ext}"
    return FileResponse(path, media_type=media_type)
