from __future__ import annotations

import json

import numpy as np

from ..config import ExperimentConfig
from ..models import Run


def build_plan(experiment_id: int, config: ExperimentConfig) -> list[Run]:
    config.validate()
    rows: list[dict[str, int | float | str]] = []
    for cell in range(8):
        a = 1 if cell & 1 else -1
        b = 1 if cell & 2 else -1
        c = 1 if cell & 4 else -1
        servers = 2 if a == 1 else 1
        arrival_rate = 0.9 if b == 1 else 0.5
        service = "const" if c == 1 else "exp"
        for replica in range(1, config.replicas + 1):
            run_id = cell * config.replicas + replica
            rows.append({
                "run_id": run_id, "cell": cell + 1, "replica": replica,
                "factor_a": a, "factor_b": b, "factor_c": c,
                "servers": servers, "arrival_rate": arrival_rate, "service": service,
                "rho": arrival_rate / servers, "spawn_key": run_id - 1,
            })
    order = np.random.default_rng(config.seed_order).permutation(len(rows))
    plan: list[Run] = []
    for execution_order, index in enumerate(order, start=1):
        row = rows[int(index)]
        plan.append(Run(
            experiment_id=experiment_id, execution_order=execution_order,
            state="pendiente", **row,
        ))
    return plan


def config_json(config: ExperimentConfig) -> str:
    return json.dumps(config.as_dict(), sort_keys=True)