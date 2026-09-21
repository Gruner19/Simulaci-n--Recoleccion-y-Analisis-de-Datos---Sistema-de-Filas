---
description: Fase 4 — análisis factorial (efectos, variación, ANOVA, IC) y diagnóstico de residuos.
agent: agent
---
Implementa la FASE 4. Carga la skill `diseno-factorial-2k`; consulta Context7 para statsmodels y SciPy.
Alcance: tabla de signos, efectos q0..qABC, asignación de la variación (%), ANOVA, IC de 95 %, pruebas de significancia
y diagnóstico de residuos (residuos vs. ajustados, Q–Q, Shapiro–Wilk, Levene). Interruptor de escala original / ln
(opcional Box–Cox) con comparación lado a lado; sin decisión por defecto. Todo marcado "preliminar".
Criterios: efectos y ANOVA coinciden con statsmodels hasta 1e-8 (pruebas con datos sintéticos de efectos conocidos);
el módulo permanece bloqueado sin las 2^k × r corridas; advertencia de bajo poder junto a cada test.
