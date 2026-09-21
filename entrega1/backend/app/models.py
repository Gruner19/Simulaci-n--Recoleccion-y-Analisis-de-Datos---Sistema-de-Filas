from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    status: Mapped[str] = mapped_column(String(20), default="configurado")
    config_json: Mapped[str] = mapped_column(Text)
    hypothesis_id: Mapped[int | None] = mapped_column(ForeignKey("hypotheses.id"), nullable=True)


class Hypothesis(Base):
    __tablename__ = "hypotheses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    experiment_id: Mapped[int] = mapped_column(Integer, index=True)
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Run(Base):
    __tablename__ = "runs"
    __table_args__ = (UniqueConstraint("experiment_id", "run_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    experiment_id: Mapped[int] = mapped_column(Integer, index=True)
    run_id: Mapped[int] = mapped_column(Integer)
    cell: Mapped[int] = mapped_column(Integer)
    replica: Mapped[int] = mapped_column(Integer)
    factor_a: Mapped[int] = mapped_column(Integer)
    factor_b: Mapped[int] = mapped_column(Integer)
    factor_c: Mapped[int] = mapped_column(Integer)
    servers: Mapped[int] = mapped_column(Integer)
    arrival_rate: Mapped[float] = mapped_column(Float)
    service: Mapped[str] = mapped_column(String(10))
    rho: Mapped[float] = mapped_column(Float)
    spawn_key: Mapped[int] = mapped_column(Integer)
    execution_order: Mapped[int] = mapped_column(Integer)
    response: Mapped[float | None] = mapped_column(Float, nullable=True)
    elapsed_s: Mapped[float | None] = mapped_column(Float, nullable=True)
    state: Mapped[str] = mapped_column(String(20), default="pendiente")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)