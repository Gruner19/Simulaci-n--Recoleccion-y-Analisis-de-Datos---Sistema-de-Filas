---
description: Fase 1 — backend con simulador, plan aleatorizado y ejecución en segundo plano, con pruebas.
agent: agent
---
Implementa la FASE 1 (backend) en `backend/`, reutilizando `referencia/`.
Carga las skills `simulador-de-colas` y `diseno-factorial-2k`. Consulta con Context7 la documentación de FastAPI,
SQLAlchemy y SimPy antes de usar sus APIs.
Alcance: modelos y esquemas; endpoints de configuración (validando ρ < 1), hipótesis con bloqueo y marca de tiempo,
plan (8 celdas + 80 corridas en orden aleatorio, exportable a CSV) y ejecución con ProcessPoolExecutor, progreso por
SSE, cancelación y reintento; persistencia en SQLite; exportación CSV.
Criterios de aceptación: prueba de reproducibilidad (mismas semillas ⇒ mismos resultados con 1 y con 4 procesos);
80 corridas con N = 50.000 en ≈ 40 s por núcleo; pytest en verde. Al terminar, resume y espera confirmación.
