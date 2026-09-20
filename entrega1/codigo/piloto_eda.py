"""Piloto exploratório e Análise Exploratória dos Dados (AED) da Entrega 1.

O piloto usa UMA única configuração (célula 3 do projeto: c=1, lambda=0,9, serviço exponencial), escolhida a priori
como a mais exigente para dimensionar as corridas. Ele NÃO compara níveis de fatores, NÃO estima efeitos e NÃO avalia
a hipótese geral: apenas caracteriza a variável de resposta e justifica a viabilidade do experimento.
As corridas piloto usam sementes diferentes das do experimento e não entram na análise fatorial.

Gera: dados/piloto_*.csv, figuras/*.pdf, tabelas/*.tex (tabelas e macros numéricos).
Uso:  python codigo/piloto_eda.py
"""
from __future__ import annotations

import os
import platform
import subprocess
import sys
import time
from importlib import metadata
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter
from scipy import stats
from statsmodels.tsa.stattools import acf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import (AQUECIMENTO, CONFIG_PILOTO, DADOS, FIGURAS, JANELA_WELCH, N_CLIENTES, N_WELCH, R,
                    R_PILOTO, R_WELCH, SEED_PILOTO, TABELAS)
from simulador import espera_teorica, simular_fila

for pasta in (DADOS, FIGURAS, TABELAS):
    pasta.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 9.5, "axes.labelsize": 9,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": False,
    "pdf.fonttype": 42, "ps.fonttype": 42, "figure.dpi": 150, "savefig.bbox": "tight", "legend.frameon": False,
})
COR = "#1f4e79"
VIRG = FuncFormatter(lambda v, _: f"{v:g}".replace(".", ","))
MIL = FuncFormatter(lambda v, _: f"{int(v):,}".replace(",", "."))


def br(x: float, d: int = 2) -> str:
    sinal = "$-$" if round(x, d) < 0 else ""
    return sinal + f"{abs(x):.{d}f}".replace(".", ",")


def pval(p: float) -> str:
    return "$<$ 0,001" if p < 0.001 else br(p, 3)


def salvar(fig, nome):
    fig.savefig(FIGURAS / f"{nome}.pdf")
    plt.close(fig)


macros: dict[str, str] = {}


def M(nome: str, valor: str):
    macros[nome] = valor


c, lam, servico = CONFIG_PILOTO["c"], CONFIG_PILOTO["lam"], CONFIG_PILOTO["servico"]
rho = lam / c
teo = espera_teorica(c, lam, servico)
taxa = 1.0 - lam  # mu - lambda (mu = 1)

# ------------------------------------------------------------------ 1) piloto principal e comprimento da corrida
raiz = np.random.SeedSequence(SEED_PILOTO)
seq_principal, seq_curto, seq_welch = raiz.spawn(3)
N_CURTO = 10_000

linhas, esperas_rep0 = [], None
for k, filho in enumerate(seq_principal.spawn(R_PILOTO)):
    t0 = time.perf_counter()
    w = simular_fila(c, lam, servico, N_CLIENTES, np.random.default_rng(filho))
    dt = time.perf_counter() - t0
    if k == 0:
        esperas_rep0 = w[AQUECIMENTO:]
    linhas.append({"n_clientes": N_CLIENTES, "aquecimento": AQUECIMENTO, "replica": k + 1,
                   "resposta": w[AQUECIMENTO:].mean(), "tempo_s": dt})
for k, filho in enumerate(seq_curto.spawn(R_PILOTO)):
    t0 = time.perf_counter()
    w = simular_fila(c, lam, servico, N_CURTO, np.random.default_rng(filho))
    linhas.append({"n_clientes": N_CURTO, "aquecimento": AQUECIMENTO, "replica": k + 1,
                   "resposta": w[AQUECIMENTO:].mean(), "tempo_s": time.perf_counter() - t0})
df = pd.DataFrame(linhas)
df.to_csv(DADOS / "piloto_medias_corridas.csv", index=False)
principal = df[df.n_clientes == N_CLIENTES]

