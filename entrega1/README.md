# Entrega 1 — Proposta e Análise Exploratória dos Dados

Projeto e Análise de Experimentos Computacionais (UFOP). Experimento fatorial 2³ com r = 10 sobre um sistema de filas simulado (SimPy).

- `relatorio/relatorio.pdf` — relatório em APA 7 (LaTeX, classe apa7)
- `apresentacao/apresentacao.pdf` — slides (Beamer, citações em APA)
- `codigo/` — simulador, piloto/EDA, plano experimental, verificação, executor e análise de resultados
- `dados/`, `figuras/`, `tabelas/`, `salidas/` — saídas geradas pelos scripts

## Reproducción

```bash
make setup                 # crea .venv e instala codigo/requirements.txt
make dados                 # plano + verificación + piloto (figuras/tablas)
make experimento           # 80 corridas del fatorial (paralelizadas, deterministas)
make resultados            # ayuda del sistema de manipulación/exportación de resultados (CLI)
make interfaz              # abre panel web amigable en el navegador
```

Todo el flujo también roda con `make all`. Los scripts usan el venv `.venv` si existe; sino, `python3`.

## Simulación

- `codigo/verificacao_simulador.py` — simula contra fórmulas teóricas (M/M/1, M/D/1, Erlang C). **Paralelizado** y determinista.
- `codigo/piloto_eda.py` — piloto exploratorio y AED sobre la célula 3.
- `codigo/plano_experimental.py` — genera `dados/plano_experimental.csv` (80 corridas aleatorizadas).
- `codigo/executar_experimento.py` — **paralelizado** (multiprocessing); cada réplica es determinista porque su semente deriva solo de SEED_EXPERIMENTO + spawn_key. Salida: `dados/resultados_fatorial.csv`.

## Interfaz web (gráfica, sin dependencias extra)

```bash
make interfaz              # abre http://localhost:8000 en el navegador
make interfaz-servidor     # solo arranca el servidor (sin abrir navegador)
```

El panel tiene pestañas:
- **Resumen** — estadísticas del dataset.
- **Agrupar** — agrupa por A, B, C, celula; media, desv, IC 95 %, CV, n.
- **Efectos** — efectos del fatorial 2³ (unidades o ln) con % de contribución.
- **ANOVA** — tabla OLS (R², coef, se, t, p, significancia).
- **Filtrar** — expresión pandas; tabla resultante.
- **Simular** — botones para lanzar verificación, plano, piloto y experimento (80 corridas), con log en vivo.

Todos los comandos de análisis permiten exportar con un clic a **CSV / Excel / JSON / LaTeX**. El panel sirve también los archivos de `salidas/` para descarga directa.

## Sistema de manipulación/exportación (CLI)

`codigo/analizar_resultados.py` lee los CSV de salida y permite explorar, filtrar, agregar,
estimar efectos del fatorial 2³, correr ANOVA (OLS) y exportar a **CSV / Excel / JSON / LaTeX**.

```bash
python codigo/analizar_resultados.py listar                       # CSVs disponibles
python codigo/analizar_resultados.py resumen                      # estadísticas
python codigo/analizar_resultados.py agregar -p celula            # resumen por célula
python codigo/analizar_resultados.py agregar -p A B C --salida salidas/ag.csv --formato csv
python codigo/analizar_resultados.py filtrar --donde "celula==2 & replica>=5" --salida salidas/f.csv
python codigo/analizar_resultados.py factorial [--log] --salida salidas/efectos.csv
python codigo/analizar_resultados.py anova [--log] --salida salidas/anova.xlsx --formato xlsx
python codigo/analizar_resultados.py informe --salida salidas    # informe consolidado (MD + CSVs)
```

Todos los comandos aceptan `--entrada <csv>` (por defecto `dados/resultados_fatorial.csv`),
`--salida` y `--formato csv|xlsx|json|latex`. Ejemplos generados em `salidas/`.

## Notas

- Las 80 corridas del experimento solo deben ejecutarse após aprobación (`make experimento`).
- Hardware del piloto: editar `tabelas/ambiente_hardware.tex` si las corridas se hacen en otra máquina.
- El fatorial está dimensionado con la célula más exigente (cel 3, ρ = 0,90, servicio exp).
