"""Verificação do simulador contra fórmulas teóricas (M/M/1, M/D/1 e M/M/2 -- Erlang C).

Corridas LONGAS (não são réplicas do experimento fatorial) apenas para conferir a implementação.
Saída: dados/verificacao_simulador.csv e o macro \\VerifMaxErro em tabelas/numeros_verificacao.tex
"""
from __future__ import annotations

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
linhas = []
for (c, lam, serv), seq in zip(CELULAS, raiz.spawn(len(CELULAS))):
    medias = [simular_fila(c, lam, serv, N_LONGO, np.random.default_rng(f))[W_LONGO:].mean() for f in seq.spawn(REPS)]
    teo = espera_teorica(c, lam, serv)
    linhas.append({"c": c, "lambda": lam, "servico": serv, "media_simulada": np.mean(medias), "teorico": teo,
                   "erro_rel_pct": 100 * (np.mean(medias) / teo - 1)})
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
