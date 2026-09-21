from __future__ import annotations

from pathlib import Path

from app.services.aed import PilotConfig, run_pilot
from app.services.verificacao import VerificationConfig, verify


def test_verification_marks_md_multi_server_without_exact_formula() -> None:
    result = verify(VerificationConfig(n_clients=200, warmup=20, replicas=2, workers=1))
    exact = [row for row in result["cells"] if row["servers"] == 2 and row["service"] == "const"]
    assert len(exact) == 2
    assert all(row["status"] == "sem_formula_exata" for row in exact)
    assert result["criterion_pct"] == 2.0


def test_pilot_is_separate_and_reproducible(tmp_path: Path) -> None:
    config = PilotConfig(n_clients=80, warmup=10, replicas=4, short_clients=30, welch_clients=40, welch_replicas=3, welch_window=5)
    first = run_pilot(config, tmp_path / "one")
    second = run_pilot(config, tmp_path / "two")
    assert first["pilot_only"] is True
    assert first["factorial_eligible"] is False
    assert first["summary"] == second["summary"]
    assert len(first["figures"]) == 3