from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime


class CarBase(BaseModel):
    make: str = Field(..., min_length=1, max_length=64)
    model: str = Field(..., min_length=1, max_length=64)
    year: int = Field(..., ge=1950, le=2030)
    body_type: Optional[str] = Field(default=None, max_length=64)
    mileage: Optional[float] = Field(default=None, ge=0, le=2_000_000)
    door_count: Optional[int] = Field(default=None, ge=2, le=6)
    nr_seats: Optional[int] = Field(default=None, ge=1, le=12)
    color: Optional[str] = Field(default=None, max_length=64)
    fuel_type: Optional[str] = Field(default=None, max_length=64)
    engine_capacity: Optional[float] = Field(default=None, ge=50, le=10_000)
    engine_power: Optional[float] = Field(default=None, ge=1, le=2_000)
    gearbox: Optional[str] = Field(default=None, max_length=32)
    transmission: Optional[str] = Field(default=None, max_length=32)
    pollution_standard: Optional[str] = Field(default=None, max_length=32)
    price: float = Field(..., ge=0, le=10_000_000)


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
    user_id: Optional[int] = None
    source_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


class CarListResponse(BaseModel):
    items: List[CarOut]
    total: int
    page: int
    page_size: int


class PredictionInput(BaseModel):
    make: str = Field(..., min_length=1, max_length=64)
    model: str = Field(..., min_length=1, max_length=64)
    year: int = Field(..., ge=1950, le=2030)
    body_type: str = Field(..., min_length=1, max_length=64)
    mileage: float = Field(..., ge=0, le=2_000_000)
    color: str = Field(..., min_length=1, max_length=64)
    fuel_type: str = Field(..., min_length=1, max_length=64)
    engine_capacity: float = Field(..., ge=50, le=10_000)
    engine_power: float = Field(..., ge=1, le=2_000)
    gearbox: str = Field(..., min_length=1, max_length=32)
    transmission: str = Field(..., min_length=1, max_length=32)
    pollution_standard: str = Field(..., min_length=1, max_length=32)
    equipment_count: Optional[int] = Field(default=0, ge=0, le=100)


class PredictionOut(BaseModel):
    id: int
    user_id: Optional[int] = None
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


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str = Field(..., min_length=1, max_length=64)
    phone: Optional[str] = Field(default=None, max_length=32)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    display_name: str
    phone: Optional[str] = None
    role: str
    is_active: bool
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


class AdminUserUpdate(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None


class AdminUserListResponse(BaseModel):
    items: List[UserOut]
    total: int
    page: int
    page_size: int
