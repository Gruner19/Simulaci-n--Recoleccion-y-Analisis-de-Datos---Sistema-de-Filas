from __future__ import annotations

import csv
import io
import json
import threading
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import ExperimentConfig
from .database import Base, engine, init_db, session
from .models import Experiment, Hypothesis, Run, now_utc
from .schemas import ConfigCreate, ExperimentOut, HypothesisCreate, PilotRequest, RunOut, VerificationRequest
from .services.aed import PilotConfig, run_pilot
from .services.execution import RunTask, execute_tasks
from .services.plan import build_plan, config_json
from .services.verificacao import VerificationConfig, verify

app = FastAPI(title="Plataforma de Experimentos Fatoriais")
app.state.jobs: dict[int, dict[str, object]] = {}
app.state.jobs_lock = threading.Lock()


@app.get("/")
def root() -> dict[str, str]:
    return {
        "nome": "Plataforma de Experimentos Fatoriais",
        "status": "online",
        "documentacao": "/docs",
    }


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/verificacao")
def run_verification(payload: VerificationRequest) -> dict[str, object]:
    try:
        return verify(VerificationConfig(**payload.model_dump()))
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.post("/api/piloto")
def run_pilot_endpoint(payload: PilotRequest) -> dict[str, object]:
    try:
        return run_pilot(PilotConfig(**payload.model_dump()))
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.on_event("startup")
def startup() -> None:
    init_db()


def get_db() -> Generator[Session, None, None]:
    db = session()
    try:
        yield db
    finally:
        db.close()


def get_experiment(experiment_id: int, db: Session) -> Experiment:
    experiment = db.get(Experiment, experiment_id)
    if experiment is None:
        raise HTTPException(404, "Experimento não encontrado")
    return experiment


@app.post("/api/experiments", response_model=ExperimentOut, status_code=201)
def create_experiment(payload: ConfigCreate, db: Session = Depends(get_db)) -> Experiment:
    config = ExperimentConfig(**payload.model_dump())
    try:
        config.validate()
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    experiment = Experiment(config_json=config_json(config), status="configurado")
    db.add(experiment)
    db.commit()
    db.refresh(experiment)
    return experiment


@app.post("/api/experiments/{experiment_id}/hypothesis", response_model=ExperimentOut)
def save_hypothesis(experiment_id: int, payload: HypothesisCreate, db: Session = Depends(get_db)) -> Experiment:
    experiment = get_experiment(experiment_id, db)
    if experiment.status in {"executando", "concluido", "cancelado"}:
        raise HTTPException(409, "A hipótese já está bloqueada")
    hypothesis = Hypothesis(experiment_id=experiment_id, text=payload.text)
    db.add(hypothesis)
    db.flush()
    experiment.hypothesis_id = hypothesis.id
    db.commit()
    db.refresh(experiment)
    return experiment


@app.post("/api/experiments/{experiment_id}/plan", response_model=list[RunOut])
def create_plan(experiment_id: int, db: Session = Depends(get_db)) -> list[Run]:
    experiment = get_experiment(experiment_id, db)
    if experiment.hypothesis_id is None:
        raise HTTPException(409, "Registre a hipótese antes do plano")
    existing = db.scalars(select(Run).where(Run.experiment_id == experiment_id)).all()
    if existing:
        return list(sorted(existing, key=lambda run: run.execution_order))
    config = ExperimentConfig(**json.loads(experiment.config_json))
    runs = build_plan(experiment_id, config)
    db.add_all(runs)
    db.commit()
    return runs


@app.get("/api/experiments/{experiment_id}/plan", response_model=list[RunOut])
def get_plan(experiment_id: int, db: Session = Depends(get_db)) -> list[Run]:
    get_experiment(experiment_id, db)
    return list(db.scalars(select(Run).where(Run.experiment_id == experiment_id).order_by(Run.execution_order)).all())


@app.get("/api/experiments/{experiment_id}/plan.csv")
def export_plan_csv(experiment_id: int, db: Session = Depends(get_db)) -> StreamingResponse:
    get_experiment(experiment_id, db)
    runs = db.scalars(select(Run).where(Run.experiment_id == experiment_id).order_by(Run.execution_order)).all()
    columns = [column.name for column in Run.__table__.columns if column.name not in {"id", "experiment_id", "response", "elapsed_s", "state", "error"}]
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(columns)
    for run in runs:
        writer.writerow([getattr(run, column) for column in columns])
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=plano-{experiment_id}.csv"})


