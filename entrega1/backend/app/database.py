from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


def database_url() -> str:
    default = Path(__file__).resolve().parents[2] / "dados" / "experimentos.sqlite3"
    return os.getenv("DATABASE_URL", f"sqlite:///{default}")


engine = create_engine(
    database_url(),
    connect_args={"check_same_thread": False} if database_url().startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    from . import models

    url = database_url()
    if url.startswith("sqlite:///"):
        Path(url.removeprefix("sqlite:///")) .parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)


def session() -> Session:
    return SessionLocal()