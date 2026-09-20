"""Simulador de eventos discretos de filas M/M/c e M/D/c (SimPy).

Modelo
------
- Chegadas de Poisson com taxa `lam` (clientes/min): tempos entre chegadas exponenciais.
- `c` servidores idênticos e uma única fila FIFO.
- Tempo de serviço com média `media_servico` (min): exponencial ("exp") ou constante ("const").
- Resposta por corrida: espera média na fila (min) dos clientes após o aquecimento.
"""
from __future__ import annotations

from math import factorial

import numpy as np
import simpy

MEDIA_SERVICO = 1.0  # min (mantida constante em todo o experimento)


def simular_fila(c: int, lam: float, servico: str, n_clientes: int,
                 rng: np.random.Generator,
                 media_servico: float = MEDIA_SERVICO) -> np.ndarray:
    """Executa UMA corrida e devolve as esperas na fila (min), na ordem de chegada."""
    if servico not in ("exp", "const"):
        raise ValueError("servico deve ser 'exp' ou 'const'")

    # Números aleatórios pré-gerados: a corrida fica 100% determinada pela semente.
    entre_chegadas = rng.exponential(1.0 / lam, size=n_clientes)
    if servico == "exp":
        tempos_servico = rng.exponential(media_servico, size=n_clientes)
    else:
        tempos_servico = np.full(n_clientes, media_servico)

    env = simpy.Environment()
    servidores = simpy.Resource(env, capacity=c)  # disciplina FIFO por padrão
    esperas = np.empty(n_clientes)

    def cliente(i: int):
        chegada = env.now
        with servidores.request() as req:
            yield req
            esperas[i] = env.now - chegada
            yield env.timeout(tempos_servico[i])

    def fonte():
        for i in range(n_clientes):
            yield env.timeout(entre_chegadas[i])
            env.process(cliente(i))

    env.process(fonte())
    env.run()
    return esperas


def resposta_corrida(esperas: np.ndarray, aquecimento: int) -> float:
    """Variável de resposta: espera média na fila após descartar o aquecimento."""
    return float(esperas[aquecimento:].mean())


def espera_teorica(c: int, lam: float, servico: str,
                   media_servico: float = MEDIA_SERVICO) -> float:
    """Espera média em fila W_q quando existe fórmula fechada; NaN caso contrário.

    - M/M/1 e M/D/1: Pollaczek-Khinchine, W_q = rho (1 + cs^2) / (2 mu (1 - rho)).
    - M/M/c: fórmula de Erlang C.
    - M/D/c com c > 1: sem fórmula fechada simples -> NaN.
    """
    mu = 1.0 / media_servico
    rho = lam / (c * mu)
    if rho >= 1:
        return float("inf")
    if c == 1:
        cs2 = 1.0 if servico == "exp" else 0.0
        return rho * (1 + cs2) / (2 * mu * (1 - rho))
    if servico == "exp":
        a = lam / mu
        soma = sum(a ** k / factorial(k) for k in range(c))
        termo = a ** c / (factorial(c) * (1 - rho))
        erlang_c = termo / (soma + termo)
        return erlang_c / (c * mu - lam)
    return float("nan")
