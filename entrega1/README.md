# Entrega 1 — Proposta e Análise Exploratória dos Dados

Projeto e Análise de Experimentos Computacionais (UFOP). Experimento fatorial 2³ com r = 10 sobre um sistema de filas simulado (SimPy).

- `relatorio/relatorio.pdf` — relatório em APA 7 (LaTeX, classe apa7)
- `apresentacao/apresentacao.pdf` — slides (Beamer, citações em APA)
- `codigo/` — simulador, piloto/EDA, plano experimental, verificação e executor do experimento
- `dados/`, `figuras/`, `tabelas/` — saídas geradas pelos scripts

Reprodução: `pip install -r codigo/requirements.txt` e `make all`.
As 80 corridas do experimento só são executadas depois da aprovação: `make experimento`.
Hardware do piloto: editar `tabelas/ambiente_hardware.tex` se as corridas forem feitas em outra máquina.
