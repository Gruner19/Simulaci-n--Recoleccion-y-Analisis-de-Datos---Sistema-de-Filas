---
name: aed-antes-del-factorial
description: Reglas y contenido del Análisis Exploratorio de Datos (AED) previo al experimento factorial — piloto de una sola configuración, sin anticipar conclusiones. Úsalo al implementar o revisar el módulo de piloto/AED.
---
# AED previo al factorial

## Reglas
- Piloto con UNA sola configuración elegida antes de correr (la más exigente: mayor ρ). Semillas distintas a las del experimento.
- No compara niveles de factores, no estima efectos, no evalúa la hipótesis y no entra en el análisis factorial.
- Objetivo: caracterizar la respuesta y justificar la viabilidad (N, W, tiempo total, réplicas independientes).

## Contenido (30 corridas piloto por defecto)
1. Estadísticos de las medias por corrida: media, desvío, CV, cuartiles, mínimo/máximo, asimetría, curtosis,
   Shapiro–Wilk e IC 95 % de la media, más valor teórico y error relativo cuando existe fórmula.
2. Histograma y Q–Q de las medias por corrida.
3. Media por corrida según el orden de réplica y correlación lag-1 (independencia entre réplicas).
4. Esperas individuales de una corrida: histograma en escala log contra la densidad teórica M/M/1
   (ρ·(μ−λ)·e^{−(μ−λ)t}) y fracción sin espera (teórica 1 − ρ).
5. ACF de las esperas individuales (justifica que la unidad sea la media por corrida).
6. Welch: 300 réplicas cortas, media móvil (ventana 250), marca de W.
7. Tabla de largo de corrida (N = 10.000 vs 50.000): CV y media-anchura del IC para r = 10, tiempo por corrida.

## Cómo redactar los resultados
- Describe, no concluyas sobre factores. Una asimetría o un rechazo de normalidad se reporta como un hecho del piloto
  que obliga a revisar residuos, no como una decisión de transformar.
- Con n = 30 los tests tienen poco poder: dilo.
