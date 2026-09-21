# Resultados — Entrega 1

## 1. Verificación del simulador vs. teoría
Error relativo máximo = **1.30%**.

| c | λ | serviço | simulado | teórico | err% |
|---|----|---------|----------|---------|------|
| 1 | 0.5 | exp | 1.0004 | 1.0000 | 0.04 |
| 1 | 0.9 | exp | 9.0027 | 9.0000 | 0.03 |
| 2 | 0.5 | exp | 0.0670 | 0.0667 | 0.48 |
| 2 | 0.9 | exp | 0.2556 | 0.2539 | 0.67 |
| 1 | 0.5 | const | 0.5017 | 0.5000 | 0.34 |
| 1 | 0.9 | const | 4.4415 | 4.5000 | -1.30 |

## 2. Experimento fatorial 2^3 — resumen por célula (r = 10)

| cel | n | media | desv | IC95 inf | IC95 sup | CV% |
|-----|---|-------|------|----------|----------|-----|
| 3 | 10 | 8.9411 | 0.7440 | 8.4089 | 9.4733 | 8.32 |
| 7 | 10 | 4.2590 | 0.1646 | 4.1413 | 4.3767 | 3.86 |
| 6 | 10 | 0.0379 | 0.0009 | 0.0372 | 0.0385 | 2.36 |
| 8 | 10 | 0.1372 | 0.0021 | 0.1357 | 0.1387 | 1.56 |
| 2 | 10 | 0.0663 | 0.0030 | 0.0642 | 0.0684 | 4.46 |
| 1 | 10 | 1.0022 | 0.0267 | 0.9831 | 1.0213 | 2.66 |
| 5 | 10 | 0.4959 | 0.0082 | 0.4900 | 0.5017 | 1.66 |
| 4 | 10 | 0.2544 | 0.0097 | 0.2475 | 0.2614 | 3.82 |

## 3. Efectos del fatorial 2^3 (sobre log(resposta))

| efecto | magnitud(log) |
|--------|---------------|
| A | -3.0700 |
| B | 1.7419 |
| C | -0.6549 |
| AB | -1.1693 |
| AC | -2.4390 |
| BC | 0.7092 |
| ABC | -1.3549 |

## 4. Reproducción

```
python3 -m venv .venv && .venv/bin/pip install -r codigo/requirements.txt
make dados experimento
make resultados
```
*Fecha de generación*: 2026-09-20 19:25
