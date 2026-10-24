from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from backend.models.startup import Startup
from backend.schemas.startup import StartupCreate, StartupUpdate


def create_startup(db: Session, data: StartupCreate) -> Startup:
    """Create a new startup record and commit to database."""
    startup = Startup(
        name=data.name.strip(),
        description=data.description.strip() if data.description else None
    )
    db.add(startup)
    db.commit()
    db.refresh(startup)
    return startup


def get_startups(db: Session, skip: int = 0, limit: int = 100) -> List[Startup]:
    """Retrieve all startup records with pagination."""
    return db.query(Startup).offset(skip).limit(limit).all()


def get_startup(db: Session, startup_id: int) -> Optional[Startup]:
    """Retrieve a single startup record by ID."""
    return db.query(Startup).filter(Startup.id == startup_id).first()


def update_startup(db: Session, startup_id: int, data: StartupUpdate) -> Optional[Startup]:
    """Update an existing startup record by ID."""
    startup = get_startup(db, startup_id)
    if not startup:
        return None

    if data.name is not None:
        startup.name = data.name.strip()
    if data.description is not None:
        startup.description = data.description.strip()
    startup.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(startup)
    return startup


def delete_startup(db: Session, startup_id: int) -> bool:
    """Delete a startup record by ID."""
    startup = get_startup(db, startup_id)
    if not startup:
        return False

    db.delete(startup)
    db.commit()
    return True
