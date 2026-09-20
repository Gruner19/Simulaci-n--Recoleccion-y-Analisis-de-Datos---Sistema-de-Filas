"""Parâmetros centrais do experimento (única fonte de verdade para código e documentos)."""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "dados"
FIGURAS = RAIZ / "figuras"
TABELAS = RAIZ / "tabelas"

# ---------------------------------------------------------------- experimento fatorial 2^3 r
R = 10                    # réplicas independentes por combinação (exigência: r >= 10)
N_CLIENTES = 50_000       # clientes simulados por corrida
AQUECIMENTO = 1_000       # clientes iniciais descartados (transiente inicial)
MEDIA_SERVICO = 1.0       # min, constante em todo o experimento

# Níveis codificados: -1 (baixo) e +1 (alto)
NIVEIS = {
    "A": {"nome": "Número de servidores (c)", "menos": 1,     "mais": 2},
    "B": {"nome": "Taxa de chegada (lambda)",  "menos": 0.5,   "mais": 0.9},
    "C": {"nome": "Tempo de serviço",          "menos": "exp", "mais": "const"},
}

# ---------------------------------------------------------------- sementes (registradas no relatório)
SEED_PILOTO = 20260920        # piloto exploratório (não entra na análise fatorial)
SEED_EXPERIMENTO = 20260922   # corridas do experimento fatorial (SeedSequence.spawn)
SEED_ORDEM = 20260923         # permutação aleatória da ordem de execução
SEED_VERIFICACAO = 20260924   # verificação do simulador contra fórmulas teóricas

# ---------------------------------------------------------------- piloto
R_PILOTO = 30                 # réplicas piloto por configuração
N_WELCH = 6_000               # clientes por corrida no piloto de aquecimento (Welch)
R_WELCH = 300                 # réplicas no piloto de aquecimento
JANELA_WELCH = 250            # janela da média móvel de Welch

# Configuração ÚNICA do piloto: célula 3 do projeto (A-, B+, C-). Escolhida a priori como a mais exigente para
# dimensionar as corridas (maior utilização: transiente mais longo e maior variância da média). O piloto NÃO compara
# níveis de fatores e NÃO estima efeitos: apenas caracteriza a resposta e dimensiona N e W.
CONFIG_PILOTO = {"c": 1, "lam": 0.9, "servico": "exp"}
