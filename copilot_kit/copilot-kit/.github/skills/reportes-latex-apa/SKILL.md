---
name: reportes-latex-apa
description: Generación de tablas y figuras y exportación de reportes en LaTeX con estilo APA 7 en portugués de Brasil (decimales con coma, booktabs, cifras generadas por código). Úsalo al implementar la exportación de reportes o al editar plantillas .tex.
---
# Reportes LaTeX / APA 7 (pt-BR)

- Clase `apa7` (modo `stu`), `babel` brasileño y `biblatex-apa` con `\DeclareLanguageMapping{brazilian}{brazilian-apa}`.
  Compilar: pdflatex → biber → pdflatex → pdflatex. El proyecto de referencia está en `referencia/` (relatorio/, apresentacao/).
- Las cifras del texto salen de macros generados por código (`\newcommand{\PilotoMedia}{9,112\xspace}`); nunca copies números a mano.
- Tablas con `booktabs` (sin líneas verticales), título "Tabela n" en negrita y título en cursiva arriba, nota abajo.
  Decimales con coma; valores negativos con `$-$`.
- Figuras en PDF vectorial (fuentes incrustadas), ejes rotulados con unidades, paleta legible en blanco y negro.
- Al exportar, incluye el resumen de reproducibilidad: versiones de software, semillas, hardware y fecha.
- Las referencias vienen de un `.bib` versionado; cita solo lo que se usa en el texto.
