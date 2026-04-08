from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from .. import crud

router = APIRouter(prefix="/makes", tags=["makes"])


@router.get("")
def get_makes(db: Session = Depends(get_db)):
    """All unique car makes (sorted)."""
    return {"makes": crud.get_makes(db)}


# NOTE: static route /options must be declared BEFORE /{make}/models
@router.get("/options")
def get_options(db: Session = Depends(get_db)):
    """All unique values for every filterable field."""
    return crud.get_field_options(db)


@router.get("/{make}/models")
def get_models(make: str, db: Session = Depends(get_db)):
    """All models available for a given make."""
    return {"make": make, "models": crud.get_models_for_make(db, make)}
