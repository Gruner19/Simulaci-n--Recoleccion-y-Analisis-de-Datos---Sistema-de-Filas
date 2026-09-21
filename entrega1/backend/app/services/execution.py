from __future__ import annotations

import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from threading import Event

import numpy as np

from codigo.simulador import resposta_corrida, simular_fila

from ..config import ExperimentConfig


@dataclass(frozen=True)
class RunTask:
    run_id: int
    spawn_key: int
    servers: int
    arrival_rate: float
    service: str
    config: ExperimentConfig


def execute_one(task: RunTask) -> dict[str, int | float]:
    seed_root = np.random.SeedSequence(task.config.seed_experiment)
    child = seed_root.spawn(task.config.total_runs)[task.spawn_key]
    rng = np.random.default_rng(child)
    started = time.perf_counter()
    waits = simular_fila(
        task.servers, task.arrival_rate, task.service,
        task.config.n_clients, rng, task.config.service_mean,
    )
    return {
        "run_id": task.run_id,
        "response": resposta_corrida(waits, task.config.warmup),
        "elapsed_s": time.perf_counter() - started,
    }


def execute_tasks(tasks: list[RunTask], workers: int, cancel_event: Event | None = None) -> list[dict[str, int | float]]:
    if not tasks:
        return []
    if workers <= 1:
        results = []
        for task in tasks:
            if cancel_event and cancel_event.is_set():
                break
            results.append(execute_one(task))
        return sorted(results, key=lambda item: int(item["run_id"]))
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(execute_one, task) for task in tasks]
        results = []
        for future in as_completed(futures):
            if cancel_event and cancel_event.is_set():
                for pending in futures:
                    pending.cancel()
                break
            results.append(future.result())
    return sorted(results, key=lambda item: int(item["run_id"]))