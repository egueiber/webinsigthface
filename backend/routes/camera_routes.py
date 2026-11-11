from fastapi import Depends, APIRouter, HTTPException
from backend.services.auth_dependency import apenas_admin
from backend.services.database_service import (
    list_cameras,
    get_camera_by_id,
    save_camera,
    delete_camera
)

router = APIRouter(prefix="/cameras", tags=["Cameras"])


@router.get("/", dependencies=[Depends(apenas_admin)])
def get_all_cameras(filter: str = ""):
    return list_cameras(filter)


@router.get("/{camera_id}", dependencies=[Depends(apenas_admin)])
def get_camera(camera_id: int):
    camera = get_camera_by_id(camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    return camera


@router.post("/", dependencies=[Depends(apenas_admin)])
def create_camera(
    name: str, location_id: int,
    floor: int = 0, room_number: int = 0,
    ignore_threshold: float = 0.7, identification_threshold: float = 0.7,
    url_rtsp: str = None, processar_tempo_real: bool = False
):
    try:
        save_camera(name, location_id, floor, room_number, ignore_threshold, identification_threshold, None, url_rtsp, processar_tempo_real)
        return {"message": "Camera created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{camera_id}", dependencies=[Depends(apenas_admin)])
def update_camera(
    camera_id: int, name: str, location_id: int,
    floor: int = 0, room_number: int = 0,
    ignore_threshold: float = 0.7, identification_threshold: float = 0.7,
    url_rtsp: str = None, processar_tempo_real: bool = False
):
    try:
        save_camera(name, location_id, floor, room_number, ignore_threshold, identification_threshold, camera_id, url_rtsp, processar_tempo_real)
        return {"message": "Camera updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{camera_id}", dependencies=[Depends(apenas_admin)])
def remove_camera(camera_id: int):
    try:
        delete_camera(camera_id)
        return {"message": "Camera deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
