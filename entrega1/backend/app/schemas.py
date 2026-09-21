from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ConfigCreate(BaseModel):
    replicas: int = Field(default=10, ge=10)
    n_clients: int = Field(default=50_000, gt=0)
    warmup: int = Field(default=1_000, ge=0)
    service_mean: float = Field(default=1.0, gt=0)
    seed_experiment: int = 20260922
    seed_order: int = 20260923


class HypothesisCreate(BaseModel):
    text: str = Field(min_length=1, max_length=10_000)


class VerificationRequest(BaseModel):
    n_clients: int = Field(default=400_000, gt=1)
    warmup: int = Field(default=10_000, ge=0)
    replicas: int = Field(default=5, ge=1)
    seed: int = 20260924
    workers: int = Field(default=1, ge=1)


class PilotRequest(BaseModel):
    servers: int = Field(default=1, ge=1)
    arrival_rate: float = Field(default=0.9, gt=0)
    service: str = "exp"
    n_clients: int = Field(default=50_000, gt=1)
    warmup: int = Field(default=1_000, ge=0)
    replicas: int = Field(default=30, ge=1)
    short_clients: int = Field(default=10_000, gt=1)
    welch_clients: int = Field(default=6_000, gt=1)
    welch_replicas: int = Field(default=300, ge=1)
    welch_window: int = Field(default=250, ge=1)
    seed: int = 20260920


class ExperimentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    status: str
    hypothesis_id: int | None


class RunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    run_id: int
    cell: int
    replica: int
    factor_a: int
    factor_b: int
    factor_c: int
    servers: int
    arrival_rate: float
    service: str
    rho: float
    spawn_key: int
    execution_order: int
    response: float | None
    elapsed_s: float | None
    state: str
    error: str | None