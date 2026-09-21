"""Executa as 80 corridas do fatorial 2^3 r, na ordem aleatória definida em dados/plano_experimental.csv.

ATENÇÃO: este script só deve ser rodado DEPOIS da aprovação da proposta (Entrega 1);
a hipótese e o plano ficam registrados antes de qualquer corrida do experimento.

Paraleliza por corrida com multiprocessing (cada réplica es determinista: sua semente
deriva apenas de SEED_EXPERIMENTO + spawn_key, e não há estado compartilhado).

Uso:  python codigo/executar_experimento.py [--saida CAMINHO.csv] [--force] [--n-procs N] [--corrida K]
"""
from __future__ import annotations

import argparse
import multiprocessing as mp
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import AQUECIMENTO, DADOS, N_CLIENTES, SEED_EXPERIMENTO
from simulador import resposta_corrida, simular_fila


def _corrida(tarea):
    """Ejecuta UNA corrida (picklable). Returna el diccionario con la respuesta."""
    spawn_key, servidores, lam, servico, n_clientes, aquec = tarea
    rng = np.random.default_rng(np.random.SeedSequence(SEED_EXPERIMENTO).spawn(80)[int(spawn_key)])
    t0 = time.perf_counter()
    esperas = simular_fila(int(servidores), float(lam), servico, n_clientes, rng)
    return {"resposta": resposta_corrida(esperas, aquec), "tempo_s": time.perf_counter() - t0}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", default=str(DADOS / "resultados_fatorial.csv"))
    ap.add_argument("--n-clientes", type=int, default=N_CLIENTES)
    ap.add_argument("--aquecimento", type=int, default=AQUECIMENTO)
    ap.add_argument("--n-procs", type=int, default=min(mp.cpu_count(), 8))
    ap.add_argument("--corrida", type=lambda s: [int(x) for x in s.split(",")],
                    help="solo estas spawn_key (0..79), p. ej. 0,1,2 (depurar)")
    ap.add_argument("--force", action="store_true", help="sobrescreve o arquivo de saída existente")
    args = ap.parse_args()

    saida = Path(args.saida)
    if saida.exists() and not args.force:
        sys.exit(f"{saida} já existe; use --force para sobrescrever.")

    plano = pd.read_csv(DADOS / "plano_experimental.csv").sort_values("ordem_execucao")
    tareas = [(int(r.spawn_key), int(r.servidores), float(r["lambda"]), r.servico,
               args.n_clientes, args.aquecimento) for _, r in plano.iterrows()]
    if args.corrida:
        tareas = [t for t in tareas if t[0] in args.corrida]
        if not tareas:
            sys.exit("nenhuna corrida corresponde às spawn_keys indicadas.")

    print(f"Executando {len(tareas)} corridas con {args.n_procs} procesos...", flush=True)
    t0 = time.perf_counter()
    if args.n_procs > 1 and len(tareas) > 1:
        with mp.Pool(args.n_procs) as pool:
            resultados = pool.map(_corrida, tareas)
    else:
        resultados = [_corrida(t) for t in tareas]
    print(f"Tempo total: {time.perf_counter() - t0:.1f} s", flush=True)

    resumo = {int(r.spawn_key): res for r, res in zip(plano.itertuples(), resultados)}
    # alineamos por orden de ejecución (clave: spawn_key -> fila del plano)
    plano = plano.sort_values("ordem_execucao").reset_index(drop=True)
    filas = []
    for _, r in plano.iterrows():
        res = resumo[int(r.spawn_key)]
        filas.append({**r.to_dict(), "resposta": res["resposta"], "tempo_s": res["tempo_s"]})
    df = pd.DataFrame(filas).sort_values("ordem_execucao")
    saida.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(saida, index=False)
    print("resultados salvos em", saida)
    for _, r in df.iterrows():
        print(f"corrida {int(r.ordem_execucao):2d}/{len(df)}  célula {int(r.celula):2d}  "
              f"réplica {int(r.replica):2d}  resposta = {r.resposta:.4f}", flush=True)


if __name__ == "__main__":
    main()
