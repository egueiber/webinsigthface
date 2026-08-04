from fastapi import APIRouter, HTTPException
from backend.services.database_service import (
    list_person_events,
    get_person_event_by_id,
    save_person_event,
    delete_person_event,
)
from datetime import datetime

router = APIRouter(prefix="/person-events", tags=["Person Events"])


@router.get("/")
def get_all_person_events(person_id: int = None):
    return list_person_events(person_id)


@router.get("/{person_event_id}")
def get_person_event(person_event_id: int):
    pe = get_person_event_by_id(person_event_id)
    if not pe:
        raise HTTPException(status_code=404, detail="Person event not found")
    return pe


@router.post("/")
def create_person_event(
    person_id: int, event_id: int, entry_datetime: str,
    expected_exit_datetime: str = None, actual_exit_datetime: str = None,
    event_cancelled: bool = False,
):
    try:
        entry    = datetime.fromisoformat(entry_datetime.replace("Z", "+00:00"))
        expected = datetime.fromisoformat(expected_exit_datetime.replace("Z", "+00:00")) if expected_exit_datetime else None
        actual   = datetime.fromisoformat(actual_exit_datetime.replace("Z", "+00:00"))   if actual_exit_datetime   else None
        save_person_event(person_id, event_id, entry, expected, actual, event_cancelled)
        return {"message": "Person event created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{person_event_id}")
def update_person_event(
    person_event_id: int, person_id: int, event_id: int, entry_datetime: str,
    expected_exit_datetime: str = None, actual_exit_datetime: str = None,
    event_cancelled: bool = False,
):
    try:
        entry    = datetime.fromisoformat(entry_datetime.replace("Z", "+00:00"))
        expected = datetime.fromisoformat(expected_exit_datetime.replace("Z", "+00:00")) if expected_exit_datetime else None
        actual   = datetime.fromisoformat(actual_exit_datetime.replace("Z", "+00:00"))   if actual_exit_datetime   else None
        save_person_event(person_id, event_id, entry, expected, actual, event_cancelled, person_event_id)
        return {"message": "Person event updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{person_event_id}")
def remove_person_event(person_event_id: int):
    try:
        delete_person_event(person_event_id)
        return {"message": "Person event deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
