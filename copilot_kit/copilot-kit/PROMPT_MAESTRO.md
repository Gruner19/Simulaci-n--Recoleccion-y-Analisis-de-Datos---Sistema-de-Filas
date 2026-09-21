# Prompt maestro (pegar en el chat de Copilot en modo agente, con el agente "planificador")

Actúa como ingeniero full-stack senior. Construye una plataforma web para PLANIFICAR, EJECUTAR y ANALIZAR un
experimento factorial 2^3 con r réplicas sobre un simulador de colas. En `referencia/` está el código validado
(simulador SimPy, plan aleatorizado, piloto/AED, verificación teórica): reutilízalo. Interfaz en portugués (BR),
decimales con coma.

## Contexto del experimento
- Sistema: cola M/M/c o M/D/c, FIFO, fila infinita, llegadas de Poisson, servicio de media 1 min.
- Factores: A = servidores (1 | 2), B = tasa de llegada λ (0,5 | 0,9), C = servicio (exponencial | constante).
- Respuesta: espera media en cola por corrida (min), tras descartar W clientes. Por defecto r = 10 (mínimo 10),
  N = 50.000, W = 1.000; 2^3 × r = 80 corridas.
- Aleatorización: semillas independientes con SeedSequence.spawn (PCG64) y orden de ejecución sorteado con una
  permutación uniforme de semilla propia. Cada réplica es una ejecución completa (sistema vacío, semilla nueva).

## Stack
Backend: Python 3.12, FastAPI, SimPy, NumPy, SciPy, statsmodels, pandas, SQLite (SQLAlchemy), pytest.
Frontend: React + Vite + TypeScript + Plotly. Corridas con ProcessPoolExecutor y progreso por SSE. Docker + compose.

## Módulos
1. Configuración (validar ρ = λ/(cμ) < 1 en todas las celdas). 2. Hipótesis con marca de tiempo, bloqueada antes de ejecutar.
3. Plan (8 combinaciones con signos y ρ; 80 corridas en orden aleatorio; CSV). 4. Ejecución con progreso, cancelación y
reintento. 5. Verificación del simulador contra la teoría. 6. AED del piloto (UNA configuración). 7. Análisis factorial
(solo con las 80 corridas): efectos, variación, ANOVA, IC, residuos, escala original vs ln. 8. Reportes LaTeX/CSV/figuras
y resumen de reproducibilidad.

## Reglas no negociables (aprendidas del piloto; las cifras son orientativas)
- Unidad de análisis = media por corrida (ACF de esperas individuales ≈ 0,99 en lag 1 y ≈ 0,90 en lag 10).
- Réplicas = corridas completas con semilla nueva; nunca lotes de una corrida larga.
- AED separada del factorial: no compara niveles ni estima efectos; el módulo factorial se habilita con las 80 corridas.
- La respuesta puede salir asimétrica a la derecha (piloto con ρ = 0,9: asimetría ≈ 1,3; Shapiro–Wilk p ≈ 0,005; en ln
  ≈ 0,96): no decidas la transformación por defecto.
- Con r = 10 los tests de normalidad tienen poco poder: dilo en la interfaz.
- Reproducibilidad total: mismas semillas ⇒ mismos resultados, con cualquier número de procesos.

## Herramientas de Copilot que debes usar
- Instrucciones del repositorio (`.github/copilot-instructions.md` y `.github/instructions/`): se aplican solas.
- Skills (`.github/skills/`): `simulador-de-colas`, `diseno-factorial-2k`, `aed-antes-del-factorial`, `reportes-latex-apa`.
  Cárgalas cuando la tarea las toque.
- MCP: `context7` para consultar documentación real antes de usar una API; `playwright` para verificar la interfaz;
  `sqlite` y `github` (opcionales) para inspeccionar la base y gestionar issues/PR.
- Agentes: `planificador` (plan, sin editar), `implementador` (una fase a la vez), `revisor-metodologico` (auditoría).
- Prompts por fase: `/fase1-backend`, `/fase2-aed-verificacion`, `/fase3-frontend`, `/fase4-analisis-factorial`,
  `/fase5-reportes-docker` y `/revision-metodologica`.

## Criterios de aceptación globales
Reproducibilidad idéntica; verificación teórica con error < 2 %; efectos y ANOVA iguales a statsmodels hasta 1e-8;
80 corridas con N = 50.000 en ≈ 40 s por núcleo; pytest y pruebas E2E en verde.

## Tu primera respuesta
No escribas código todavía. Lee el repositorio y `referencia/`, y entrega el plan por fases con archivos, riesgos,
criterios de aceptación y preguntas abiertas. Espera mi confirmación antes de la Fase 1.
