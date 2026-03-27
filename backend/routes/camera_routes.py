from fastapi import APIRouter, HTTPException
from backend.services.database_service import (
    list_cameras,
    get_camera_by_id,
    save_camera,
    delete_camera
)

router = APIRouter(prefix="/cameras", tags=["Cameras"])


@router.get("/")
def get_all_cameras(filter: str = ""):
    return list_cameras(filter)


@router.get("/{camera_id}")
def get_camera(camera_id: int):
    camera = get_camera_by_id(camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    return camera


@router.post("/")
def create_camera(
    name: str, location_id: int,
    floor: int = 0, room_number: int = 0,
    ignore_threshold: float = 0.7, identification_threshold: float = 0.7
):
    try:
        save_camera(name, location_id, floor, room_number, ignore_threshold, identification_threshold)
        return {"message": "Camera created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{camera_id}")
def update_camera(
    camera_id: int, name: str, location_id: int,
    floor: int = 0, room_number: int = 0,
    ignore_threshold: float = 0.7, identification_threshold: float = 0.7
):
    try:
        save_camera(name, location_id, floor, room_number, ignore_threshold, identification_threshold, camera_id)
        return {"message": "Camera updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{camera_id}")
def remove_camera(camera_id: int):
    try:
        delete_camera(camera_id)
        return {"message": "Camera deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
