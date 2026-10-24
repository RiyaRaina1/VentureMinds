from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from backend.database.connection import get_db
from backend.schemas.startup import StartupCreate, StartupUpdate, StartupResponse
from backend.services.startup_service import (
    create_startup,
    get_startups,
    get_startup,
    update_startup,
    delete_startup,
)

router = APIRouter(prefix="/api/startups", tags=["Startups"])


@router.post(
    "",
    response_model=StartupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new startup project",
    description="Registers and persists a new startup project into the database."
)
def create_new_startup(payload: StartupCreate, db: Session = Depends(get_db)):
    try:
        new_startup = create_startup(db, payload)
        return new_startup
    except SQLAlchemyError as err:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while creating startup project."
        )


@router.get(
    "",
    response_model=List[StartupResponse],
    status_code=status.HTTP_200_OK,
    summary="List all startup projects",
    description="Retrieves persisted startup projects from the database."
)
def list_startups(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    if skip < 0 or limit <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pagination parameters 'skip' must be >= 0 and 'limit' must be > 0."
        )
    try:
        return get_startups(db, skip=skip, limit=limit)
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while retrieving startup projects."
        )


@router.get(
    "/{startup_id}",
    response_model=StartupResponse,
    status_code=status.HTTP_200_OK,
    summary="Get startup project by ID",
    description="Retrieves a single startup project record by its unique database ID."
)
def get_startup_by_id(startup_id: int, db: Session = Depends(get_db)):
    if startup_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid startup ID. ID must be a positive integer."
        )
    startup = get_startup(db, startup_id)
    if not startup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Startup with ID {startup_id} not found."
        )
    return startup


@router.put(
    "/{startup_id}",
    response_model=StartupResponse,
    status_code=status.HTTP_200_OK,
    summary="Update startup project by ID",
    description="Updates existing startup metadata in the database."
)
def update_startup_by_id(startup_id: int, payload: StartupUpdate, db: Session = Depends(get_db)):
    if startup_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid startup ID. ID must be a positive integer."
        )
    try:
        updated = update_startup(db, startup_id, payload)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Startup with ID {startup_id} not found."
            )
        return updated
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while updating startup project."
        )


@router.delete(
    "/{startup_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete startup project by ID",
    description="Deletes a startup project from the database."
)
def delete_startup_by_id(startup_id: int, db: Session = Depends(get_db)):
    if startup_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid startup ID. ID must be a positive integer."
        )
    try:
        deleted = delete_startup(db, startup_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Startup with ID {startup_id} not found."
            )
        return {"status": "ok", "message": f"Startup {startup_id} deleted successfully", "id": startup_id}
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while deleting startup project."
        )