# ------------------------------------------------------------------ 2) piloto de aquecimento (Welch)
mat = np.array([simular_fila(c, lam, servico, N_WELCH, np.random.default_rng(f)) for f in seq_welch.spawn(R_WELCH)])
media_por_cliente = mat.mean(axis=0)
mm = np.convolve(media_por_cliente, np.ones(JANELA_WELCH) / JANELA_WELCH, mode="valid")
xw = np.arange(len(mm)) + JANELA_WELCH / 2
pd.DataFrame({"indice_cliente": xw, "media_movel": mm}).to_csv(DADOS / "piloto_welch_mediamovel.csv", index=False)
ini = mat[:, :500].mean(axis=1)
plato = mat[:, AQUECIMENTO:].mean(axis=1)
dif_ini = ini - plato
resid = mat[:, AQUECIMENTO:2 * AQUECIMENTO].mean(axis=1) - mat[:, 3 * AQUECIMENTO:].mean(axis=1)

# ------------------------------------------------------------------ 3) estatísticas das médias por corrida
x = principal.resposta.to_numpy()
n = len(x)
dp = x.std(ddof=1)
tcrit = stats.t.ppf(0.975, n - 1)
ic = (x.mean() - tcrit * dp / np.sqrt(n), x.mean() + tcrit * dp / np.sqrt(n))
sw = stats.shapiro(x)
q1, med, q3 = np.percentile(x, [25, 50, 75])
r_rep, p_rep = stats.pearsonr(x[:-1], x[1:])  # independência entre réplicas consecutivas
lnx = np.log(x)
sw_ln = stats.shapiro(lnx)  # diagnóstico da escala logarítmica (mesma configuração)
assim_ln = stats.skew(lnx, bias=False)
tempo = principal.tempo_s.mean()

linhas_t = [
    ("Utilização do servidor ($\\rho$)", br(rho, 2)),
    ("Réplicas piloto ($n$)", str(n)),
    ("Média (min)", br(x.mean(), 3)),
    ("Desvio-padrão (min)", br(dp, 3)),
    ("Coeficiente de variação (\\%)", br(100 * dp / x.mean(), 1)),
    ("Mínimo (min)", br(x.min(), 3)),
    ("1.º quartil (min)", br(q1, 3)),
    ("Mediana (min)", br(med, 3)),
    ("3.º quartil (min)", br(q3, 3)),
    ("Máximo (min)", br(x.max(), 3)),
    ("Assimetria", br(stats.skew(x, bias=False), 2)),
    ("Curtose (excesso)", br(stats.kurtosis(x, bias=False), 2)),
    ("Shapiro--Wilk $W$ ($p$)", f"{br(sw.statistic, 3)} ({pval(sw.pvalue)})"),
    ("IC 95\\% da média (min)", f"[{br(ic[0], 3)}; {br(ic[1], 3)}]"),
]
t1 = ["\\begin{tabular}{lr}", "\\toprule", "Estatística & Valor \\\\", "\\midrule"]
t1 += [f"{a} & {b} \\\\" for a, b in linhas_t]
t1 += ["\\midrule", f"Valor teórico de $W_q$ (min) & {br(teo, 3)} \\\\",
       f"Erro relativo da média (\\%) & {br(100 * (x.mean() / teo - 1), 1)} \\\\", "\\bottomrule", "\\end{tabular}"]
(TABELAS / "tab_descritivas_medias.tex").write_text("\n".join(t1) + "\n", encoding="utf-8")

# ------------------------------------------------------------------ 4) esperas individuais (1.ª corrida piloto)
w = esperas_rep0


def quantil_teorico(q):
    return 0.0 if q <= 1 - rho else -np.log((1 - q) / rho) / taxa


var_t = 2 * rho / taxa ** 2 - (rho / taxa) ** 2
r_acf = acf(w, nlags=200, fft=True)
p0 = float(np.mean(w <= 1e-12))
p90, p99 = np.percentile(w, 90), np.percentile(w, 99)
t2 = ["\\begin{tabular}{lrr}", "\\toprule", "Estatística & Empírico & Teórico (M/M/1) \\\\", "\\midrule",
      f"Clientes analisados & {len(w):,} & --- \\\\".replace(",", "."),
      f"$P(W_q=0)$ & {br(p0, 3)} & {br(1 - rho, 3)} \\\\",
      f"Média (min) & {br(w.mean(), 2)} & {br(rho / taxa, 2)} \\\\",
      f"Desvio-padrão (min) & {br(w.std(ddof=1), 2)} & {br(np.sqrt(var_t), 2)} \\\\",
      f"Percentil 90 (min) & {br(p90, 2)} & {br(quantil_teorico(0.90), 2)} \\\\",
      f"Percentil 99 (min) & {br(p99, 2)} & {br(quantil_teorico(0.99), 2)} \\\\",
      f"Máximo (min) & {br(w.max(), 1)} & --- \\\\",
      f"Assimetria & {br(stats.skew(w), 2)} & --- \\\\",
      f"Autocorrelação (defasagem 1) & {br(r_acf[1], 2)} & --- \\\\", "\\bottomrule", "\\end{tabular}"]
