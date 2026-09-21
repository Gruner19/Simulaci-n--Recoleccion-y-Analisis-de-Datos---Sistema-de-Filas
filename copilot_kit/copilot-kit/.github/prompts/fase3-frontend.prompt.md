---
description: Fase 3 — frontend de configuración, hipótesis, plan, ejecución y AED.
agent: agent
---
Implementa la FASE 3 en `frontend/` (React + Vite + TypeScript + Plotly), consumiendo la API de las fases 1 y 2.
Consulta Context7 para React, Vite, TanStack Query y Plotly. Interfaz en portugués (BR), decimales con coma.
Pantallas: configuración (factores, niveles, r, N, W, semillas, validación de ρ), hipótesis (se bloquea al ejecutar),
plan (tabla de signos y orden aleatorio), ejecución (progreso en tiempo real, cancelar y reintentar) y AED/verificación.
El módulo factorial aparece deshabilitado y con explicación hasta tener todas las corridas.
Verifica con Playwright: flujo completo con N pequeño, capturas de cada pantalla y gráficos renderizados.
