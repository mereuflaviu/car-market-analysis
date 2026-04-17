from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    display_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    role = Column(String, nullable=False, default="user")   # "user" | "admin"
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Car(Base):
    __tablename__ = "cars"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    make = Column(String, nullable=False, index=True)
    model = Column(String, nullable=False, index=True)
    year = Column(Integer, nullable=False)
    body_type = Column(String)
    mileage = Column(Float)
    door_count = Column(Integer)
    nr_seats = Column(Integer)
    color = Column(String)
    fuel_type = Column(String, index=True)
    engine_capacity = Column(Float)
    engine_power = Column(Float)
    gearbox = Column(String, index=True)
    transmission = Column(String)
    pollution_standard = Column(String)
    price = Column(Float, nullable=False)
    source_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    make = Column(String)
    model = Column(String)
    year = Column(Integer)
    body_type = Column(String)
    mileage = Column(Float)
    color = Column(String)
    fuel_type = Column(String)
    engine_capacity = Column(Float)
    engine_power = Column(Float)
    gearbox = Column(String)
    transmission = Column(String)
    pollution_standard = Column(String)
    predicted_price = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
