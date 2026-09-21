---
applyTo: "backend/**/*.py"
---
- Tipado estático (type hints) en funciones públicas; docstrings cortos con fórmulas cuando corresponda.
- Las corridas de simulación se ejecutan con `ProcessPoolExecutor`; cada tarea recibe su `SeedSequence` hija y
  devuelve resultados independientes del número de workers y del orden de finalización.
- Endpoints con esquemas Pydantic; errores con códigos HTTP claros. El progreso se transmite por SSE.
- Persistencia: una fila por corrida (run_id, celda, réplica, A, B, C, spawn_key, orden, respuesta, tiempo_s, estado).
- Nada de estado global mutable. La configuración del experimento se congela al iniciar la ejecución.