(TABELAS / "tab_esperas_individuais.tex").write_text("\n".join(t2) + "\n", encoding="utf-8")

# ------------------------------------------------------------------ 5) comprimento da corrida
tcrit9 = stats.t.ppf(0.975, R - 1)
t3 = ["\\begin{tabular}{rrrrr}", "\\toprule",
      "$N$ (clientes) & $s$ (min) & CV (\\%) & Meia-largura do IC ($r=10$) & Tempo/corrida (s) \\\\", "\\midrule"]
comp = {}
for n_cl in (N_CURTO, N_CLIENTES):
    sub = df[df.n_clientes == n_cl]
    xx = sub.resposta.to_numpy()
    d_, m_ = xx.std(ddof=1), xx.mean()
    meia = 100 * tcrit9 * d_ / np.sqrt(R) / m_
    comp[n_cl] = dict(cv=100 * d_ / m_, meia=meia)
    t3.append(f"{n_cl:,} & {br(d_, 3)} & {br(100 * d_ / m_, 1)} & $\\pm$ {br(meia, 1)}\\% & "
              f"{br(sub.tempo_s.mean(), 3)} \\\\".replace(",", ".", 1))
t3 += ["\\bottomrule", "\\end{tabular}"]
(TABELAS / "tab_comprimento_corrida.tex").write_text("\n".join(t3) + "\n", encoding="utf-8")

# ------------------------------------------------------------------ 6) figuras
# Welch
fig, ax = plt.subplots(figsize=(4.8, 2.8))
ax.axvspan(0, AQUECIMENTO, color="0.9", lw=0)
ax.plot(xw, mm, color=COR, lw=1.1)
ax.axhline(teo, color="k", ls="--", lw=0.8)
ax.axvline(AQUECIMENTO, color="k", ls=":", lw=0.8)
ax.set_xlabel("Índice do cliente (ordem de chegada)")
ax.set_ylabel("Espera média em fila (min)")
ax.set_xlim(0, N_WELCH)
ax.set_ylim(0, None)
ax.text(AQUECIMENTO + 80, ax.get_ylim()[1] * 0.06, f"W = {AQUECIMENTO:,}".replace(",", "."), fontsize=8)
ax.yaxis.set_major_formatter(VIRG)
ax.xaxis.set_major_formatter(MIL)
fig.tight_layout()
salvar(fig, "fig_welch")

# esperas individuais
fig, ax = plt.subplots(figsize=(4.8, 2.8))
pos = w[w > 1e-12]
bins = np.linspace(0, np.percentile(w, 99.9), 45)
cont, bordas = np.histogram(pos, bins=bins)
dens = cont / (len(w) * np.diff(bordas))
ax.bar(bordas[:-1], dens, width=np.diff(bordas), align="edge", color=COR, alpha=0.55, lw=0)
t = np.linspace(0, bins[-1], 300)
ax.plot(t, rho * taxa * np.exp(-taxa * t), color="k", lw=1)
ax.set_yscale("log")
ax.set_xlabel("Espera na fila (min)")
ax.set_ylabel("Densidade (escala log)")
ax.text(0.97, 0.95, f"$P(W_q=0)$ = {br(p0, 3)}\n(teórico {br(1 - rho, 3)})", transform=ax.transAxes,
        ha="right", va="top", fontsize=8)
ax.xaxis.set_major_formatter(VIRG)
fig.tight_layout()
salvar(fig, "fig_esperas_individuais")

# autocorrelação entre clientes
fig, ax = plt.subplots(figsize=(4.6, 2.7))
ax.plot(np.arange(len(r_acf)), r_acf, color=COR, lw=1.3)
ax.axhline(0, color="k", lw=0.6)
ax.set_xlabel("Defasagem (número de clientes)")
ax.set_ylabel("Autocorrelação")
ax.yaxis.set_major_formatter(VIRG)
fig.tight_layout()
salvar(fig, "fig_acf")

