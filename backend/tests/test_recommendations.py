import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app import models, crud


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed cars
    cars = [
        models.Car(make="BMW", model="320d", year=2019, mileage=60000, price=20000),
        models.Car(make="BMW", model="320d", year=2020, mileage=40000, price=22000),
        models.Car(make="BMW", model="320d", year=2018, mileage=90000, price=17000),
        models.Car(make="BMW", model="X5",   year=2019, mileage=55000, price=45000),
        models.Car(make="BMW", model="X5",   year=2021, mileage=20000, price=52000),
        models.Car(make="Audi", model="A4",  year=2019, mileage=50000, price=21000),
    ]
    session.add_all(cars)
    session.commit()
    yield session
    session.close()


def test_returns_same_make_model_first(db):
    results = crud.get_recommendations(db, make="BMW", model="320d", year=2019, mileage=60000, limit=5)
    makes_models = [(c.make, c.model) for c in results]
    assert makes_models[0] == ("BMW", "320d")
    assert makes_models[1] == ("BMW", "320d")
    assert makes_models[2] == ("BMW", "320d")


def test_falls_back_to_same_make_when_insufficient(db):
    results = crud.get_recommendations(db, make="BMW", model="530d", year=2019, mileage=60000, limit=5)
    assert len(results) > 0
    assert all(c.make == "BMW" for c in results)


def test_does_not_include_other_makes(db):
    results = crud.get_recommendations(db, make="BMW", model="320d", year=2019, mileage=60000, limit=5)
    assert all(c.make == "BMW" for c in results)


def test_closest_year_ranked_first(db):
    results = crud.get_recommendations(db, make="BMW", model="320d", year=2019, mileage=60000, limit=3)
    same_model = [c for c in results if c.model == "320d"]
    assert same_model[0].year == 2019


def test_respects_limit(db):
    results = crud.get_recommendations(db, make="BMW", model="320d", year=2019, mileage=60000, limit=2)
    assert len(results) == 2


def test_empty_when_make_not_found(db):
    results = crud.get_recommendations(db, make="Ferrari", model="488", year=2020, mileage=10000, limit=5)
    assert results == []


def test_endpoint_returns_200():
    from unittest.mock import patch
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    with patch("app.routes.cars.crud.get_recommendations", return_value=[]):
        resp = client.get("/api/cars/recommendations?make=BMW&model=320d&year=2019&mileage=60000")
    assert resp.status_code == 200
    assert resp.json() == []


def test_endpoint_requires_make():
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    resp = client.get("/api/cars/recommendations?model=320d&year=2019&mileage=60000")
    assert resp.status_code == 422
