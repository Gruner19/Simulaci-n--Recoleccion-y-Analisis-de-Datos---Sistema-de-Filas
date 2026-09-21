# Instrucciones del proyecto: plataforma web para experimentos factoriales 2^3 sobre un simulador de colas

## Qué es
Sistema web para PLANIFICAR, EJECUTAR y ANALIZAR un experimento factorial 2^3 con r réplicas sobre un simulador
de colas M/M/c y M/D/c (SimPy). El código de referencia validado está en `referencia/` (simulador, plan, piloto,
verificación). Reutilízalo; no lo reescribas desde cero.

## Reglas que nunca se rompen
1. Unidad de análisis = MEDIA POR CORRIDA. Las esperas de clientes consecutivos están fuertemente correlacionadas
   (ACF ≈ 0,99 en lag 1); nunca las uses como muestra independiente ni en el ANOVA.
2. Cada réplica es una ejecución COMPLETA (sistema vacío, semilla nueva). Prohibido dividir una corrida larga en
   lotes y llamarlos réplicas.
3. AED y análisis factorial están separados. La AED (piloto de UNA sola configuración) no compara niveles, no estima
   efectos y no evalúa la hipótesis. El análisis factorial se habilita solo con las 80 corridas terminadas.
4. La hipótesis se guarda con marca de tiempo y se bloquea ANTES de la primera corrida del experimento.
5. Reproducibilidad total: misma configuración + mismas semillas = mismos resultados. Usa `np.random.Generator` y
   `SeedSequence.spawn`; nunca `np.random.seed` global ni semillas compartidas entre corridas.
6. No decidas la transformación de la respuesta por defecto: muestra diagnósticos de escala original y ln, y deja elegir.
7. Los tests de normalidad tienen poco poder con r = 10: dilo en la interfaz junto a cada test.

## Convenciones
- Interfaz en portugués de Brasil, con decimales con coma. Identificadores como en `referencia/`. Commits en español.
- Backend: Python 3.12, FastAPI, SQLAlchemy + SQLite, pytest. Frontend: React + Vite + TypeScript + Plotly.
- Versiones de dependencias fijadas. Sin secretos en el repositorio.
- Toda función estadística nueva lleva una prueba que la compare con `statsmodels`/`scipy` (tolerancia 1e-8).

## Cómo usar las herramientas
- Antes de usar una API de FastAPI, SimPy, statsmodels, SciPy, SQLAlchemy, React o Plotly, consulta la documentación
  con el MCP `context7`; no inventes firmas de funciones.
- Para verificar la interfaz (formularios, progreso, gráficos), usa el MCP `playwright` y guarda capturas.
- Las skills del proyecto (`simulador-de-colas`, `diseno-factorial-2k`, `aed-antes-del-factorial`,
  `reportes-latex-apa`) contienen las fórmulas y reglas detalladas: cárgalas cuando la tarea las toque.
- Al terminar cada fase, ejecuta las pruebas, resume qué se hizo y qué quedó pendiente, y espera confirmación.
