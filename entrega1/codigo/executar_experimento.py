"""Executa as 80 corridas do fatorial 2^3 r, na ordem aleatória definida em dados/plano_experimental.csv.

ATENÇÃO: este script só deve ser rodado DEPOIS da aprovação da proposta (Entrega 1);
a hipótese e o plano ficam registrados antes de qualquer corrida do experimento.

Uso:  python codigo/executar_experimento.py [--saida CAMINHO.csv] [--force]
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import AQUECIMENTO, DADOS, N_CLIENTES, SEED_EXPERIMENTO
from simulador import resposta_corrida, simular_fila


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", default=str(DADOS / "resultados_fatorial.csv"))
    ap.add_argument("--n-clientes", type=int, default=N_CLIENTES)
    ap.add_argument("--aquecimento", type=int, default=AQUECIMENTO)
    ap.add_argument("--force", action="store_true", help="sobrescreve o arquivo de saída existente")
    args = ap.parse_args()

    saida = Path(args.saida)
    if saida.exists() and not args.force:
        sys.exit(f"{saida} já existe; use --force para sobrescrever.")

    plano = pd.read_csv(DADOS / "plano_experimental.csv").sort_values("ordem_execucao")
    sementes = np.random.SeedSequence(SEED_EXPERIMENTO).spawn(len(plano))
    linhas = []
    for _, r in plano.iterrows():
        rng = np.random.default_rng(sementes[int(r.spawn_key)])
        t0 = time.perf_counter()
        esperas = simular_fila(int(r.servidores), float(r["lambda"]), r.servico, args.n_clientes, rng)
        linhas.append({**r.to_dict(), "resposta": resposta_corrida(esperas, args.aquecimento),
                       "tempo_s": time.perf_counter() - t0})
        print(f"corrida {int(r.ordem_execucao):2d}/{len(plano)}  célula {int(r.celula)}  "
              f"resposta = {linhas[-1]['resposta']:.4f}", flush=True)
    saida.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(linhas).to_csv(saida, index=False)
    print("resultados salvos em", saida)


if __name__ == "__main__":
    main()
