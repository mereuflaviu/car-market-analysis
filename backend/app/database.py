import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cars.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.abspath(DB_PATH)}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    pool_size=5,
    max_overflow=10,
)


# Enable WAL mode: readers don't block writers and vice-versa.
# Critical for concurrent requests in production.
@event.listens_for(engine, "connect")
def _set_wal_mode(conn, _):
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")  # safe with WAL, faster than FULL

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
