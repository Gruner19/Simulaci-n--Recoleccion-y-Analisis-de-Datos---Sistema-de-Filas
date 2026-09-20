# Reprodução da Entrega 1.  Uso:  make all
PY = python3

all: dados relatorio apresentacao

dados:
	$(PY) codigo/verificacao_simulador.py
	$(PY) codigo/piloto_eda.py
	$(PY) codigo/plano_experimental.py

relatorio: dados
	cd relatorio && pdflatex relatorio && biber relatorio && pdflatex relatorio && pdflatex relatorio

apresentacao: dados
	cd apresentacao && pdflatex apresentacao && biber apresentacao && pdflatex apresentacao && pdflatex apresentacao

# Só depois da aprovação da proposta:
experimento:
	$(PY) codigo/executar_experimento.py

limpar:
	cd relatorio && rm -f *.aux *.bbl *.bcf *.blg *.log *.out *.run.xml *.toc
	cd apresentacao && rm -f *.aux *.bbl *.bcf *.blg *.log *.out *.run.xml *.toc *.nav *.snm

.PHONY: all dados relatorio apresentacao experimento limpar
