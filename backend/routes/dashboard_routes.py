from fastapi import APIRouter, HTTPException
from backend.services.dashboard_service import (
    get_indicators,
    get_delayed_persons,
    get_locations_for_filter,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/indicators")
def indicators(start_date: str, end_date: str, location_id: int = None):
    try:
        return get_indicators(start_date, end_date, location_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/delayed-persons")
def delayed_persons(start_date: str, end_date: str, location_id: int = None):
    try:
        return get_delayed_persons(start_date, end_date, location_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/locations")
def locations_filter():
    return get_locations_for_filter()
