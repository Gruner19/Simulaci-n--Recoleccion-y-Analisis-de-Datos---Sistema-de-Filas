---
applyTo: "backend/tests/**/*.py"
---
- Prueba de reproducibilidad: dos ejecuciones con la misma configuración y semillas dan resultados idénticos.
- Verificación teórica: error relativo < 2 % en corridas largas frente a Pollaczek–Khinchine y Erlang C.
- Efectos y ANOVA deben coincidir con `statsmodels` (OLS con factores codificados en −1/+1) hasta 1e-8.
- Sin dependencias del reloj ni de la red; corridas de prueba con N pequeño.
