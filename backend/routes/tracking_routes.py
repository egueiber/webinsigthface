from fastapi import APIRouter, HTTPException
from backend.services.database_service import (
    get_area_tracking_data,
    get_person_path_data,
    get_persons_in_period
)

router = APIRouter(prefix="/tracking", tags=["Tracking"])


@router.get("/area")
def area_tracking(location_id: int, date_filter: str):
    """Detecções numa localização em uma data. date_filter: YYYY-MM-DD"""
    try:
        return get_area_tracking_data(location_id, date_filter)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/persons")
def persons_in_period(start_date: str, end_date: str, location_id: int = None):
    """Pessoas com registros no período."""
    try:
        return get_persons_in_period(start_date, end_date, location_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/person-path")
def person_path(person_id: int, start_date: str, end_date: str, identified_only: bool = True):
    """Sequência de câmeras percorridas por uma pessoa."""
    try:
        return get_person_path_data(person_id, start_date, end_date, identified_only)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
