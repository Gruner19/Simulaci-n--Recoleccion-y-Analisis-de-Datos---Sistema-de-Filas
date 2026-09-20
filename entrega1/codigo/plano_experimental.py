"""Gera o plano experimental do fatorial 2^3 com r réplicas e a ordem de execução aleatorizada.

Saídas:
  - dados/plano_experimental.csv        (80 corridas, já na ordem aleatória de execução)
  - tabelas/tab_delineamento.tex        (as 2^3 combinações, com utilização do servidor)
  - tabelas/tab_plano_excerto.tex       (primeiras corridas da ordem aleatória, para o apêndice)

O plano é gerado UMA vez e versionado; as corridas em si só são executadas depois da aprovação
da proposta (executar_experimento.py).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DADOS, NIVEIS, R, SEED_EXPERIMENTO, SEED_ORDEM, TABELAS

DADOS.mkdir(exist_ok=True)
TABELAS.mkdir(exist_ok=True)


def br(x, d=1):
    return f"{x:.{d}f}".replace(".", ",")


def rotulo_servico(v):
    return "exponencial" if v == "exp" else "constante"


# ---- 1) as 2^3 combinações em ordem padrão (A varia mais rápido, depois B, depois C)
celulas = []
for k in range(8):
    a, b, c = (-1, 1)[k & 1], (-1, 1)[(k >> 1) & 1], (-1, 1)[(k >> 2) & 1]
    nivel = lambda fator, cod: NIVEIS[fator]["mais" if cod > 0 else "menos"]
    servidores, lam, servico = nivel("A", a), nivel("B", b), nivel("C", c)
    celulas.append({"celula": k + 1, "A": a, "B": b, "C": c, "servidores": servidores, "lambda": lam,
                    "servico": servico, "rho": lam / servidores})

# ---- 2) r réplicas por célula, sementes independentes (SeedSequence.spawn) e ordem aleatória
linhas = []
for cel in celulas:
    for rep in range(1, R + 1):
        run_id = (cel["celula"] - 1) * R + rep
        linhas.append({**cel, "replica": rep, "run_id": run_id, "spawn_key": run_id - 1})
plano = pd.DataFrame(linhas)
ordem = np.random.default_rng(SEED_ORDEM).permutation(len(plano)) + 1  # ordem de execução de cada run_id
plano["ordem_execucao"] = ordem
plano = plano.sort_values("ordem_execucao").reset_index(drop=True)
plano = plano[["ordem_execucao", "run_id", "celula", "replica", "A", "B", "C", "servidores", "lambda",
               "servico", "rho", "spawn_key"]]
plano.to_csv(DADOS / "plano_experimental.csv", index=False)

# ---- 3) tabela do delineamento (LaTeX)
sinal = {-1: "$-$", 1: "$+$"}
t = ["\\begin{tabular}{cccccccc}", "\\toprule",
     "Célula & $A$ & $B$ & $C$ & $c$ & $\\lambda$ (cl/min) & Serviço & $\\rho$ \\\\", "\\midrule"]
for cel in celulas:
    t.append(f"{cel['celula']} & {sinal[cel['A']]} & {sinal[cel['B']]} & {sinal[cel['C']]} & {cel['servidores']} & "
             f"{br(cel['lambda'], 1)} & {rotulo_servico(cel['servico'])} & {br(cel['rho'], 2)} \\\\")
t += ["\\bottomrule", "\\end{tabular}"]
(TABELAS / "tab_delineamento.tex").write_text("\n".join(t) + "\n", encoding="utf-8")

# ---- 4) excerto da ordem aleatória (apêndice)
t = ["\\begin{tabular}{ccccccc}", "\\toprule",
     "Ordem & Corrida & Célula & Réplica & $c$ & $\\lambda$ / Serviço & Chave da semente \\\\", "\\midrule"]
for _, r in plano.head(12).iterrows():
    t.append(f"{int(r.ordem_execucao)} & {int(r.run_id)} & {int(r.celula)} & {int(r.replica)} & {int(r.servidores)} & "
             f"{br(r['lambda'], 1)} / {rotulo_servico(r.servico)} & {int(r.spawn_key)} \\\\")
t += ["\\bottomrule", "\\end{tabular}"]
(TABELAS / "tab_plano_excerto.tex").write_text("\n".join(t) + "\n", encoding="utf-8")

print(plano.head(12).to_string(index=False))
print("corridas:", len(plano), "| células:", plano.celula.nunique(), "| réplicas/célula:", R)
print("SEED_EXPERIMENTO =", SEED_EXPERIMENTO, "| SEED_ORDEM =", SEED_ORDEM)
