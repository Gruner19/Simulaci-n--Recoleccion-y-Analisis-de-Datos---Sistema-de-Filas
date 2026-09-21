from __future__ import annotations

from app.config import ExperimentConfig
from app.services.execution import RunTask, execute_tasks
from app.services.plan import build_plan


def test_plan_has_eight_cells_and_randomized_order() -> None:
    config = ExperimentConfig(replicas=10, n_clients=20, warmup=5)
    plan = build_plan(1, config)
    assert len(plan) == 80
    assert {run.cell for run in plan} == set(range(1, 9))
    assert sorted(run.execution_order for run in plan) == list(range(1, 81))
    assert [run.run_id for run in plan] != list(range(1, 81))
    assert all(run.rho < 1 for run in plan)


def test_same_seed_is_independent_of_worker_count() -> None:
    config = ExperimentConfig(replicas=10, n_clients=40, warmup=5)
    plan = build_plan(1, config)
    tasks = [RunTask(run.run_id, run.spawn_key, run.servers, run.arrival_rate, run.service, config) for run in plan[:2]]
    one_worker = execute_tasks(tasks, workers=1)
    two_workers = execute_tasks(tasks, workers=2)
    assert [(item["run_id"], item["response"]) for item in one_worker] == [(item["run_id"], item["response"]) for item in two_workers]