from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import engine
from . import models
from .routes import cars, predictions, analytics, makes

# Create all tables on startup
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Car Price Analysis API",
    description="REST API for used car market analysis and ML price prediction",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:4173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cars.router, prefix="/api")
app.include_router(predictions.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(makes.router, prefix="/api")


@app.get("/")
def root():
    return {"message": "Car Price Analysis API", "docs": "/docs", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "ok"}
