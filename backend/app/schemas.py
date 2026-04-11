from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class CarBase(BaseModel):
    make: str
    model: str
    year: int
    body_type: Optional[str] = None
    mileage: Optional[float] = None
    door_count: Optional[int] = None
    nr_seats: Optional[int] = None
    color: Optional[str] = None
    fuel_type: Optional[str] = None
    engine_capacity: Optional[float] = None
    engine_power: Optional[float] = None
    gearbox: Optional[str] = None
    transmission: Optional[str] = None
    pollution_standard: Optional[str] = None
    price: float


class CarCreate(CarBase):
    pass


class CarUpdate(BaseModel):
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    body_type: Optional[str] = None
    mileage: Optional[float] = None
    door_count: Optional[int] = None
    nr_seats: Optional[int] = None
    color: Optional[str] = None
    fuel_type: Optional[str] = None
    engine_capacity: Optional[float] = None
    engine_power: Optional[float] = None
    gearbox: Optional[str] = None
    transmission: Optional[str] = None
    pollution_standard: Optional[str] = None
    price: Optional[float] = None


class CarOut(CarBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


class CarListResponse(BaseModel):
    items: List[CarOut]
    total: int
    page: int
    page_size: int


class PredictionInput(BaseModel):
    make: str
    model: str
    year: int
    body_type: str
    mileage: float
    color: str
    fuel_type: str
    engine_capacity: float
    engine_power: float
    gearbox: str
    transmission: str
    pollution_standard: str
    equipment_count: Optional[int] = 0


class PredictionOut(BaseModel):
    id: int
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    body_type: Optional[str] = None
    mileage: Optional[float] = None
    color: Optional[str] = None
    fuel_type: Optional[str] = None
    engine_capacity: Optional[float] = None
    engine_power: Optional[float] = None
    gearbox: Optional[str] = None
    transmission: Optional[str] = None
    pollution_standard: Optional[str] = None
    predicted_price: float
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


class PredictResponse(BaseModel):
    predicted_price: float
    prediction_id: int
    input: PredictionInput


class StatsResponse(BaseModel):
    total_cars: int
    avg_price: float
    min_price: float
    max_price: float
    avg_mileage: float
    total_makes: int
