---
description: Fase 5 — exportación de reportes LaTeX/CSV, resumen de reproducibilidad, Docker y README.
agent: agent
---
Implementa la FASE 5. Carga la skill `reportes-latex-apa`.
Alcance: exportar tablas en LaTeX (booktabs, decimales con coma) y CSV, figuras en PDF/PNG, y un resumen de
reproducibilidad (versiones, semillas, hardware, fecha). Dockerfile del backend y del frontend, docker-compose,
dependencias con versiones fijadas y README con instrucciones de uso y de reproducción.
Criterios: `docker compose up` levanta todo; un experimento completo con N pequeño se ejecuta de punta a punta
y el reporte exportado compila con pdflatex + biber.
