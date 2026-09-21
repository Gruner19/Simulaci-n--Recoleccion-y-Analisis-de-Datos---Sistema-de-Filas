# Reprodução da Entrega 1.  Usa o venv .venv se existir, senão python3.  Uso:  make all
PY = $(shell .venv/bin/python --version >/dev/null 2>&1 && echo .venv/bin/python || echo python3)

# Não roda em paralelo: cada script depende do anterior (tab_*.tex, macros, etc.).
.NOTPARALLEL:

all: dados relatorio apresentacao

# Cria o venv e instala as dependências (codigo/requirements.txt)
setup:
	python3 -m venv .venv && .venv/bin/pip install --upgrade pip && .venv/bin/pip install -r codigo/requirements.txt

dados: setup-venv
	$(PY) codigo/plano_experimental.py
	$(PY) codigo/verificacao_simulador.py
	$(PY) codigo/piloto_eda.py

setup-venv:
	@test -x .venv/bin/python || $(MAKE) setup

relatorio: dados
	cd relatorio && pdflatex relatorio && biber relatorio && pdflatex relatorio && pdflatex relatorio

apresentacao: dados
	cd apresentacao && pdflatex apresentacao && biber apresentacao && pdflatex apresentacao && pdflatex apresentacao

# Só depois da aprovação da proposta (paralelizado por semente; determinista):
experimento:
	$(PY) codigo/executar_experimento.py

# Sistema de manipulação/exportación de resultados (CLI):
resultados:
	$(PY) codigo/analizar_resultados.py --help

# Interfaz web amigable (panel en el navegador):
interfaz:
	$(PY) codigo/interfaz.py --abrir

interfaz-servidor:
	$(PY) codigo/interfaz.py

limpar:
	cd relatorio && rm -f *.aux *.bbl *.bcf *.blg *.log *.out *.run.xml *.toc
	cd apresentacao && rm -f *.aux *.bbl *.bcf *.blg *.log *.out *.run.xml *.toc *.nav *.snm

.PHONY: all dados relatorio apresentacao experimento limpar
