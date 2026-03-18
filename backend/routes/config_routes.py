from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.services.config_service import (
    initialize_db_parameters,
    list_parameters,
    get_parameter_by_id,
    save_parameters,
    delete_parameter,
    load_parameters
)

router = APIRouter(prefix="/config", tags=["Config"])


class ParameterData(BaseModel):
    name: str
    photos_path: Optional[str] = ""
    maps_path: Optional[str] = ""
    videos_to_process_path: Optional[str] = ""
    processed_videos_path: Optional[str] = ""
    video_markers_path: Optional[str] = ""
    frame_interval: Optional[int] = 10
    image_scale: Optional[float] = 1.0
    detection_model: Optional[str] = "hog"
    recognition_tolerance: Optional[float] = 0.6
    generate_markers: Optional[bool] = False
    finish_when_all_identified: Optional[bool] = False


@router.post("/initialize")
def initialize():
    try:
        initialize_db_parameters()
        return {"message": "Parameters initialized successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/parameters")
def get_all_parameters(filter: str = ""):
    return list_parameters(filter)


@router.get("/parameters/default")
def get_default_parameters():
    try:
        params = load_parameters()
        if not params:
            raise HTTPException(status_code=404, detail="No default parameters found")
        return params
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/parameters/{param_id}")
def get_parameter(param_id: int):
    param = get_parameter_by_id(param_id)
    if not param:
        raise HTTPException(status_code=404, detail="Parameter not found")
    return param


@router.post("/parameters")
def create_parameter(data: ParameterData):
    try:
        param_id = save_parameters(data.model_dump())
        return {"message": "Parameter created successfully", "id": param_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/parameters/{param_id}")
def update_parameter(param_id: int, data: ParameterData):
    try:
        save_parameters(data.model_dump(), param_id)
        return {"message": "Parameter updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/parameters/{param_id}")
def remove_parameter(param_id: int):
    try:
        delete_parameter(param_id)
        return {"message": "Parameter deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))