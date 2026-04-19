import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from .. import crud, schemas, models
from ..ml import inference
from ..dependencies import get_current_user
from ..limiter import limiter

logger = logging.getLogger("autoscope.predictions")

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("/model-info")
def model_info():
    return inference.get_model_info()


@router.get("/equipment-values")
def equipment_values():
    """Return equipment resale value map (EUR) used by the ML model."""
    from ..ml.train_extended import EQUIPMENT_VALUE
    return {"values": EQUIPMENT_VALUE}


@router.post("/predict", response_model=schemas.PredictResponse)
@limiter.limit("20/minute")
def predict_price(
    request: Request,
    payload: schemas.PredictionInput,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not inference.is_ready():
        raise HTTPException(status_code=503, detail="Model not trained.")
    try:
        result = inference.predict(payload.model_dump())
    except Exception as exc:
        logger.error("Inference failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Prediction failed due to a model error.")

    record = crud.create_prediction_record(db, payload.model_dump(), result["predicted_price"], user_id=current_user.id)
    return schemas.PredictResponse(
        predicted_price=result["predicted_price"],
        prediction_id=record.id,
        input=payload,
    )


@router.get("/history", response_model=List[schemas.PredictionOut])
def get_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return crud.get_predictions(db, skip=skip, limit=limit, user_id=current_user.id)


@router.get("/{prediction_id}", response_model=schemas.PredictionOut)
def get_prediction(
    prediction_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    pred = crud.get_prediction(db, prediction_id)
    if not pred:
        raise HTTPException(status_code=404, detail="Prediction not found")
    if current_user.role != "admin" and pred.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return pred


@router.delete("/{prediction_id}", status_code=204)
def delete_prediction(
    prediction_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    pred = crud.get_prediction(db, prediction_id)
    if not pred:
        raise HTTPException(status_code=404, detail="Prediction not found")
    if current_user.role != "admin" and pred.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    crud.delete_prediction(db, prediction_id)
