from fastapi import Depends, APIRouter, HTTPException
from backend.services.auth_dependency import apenas_admin
from backend.services.scenario_service import (
    list_scenarios,
    get_scenario_by_id,
    save_scenario,
    delete_scenario,
    get_cameras_for_scenario,
    add_camera_to_scenario,
    remove_camera_from_scenario,
    list_available_cameras,
    list_available_parameters,
)

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])


@router.get("/", dependencies=[Depends(apenas_admin)])
def get_all_scenarios(filter: str = ""):
    return list_scenarios(filter)


@router.get("/cameras/available", dependencies=[Depends(apenas_admin)])
def get_available_cameras():
    return list_available_cameras()


@router.get("/parameters/available", dependencies=[Depends(apenas_admin)])
def get_available_parameters():
    return list_available_parameters()


@router.get("/{scenario_id}", dependencies=[Depends(apenas_admin)])
def get_scenario(scenario_id: int):
    scenario = get_scenario_by_id(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario


@router.get("/{scenario_id}/cameras", dependencies=[Depends(apenas_admin)])
def get_scenario_cameras(scenario_id: int):
    return get_cameras_for_scenario(scenario_id)


@router.post("/", dependencies=[Depends(apenas_admin)])
def create_scenario(
    description: str, parameter_id: int, active: bool = True, default: bool = False
):
    try:
        scenario_id = save_scenario(description, parameter_id, active, default)
        return {"message": "Scenario created successfully", "id": scenario_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{scenario_id}", dependencies=[Depends(apenas_admin)])
def update_scenario(
    scenario_id: int,
    description: str,
    parameter_id: int,
    active: bool = True,
    default: bool = False,
):
    try:
        save_scenario(description, parameter_id, active, default, scenario_id)
        return {"message": "Scenario updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{scenario_id}", dependencies=[Depends(apenas_admin)])
def remove_scenario(scenario_id: int):
    try:
        delete_scenario(scenario_id)
        return {"message": "Scenario deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{scenario_id}/cameras/{camera_id}", dependencies=[Depends(apenas_admin)])
def add_camera(scenario_id: int, camera_id: int):
    try:
        add_camera_to_scenario(scenario_id, camera_id)
        return {"message": "Camera added to scenario successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{scenario_id}/cameras/{scenario_camera_id}", dependencies=[Depends(apenas_admin)])
def remove_camera(scenario_id: int, scenario_camera_id: int):
    try:
        remove_camera_from_scenario(scenario_camera_id)
        return {"message": "Camera removed from scenario successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
