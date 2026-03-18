from fastapi import APIRouter, HTTPException
from backend.services.event_service import (
    list_events,
    get_event_by_id,
    save_event,
    delete_event
)

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("/")
def get_all_events(filter: str = ""):
    return list_events(filter)


@router.get("/{event_id}")
def get_event(event_id: int):
    event = get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.post("/")
def create_event(name: str, duration: int):
    try:
        save_event(name, duration)
        return {"message": "Event created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{event_id}")
def update_event(event_id: int, name: str, duration: int):
    try:
        save_event(name, duration, event_id)
        return {"message": "Event updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{event_id}")
def remove_event(event_id: int):
    try:
        delete_event(event_id)
        return {"message": "Event deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))