from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass

import numpy as np

from codigo.simulador import espera_teorica, simular_fila


CELLS = (
    (1, 0.5, "exp"), (1, 0.9, "exp"),
    (2, 0.5, "exp"), (2, 0.9, "exp"),
    (1, 0.5, "const"), (1, 0.9, "const"),
    (2, 0.5, "const"), (2, 0.9, "const"),
)


@dataclass(frozen=True)
class VerificationConfig:
    n_clients: int = 400_000
    warmup: int = 10_000
    replicas: int = 5
    seed: int = 20260924
    workers: int = 1

    def validate(self) -> None:
        if self.n_clients <= self.warmup or self.warmup < 0:
            raise ValueError("N deve ser maior que W e W não pode ser negativo")
        if self.replicas < 1:
            raise ValueError("deve haver pelo menos uma réplica")
        if self.workers < 1:
            raise ValueError("workers deve ser positivo")


def _simulate(task: tuple[int, int, float, str, int, int, np.random.SeedSequence]) -> tuple[int, float]:
    index, servers, arrival_rate, service, n_clients, warmup, child = task
    waits = simular_fila(servers, arrival_rate, service, n_clients, np.random.default_rng(child))
    return index, float(waits[warmup:].mean())


def verify(config: VerificationConfig) -> dict[str, object]:
    config.validate()
    root = np.random.SeedSequence(config.seed)
    tasks = []
    cell_roots = root.spawn(len(CELLS))
    for index, (servers, arrival_rate, service) in enumerate(CELLS):
        cell_root = cell_roots[index]
        for child in cell_root.spawn(config.replicas):
            tasks.append((index, servers, arrival_rate, service, config.n_clients, config.warmup, child))
    if config.workers == 1:
        raw = [_simulate(task) for task in tasks]
    else:
        with ProcessPoolExecutor(max_workers=config.workers) as pool:
            raw = list(pool.map(_simulate, tasks))
    by_cell: list[list[float]] = [[] for _ in CELLS]
    for index, response in raw:
        by_cell[index].append(response)
    rows = []
    for index, (servers, arrival_rate, service) in enumerate(CELLS):
        theoretical = float(espera_teorica(servers, arrival_rate, service))
        simulated = float(np.mean(by_cell[index]))
        exact = bool(np.isfinite(theoretical))
        rows.append({
            "cell": index + 1, "servers": servers, "arrival_rate": arrival_rate,
            "service": service, "simulated": simulated,
            "theoretical": theoretical if exact else None,
            "relative_error_pct": 100 * (simulated / theoretical - 1) if exact else None,
            "status": "verificado" if exact else "sem_formula_exata",
        })
    errors = [abs(float(row["relative_error_pct"])) for row in rows if row["relative_error_pct"] is not None]
    return {
        "config": config.__dict__, "cells": rows,
        "max_relative_error_pct": max(errors) if errors else None,
        "criterion_pct": 2.0,
        "passed": bool(errors) and max(errors) < 2.0,
    }