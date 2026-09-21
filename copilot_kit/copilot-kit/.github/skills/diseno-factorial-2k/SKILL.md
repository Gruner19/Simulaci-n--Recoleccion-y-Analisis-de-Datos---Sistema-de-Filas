---
name: diseno-factorial-2k
description: Diseño factorial 2^k con r réplicas — tabla de signos, efectos, asignación de la variación, ANOVA, intervalos de confianza y diagnóstico de residuos, con verificación contra statsmodels. Úsalo al implementar o revisar el módulo de análisis factorial.
---
# Diseño factorial 2^k r (k = 3, r ≥ 10)

## Plan
- 2^k celdas en orden estándar (A varía más rápido). Niveles codificados −1/+1. Aleatoriza el orden de las 2^k·r corridas.
- Cada réplica es una corrida completa con semilla propia. Total = 2^k × r (80 con k = 3, r = 10).

## Modelo y efectos (Jain, cap. 17–18)
y = q0 + qA·xA + qB·xB + qC·xC + qAB·xA·xB + qAC·xA·xC + qBC·xB·xC + qABC·xA·xB·xC + e.
- Sobre las medias de celda ȳ_i: q_j = (1/2^k) Σ_i x_ij · ȳ_i.
- Con factores en ±1 balanceados, q_j coincide con el coeficiente de un OLS en statsmodels (prueba obligatoria, tolerancia 1e-8).

## Variación y ANOVA
- SS_j = 2^k · r · q_j²   (cada efecto; para q0 aparte)
- SSE = Σ_i Σ_j (y_ij − ȳ_i)²     (grados de libertad: 2^k (r − 1))
- SST = Σ SS_j (sin q0) + SSE. Porcentaje explicado por j = 100 · SS_j / SST.
- s_e² = SSE / [2^k (r − 1)];  error estándar de q_j: s_q = s_e / √(2^k · r).
- IC (1−α) de q_j: q_j ± t_{1−α/2; 2^k(r−1)} · s_q. Un efecto es significativo si su IC no contiene 0.
- ANOVA: F_j = (SS_j / 1) / (SSE / [2^k (r − 1)]).

## Suposiciones y diagnóstico (solo con las 2^k·r corridas terminadas)
- Residuos vs. ajustados (varianza constante), Q–Q de residuos (normalidad), Shapiro–Wilk, Levene entre celdas.
- Ofrece siempre escala original y ln(respuesta) lado a lado (opcional Box–Cox); la decisión es del usuario.
- Con r = 10 los tests tienen poco poder: muestra esa advertencia junto a cada test.
- Marca todo como "preliminar" hasta la entrega final.

## Separación con la AED
El piloto NUNCA entra en este análisis, y este módulo no se habilita antes de que existan todas las corridas.