# distribuição das médias por corrida: histograma + Q-Q
fig, axs = plt.subplots(1, 2, figsize=(6.6, 2.9))
ax = axs[0]
ax.hist(x, bins=8, color=COR, alpha=0.6, edgecolor="white")
ax.axvline(x.mean(), color=COR, lw=1.4, label="média do piloto")
ax.axvline(teo, color="k", ls="--", lw=1, label="valor teórico")
ax.set_ylim(0, ax.get_ylim()[1] * 1.35)
ax.legend(loc="upper center", ncol=2, fontsize=7)
ax.set_xlabel("Espera média por corrida (min)")
ax.set_ylabel("Frequência")
ax.set_title("Histograma")
ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.1f}".replace(".", ",")))
ax = axs[1]
(tq, ordenados), (incl, inter, _) = stats.probplot(x, dist="norm")
ax.plot(tq, ordenados, "o", ms=3.5, color=COR)
ax.plot(tq, inter + incl * tq, "k-", lw=0.9)
ax.set_xlabel("Quantis teóricos (normal)")
ax.set_ylabel("Quantis amostrais (min)")
ax.set_title("Gráfico Q–Q normal")
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.1f}".replace(".", ",")))
ax.xaxis.set_major_formatter(VIRG)
fig.tight_layout()
salvar(fig, "fig_distribuicao_medias")

# independência entre réplicas: média por corrida x ordem da réplica
fig, ax = plt.subplots(figsize=(4.8, 2.7))
ax.plot(np.arange(1, n + 1), x, "o-", ms=3.5, lw=0.7, color=COR)
ax.axhline(x.mean(), color=COR, lw=1)
ax.axhline(teo, color="k", ls="--", lw=0.8)
ax.set_xlabel("Ordem da réplica piloto")
ax.set_ylabel("Espera média por corrida (min)")
ax.text(0.98, 0.04, f"$r$(lag 1) = {br(r_rep, 2)}  ($p$ = {br(p_rep, 2)})", transform=ax.transAxes, ha="right", fontsize=8)
ax.yaxis.set_major_formatter(VIRG)
fig.tight_layout()
salvar(fig, "fig_replicas")

# ------------------------------------------------------------------ 7) ambiente computacional
def versao(pkg):
    try:
        return metadata.version(pkg)
    except metadata.PackageNotFoundError:
        return "n/d"


def cmd(args):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=20).stdout.strip()
    except Exception:
        return ""


cpu, ram_gb = "n/d", "n/d"
try:
    for linha in open("/proc/cpuinfo"):
        if linha.startswith("model name"):
            cpu = linha.split(":", 1)[1].strip()
            break
    for linha in open("/proc/meminfo"):
        if linha.startswith("MemTotal"):
            ram_gb = br(int(linha.split()[1]) / 1024 / 1024, 1)
            break
except OSError:
    pass
tex_ver = (cmd(["pdflatex", "--version"]).splitlines() or ["n/d"])[0].replace("_", "\\_")
biber_ver = (cmd(["biber", "--version"]).splitlines() or ["n/d"])[0].replace("biber version:", "").strip()

soft = [("Python", platform.python_version()), ("SimPy", versao("simpy")), ("NumPy", versao("numpy")),
        ("SciPy", versao("scipy")), ("pandas", versao("pandas")), ("statsmodels", versao("statsmodels")),
        ("Matplotlib", versao("matplotlib"))]
t4 = ["\\begin{tabular}{ll}", "\\toprule", "Componente & Versão \\\\", "\\midrule"]
t4 += [f"{a} & {b} \\\\" for a, b in soft] + ["\\bottomrule", "\\end{tabular}"]
(TABELAS / "tab_ambiente_software.tex").write_text("\n".join(t4) + "\n", encoding="utf-8")
hw = [
    "% Recursos de hardware do ambiente onde o piloto foi executado.",
    "% >>> Se as corridas finais forem executadas em outra máquina, edite estas linhas. <<<",
    f"\\newcommand{{\\HwCPU}}{{{cpu}}}", f"\\newcommand{{\\HwNucleos}}{{{os.cpu_count()}}}",
    f"\\newcommand{{\\HwRAM}}{{{ram_gb}}}", f"\\newcommand{{\\HwSO}}{{{platform.system()} {platform.release()}}}",
    f"\\newcommand{{\\SwTeX}}{{{tex_ver}}}", f"\\newcommand{{\\SwBiber}}{{{biber_ver}}}",
]
(TABELAS / "ambiente_hardware.tex").write_text("\n".join(hw) + "\n", encoding="utf-8")

