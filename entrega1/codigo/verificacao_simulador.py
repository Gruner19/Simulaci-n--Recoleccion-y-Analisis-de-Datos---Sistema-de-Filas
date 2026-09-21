"""Verificação do simulador contra fórmulas teóricas (M/M/1, M/D/1 e M/M/2 -- Erlang C).

Corridas LONGAS (não são réplicas do experimento fatorial) apenas para conferir a implementação.
Paraleliza por célula x réplica com multiprocessing (cada réplica é determinista por semente).
Saída: dados/verificacao_simulador.csv e o macro \\VerifMaxErro em tabelas/numeros_verificacion.tex
"""
from __future__ import annotations

import multiprocessing as mp
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DADOS, SEED_VERIFICACAO, TABELAS
from simulador import espera_teorica, simular_fila

N_LONGO, W_LONGO, REPS = 400_000, 10_000, 5
CELULAS = [(1, 0.5, "exp"), (1, 0.9, "exp"), (2, 0.5, "exp"), (2, 0.9, "exp"), (1, 0.5, "const"), (1, 0.9, "const")]

raiz = np.random.SeedSequence(SEED_VERIFICACAO)


def _replica(tarea) -> tuple:
    """(índice de célula, média de espera). Una réplica = una corrida larga determinista."""
    ic, c, lam, serv, filho = tarea
    esperas = simular_fila(c, lam, serv, N_LONGO, np.random.default_rng(filho))
    return ic, float(esperas[W_LONGO:].mean())


def main():
    # un único pool, un task por (célula, réplica) -> evita pools anidados (daemonic)
    tareas = []
    for ic, ((c, lam, serv), seq) in enumerate(zip(CELULAS, raiz.spawn(len(CELULAS)))):
        for filho in seq.spawn(REPS):
            tareas.append((ic, c, lam, serv, filho))
    nel = len(CELULAS)
    if len(tareas) > 1:
        with mp.Pool(min(mp.cpu_count(), 8)) as pool:
            res = pool.map(_replica, tareas)
    else:
        res = [_replica(t) for t in tareas]

    medias = [[] for _ in range(nel)]
    for ic, m in res:
        medias[ic].append(m)
    linhas = []
    for ic, ((c, lam, serv), _) in enumerate(zip(CELULAS, raiz.spawn(len(CELULAS)))):
        m = float(np.mean(medias[ic]))
        linhas.append({"c": c, "lambda": lam, "servico": serv, "media_simulada": m,
                       "teorico": float(espera_teorica(c, lam, serv)),
                       "erro_rel_pct": 100 * (m / espera_teorica(c, lam, serv) - 1)})
    df = pd.DataFrame(linhas)
    DADOS.mkdir(exist_ok=True)
    df.to_csv(DADOS / "verificacao_simulador.csv", index=False)
    max_erro = df.erro_rel_pct.abs().max()
    print(df.round(4).to_string(index=False))
    print("erro relativo máximo (%):", round(max_erro, 2))
    erro_txt = f"{max_erro:.1f}".replace(".", ",")
    n_txt = f"{N_LONGO:,}".replace(",", ".")
    (TABELAS / "numeros_verificacao.tex").write_text(
        "% Gerado por codigo/verificacao_simulador.py\n"
        f"\\newcommand{{\\VerifMaxErro}}{{{erro_txt}\\xspace}}\n"
        f"\\newcommand{{\\VerifNLongo}}{{{n_txt}\\xspace}}\n"
        f"\\newcommand{{\\VerifReps}}{{{REPS}\\xspace}}\n", encoding="utf-8")


if __name__ == "__main__":
    main()
