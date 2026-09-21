# Kit de Copilot para la plataforma de experimentos factoriales

## Instalación (5 pasos)
1. Crea el repositorio y copia dentro las carpetas `.github/` y `.vscode/` de este kit.
2. Descomprime `entrega1_fontes.zip` y copia su carpeta `codigo/` (más `relatorio/referencias.bib` y `tabelas/` si quieres
   las plantillas LaTeX) a `referencia/` en la raíz del repositorio. Copilot la usará como código validado.
3. Abre la carpeta en VS Code (con la extensión GitHub Copilot) y acepta iniciar los servidores MCP de `.vscode/mcp.json`
   (ícono de "play" sobre cada servidor). Necesitas Node.js (npx) y `uv` (uvx). `sqlite` y `github` son opcionales.
4. Verifica: en el chat escribe `/skills` (deben aparecer las 4 skills); abre el selector de herramientas (debe listar
   context7 y playwright); abre el selector de agentes (planificador, implementador, revisor-metodologico).
5. Pega `PROMPT_MAESTRO.md` con el agente `planificador`. Cuando confirmes el plan, ejecuta `/fase1-backend` con el
   agente `implementador`, y al final de cada fase `/revision-metodologica`.

## Notas
- Los formatos de personalización de VS Code cambian rápido. Si tu versión usa `mode: agent` en lugar de `agent: agent`
  en los `.prompt.md`, o nombres distintos de herramientas, ajústalos (Command Palette → "Chat: Open Customizations").
- Los servidores MCP ejecutan código en tu máquina: revisa cada uno antes de aceptarlo.
- Las cifras del piloto en las skills son orientativas; otra semilla dará valores distintos.
