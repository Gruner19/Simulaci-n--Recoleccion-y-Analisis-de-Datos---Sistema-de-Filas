---
description: Fase 2 — módulos de AED (piloto) y verificación del simulador contra la teoría.
agent: agent
---
Implementa la FASE 2 en el backend (y sus endpoints).
Carga las skills `aed-antes-del-factorial` y `simulador-de-colas`.
Alcance: verificación con corridas largas (error relativo por celda; M/D/c con c > 1 marcado "sin fórmula exacta") y
piloto de UNA configuración elegida por el usuario, con semillas distintas a las del experimento: estadísticos,
histograma y Q–Q de las medias, media por réplica con correlación lag-1, esperas individuales contra la densidad teórica,
ACF, Welch (300 réplicas) y tabla de largo de corrida (N = 10.000 vs 50.000).
Reglas: el piloto no compara niveles ni estima efectos ni entra en el análisis factorial.
Criterios: error relativo < 2 % en la verificación; cada gráfico con datos reproducibles y pruebas; pytest en verde.
