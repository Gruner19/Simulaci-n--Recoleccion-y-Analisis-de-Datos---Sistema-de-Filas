from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
from statsmodels.tsa.stattools import acf

from codigo.simulador import espera_teorica, simular_fila


@dataclass(frozen=True)
class PilotConfig:
    servers: int = 1
    arrival_rate: float = 0.9
    service: str = "exp"
    n_clients: int = 50_000
    warmup: int = 1_000
    replicas: int = 30
    short_clients: int = 10_000
    welch_clients: int = 6_000
    welch_replicas: int = 300
    welch_window: int = 250
    seed: int = 20260920

    def validate(self) -> None:
        if self.servers < 1 or self.arrival_rate <= 0 or self.arrival_rate / self.servers >= 1:
            raise ValueError("a configuração do piloto deve ter rho < 1")
        if self.service not in {"exp", "const"}:
            raise ValueError("service deve ser 'exp' ou 'const'")
        if self.n_clients <= self.warmup or self.short_clients <= self.warmup:
            raise ValueError("N deve ser maior que W")
        if min(self.replicas, self.welch_replicas, self.welch_clients, self.welch_window) < 1:
            raise ValueError("os tamanhos do piloto devem ser positivos")


def _br(value: float) -> str:
    return f"{value:.4f}".replace(".", ",")


def run_pilot(config: PilotConfig, output_dir: Path | None = None) -> dict[str, object]:
    config.validate()
    output_dir = output_dir or Path(__file__).resolve().parents[3] / "figuras" / "aed"
    output_dir.mkdir(parents=True, exist_ok=True)
    root = np.random.SeedSequence(config.seed)
    main_root, short_root, welch_root = root.spawn(3)
    main_rows = []
    first_waits: np.ndarray | None = None
    for replica, child in enumerate(main_root.spawn(config.replicas), start=1):
        started = time.perf_counter()
        waits = simular_fila(config.servers, config.arrival_rate, config.service, config.n_clients, np.random.default_rng(child))
        if first_waits is None:
            first_waits = waits[config.warmup:]
        main_rows.append({"replica": replica, "n_clients": config.n_clients, "response": float(waits[config.warmup:].mean()), "elapsed_s": time.perf_counter() - started})
    short_rows = []
    for replica, child in enumerate(short_root.spawn(config.replicas), start=1):
        started = time.perf_counter()
        waits = simular_fila(config.servers, config.arrival_rate, config.service, config.short_clients, np.random.default_rng(child))
        short_rows.append({"replica": replica, "n_clients": config.short_clients, "response": float(waits[config.warmup:].mean()), "elapsed_s": time.perf_counter() - started})
    x = np.asarray([row["response"] for row in main_rows], dtype=float)
    log_x = np.log(x)
    t_critical = stats.t.ppf(0.975, len(x) - 1)
    sd = float(x.std(ddof=1))
    theoretical = float(espera_teorica(config.servers, config.arrival_rate, config.service))
    lag_correlation = float(stats.pearsonr(x[:-1], x[1:]).statistic) if len(x) > 2 else None
    welch_matrix = np.array([
        simular_fila(config.servers, config.arrival_rate, config.service, config.welch_clients, np.random.default_rng(child))
        for child in welch_root.spawn(config.welch_replicas)
    ])
    moving = np.convolve(welch_matrix.mean(axis=0), np.ones(config.welch_window) / config.welch_window, mode="valid")
    individual = first_waits if first_waits is not None else np.array([])
    acf_values = acf(individual, nlags=min(50, max(1, len(individual) - 2)), fft=True).tolist()
    q_q = stats.probplot(x, dist="norm")
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.5))
    axes[0].hist(x, bins=min(12, max(4, len(x) // 2)), color="#1f4e79", alpha=0.8)
    axes[0].set(title="Médias por corrida", xlabel="Espera média (min)", ylabel="Frequência")
    axes[1].plot(q_q[0][0], q_q[0][1], "o", color="#b04a35")
    axes[1].set(title="Q-Q das médias", xlabel="Quantis teóricos", ylabel="Quantis observados")
    fig.tight_layout()
    hist_path = output_dir / "piloto_medias_hist_qq.png"
    fig.savefig(hist_path, dpi=150)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.5))
    positive = individual[individual > 0]
    axes[0].hist(positive, bins=30, density=True, color="#1f4e79", alpha=0.7)
    t = np.linspace(0, max(positive.max() if len(positive) else 1, 1), 200)
    rate = 1 - config.arrival_rate / config.servers
    axes[0].plot(t, (config.arrival_rate / config.servers) * rate * np.exp(-rate * t), color="#b04a35")
    axes[0].set(title="Esperas individuais", xlabel="Espera (min)", ylabel="Densidade")
    axes[1].plot(acf_values, color="#1f4e79")
    axes[1].set(title="ACF das esperas individuais", xlabel="Defasagem", ylabel="ACF")
    fig.tight_layout()
    waits_path = output_dir / "piloto_esperas_acf.png"
    fig.savefig(waits_path, dpi=150)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.plot(np.arange(len(moving)) + config.welch_window / 2, moving, color="#1f4e79")
    ax.axvline(config.warmup, color="#b04a35", linestyle="--")
    ax.axhline(theoretical, color="black", linestyle=":")
    ax.set(title="Welch", xlabel="Índice do cliente", ylabel="Espera média (min)")
    fig.tight_layout()
    welch_path = output_dir / "piloto_welch.png"
    fig.savefig(welch_path, dpi=150)
    plt.close(fig)
    comparison = []
    for size, rows in ((config.short_clients, short_rows), (config.n_clients, main_rows)):
        values = np.asarray([row["response"] for row in rows])
        comparison.append({"n_clients": size, "cv_pct": float(100 * values.std(ddof=1) / values.mean()), "ci_half_width_pct": float(100 * stats.t.ppf(0.975, len(values) - 1) * values.std(ddof=1) / np.sqrt(len(values)) / values.mean()), "mean_time_s": float(np.mean([row["elapsed_s"] for row in rows]))})
    return {
        "pilot_only": True, "factorial_eligible": False, "config": config.__dict__,
        "summary": {
            "replicas": len(x), "mean": float(x.mean()), "sd": sd, "cv_pct": float(100 * sd / x.mean()),
            "ci95": [float(x.mean() - t_critical * sd / np.sqrt(len(x))), float(x.mean() + t_critical * sd / np.sqrt(len(x)))],
            "skewness": float(stats.skew(x, bias=False)), "shapiro_p": float(stats.shapiro(x).pvalue),
            "log_skewness": float(stats.skew(log_x, bias=False)), "log_shapiro_p": float(stats.shapiro(log_x).pvalue),
            "lag1_correlation": lag_correlation, "theoretical_mean": theoretical,
            "relative_error_pct": float(100 * (x.mean() / theoretical - 1)),
            "normality_warning": "Com r pequeno, testes de normalidade têm pouco poder; interpretar com cautela.",
        },
        "individual_waits": {"n": int(len(individual)), "zero_wait_pct": float(100 * np.mean(individual <= 1e-12)), "acf": acf_values},
        "welch": {"replicas": config.welch_replicas, "window": config.welch_window, "n_points": len(moving)},
        "run_length": comparison,
        "figures": [str(hist_path), str(waits_path), str(welch_path)],
    }