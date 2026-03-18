from fastapi import APIRouter, HTTPException
from backend.services.database_service import (
    list_persons,
    get_person_by_id,
    save_person,
    delete_person
)

router = APIRouter(prefix="/persons", tags=["Persons"])


@router.get("/")
def get_all_persons(filter: str = ""):
    return list_persons(filter)


@router.get("/{person_id}")
def get_person(person_id: int):
    person = get_person_by_id(person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person


@router.post("/")
def create_person(name: str, document: str, photos_folder: str = ""):
    try:
        save_person(name, document, photos_folder)
        return {"message": "Person created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{person_id}")
def remove_person(person_id: int):
    try:
        delete_person(person_id)
        return {"message": "Person deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))