# ------------------------------------------------------------------ 8) macros numéricos
M("PilotoRho", br(rho, 2))
M("PilotoMedia", br(x.mean(), 3))
M("PilotoDp", br(dp, 3))
M("PilotoCv", br(100 * dp / x.mean(), 1))
M("PilotoAssim", br(stats.skew(x, bias=False), 2))
M("PilotoShapW", br(sw.statistic, 3))
M("PilotoShapP", pval(sw.pvalue))
M("PilotoTeo", br(teo, 2))
M("PilotoErro", br(100 * (x.mean() / teo - 1), 1))
M("PilotoIcInf", br(ic[0], 2))
M("PilotoIcSup", br(ic[1], 2))
M("PilotoZeroEmp", br(100 * p0, 1))
M("PilotoZeroTeo", br(100 * (1 - rho), 0))
M("PilotoLagum", br(r_acf[1], 2))
M("PilotoLagdez", br(r_acf[10], 2))
M("PilotoPnoventa", br(p99, 1))
M("PilotoMaximo", br(w.max(), 1))
M("PilotoTempo", br(tempo, 2))
M("PilotoLnAssim", br(assim_ln, 2))
M("PilotoLnShapP", pval(sw_ln.pvalue))
M("RepLagum", br(r_rep, 2))
M("RepLagumP", br(p_rep, 2))
M("WelchIniMedia", br(ini.mean(), 2))
M("WelchPlatoMedia", br(plato.mean(), 2))
M("WelchDifPct", br(100 * dif_ini.mean() / plato.mean(), 1))
M("WelchResidDif", br(resid.mean(), 2))
M("WelchResidEp", br(resid.std(ddof=1) / np.sqrt(R_WELCH), 2))
M("CompCurtoCv", br(comp[N_CURTO]["cv"], 1))
M("CompCurtoMeia", br(comp[N_CURTO]["meia"], 1))
M("CompLongoCv", br(comp[N_CLIENTES]["cv"], 1))
M("CompLongoMeia", br(comp[N_CLIENTES]["meia"], 1))
M("TempoTotalEstimado", br(R * 8 * tempo, 0))
M("NClientes", f"{N_CLIENTES:,}".replace(",", "."))
M("NCurto", f"{N_CURTO:,}".replace(",", "."))
M("Aquecimento", f"{AQUECIMENTO:,}".replace(",", "."))
M("RPiloto", str(R_PILOTO))
M("RWelch", str(R_WELCH))
M("NWelch", f"{N_WELCH:,}".replace(",", "."))
M("JanelaWelch", str(JANELA_WELCH))

(TABELAS / "numeros.tex").write_text(
    "% Gerado automaticamente por codigo/piloto_eda.py -- não editar à mão.\n"
    + "\n".join(f"\\newcommand{{\\{k}}}{{{v}\\xspace}}" for k, v in macros.items()) + "\n", encoding="utf-8")

print(f"média={x.mean():.3f} dp={dp:.3f} cv={100*dp/x.mean():.1f}% teo={teo:.3f} erro={100*(x.mean()/teo-1):.1f}% "
      f"skew={stats.skew(x, bias=False):.2f} SW p={sw.pvalue:.3f} tempo/corrida={tempo:.2f}s")
print(f"ln: skew={assim_ln:.2f} SW p={sw_ln.pvalue:.3f}")
print(f"réplicas lag1 r={r_rep:.3f} p={p_rep:.3f} | acf clientes lag1={r_acf[1]:.2f} lag10={r_acf[10]:.2f}")
print(f"welch ini500={ini.mean():.2f} platô={plato.mean():.2f} dif={dif_ini.mean():.2f} | resíduo={resid.mean():.3f}±{resid.std(ddof=1)/np.sqrt(R_WELCH):.3f}")
print("comprimento:", {k: {a: round(b, 2) for a, b in v.items()} for k, v in comp.items()})
