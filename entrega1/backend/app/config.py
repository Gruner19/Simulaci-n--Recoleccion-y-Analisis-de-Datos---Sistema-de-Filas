from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExperimentConfig:
    replicas: int = 10
    n_clients: int = 50_000
    warmup: int = 1_000
    service_mean: float = 1.0
    seed_experiment: int = 20260922
    seed_order: int = 20260923

    def validate(self) -> None:
        if self.replicas < 10:
            raise ValueError("r deve ser maior ou igual a 10")
        if self.n_clients <= self.warmup:
            raise ValueError("N deve ser maior que W")
        if self.warmup < 0:
            raise ValueError("W não pode ser negativo")
        if self.service_mean <= 0:
            raise ValueError("a média do serviço deve ser positiva")
        for servers in (1, 2):
            for arrival_rate in (0.5, 0.9):
                rho = arrival_rate / (servers / self.service_mean)
                if rho >= 1:
                    raise ValueError(f"rho deve ser menor que 1; obtido {rho:g}")

    @property
    def total_runs(self) -> int:
        return 8 * self.replicas

    def as_dict(self) -> dict[str, int | float]:
        return {
            "replicas": self.replicas,
            "n_clients": self.n_clients,
            "warmup": self.warmup,
            "service_mean": self.service_mean,
            "seed_experiment": self.seed_experiment,
            "seed_order": self.seed_order,
        }