def _run_experiment(experiment_id: int, workers: int) -> None:
    db = session()
    try:
        experiment = db.get(Experiment, experiment_id)
        if experiment is None:
            return
        config = ExperimentConfig(**json.loads(experiment.config_json))
        runs = list(db.scalars(select(Run).where(Run.experiment_id == experiment_id).order_by(Run.execution_order)).all())
        tasks = [RunTask(r.run_id, r.spawn_key, r.servers, r.arrival_rate, r.service, config) for r in runs if r.state != "concluida"]
        with app.state.jobs_lock:
            job = app.state.jobs[experiment_id]
            job["total"] = len(tasks)
            job["completed"] = 0
        cancel_event = app.state.jobs[experiment_id]["cancel_event"]
        results = execute_tasks(tasks, workers, cancel_event)
        by_id = {int(result["run_id"]): result for result in results}
        for run in runs:
            result = by_id.get(run.run_id)
            if result:
                run.response = float(result["response"])
                run.elapsed_s = float(result["elapsed_s"])
                run.state = "concluida"
                with app.state.jobs_lock:
                    app.state.jobs[experiment_id]["completed"] = int(app.state.jobs[experiment_id]["completed"]) + 1
        experiment.status = "cancelado" if cancel_event.is_set() else "concluido"
        hypothesis = db.get(Hypothesis, experiment.hypothesis_id) if experiment.hypothesis_id else None
        if hypothesis and hypothesis.locked_at is None:
            hypothesis.locked_at = now_utc()
        db.commit()
    except Exception as exc:
        db.rollback()
        experiment = db.get(Experiment, experiment_id)
        if experiment:
            experiment.status = "erro"
            db.commit()
        with app.state.jobs_lock:
            app.state.jobs.setdefault(experiment_id, {})["error"] = str(exc)
    finally:
        with app.state.jobs_lock:
            app.state.jobs.setdefault(experiment_id, {})["running"] = False
        db.close()


@app.post("/api/experiments/{experiment_id}/run")
def start_experiment(experiment_id: int, workers: int = 1, db: Session = Depends(get_db)) -> dict[str, object]:
    experiment = get_experiment(experiment_id, db)
    if experiment.hypothesis_id is None:
        raise HTTPException(409, "Registre e revise a hipótese antes de executar")
    runs = db.scalars(select(Run).where(Run.experiment_id == experiment_id)).all()
    if len(runs) != ExperimentConfig(**json.loads(experiment.config_json)).total_runs:
        raise HTTPException(409, "Gere o plano completo antes de executar")
    with app.state.jobs_lock:
        current = app.state.jobs.get(experiment_id)
        if current and current.get("running"):
            raise HTTPException(409, "O experimento já está em execução")
        app.state.jobs[experiment_id] = {
            "running": True, "completed": 0, "total": 0, "error": None,
            "cancel_event": threading.Event(),
        }
    experiment.status = "executando"
    hypothesis = db.get(Hypothesis, experiment.hypothesis_id)
    if hypothesis:
        hypothesis.locked_at = now_utc()
    db.commit()
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(_run_experiment, experiment_id, max(1, workers))
    future.add_done_callback(lambda _: executor.shutdown(wait=False))
    return {"experiment_id": experiment_id, "status": "executando"}


@app.post("/api/experiments/{experiment_id}/cancel")
def cancel_experiment(experiment_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    get_experiment(experiment_id, db)
    with app.state.jobs_lock:
        job = app.state.jobs.get(experiment_id)
        if not job or not job.get("running"):
            raise HTTPException(409, "Não há execução ativa")
        job["cancel_event"].set()
    return {"experiment_id": experiment_id, "status": "cancelamento_solicitado"}


@app.post("/api/experiments/{experiment_id}/retry")
def retry_experiment(experiment_id: int, workers: int = 1, db: Session = Depends(get_db)) -> dict[str, object]:
    experiment = get_experiment(experiment_id, db)
    if experiment.status not in {"cancelado", "erro"}:
        raise HTTPException(409, "Só é possível reintentar uma execução cancelada ou com erro")
    runs = db.scalars(select(Run).where(Run.experiment_id == experiment_id)).all()
    for run in runs:
        if run.state != "concluida":
            run.state = "pendiente"
            run.error = None
    experiment.status = "configurado"
    db.commit()
    return start_experiment(experiment_id, workers, db)


@app.get("/api/experiments/{experiment_id}/events")
def events(experiment_id: int) -> StreamingResponse:
    def stream() -> Generator[str, None, None]:
        while True:
            with app.state.jobs_lock:
                state = dict(app.state.jobs.get(experiment_id, {"running": False, "completed": 0, "total": 0}))
            state.pop("cancel_event", None)
            yield f"event: progresso\ndata: {json.dumps(state)}\n\n"
            if not state.get("running"):
                break
            threading.Event().wait(0.25)
    return StreamingResponse(stream(), media_type="text/event-stream")


@app.get("/api/experiments/{experiment_id}/csv")
def export_csv(experiment_id: int, db: Session = Depends(get_db)) -> StreamingResponse:
    get_experiment(experiment_id, db)
    runs = db.scalars(select(Run).where(Run.experiment_id == experiment_id).order_by(Run.execution_order)).all()
    output = io.StringIO()
    if runs:
        writer = csv.writer(output)
        writer.writerow([column.name for column in Run.__table__.columns if column.name not in {"id", "experiment_id"}])
        for run in runs:
            writer.writerow([getattr(run, column.name) for column in Run.__table__.columns if column.name not in {"id", "experiment_id"}])
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=experimento-{experiment_id}.csv"})