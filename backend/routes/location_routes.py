from fastapi import Depends, APIRouter, HTTPException
from backend.services.auth_dependency import apenas_admin
from backend.services.location_service import (
    list_locations,
    get_location_by_id,
    save_location,
    delete_location
)

router = APIRouter(prefix="/locations", tags=["Locations"])


@router.get("/")
def get_all_locations(filter: str = ""):
    return list_locations(filter)


@router.get("/{location_id}", dependencies=[Depends(apenas_admin)])
def get_location(location_id: int):
    location = get_location_by_id(location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location


@router.post("/", dependencies=[Depends(apenas_admin)])
def create_location(name: str, map_path: str = ""):
    try:
        new_id = save_location(name, map_path)
        return {"message": "Location created successfully", "id": new_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{location_id}", dependencies=[Depends(apenas_admin)])
def update_location(location_id: int, name: str, map_path: str = ""):
    try:
        save_location(name, map_path, location_id)
        return {"message": "Location updated successfully", "id": location_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{location_id}", dependencies=[Depends(apenas_admin)])
def remove_location(location_id: int, map_path: str = None):
    try:
        delete_location(location_id, map_path)
        return {"message": "Location deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))