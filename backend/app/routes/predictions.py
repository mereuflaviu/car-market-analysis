from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from .. import crud, schemas
from ..ml import inference

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("/model-info")
def model_info():
    """Current ML model status and metrics."""
    return inference.get_model_info()


@router.post("/predict", response_model=schemas.PredictResponse)
def predict_price(payload: schemas.PredictionInput, db: Session = Depends(get_db)):
    """Run XGBoost price prediction and save to history."""
    if not inference.is_ready():
        raise HTTPException(
            status_code=503,
            detail="Model not trained. Run: cd backend && python app/ml/train.py",
        )
    result = inference.predict(payload.model_dump())
    record = crud.create_prediction_record(db, payload.model_dump(), result["predicted_price"])
    return schemas.PredictResponse(
        predicted_price=result["predicted_price"],
        prediction_id=record.id,
        input=payload,
    )


@router.get("/history", response_model=List[schemas.PredictionOut])
def get_history(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """Prediction history (newest first)."""
    return crud.get_predictions(db, skip=skip, limit=limit)


@router.get("/{prediction_id}", response_model=schemas.PredictionOut)
def get_prediction(prediction_id: int, db: Session = Depends(get_db)):
    """Get a single prediction by ID."""
    pred = crud.get_prediction(db, prediction_id)
    if not pred:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return pred


@router.delete("/{prediction_id}", status_code=204)
def delete_prediction(prediction_id: int, db: Session = Depends(get_db)):
    """Remove a prediction from history."""
    if not crud.delete_prediction(db, prediction_id):
        raise HTTPException(status_code=404, detail="Prediction not found")
