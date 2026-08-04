import os
import re
from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(prefix="/media", tags=["Media"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def _media_type(ext: str) -> str:
    return "image/jpeg" if ext in {".jpg", ".jpeg"} else f"image/{ext.lstrip('.')}"


@router.get("/frame")
def get_frame(path: str):
    """
    Serve uma imagem pelo caminho absoluto no servidor.
    Exemplo: GET /media/frame?path=/app/data/fotos/joao_silva/foto_001.jpg
    """
    if not path:
        raise HTTPException(status_code=400, detail="Caminho nao informado")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Arquivo nao encontrado")
    ext = os.path.splitext(path)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Tipo de arquivo nao permitido")
    return FileResponse(path, media_type=_media_type(ext))


def _parse_horario_arquivo(nome_arquivo: str):
    """
    Converte o nome do arquivo de frame em segundos do dia.
    Padrao esperado: HH-MM-SS_mmm.jpg  (ex: 08-11-40_886.jpg)
    Retorna float (segundos desde a meia-noite) ou None se nao bater o padrao.
    """
    base = os.path.splitext(nome_arquivo)[0]
    m = re.match(r"^(\d{2})-(\d{2})-(\d{2})(?:[_-](\d{1,3}))?$", base)
    if not m:
        return None
    h, mi, s = int(m.group(1)), int(m.group(2)), int(m.group(3))
    ms = int(m.group(4) or 0)
    return h * 3600 + mi * 60 + s + ms / 1000.0


@router.get("/detection-frame")
def get_detection_frame(video_path: str, person_folder: str, datahora_ao_vivo: str = ""):
    """
    Serve o frame de uma deteccao.

    A pasta de fotos fica ao lado do video de marcacao:
        dirname(video_path) / person_folder / [HH-MM-SS_mmm].jpg

    Se 'datahora_ao_vivo' for informado, retorna a foto cujo horario no nome
    for o mais proximo desse momento. Caso contrario, retorna a primeira foto.
    """
    if not video_path:
        raise HTTPException(status_code=400, detail="Caminho do video nao informado")
    if not person_folder:
        raise HTTPException(status_code=400, detail="Pasta da pessoa nao informada")

    # Normaliza separadores (o banco pode ter caminhos gravados no padrao Windows)
    video_path_norm = video_path.replace("\\", "/")
    pasta_fotos = os.path.join(os.path.dirname(video_path_norm), person_folder)

    if not os.path.isdir(pasta_fotos):
        raise HTTPException(
            status_code=404,
            detail=f"Pasta de frames nao encontrada no servidor: {pasta_fotos}"
        )

    fotos = [
        f for f in os.listdir(pasta_fotos)
        if os.path.splitext(f)[1].lower() in ALLOWED_EXTENSIONS
    ]
    if not fotos:
        raise HTTPException(status_code=404, detail="Nenhum frame encontrado na pasta")

    escolhida = None

    if datahora_ao_vivo:
        try:
            dt = datetime.fromisoformat(datahora_ao_vivo.replace("Z", "+00:00"))
            alvo = dt.hour * 3600 + dt.minute * 60 + dt.second + dt.microsecond / 1_000_000
            melhor_dist = None
            for f in fotos:
                seg = _parse_horario_arquivo(f)
                if seg is None:
                    continue
                dist = abs(seg - alvo)
                if melhor_dist is None or dist < melhor_dist:
                    melhor_dist = dist
                    escolhida = f
        except ValueError:
            escolhida = None

    if not escolhida:
        escolhida = sorted(fotos)[0]

    caminho = os.path.join(pasta_fotos, escolhida)
    ext = os.path.splitext(caminho)[1].lower()
    return FileResponse(caminho, media_type=_media_type(ext))


@router.get("/detection-frames")
def list_detection_frames(video_path: str, person_folder: str):
    """
    Lista todos os frames disponiveis para uma deteccao (nomes dos arquivos).
    Util para navegar entre os frames daquela pessoa/data.
    """
    if not video_path or not person_folder:
        raise HTTPException(status_code=400, detail="Parametros obrigatorios ausentes")

    video_path_norm = video_path.replace("\\", "/")
    pasta_fotos = os.path.join(os.path.dirname(video_path_norm), person_folder)

    if not os.path.isdir(pasta_fotos):
        return {"frames": [], "folder": pasta_fotos}

    fotos = sorted([
        f for f in os.listdir(pasta_fotos)
        if os.path.splitext(f)[1].lower() in ALLOWED_EXTENSIONS
    ])
    return {"frames": fotos, "folder": pasta_fotos}
